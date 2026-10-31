from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Institution
from fdrs.models import FDR
from django.db.models import Sum

class InstitutionSerializer(serializers.ModelSerializer):
    fdr_count = serializers.SerializerMethodField()
    total_pledged_amount = serializers.SerializerMethodField()

    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'aicte_id', 'state', 'city', 'address',
            'contact_person', 'email', 'phone', 'created_at', 'updated_at',
            'fdr_count', 'total_pledged_amount'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(int)
    def get_fdr_count(self, obj) -> int:
        return obj.fdrs.count()

    @extend_schema_field(float)
    def get_total_pledged_amount(self, obj) -> float:
        total = obj.fdrs.exclude(status__in=[FDR.Status.REJECTED, FDR.Status.RELEASED]).aggregate(
            total=Sum('amount')
        )['total']
        return float(total) if total else 0.0
