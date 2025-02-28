from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile_img",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password2",
            "email",
        ]

    def validate(self, attrs):
        # Validate password match
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        # Validate email uniqueness explicitly
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already in use."})

        # Validate username uniqueness explicitly
        username = attrs.get("username")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already taken."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes user data in the response
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to response
        data["user"] = UserSerializer(self.user).data

        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ["profile_image"]

    def update(self, instance, validated_data):
        # Handle profile image separately
        profile_image = validated_data.pop("profile_image", None)

        if profile_image:
            # The actual upload happens in the view
            # Here we just expect to receive the URL
            instance.profile_img = profile_image

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
