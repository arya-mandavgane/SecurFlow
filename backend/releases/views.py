import datetime
from django.http import HttpResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import ReleaseRequest
from .serializers import (
    ReleaseRequestListSerializer,
    ReleaseRequestDetailSerializer,
    ReleaseRequestCreateSerializer,
    ReleaseRequestDecisionSerializer
)
from .pdf_generator import generate_release_order_pdf
from fdrs.models import FDR
from notifications.models import Notification
from accounts.models import User
from accounts.permissions import IsOwnerInstitutionOrOfficial, CanVerifyFDR
from audit.utils import log_audit_event
from audit.models import AuditLog


@extend_schema_view(
    list=extend_schema(
        tags=['Release / Refund Workflow'],
        summary='List Release Requests',
        description='Lists security deposit release and refund requests with status tracking.'
    ),
    retrieve=extend_schema(
        tags=['Release / Refund Workflow'],
        summary='Get Release Request Details',
        description='Retrieves complete details of a release request including FDR parameters and official decision.'
    )
)
class ReleaseRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['fdr__fdr_number', 'fdr__institution__name', 'fdr__institution__aicte_id', 'refund_order_number']
    ordering_fields = ['created_at', 'status', 'decision_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReleaseRequestListSerializer
        elif self.action == 'create':
            return ReleaseRequestCreateSerializer
        return ReleaseRequestDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ReleaseRequest.objects.select_related(
            'fdr', 'fdr__institution', 'requested_by', 'decided_by'
        )

        if user.role == User.Role.INSTITUTION:
            if user.institution_id:
                return queryset.filter(fdr__institution_id=user.institution_id)
            return queryset.none()

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())

        return queryset

    @extend_schema(
        tags=['Release / Refund Workflow'],
        summary='Submit New Release / Refund Request',
        description='Institution raises a lien release request for an eligible verified or active FDR deposit.',
        request=ReleaseRequestCreateSerializer,
        responses={201: ReleaseRequestDetailSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = ReleaseRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            fdr = FDR.objects.select_related('institution').get(id=data['fdr_id'])
        except FDR.DoesNotExist:
            raise ValidationError({"fdr_id": "Specified FDR deposit does not exist."})

        user = request.user
        if user.role == User.Role.INSTITUTION and fdr.institution_id != user.institution_id:
            raise PermissionDenied("You can only request releases for deposits belonging to your institution.")

        # Eligibility Validation: ONLY ACTIVE or VERIFIED FDRs can be released
        eligible_statuses = [FDR.Status.ACTIVE, FDR.Status.VERIFIED]
        if fdr.status not in eligible_statuses:
            raise ValidationError({
                "fdr_id": f"FDR #{fdr.fdr_number} is in '{fdr.get_status_display()}' status and is not eligible for release. Only ACTIVE or VERIFIED deposits can be released."
            })

        # Check if already has an open release request
        existing_request = ReleaseRequest.objects.filter(
            fdr=fdr,
            status__in=[
                ReleaseRequest.Status.REQUESTED,
                ReleaseRequest.Status.UNDER_REVIEW,
                ReleaseRequest.Status.APPROVED,
                ReleaseRequest.Status.MORE_INFO_NEEDED
            ]
        ).exists()
        if existing_request:
            raise ValidationError({
                "fdr_id": f"An active release request is already open for FDR #{fdr.fdr_number}."
            })

        release_req = ReleaseRequest.objects.create(
            fdr=fdr,
            requested_by=user,
            reason=data['reason'],
            status=ReleaseRequest.Status.REQUESTED
        )

        # Transition FDR status
        fdr_prev_status = fdr.status
        fdr.status = FDR.Status.RELEASE_REQUESTED
        fdr.save(update_fields=['status', 'updated_at'])

        # Notify institution & officials
        Notification.objects.create(
            institution=fdr.institution,
            fdr=fdr,
            title=f"Release Request Raised for FDR #{fdr.fdr_number}",
            message=f"Lien release request REL-REQ-{release_req.id:04d} for FDR #{fdr.fdr_number} (₹{float(fdr.amount):,.2f}) has been logged for regional scrutiny.",
            notification_type=Notification.Type.RELEASE_UPDATE,
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT
        )

        log_audit_event(
            request=request,
            action=AuditLog.Action.CREATE,
            entity_type='ReleaseRequest',
            entity_id=release_req.id,
            after_state={
                'fdr_id': fdr.id,
                'fdr_number': fdr.fdr_number,
                'reason': release_req.reason,
                'fdr_status_before': fdr_prev_status,
                'fdr_status_after': fdr.status
            }
        )

        detail_serializer = ReleaseRequestDetailSerializer(release_req, context={'request': request})
        return Response({
            "success": True,
            "message": f"Release request #{release_req.id} submitted successfully.",
            "data": detail_serializer.data
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Release / Refund Workflow'],
        summary='Official Release Evaluation Decision',
        description='AICTE officials evaluate release request, execute compliance checklist, and record decision.',
        request=ReleaseRequestDecisionSerializer,
        responses={200: ReleaseRequestDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='decision', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def decision(self, request, pk=None):
        release_req = self.get_object()
        serializer = ReleaseRequestDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_action = data['action']
        remarks = data['official_remarks']
        prev_status = release_req.status
        fdr = release_req.fdr

        # State Transition Rules
        invalid_transitions = {
            ReleaseRequest.Status.RELEASED: ['REQUESTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'MORE_INFO_NEEDED'],
            ReleaseRequest.Status.REJECTED: ['APPROVED', 'RELEASED'],
        }
        if prev_status in invalid_transitions and target_action in invalid_transitions[prev_status]:
            raise ValidationError(f"Invalid transition from '{prev_status}' to '{target_action}'.")

        now = timezone.now()
        release_req.official_remarks = remarks
        release_req.decided_by = request.user
        release_req.decision_date = now

        if target_action == 'APPROVED':
            release_req.status = ReleaseRequest.Status.APPROVED
            if not release_req.refund_order_number:
                order_num = data.get('refund_order_number') or f"AICTE/RO/REL/{now.year}/{release_req.id:05d}"
                release_req.refund_order_number = order_num
            notif_msg = f"Release request for FDR #{fdr.fdr_number} of INR {float(fdr.amount):,.2f} has been APPROVED by AICTE. Release Order #{release_req.refund_order_number} is available for download."

        elif target_action == 'RELEASED':
            release_req.status = ReleaseRequest.Status.RELEASED
            if not release_req.refund_order_number:
                release_req.refund_order_number = f"AICTE/RO/REL/{now.year}/{release_req.id:05d}"
            # Synchronize FDR status to RELEASED
            fdr.status = FDR.Status.RELEASED
            fdr.lien_marked_aicte = False
            fdr.save(update_fields=['status', 'lien_marked_aicte', 'updated_at'])
            notif_msg = f"Lien on FDR #{fdr.fdr_number} has been officially discharged and marked RELEASED. Order Ref: {release_req.refund_order_number}."

        elif target_action == 'REJECTED':
            release_req.status = ReleaseRequest.Status.REJECTED
            # Revert FDR to ACTIVE
            fdr.status = FDR.Status.ACTIVE
            fdr.save(update_fields=['status', 'updated_at'])
            notif_msg = f"Release request for FDR #{fdr.fdr_number} was REJECTED by AICTE. Reason: {remarks}"

        elif target_action == 'MORE_INFO_NEEDED':
            release_req.status = ReleaseRequest.Status.MORE_INFO_NEEDED
            notif_msg = f"Additional information required for release of FDR #{fdr.fdr_number}. Official Remarks: {remarks}"

        else: # UNDER_REVIEW
            release_req.status = ReleaseRequest.Status.UNDER_REVIEW
            notif_msg = f"Release request for FDR #{fdr.fdr_number} is currently under regional committee scrutiny."

        release_req.save()

        # Send notification to institution
        Notification.objects.create(
            institution=fdr.institution,
            fdr=fdr,
            title=f"Release Request Status: {release_req.get_status_display()}",
            message=notif_msg,
            notification_type=Notification.Type.RELEASE_UPDATE,
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT
        )

        log_audit_event(
            request=request,
            action=AuditLog.Action.STATUS_CHANGE,
            entity_type='ReleaseRequest',
            entity_id=release_req.id,
            before_state={'status': prev_status},
            after_state={
                'status': release_req.status,
                'action': target_action,
                'remarks': remarks,
                'refund_order_number': release_req.refund_order_number,
                'checklist': data.get('checklist', {})
            }
        )

        detail_serializer = ReleaseRequestDetailSerializer(release_req, context={'request': request})
        return Response({
            "success": True,
            "message": f"Release request updated to {release_req.get_status_display()}.",
            "data": detail_serializer.data
        })

    @extend_schema(
        tags=['Release / Refund Workflow'],
        summary='Download Official Release Order PDF Letter',
        description='Generates and streams the formal AICTE Release Order / Refund Letter PDF.'
    )
    @action(detail=True, methods=['get'], url_path='download-letter')
    def download_letter(self, request, pk=None):
        release_req = self.get_object()

        if release_req.status not in [ReleaseRequest.Status.APPROVED, ReleaseRequest.Status.RELEASED]:
            raise ValidationError(
                f"Release order is not available for request in '{release_req.get_status_display()}' status. Release order is only generated after approval."
            )

        pdf_bytes = generate_release_order_pdf(release_req)
        order_num = release_req.refund_order_number or f"AICTE_REL_{release_req.id}"
        filename = f"AICTE_Release_Order_{order_num.replace('/', '_')}.pdf"

        log_audit_event(
            request=request,
            action=AuditLog.Action.EXPORT,
            entity_type='ReleaseRequest',
            entity_id=release_req.id,
            after_state={'event': 'download_release_order_pdf', 'filename': filename}
        )

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @extend_schema(
        tags=['Release / Refund Workflow'],
        summary='Institution Resubmit / Provide Clarification for Release',
        description='Allows institutions to respond when additional information is requested.'
    )
    @action(detail=True, methods=['post'], url_path='resubmit-info')
    def resubmit_info(self, request, pk=None):
        release_req = self.get_object()
        user = request.user

        if user.role == User.Role.INSTITUTION and release_req.fdr.institution_id != user.institution_id:
            raise PermissionDenied("You can only respond for your institution's release requests.")

        if release_req.status != ReleaseRequest.Status.MORE_INFO_NEEDED:
            raise ValidationError("Response can only be provided when status is 'More Info Needed'.")

        additional_info = request.data.get('additional_info', '').strip()
        if not additional_info:
            raise ValidationError({"additional_info": "Please provide clarification information."})

        release_req.reason = f"{release_req.reason}\n\n[Institution Clarification {datetime.date.today()}]: {additional_info}"
        release_req.status = ReleaseRequest.Status.UNDER_REVIEW
        release_req.save(update_fields=['reason', 'status', 'updated_at'])

        log_audit_event(
            request=request,
            action=AuditLog.Action.UPDATE,
            entity_type='ReleaseRequest',
            entity_id=release_req.id,
            after_state={'status': release_req.status, 'clarification_provided': additional_info}
        )

        detail_serializer = ReleaseRequestDetailSerializer(release_req, context={'request': request})
        return Response({
            "success": True,
            "message": "Clarification submitted. Release request moved back to Under Review.",
            "data": detail_serializer.data
        })
