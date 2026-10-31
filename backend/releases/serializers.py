from rest_framework import serializers
from .models import ReleaseRequest
from fdrs.models import FDR
from fdrs.serializers import FDRDetailSerializer


class ReleaseRequestListSerializer(serializers.ModelSerializer):
    fdr_number = serializers.CharField(source='fdr.fdr_number', read_only=True)
    institution_id = serializers.IntegerField(source='fdr.institution_id', read_only=True)
    institution_name = serializers.CharField(source='fdr.institution.name', read_only=True)
    institution_aicte_id = serializers.CharField(source='fdr.institution.aicte_id', read_only=True)
    bank_name = serializers.CharField(source='fdr.bank_name', read_only=True)
    amount = serializers.DecimalField(source='fdr.amount', max_digits=14, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)

    class Meta:
        model = ReleaseRequest
        fields = [
            'id', 'fdr', 'fdr_number', 'institution_id', 'institution_name',
            'institution_aicte_id', 'bank_name', 'amount', 'reason', 'status',
            'status_display', 'requested_by_name', 'official_remarks',
            'refund_order_number', 'decision_date', 'created_at'
        ]


class ReleaseRequestDetailSerializer(serializers.ModelSerializer):
    fdr_details = FDRDetailSerializer(source='fdr', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    download_order_url = serializers.SerializerMethodField()

    class Meta:
        model = ReleaseRequest
        fields = [
            'id', 'fdr', 'fdr_details', 'status', 'status_display',
            'reason', 'requested_by', 'requested_by_name',
            'official_remarks', 'decided_by', 'decided_by_name',
            'decision_date', 'refund_order_number', 'download_order_url',
            'created_at', 'updated_at'
        ]

    def get_download_order_url(self, obj):
        if obj.status in [ReleaseRequest.Status.APPROVED, ReleaseRequest.Status.RELEASED]:
            request = self.context.get('request')
            rel_url = f"/api/releases/{obj.id}/download-letter/"
            if request:
                return request.build_absolute_uri(rel_url)
            return rel_url
        return None


class ReleaseRequestCreateSerializer(serializers.Serializer):
    fdr_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True, min_length=10, help_text="Detailed justification for release")


class ReleaseRequestDecisionSerializer(serializers.Serializer):
    class Action(serializers.ChoiceField):
        pass

    action = serializers.ChoiceField(
        choices=[
            ('UNDER_REVIEW', 'Move to Under Review'),
            ('APPROVED', 'Approve Release Request'),
            ('REJECTED', 'Reject Release Request'),
            ('MORE_INFO_NEEDED', 'Request More Info / Clarification'),
            ('RELEASED', 'Mark as Discharged / Released')
        ],
        required=True
    )
    official_remarks = serializers.CharField(required=True, min_length=5)
    refund_order_number = serializers.CharField(required=False, allow_blank=True)
    checklist = serializers.DictField(required=False, default=dict)
