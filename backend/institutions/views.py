from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Institution
from .serializers import InstitutionSerializer
from accounts.models import User
from accounts.permissions import IsOwnerInstitutionOrOfficial, IsAdminUserRole
from audit.utils import log_audit_event
from audit.models import AuditLog

@extend_schema_view(
    list=extend_schema(
        tags=['Institutions'],
        summary='List Technical Institutions',
        description='Fetches institutions. Admins & Officials see all; Institution users only see their own.',
        parameters=[
            OpenApiParameter('state', str, description='Filter by Indian State'),
            OpenApiParameter('search', str, description='Search by Name or AICTE Institute ID'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Institutions'],
        summary='Get Institution Details',
        description='Retrieves complete details of an institution including active FDR summary.'
    ),
    create=extend_schema(
        tags=['Institutions'],
        summary='Create Institution (Admin Only)',
        description='Registers a new technical institution under AICTE portal.'
    ),
    update=extend_schema(
        tags=['Institutions'],
        summary='Update Institution',
        description='Updates institutional master information.'
    ),
    destroy=extend_schema(
        tags=['Institutions'],
        summary='Delete Institution (Admin Only)',
        description='Removes an institution record.'
    )
)
class InstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'aicte_id', 'city', 'state']
    ordering_fields = ['name', 'state', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        queryset = Institution.objects.all()

        # RBAC: Institution users are scoped to their own institution only
        if user.role == User.Role.INSTITUTION:
            if user.institution_id:
                return queryset.filter(id=user.institution_id)
            return queryset.none()

        # Officials & Admins can filter by state
        state = self.request.query_params.get('state')
        if state:
            queryset = queryset.filter(state__iexact=state)

        return queryset

    def perform_create(self, serializer):
        # Only admin can create institutions
        if not (self.request.user.role == User.Role.ADMIN or self.request.user.is_superuser):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only portal administrators can register new institutions.")
        
        instance = serializer.save()
        log_audit_event(
            request=self.request,
            action=AuditLog.Action.CREATE,
            entity_type='Institution',
            entity_id=instance.id,
            after_state={'name': instance.name, 'aicte_id': instance.aicte_id}
        )

    def perform_update(self, serializer):
        before = {
            'name': serializer.instance.name,
            'contact_person': serializer.instance.contact_person,
            'email': serializer.instance.email,
            'phone': serializer.instance.phone
        }
        instance = serializer.save()
        log_audit_event(
            request=self.request,
            action=AuditLog.Action.UPDATE,
            entity_type='Institution',
            entity_id=instance.id,
            before_state=before,
            after_state={'name': instance.name, 'email': instance.email}
        )

    def perform_destroy(self, instance):
        if not (self.request.user.role == User.Role.ADMIN or self.request.user.is_superuser):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only portal administrators can delete institutions.")
        
        inst_id = instance.id
        inst_name = instance.name
        instance.delete()
        log_audit_event(
            request=self.request,
            action=AuditLog.Action.DELETE,
            entity_type='Institution',
            entity_id=inst_id,
            before_state={'name': inst_name}
        )

    @extend_schema(
        tags=['Institutions'],
        summary='Get My Institution Profile',
        description='Directly retrieves the institutional profile for the currently logged-in institution user.'
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        if not request.user.institution:
            return Response({
                "success": False,
                "error": {"message": "Current user has no associated institution record."}
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(request.user.institution)
        return Response({
            "success": True,
            "data": serializer.data
        })

    @extend_schema(
        tags=['Institutions'],
        summary='Get Complete Institution FDR History & Document Repository',
        description='Fetches all historical FDRs, active deposit totals, and document repository for a specific institution.'
    )
    @action(detail=True, methods=['get'], url_path='fdrs', permission_classes=[permissions.IsAuthenticated, IsOwnerInstitutionOrOfficial])
    def fdr_history(self, request, pk=None):
        institution = self.get_object()
        from fdrs.models import FDR, FDRDocument
        from fdrs.serializers import FDRDetailSerializer, FDRDocumentSerializer
        from django.db.models import Sum

        fdrs = FDR.objects.filter(institution=institution).select_related('parent_fdr').prefetch_related('documents', 'verification_records').order_by('-created_at')
        total_value = fdrs.aggregate(sum=Sum('amount'))['sum'] or 0
        active_value = fdrs.filter(status__in=[FDR.Status.ACTIVE, FDR.Status.VERIFIED]).aggregate(sum=Sum('amount'))['sum'] or 0

        documents = FDRDocument.objects.filter(fdr__institution=institution).select_related('uploaded_by').order_by('-upload_timestamp')

        fdr_serializer = FDRDetailSerializer(fdrs, many=True, context={'request': request})
        doc_serializer = FDRDocumentSerializer(documents, many=True, context={'request': request})

        return Response({
            "success": True,
            "data": {
                "institution": self.get_serializer(institution).data,
                "summary": {
                    "total_fdrs": fdrs.count(),
                    "total_pledged_value": float(total_value),
                    "active_value": float(active_value),
                    "document_count": documents.count()
                },
                "fdrs": fdr_serializer.data,
                "documents": doc_serializer.data
            }
        })
