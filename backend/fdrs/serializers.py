from django.db import models
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import FDR, FDRDocument
from verification.models import VerificationRecord
from institutions.serializers import InstitutionSerializer
from institutions.models import Institution
import datetime
import decimal

class FDRDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = FDRDocument
        fields = [
            'id', 'file', 'file_name', 'file_type', 'file_type_display',
            'uploaded_by', 'uploaded_by_name', 'checksum', 'file_size',
            'mime_type', 'upload_timestamp', 'download_url'
        ]
        read_only_fields = ['id', 'checksum', 'file_size', 'mime_type', 'upload_timestamp', 'download_url']

    @extend_schema_field(str)
    def get_download_url(self, obj) -> str:
        request = self.context.get('request')
        relative_url = f"/api/fdrs/{obj.fdr_id}/documents/{obj.id}/download/"
        if request:
            return request.build_absolute_uri(relative_url)
        return relative_url


class FDRDocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FDRDocument
        fields = ['file', 'file_type']


class VerificationRecordSerializer(serializers.ModelSerializer):
    official_name = serializers.CharField(source='official.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = VerificationRecord
        fields = [
            'id', 'official', 'official_name', 'status', 'status_display',
            'remarks', 'mismatches', 'is_automated_draft', 'timestamp'
        ]
        read_only_fields = ['id', 'official', 'official_name', 'status_display', 'timestamp']


class FDRListSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    institution_aicte_id = serializers.CharField(source='institution.aicte_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_count = serializers.IntegerField(source='documents.count', read_only=True)

    class Meta:
        model = FDR
        fields = [
            'id', 'fdr_number', 'institution', 'institution_name', 'institution_aicte_id',
            'bank_name', 'branch', 'amount', 'interest_rate', 'issue_date', 'maturity_date',
            'lien_marked_aicte', 'purpose_approval_cycle', 'status', 'status_display',
            'document_count', 'created_at'
        ]


class FDRDetailSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents = FDRDocumentSerializer(many=True, read_only=True)
    verification_records = VerificationRecordSerializer(many=True, read_only=True)
    parent_fdr_number = serializers.CharField(source='parent_fdr.fdr_number', read_only=True)

    class Meta:
        model = FDR
        fields = [
            'id', 'fdr_number', 'institution', 'bank_name', 'branch',
            'amount', 'interest_rate', 'issue_date', 'maturity_date',
            'lien_marked_aicte', 'purpose_approval_cycle', 'status', 'status_display',
            'extracted_data', 'parent_fdr', 'parent_fdr_number', 'remarks',
            'documents', 'verification_records', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status_display', 'created_at', 'updated_at']


class FDRCreateUpdateSerializer(serializers.ModelSerializer):
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = FDR
        fields = [
            'id', 'fdr_number', 'institution', 'bank_name', 'branch',
            'amount', 'interest_rate', 'issue_date', 'maturity_date',
            'lien_marked_aicte', 'purpose_approval_cycle', 'remarks'
        ]
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value <= decimal.Decimal('0.00'):
            raise serializers.ValidationError("FDR amount must be greater than zero.")
        return value

    def validate(self, attrs):
        issue_date = attrs.get('issue_date', getattr(self.instance, 'issue_date', None))
        maturity_date = attrs.get('maturity_date', getattr(self.instance, 'maturity_date', None))

        if issue_date and maturity_date:
            if maturity_date <= issue_date:
                raise serializers.ValidationError({"maturity_date": "Maturity date must be strictly after the issue date."})

        # Ensure lien is marked in favour of AICTE for compliance
        lien = attrs.get('lien_marked_aicte', getattr(self.instance, 'lien_marked_aicte', False))
        if not lien:
            # We allow submission but will require official attention
            pass

        return attrs


class FDRVerificationActionSerializer(serializers.Serializer):
    class Action(models.TextChoices):
        APPROVE = 'APPROVE', 'Approve / Verified'
        REJECT = 'REJECT', 'Reject Submission'
        REQUEST_CLARIFICATION = 'REQUEST_CLARIFICATION', 'Request Clarification from Institution'

    action = serializers.ChoiceField(choices=Action.choices, required=True)
    remarks = serializers.CharField(required=True, min_length=5, help_text="Official remarks or justification")
    mismatches = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Flagged mismatches between OCR and submitted form data"
    )
    field_overrides = serializers.DictField(
        required=False,
        default=dict,
        help_text="Dictionary of field values manually overridden or confirmed by official during verification"
    )
