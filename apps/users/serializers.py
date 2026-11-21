import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User representation serializer."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
        )
        read_only_fields = ("id", "email", "role")


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
            "role",
        )
        read_only_fields = ("id", "role")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu email manzili allaqachon ro'yxatdan o'tgan.")
        return value.lower()

    def validate_phone_number(self, value):
        if value:
            if not re.match(r"^\+998\d{9}$", value):
                raise serializers.ValidationError(
                    "Telefon raqami '+998XXXXXXXXX' formatida bo'lishi kerak."
                )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Parollar bir-biriga mos kelmadi."}
            )

        validate_password(password)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        # Ensure role cannot be set via registration endpoint
        validated_data["role"] = User.Role.USER
        return User.objects.create_user(**validated_data)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user's profile."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
        )
        read_only_fields = ("id", "email", "role")

    def validate_phone_number(self, value):
        if value:
            if not re.match(r"^\+998\d{9}$", value):
                raise serializers.ValidationError(
                    "Telefon raqami '+998XXXXXXXXX' formatida bo'lishi kerak."
                )
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT login serializer with extra user info in token if needed."""

    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)
        # Return access and refresh as per README 9.2
        return data
