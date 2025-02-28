from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    ProfileUpdateSerializer,
)
from django.conf import settings
import boto3
import uuid
import os

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Get the refresh token from request
            refresh_token = request.data.get("refresh")

            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response(
                {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_active=True)


@action(
    detail=False, methods=["put", "patch"], parser_classes=[MultiPartParser, FormParser]
)
def profile(self, request):
    user = request.user

    # Handle profile image upload
    if "profile_image" in request.FILES:
        image_file = request.FILES["profile_image"]

        try:
            # Generate unique filename
            ext = image_file.name.split(".")[-1]
            filename = f"profile/{user.id}/{uuid.uuid4()}.{ext}"

            # Get default storage (MediaStorage)
            from django.core.files.storage import default_storage

            # Save the file directly to R2
            file_path = default_storage.save(filename, image_file)

            # Get the URL (this will use the Worker URL due to our override)
            image_url = default_storage.url(file_path)

            # Save URL to user model
            user.profile_img = image_url
            user.save(update_fields=["profile_img"])

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
