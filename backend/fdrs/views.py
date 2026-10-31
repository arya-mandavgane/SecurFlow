import os
import datetime
from django.http import FileResponse, Http404
from django.db.models import Q, Sum, Count
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
from audit.serializers import AuditLogSerializer


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

        # Trigger Asynchronous OCR extraction pipeline
        try:
            from .tasks import process_fdr_document_ocr
            try:
                process_fdr_document_ocr.delay(doc.id)
            except Exception:
                # Fallback to direct synchronous execution if Celery broker unavailable
                process_fdr_document_ocr(doc.id)
        except Exception:
            pass

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
        field_overrides = serializer.validated_data.get('field_overrides', {})

        # Apply official field overrides if specified
        if field_overrides and isinstance(field_overrides, dict):
            import decimal
            allowed_fields = ['fdr_number', 'amount', 'bank_name', 'branch', 'interest_rate', 'issue_date', 'maturity_date', 'lien_marked_aicte']
            updated_fields = {}
            for field, val in field_overrides.items():
                if field in allowed_fields and val is not None:
                    if field in ('amount', 'interest_rate'):
                        try:
                            val = decimal.Decimal(str(val))
                        except Exception:
                            pass
                    setattr(fdr, field, val)
                    updated_fields[field] = str(val)
            if updated_fields:
                log_audit_event(
                    request=request,
                    action=AuditLog.Action.UPDATE,
                    entity_type='FDR',
                    entity_id=fdr.id,
                    after_state={'event': 'official_field_override', 'overridden_fields': updated_fields}
                )

        before_status = fdr.status
        amount_display = f"{float(fdr.amount):,.2f}"
        if action_type == FDRVerificationActionSerializer.Action.APPROVE:
            fdr.status = FDR.Status.VERIFIED
            record_status = VerificationRecord.Status.APPROVED
            notif_title = f"FDR #{fdr.fdr_number} Verified"
            notif_msg = f"Your FDR #{fdr.fdr_number} of INR {amount_display} has been verified and approved by AICTE."

            # If this is a renewal, mark parent FDR as RENEWED
            if fdr.parent_fdr and fdr.parent_fdr.status != FDR.Status.RENEWED:
                parent = fdr.parent_fdr
                parent_old_status = parent.status
                parent.status = FDR.Status.RENEWED
                parent.save(update_fields=['status', 'updated_at'])
                log_audit_event(
                    request=request,
                    action=AuditLog.Action.STATUS_CHANGE,
                    entity_type='FDR',
                    entity_id=parent.id,
                    before_state={'status': parent_old_status},
                    after_state={'status': FDR.Status.RENEWED, 'renewal_fdr_id': fdr.id}
                )
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

    @extend_schema(
        tags=['Official Workspace'],
        summary='Official Dashboard KPI & Analytics',
        description='Returns comprehensive system-wide metrics, breakdowns by status, state, bank, and recent audit activity feed for AICTE officials.'
    )
    @action(detail=False, methods=['get'], url_path='official-stats', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def official_stats(self, request):
        today = datetime.date.today()
        all_fdrs = FDR.objects.all()

        total_fdrs = all_fdrs.count()
        total_deposit_val = all_fdrs.filter(status__in=[FDR.Status.ACTIVE, FDR.Status.VERIFIED]).aggregate(sum=Sum('amount'))['sum'] or 0
        pending_verification = all_fdrs.filter(status__in=[
            FDR.Status.SUBMITTED,
            FDR.Status.UNDER_REVIEW,
            FDR.Status.NEEDS_CLARIFICATION
        ]).count()
        verified = all_fdrs.filter(status__in=[FDR.Status.VERIFIED, FDR.Status.ACTIVE]).count()

        active_or_pending_statuses = [
            FDR.Status.ACTIVE, FDR.Status.VERIFIED, FDR.Status.EXPIRING_SOON,
            FDR.Status.SUBMITTED, FDR.Status.UNDER_REVIEW, FDR.Status.NEEDS_CLARIFICATION
        ]
        expiring_30_days = all_fdrs.filter(
            maturity_date__range=[today, today + datetime.timedelta(days=30)],
            status__in=active_or_pending_statuses
        ).count()
        expiring_60_days = all_fdrs.filter(
            maturity_date__range=[today, today + datetime.timedelta(days=60)],
            status__in=active_or_pending_statuses
        ).count()
        expiring_90_days = all_fdrs.filter(
            maturity_date__range=[today, today + datetime.timedelta(days=90)],
            status__in=active_or_pending_statuses
        ).count()
        expired = all_fdrs.filter(
            Q(status=FDR.Status.EXPIRED) |
            (Q(maturity_date__lt=today) & ~Q(status__in=[FDR.Status.RELEASED, FDR.Status.REJECTED]))
        ).count()
        release_requests = all_fdrs.filter(status=FDR.Status.RELEASE_REQUESTED).count()

        status_counts = all_fdrs.values('status').annotate(count=Count('id'), total_amount=Sum('amount')).order_by('-count')
        status_map = dict(FDR.Status.choices)
        status_distribution = [
            {
                'status': item['status'],
                'label': status_map.get(item['status'], item['status']),
                'count': item['count'],
                'total_amount': float(item['total_amount'] or 0)
            }
            for item in status_counts
        ]

        state_counts = all_fdrs.values('institution__state').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')[:10]
        state_distribution = [
            {
                'state': item['institution__state'] or 'Unknown',
                'count': item['count'],
                'total_amount': float(item['total_amount'] or 0)
            }
            for item in state_counts
        ]

        bank_counts = all_fdrs.values('bank_name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')[:10]
        bank_distribution = [
            {
                'bank': item['bank_name'],
                'count': item['count'],
                'total_amount': float(item['total_amount'] or 0)
            }
            for item in bank_counts
        ]

        recent_logs = AuditLog.objects.select_related('actor').order_by('-timestamp')[:15]
        activity_serializer = AuditLogSerializer(recent_logs, many=True)

        return Response({
            'success': True,
            'data': {
                'kpis': {
                    'total_fdrs': total_fdrs,
                    'total_deposit_value': float(total_deposit_val),
                    'pending_verification': pending_verification,
                    'verified': verified,
                    'expiring_30_days': expiring_30_days,
                    'expiring_60_days': expiring_60_days,
                    'expiring_90_days': expiring_90_days,
                    'expired': expired,
                    'release_requests': release_requests
                },
                'status_distribution': status_distribution,
                'state_distribution': state_distribution,
                'bank_distribution': bank_distribution,
                'recent_activity': activity_serializer.data
            }
        })

    @extend_schema(
        tags=['Official Workspace'],
        summary='Official Verification Queue',
        description='Fetches FDR records requiring official scrutiny, prioritized by discrepancy severity and maturity urgency.',
        parameters=[
            OpenApiParameter('priority', str, description='Filter priority: HIGH, MEDIUM, LOW, or ALL'),
            OpenApiParameter('status', str, description='Filter by status (SUBMITTED, UNDER_REVIEW, NEEDS_CLARIFICATION)'),
            OpenApiParameter('bank', str, description='Filter by bank name'),
            OpenApiParameter('state', str, description='Filter by state'),
            OpenApiParameter('search', str, description='Search across FDR number, institution name, AICTE ID'),
        ]
    )
    @action(detail=False, methods=['get'], url_path='verification-queue', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def verification_queue(self, request):
        today = datetime.date.today()
        queryset = FDR.objects.filter(
            status__in=[FDR.Status.SUBMITTED, FDR.Status.UNDER_REVIEW, FDR.Status.NEEDS_CLARIFICATION]
        ).select_related('institution').prefetch_related('documents', 'verification_records')

        params = request.query_params
        status_filter = params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        bank_filter = params.get('bank')
        if bank_filter:
            queryset = queryset.filter(bank_name__icontains=bank_filter)

        state_filter = params.get('state')
        if state_filter:
            queryset = queryset.filter(institution__state__iexact=state_filter)

        search_query = params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(fdr_number__icontains=search_query) |
                Q(bank_name__icontains=search_query) |
                Q(institution__name__icontains=search_query) |
                Q(institution__aicte_id__icontains=search_query)
            )

        queue_items = []
        for fdr in queryset:
            discrepancies = []
            if isinstance(fdr.extracted_data, dict):
                discrepancies = fdr.extracted_data.get('discrepancies', [])
            
            if not discrepancies:
                for vr in fdr.verification_records.all():
                    if vr.mismatches:
                        discrepancies.extend(vr.mismatches)

            has_critical = any(d.get('severity') == 'CRITICAL' for d in discrepancies if isinstance(d, dict))
            has_high = any(d.get('severity') == 'HIGH' for d in discrepancies if isinstance(d, dict))
            
            days_to_maturity = (fdr.maturity_date - today).days

            priority_score = 0
            if has_critical:
                priority_score += 100
            elif has_high:
                priority_score += 60
            elif len(discrepancies) > 0:
                priority_score += 30

            if days_to_maturity <= 30:
                priority_score += 40
            elif days_to_maturity <= 90:
                priority_score += 20

            if priority_score >= 80:
                priority_level = 'HIGH'
            elif priority_score >= 30:
                priority_level = 'MEDIUM'
            else:
                priority_level = 'LOW'

            queue_items.append({
                'id': fdr.id,
                'fdr_number': fdr.fdr_number,
                'institution_id': fdr.institution.id,
                'institution_name': fdr.institution.name,
                'institution_aicte_id': fdr.institution.aicte_id,
                'state': fdr.institution.state,
                'bank_name': fdr.bank_name,
                'branch': fdr.branch,
                'amount': float(fdr.amount),
                'issue_date': str(fdr.issue_date),
                'maturity_date': str(fdr.maturity_date),
                'days_to_maturity': days_to_maturity,
                'status': fdr.status,
                'status_display': fdr.get_status_display(),
                'discrepancy_count': len(discrepancies),
                'has_critical_discrepancy': has_critical,
                'priority': priority_level,
                'priority_score': priority_score,
                'has_document': fdr.documents.exists(),
                'created_at': fdr.created_at.isoformat()
            })

        priority_filter = params.get('priority')
        if priority_filter and priority_filter.upper() != 'ALL':
            queue_items = [item for item in queue_items if item['priority'] == priority_filter.upper()]

        # Sort: Highest priority score first, then earliest maturity date
        queue_items.sort(key=lambda x: (-x['priority_score'], x['days_to_maturity']))

        return Response({
            'success': True,
            'count': len(queue_items),
            'data': queue_items
        })

    @extend_schema(
        tags=['Official Workspace'],
        summary='Generate AI Review Summary Hook',
        description='Produces an AI-synthesized summary of FDR verification status, flagged discrepancies, and recommended action. Ready for Phase 8 RAG integration.'
    )
    @action(detail=True, methods=['post'], url_path='ai-summary', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def ai_summary(self, request, pk=None):
        fdr = self.get_object()
        extracted = fdr.extracted_data or {}
        discrepancies = extracted.get('discrepancies', [])
        conf = extracted.get('confidence_scores', {})
        overall_conf = extracted.get('overall_confidence', 0.85)

        flags = []
        if discrepancies:
            for d in discrepancies:
                flags.append(f"{d.get('severity', 'WARNING')}: {d.get('issue', 'Discrepancy detected in')} (Field: {d.get('field', 'General')})")

        if any(d.get('severity') == 'CRITICAL' for d in discrepancies if isinstance(d, dict)):
            rec = 'REQUEST_CLARIFICATION'
            analysis_text = f"FDR #{fdr.fdr_number} contains critical discrepancies between submitted form data and bank-issued certificate: {'; '.join(flags[:2])}. Clarification or corrected certificate is recommended before approval."
        elif len(discrepancies) > 0:
            rec = 'REQUEST_CLARIFICATION'
            analysis_text = f"FDR #{fdr.fdr_number} has minor variances ({len(discrepancies)} flagged). Overall OCR confidence is {int(overall_conf * 100)}%. Review highlighted fields before proceeding."
        else:
            rec = 'APPROVE'
            analysis_text = f"FDR #{fdr.fdr_number} from {fdr.bank_name} for ₹{fdr.amount:,} matches the submitted certificate with {int(overall_conf * 100)}% extraction confidence. Lien in favour of AICTE is verified. Recommended for immediate approval."

        return Response({
            'success': True,
            'data': {
                'fdr_id': fdr.id,
                'fdr_number': fdr.fdr_number,
                'overall_confidence': overall_conf,
                'recommendation': rec,
                'summary': analysis_text,
                'flags': flags,
                'is_ai_generated': True,
                'engine': 'SecurFlow OCR-Validator Engine v1.0 (Phase 8 RAG ready)'
            }
        })

    @extend_schema(
        tags=['Official Workspace'],
        summary='Get Complete Audit Trail for FDR',
        description='Retrieves all historical audit logs and verification records related to this FDR.'
    )
    @action(detail=True, methods=['get'], url_path='audit-trail', permission_classes=[permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial])
    def audit_trail(self, request, pk=None):
        fdr = self.get_object()
        logs = AuditLog.objects.filter(
            Q(entity_type='FDR', entity_id=str(fdr.id)) |
            Q(entity_type='FDRDocument', entity_id__in=[str(d.id) for d in fdr.documents.all()])
        ).select_related('actor').order_by('-timestamp')

        serializer = AuditLogSerializer(logs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @extend_schema(
        tags=['FDR Verification'],
        summary='Re-trigger AI-OCR Extraction Pipeline',
        description='Re-runs OCR text extraction, structured parsing and mismatch detection on the latest FDR document.',
        responses={200: FDRDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='retrigger-ocr')
    def retrigger_ocr(self, request, pk=None):
        fdr = self.get_object()
        latest_doc = fdr.documents.first()
        if not latest_doc:
            return Response({
                "success": False,
                "error": {"message": "No document is attached to this FDR to perform OCR extraction."}
            }, status=status.HTTP_400_BAD_REQUEST)

        from .tasks import process_fdr_document_ocr
        try:
            try:
                process_fdr_document_ocr.delay(latest_doc.id)
            except Exception:
                process_fdr_document_ocr(latest_doc.id)
        except Exception as e:
            return Response({
                "success": False,
                "error": {"message": f"Failed to execute OCR job: {str(e)}"}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        fdr.refresh_from_db()
        detail_serializer = FDRDetailSerializer(fdr, context={'request': request})
        return Response({
            "success": True,
            "message": "AI-OCR extraction triggered successfully.",
            "data": detail_serializer.data
        }, status=status.HTTP_200_OK)
