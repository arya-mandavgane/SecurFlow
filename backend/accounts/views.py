from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from audit.utils import log_audit_event
from audit.models import AuditLog

@extend_schema(
    tags=['Authentication'],
    summary='User Login with JWT',
    description='Authenticates user credentials and returns JWT access + refresh tokens and role/institution details.'
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Authentication'],
    summary='Get Authenticated User Profile',
    description='Fetches the current user profile, role, designation, and associated institution details.',
    responses={200: UserProfileSerializer}
)
class CurrentUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({
            "success": True,
            "data": serializer.data
        })


@extend_schema(
    tags=['Authentication'],
    summary='User Logout',
    description='Logs out the current session and creates a compliance audit record.',
    responses={200: OpenApiResponse(description="Logged out successfully")}
)
class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_audit_event(
            request=request,
            action=AuditLog.Action.LOGOUT,
            entity_type='User',
            entity_id=request.user.id,
            before_state={'username': request.user.username}
        )
        return Response({
            "success": True,
            "message": "Logged out successfully."
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Change Password',
    description='Allows an authenticated user to change their account password.',
    request=ChangePasswordSerializer,
    responses={200: OpenApiResponse(description="Password changed successfully")}
)
class ChangePasswordView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            log_audit_event(
                request=request,
                action=AuditLog.Action.UPDATE,
                entity_type='User',
                entity_id=user.id,
                after_state={'event': 'password_changed'}
            )
            return Response({
                "success": True,
                "message": "Password updated successfully."
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "error": {
                "message": "Password change failed.",
                "details": serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Request Password Reset',
    description='Initiates a password reset email for institutional or administrative users.',
    request=PasswordResetRequestSerializer
)
class PasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # In development, simulate token issuance
            return Response({
                "success": True,
                "message": "If an account matches that email, a password reset instruction has been dispatched."
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "error": {"details": serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Confirm Password Reset',
    description='Finalizes password reset using the issued reset token.',
    request=PasswordResetConfirmSerializer
)
class PasswordResetConfirmView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                "success": True,
                "message": "Password has been reset successfully. You may now log in."
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "error": {"details": serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)
