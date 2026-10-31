import os
from django.http import FileResponse, Http404
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied, ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import FDR, FDRDocument
from .serializers import (
    FDRListSerializer,
    FDRDetailSerializer,
    FDRCreateUpdateSerializer,
    FDRDocumentSerializer,
    FDRDocumentUploadSerializer,
    FDRVerificationActionSerializer
)
from .validators import validate_and_process_document
from verification.models import VerificationRecord
from notifications.models import Notification
from accounts.models import User
from accounts.permissions import IsOwnerInstitutionOrOfficial, CanVerifyFDR
from audit.utils import log_audit_event
from audit.models import AuditLog


@extend_schema_view(
    list=extend_schema(
        tags=['FDR Management'],
        summary='List FDR Records',
        description='Lists FDR records with role scoping. Institution users see only their deposits; Officials & Admins see all.',
        parameters=[
            OpenApiParameter('status', str, description='Filter by FDR status (e.g. SUBMITTED, ACTIVE, EXPIRING_SOON)'),
            OpenApiParameter('bank', str, description='Filter by bank name (case-insensitive substring)'),
            OpenApiParameter('institution', int, description='Filter by Institution ID (Officials & Admins only)'),
            OpenApiParameter('maturity_from', str, description='Filter maturity date >= YYYY-MM-DD'),
            OpenApiParameter('maturity_to', str, description='Filter maturity date <= YYYY-MM-DD'),
            OpenApiParameter('search', str, description='Search across FDR number, bank name, institution name or AICTE ID'),
        ]
    ),
    retrieve=extend_schema(
        tags=['FDR Management'],
        summary='Retrieve FDR Details',
        description='Fetches complete FDR data including attached documents, verification history, and renewal relations.'
    ),
    create=extend_schema(
        tags=['FDR Management'],
        summary='Submit New FDR Record',
        description='Initiates a new FDR submission under AICTE. Defaults to SUBMITTED state.'
    ),
    update=extend_schema(
        tags=['FDR Management'],
        summary='Update FDR Details',
        description='Updates FDR information before official review or when responding to clarification.'
    ),
    destroy=extend_schema(
        tags=['FDR Management'],
        summary='Delete FDR Record',
        description='Removes an unverified FDR record.'
    )
)
class FDRViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['fdr_number', 'bank_name', 'institution__name', 'institution__aicte_id']
    ordering_fields = ['maturity_date', 'created_at', 'amount', 'fdr_number']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return FDRListSerializer
        elif self.action == 'retrieve':
            return FDRDetailSerializer
        return FDRCreateUpdateSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = FDR.objects.select_related('institution', 'parent_fdr').prefetch_related('documents', 'verification_records')

        # RBAC: Scope Institution users strictly to their own institution's FDRs
        if user.role == User.Role.INSTITUTION:
            if user.institution_id:
                queryset = queryset.filter(institution_id=user.institution_id)
            else:
                return queryset.none()

        # Filtering parameters
        params = self.request.query_params

        status_param = params.get('status')
        if status_param:
            statuses = [s.strip().upper() for s in status_param.split(',')]
            queryset = queryset.filter(status__in=statuses)

        bank = params.get('bank')
        if bank:
            queryset = queryset.filter(bank_name__icontains=bank)

        institution_id = params.get('institution')
        if institution_id and user.role in (User.Role.OFFICIAL, User.Role.ADMIN):
            queryset = queryset.filter(institution_id=institution_id)

        maturity_from = params.get('maturity_from')
        if maturity_from:
            queryset = queryset.filter(maturity_date__gte=maturity_from)

        maturity_to = params.get('maturity_to')
        if maturity_to:
            queryset = queryset.filter(maturity_date__lte=maturity_to)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == User.Role.INSTITUTION:
            if not user.institution:
                raise ValidationError("Institution user is not affiliated with any technical institution.")
            instance = serializer.save(
                institution=user.institution,
                status=FDR.Status.SUBMITTED
            )
        else:
            # Official or Admin creating on behalf of an institution
            if 'institution' not in serializer.validated_data:
                raise ValidationError({"institution": "Institution is required when submitting an FDR."})
            instance = serializer.save(status=FDR.Status.SUBMITTED)

        log_audit_event(
            request=self.request,
            action=AuditLog.Action.CREATE,
            entity_type='FDR',
            entity_id=instance.id,
            after_state={
                'fdr_number': instance.fdr_number,
                'amount': str(instance.amount),
                'bank_name': instance.bank_name,
                'status': instance.status
            }
        )

    def perform_update(self, serializer):
        fdr = self.get_object()
        user = self.request.user

        # Institution users can only update FDRs in SUBMITTED or NEEDS_CLARIFICATION status
        if user.role == User.Role.INSTITUTION:
            if fdr.status not in (FDR.Status.SUBMITTED, FDR.Status.NEEDS_CLARIFICATION):
                raise PermissionDenied("FDR cannot be modified while under official review or already verified.")

        before_state = {
            'amount': str(fdr.amount),
            'status': fdr.status,
            'maturity_date': str(fdr.maturity_date)
        }

        # Resubmitting from clarification transitions status back to UNDER_REVIEW
        extra_fields = {}
        if fdr.status == FDR.Status.NEEDS_CLARIFICATION and user.role == User.Role.INSTITUTION:
            extra_fields['status'] = FDR.Status.UNDER_REVIEW

        instance = serializer.save(**extra_fields)

        log_audit_event(
            request=self.request,
            action=AuditLog.Action.UPDATE,
            entity_type='FDR',
            entity_id=instance.id,
            before_state=before_state,
            after_state={
                'amount': str(instance.amount),
                'status': instance.status,
                'maturity_date': str(instance.maturity_date)
            }
        )

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role == User.Role.INSTITUTION and instance.status != FDR.Status.SUBMITTED:
            raise PermissionDenied("Only pending submissions in SUBMITTED status can be deleted.")

        fdr_id = instance.id
        fdr_num = instance.fdr_number
        instance.delete()

        log_audit_event(
            request=self.request,
            action=AuditLog.Action.DELETE,
            entity_type='FDR',
            entity_id=fdr_id,
            before_state={'fdr_number': fdr_num}
        )

    @extend_schema(
        tags=['FDR Documents'],
        summary='Upload Document for FDR',
        description='Uploads and cryptographically verifies an FDR certificate, bank letter, or renewal advice.',
        request=FDRDocumentUploadSerializer,
        responses={201: FDRDocumentSerializer}
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='documents')
    def upload_document(self, request, pk=None):
        fdr = self.get_object()
        file_obj = request.FILES.get('file')
        file_type = request.data.get('file_type', FDRDocument.DocType.FDR_COPY)

        if not file_obj:
            return Response({
                "success": False,
                "error": {"message": "No file was attached in the 'file' parameter."}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size, extension, MIME, virus scan hook and calculate SHA-256
        val_result = validate_and_process_document(file_obj)

        doc = FDRDocument.objects.create(
            fdr=fdr,
            file=file_obj,
            file_name=file_obj.name,
            file_type=file_type,
            uploaded_by=request.user,
            checksum=val_result['checksum'],
            file_size=val_result['file_size'],
            mime_type=val_result['mime_type']
        )

        log_audit_event(
            request=request,
            action=AuditLog.Action.CREATE,
            entity_type='FDRDocument',
            entity_id=doc.id,
            after_state={
                'file_name': doc.file_name,
                'checksum': doc.checksum,
                'fdr_number': fdr.fdr_number
            }
        )

        serializer = FDRDocumentSerializer(doc, context={'request': request})
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['FDR Documents'],
        summary='Download FDR Document',
        description='Securely serves the document file after validating RBAC permissions.'
    )
    @action(detail=True, methods=['get'], url_path='documents/(?P<doc_id>[^/.]+)/download')
    def download_document(self, request, pk=None, doc_id=None):
        fdr = self.get_object()
        try:
            doc = fdr.documents.get(id=doc_id)
        except FDRDocument.DoesNotExist:
            raise Http404("Document does not exist.")

        if not doc.file or not os.path.exists(doc.file.path):
            return Response({
                "success": False,
                "error": {"message": "Document file is not present on disk storage."}
            }, status=status.HTTP_404_NOT_FOUND)

        log_audit_event(
            request=request,
            action=AuditLog.Action.EXPORT,
            entity_type='FDRDocument',
            entity_id=doc.id,
            after_state={'event': 'document_downloaded', 'file_name': doc.file_name}
        )

        response = FileResponse(doc.file.open('rb'), content_type=doc.mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(doc.file.name)}"'
        return response

    @extend_schema(
        tags=['FDR Verification'],
        summary='Official FDR Verification Action',
        description='Executes verification review (Approve, Reject, or Request Clarification) with remarks.',
        request=FDRVerificationActionSerializer,
        responses={200: FDRDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='verify', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def verify(self, request, pk=None):
        fdr = self.get_object()
        serializer = FDRVerificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        remarks = serializer.validated_data['remarks']
        mismatches = serializer.validated_data.get('mismatches', [])

        before_status = fdr.status
        if action_type == FDRVerificationActionSerializer.Action.APPROVE:
            fdr.status = FDR.Status.VERIFIED
            record_status = VerificationRecord.Status.APPROVED
            notif_title = f"FDR #{fdr.fdr_number} Verified"
            notif_msg = f"Your FDR #{fdr.fdr_number} of INR {fdr.amount:,} has been verified and approved by AICTE."
        elif action_type == FDRVerificationActionSerializer.Action.REJECT:
            fdr.status = FDR.Status.REJECTED
            record_status = VerificationRecord.Status.REJECTED
            notif_title = f"FDR #{fdr.fdr_number} Rejected"
            notif_msg = f"Your FDR #{fdr.fdr_number} was rejected by AICTE. Reason: {remarks}"
        else: # REQUEST_CLARIFICATION
            fdr.status = FDR.Status.NEEDS_CLARIFICATION
            record_status = VerificationRecord.Status.CLARIFICATION_REQUESTED
            notif_title = f"Clarification Requested for FDR #{fdr.fdr_number}"
            notif_msg = f"AICTE officials have requested clarification regarding FDR #{fdr.fdr_number}. Remarks: {remarks}"

        fdr.save()

        # Create Verification Record
        record = VerificationRecord.objects.create(
            fdr=fdr,
            official=request.user,
            status=record_status,
            remarks=remarks,
            mismatches=mismatches,
            is_automated_draft=False
        )

        # Dispatch In-App Notification to Institution
        Notification.objects.create(
            institution=fdr.institution,
            fdr=fdr,
            title=notif_title,
            message=notif_msg,
            notification_type=Notification.Type.STATUS_CHANGE if action_type != 'REQUEST_CLARIFICATION' else Notification.Type.CLARIFICATION,
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT
        )

        # Compliance Audit Logging
        log_audit_event(
            request=request,
            action=AuditLog.Action.VERIFY,
            entity_type='FDR',
            entity_id=fdr.id,
            before_state={'status': before_status},
            after_state={
                'status': fdr.status,
                'action': action_type,
                'remarks': remarks,
                'verification_record_id': record.id
            }
        )

        detail_serializer = FDRDetailSerializer(fdr, context={'request': request})
        return Response({
            "success": True,
            "message": f"FDR state updated to {fdr.get_status_display()}.",
            "data": detail_serializer.data
        }, status=status.HTTP_200_OK)
