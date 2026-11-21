from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
)

from .serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
)


@extend_schema(
    tags=["Auth"],
    summary="Yangi foydalanuvchi ro'yxatdan o'tishi",
    description="Email, parol va shaxsiy ma'lumotlar bilan yangi hisob yaratish.",
    request=UserRegisterSerializer,
    responses={
        201: OpenApiResponse(response=UserSerializer, description="Muvaffaqiyatli ro'yxatdan o'tildi."),
        400: OpenApiResponse(description="Validation xatosi."),
    },
)
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = UserSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="Login qilish (JWT token olish)",
    description="Email va parol orqali access va refresh token olish.",
)
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Auth"],
    summary="Access tokenni yangilash",
    description="Mavjud refresh token orqali yangi access token olish.",
)
class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = [permissions.AllowAny]


@extend_schema(
    tags=["Auth"],
    summary="Joriy foydalanuvchi profili",
    description="Login qilgan foydalanuvchining ma'lumotlarini ko'rish yoki tahrirlash.",
)
class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserProfileUpdateSerializer
        return UserSerializer
