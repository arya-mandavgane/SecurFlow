from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import RenewalRecord
from .serializers import RenewalRecordSerializer, RenewalSubmitSerializer
from fdrs.models import FDR
from fdrs.serializers import FDRDetailSerializer
from notifications.models import Notification
from accounts.models import User
from accounts.permissions import IsOwnerInstitutionOrOfficial, CanVerifyFDR
from audit.utils import log_audit_event
from audit.models import AuditLog


@extend_schema_view(
    list=extend_schema(
        tags=['Renewals & Lineage'],
        summary='List Renewal Records',
        description='Lists FDR renewal records. Institutions see their own; Officials see all.'
    ),
    retrieve=extend_schema(
        tags=['Renewals & Lineage'],
        summary='Get Renewal Record',
        description='Retrieves details of an individual renewal linkage.'
    )
)
class RenewalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RenewalRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial]
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = RenewalRecord.objects.select_related('original_fdr', 'new_fdr')

        if user.role == User.Role.INSTITUTION:
            if user.institution_id:
                return queryset.filter(original_fdr__institution_id=user.institution_id)
            return queryset.none()

        inst_id = self.request.query_params.get('institution')
        if inst_id:
            queryset = queryset.filter(original_fdr__institution_id=inst_id)

        return queryset

    @extend_schema(
        tags=['Renewals & Lineage'],
        summary='Submit FDR Renewal or Replacement',
        description='Submits a renewed or replacement FDR linked to an expiring or expired deposit.',
        request=RenewalSubmitSerializer,
        responses={201: RenewalRecordSerializer}
    )
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_renewal(self, request):
        serializer = RenewalSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            original_fdr = FDR.objects.get(id=data['original_fdr_id'])
        except FDR.DoesNotExist:
            raise ValidationError({"original_fdr_id": "Original FDR deposit does not exist."})

        user = request.user
        # Check permissions: institution can only renew their own
        if user.role == User.Role.INSTITUTION and original_fdr.institution_id != user.institution_id:
            raise PermissionDenied("You can only submit renewals for deposits belonging to your institution.")

        purpose = data.get('purpose_approval_cycle') or original_fdr.purpose_approval_cycle

        # Create the new FDR linked to parent
        new_fdr = FDR.objects.create(
            institution=original_fdr.institution,
            fdr_number=data['fdr_number'],
            bank_name=data['bank_name'],
            branch=data['branch'],
            amount=data['amount'],
            interest_rate=data.get('interest_rate'),
            issue_date=data['issue_date'],
            maturity_date=data['maturity_date'],
            lien_marked_aicte=data.get('lien_marked_aicte', True),
            purpose_approval_cycle=purpose,
            status=FDR.Status.SUBMITTED,
            parent_fdr=original_fdr,
            remarks=f"Renewal of FDR #{original_fdr.fdr_number}. Reason: {data.get('reason', 'N/A')}"
        )

        # Create Renewal Record
        record = RenewalRecord.objects.create(
            original_fdr=original_fdr,
            new_fdr=new_fdr,
            renewal_type=data['renewal_type'],
            reason=data.get('reason', ''),
            renewal_date=data['issue_date']
        )

        # Notify officials & institution
        Notification.objects.create(
            institution=original_fdr.institution,
            fdr=new_fdr,
            title=f"Renewal Submitted for FDR #{original_fdr.fdr_number}",
            message=f"Renewal deposit #{new_fdr.fdr_number} (₹{float(new_fdr.amount):,.2f}) submitted successfully and queued for official scrutiny.",
            notification_type=Notification.Type.STATUS_CHANGE,
            channel=Notification.Channel.IN_APP,
            sent_status=Notification.SentStatus.SENT
        )

        log_audit_event(
            request=request,
            action=AuditLog.Action.CREATE,
            entity_type='RenewalRecord',
            entity_id=record.id,
            after_state={
                'original_fdr_id': original_fdr.id,
                'original_fdr_number': original_fdr.fdr_number,
                'new_fdr_id': new_fdr.id,
                'new_fdr_number': new_fdr.fdr_number,
                'renewal_type': record.renewal_type
            }
        )

        return Response({
            "success": True,
            "message": f"Renewal FDR #{new_fdr.fdr_number} submitted and linked to prior deposit.",
            "data": {
                "renewal_record": RenewalRecordSerializer(record).data,
                "new_fdr": FDRDetailSerializer(new_fdr, context={'request': request}).data
            }
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Renewals & Lineage'],
        summary='Get Full Renewal Lineage Chain',
        description='Traces the complete multi-year renewal tree for an FDR, returning all ancestor and descendant deposits in order.'
    )
    @action(detail=True, methods=['get'], url_path='chain')
    def renewal_chain(self, request, pk=None):
        try:
            target_fdr = FDR.objects.select_related('institution', 'parent_fdr').get(id=pk)
        except FDR.DoesNotExist:
            raise ValidationError("Target FDR does not exist.")

        user = request.user
        if user.role == User.Role.INSTITUTION and target_fdr.institution_id != user.institution_id:
            raise PermissionDenied("You do not have access to view this deposit's lineage.")

        # Step 1: Climb up to root ancestor
        root = target_fdr
        while root.parent_fdr is not None:
            root = root.parent_fdr

        # Step 2: Traverse down from root to collect all nodes in lineage
        chain_nodes = []

        def traverse_descendants(node, depth=0):
            # Find renewal record linking this node to its parent if any
            link_record = RenewalRecord.objects.filter(new_fdr=node).first()
            chain_nodes.append({
                'id': node.id,
                'fdr_number': node.fdr_number,
                'bank_name': node.bank_name,
                'branch': node.branch,
                'amount': float(node.amount),
                'issue_date': str(node.issue_date),
                'maturity_date': str(node.maturity_date),
                'status': node.status,
                'status_display': node.get_status_display(),
                'depth': depth,
                'is_current': node.id == target_fdr.id,
                'is_root': node.id == root.id,
                'parent_fdr_id': node.parent_fdr_id,
                'renewal_type': link_record.renewal_type if link_record else None,
                'renewal_type_display': link_record.get_renewal_type_display() if link_record else None,
                'reason': link_record.reason if link_record else None
            })

            # Traverse child renewals
            children = FDR.objects.filter(parent_fdr=node).order_by('issue_date')
            for child in children:
                traverse_descendants(child, depth + 1)

        traverse_descendants(root, 0)

        return Response({
            "success": True,
            "data": {
                "target_fdr_id": target_fdr.id,
                "root_fdr_id": root.id,
                "chain_length": len(chain_nodes),
                "lineage": chain_nodes
            }
        })
