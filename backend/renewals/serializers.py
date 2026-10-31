import datetime
import decimal
from rest_framework import serializers
from .models import RenewalRecord
from fdrs.models import FDR

class RenewalRecordSerializer(serializers.ModelSerializer):
    original_fdr_number = serializers.CharField(source='original_fdr.fdr_number', read_only=True)
    new_fdr_number = serializers.CharField(source='new_fdr.fdr_number', read_only=True)
    renewal_type_display = serializers.CharField(source='get_renewal_type_display', read_only=True)

    class Meta:
        model = RenewalRecord
        fields = [
            'id', 'original_fdr', 'original_fdr_number',
            'new_fdr', 'new_fdr_number', 'renewal_type',
            'renewal_type_display', 'reason', 'renewal_date', 'created_at'
        ]
        read_only_fields = ['id', 'original_fdr_number', 'new_fdr_number', 'renewal_type_display', 'created_at']


class RenewalSubmitSerializer(serializers.Serializer):
    original_fdr_id = serializers.IntegerField(required=True)
    renewal_type = serializers.ChoiceField(
        choices=RenewalRecord.RenewalType.choices,
        default=RenewalRecord.RenewalType.RENEWAL
    )
    reason = serializers.CharField(required=False, allow_blank=True, default='')
    fdr_number = serializers.CharField(max_length=100, required=True)
    bank_name = serializers.CharField(max_length=150, required=True)
    branch = serializers.CharField(max_length=150, required=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=True)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    issue_date = serializers.DateField(required=True)
    maturity_date = serializers.DateField(required=True)
    lien_marked_aicte = serializers.BooleanField(default=True)
    purpose_approval_cycle = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= decimal.Decimal('0.00'):
            raise serializers.ValidationError("FDR amount must be greater than zero.")
        return value

    def validate(self, attrs):
        if attrs['maturity_date'] <= attrs['issue_date']:
            raise serializers.ValidationError({"maturity_date": "Maturity date must be strictly after the issue date."})
        return attrs
