from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from institutions.models import Institution
from audit.utils import log_audit_event
from audit.models import AuditLog

User = get_user_model()

class InstitutionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'aicte_id', 'state', 'city']


class UserProfileSerializer(serializers.ModelSerializer):
    institution = InstitutionSummarySerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'institution', 'phone_number',
            'designation', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'role', 'role_display', 'institution', 'created_at']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['institution_id'] = user.institution_id if user.institution else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Attach comprehensive user profile to auth response
        data['user'] = UserProfileSerializer(user).data

        # Log login audit event
        request = self.context.get('request')
        log_audit_event(
            request=request,
            action=AuditLog.Action.LOGIN,
            entity_type='User',
            entity_id=user.id,
            after_state={'username': user.username, 'role': user.role},
            actor=user
        )

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is not correct."})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as old password."})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
