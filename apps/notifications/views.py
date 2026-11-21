import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class TelegramLinkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Telegram"],
        summary="Botni bog'lash uchun havola olish",
        description="Foydalanuvchi uchun unikal token yaratadi va t.me bot havolasini qaytaradi.",
        request=None,
        responses={
            200: inline_serializer(
                name="TelegramLinkResponse",
                fields={"link": serializers.CharField()},
            )
        },
    )
    def post(self, request):
        user = request.user
        token = secrets.token_urlsafe(16)
        user.telegram_link_token = token
        user.save(update_fields=["telegram_link_token"])

        bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "EventlyBot")
        deep_link = f"https://t.me/{bot_username}?start={token}"
        return Response({"link": deep_link}, status=status.HTTP_200_OK)


class TelegramConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Telegram"],
        summary="Telegram hisobini tasdiqlash va bog'lash (Faqat Bot uchun)",
        description="Bot ushbu endpointga X-Bot-Secret headeri bilan token va chat_id yuboradi.",
        request=inline_serializer(
            name="TelegramConfirmRequest",
            fields={
                "token": serializers.CharField(),
                "chat_id": serializers.IntegerField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="TelegramConfirmResponse",
                fields={"detail": serializers.CharField()},
            ),
            400: OpenApiResponse(description="Token yaroqsiz yoki eskirgan."),
            403: OpenApiResponse(description="Bot maxfiy kaliti noto'g'ri."),
        },
    )
    def post(self, request):
        bot_secret_header = request.headers.get("X-Bot-Secret")
        expected_secret = getattr(settings, "BOT_API_SECRET", "")

        if not expected_secret or bot_secret_header != expected_secret:
            return Response(
                {"detail": "Yaroqsiz bot maxfiy kaliti.", "code": "forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = request.data.get("token")
        chat_id = request.data.get("chat_id")

        if not token or not chat_id:
            return Response(
                {"detail": "token va chat_id maydonlari majburiy.", "code": "bad_request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(telegram_link_token=token).first()
        if not user:
            return Response(
                {"detail": "Yaroqsiz yoki eskirgan token.", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If another user had this chat_id, clear it
        User.objects.filter(telegram_chat_id=chat_id).exclude(id=user.id).update(
            telegram_chat_id=None
        )

        user.telegram_chat_id = chat_id
        user.telegram_link_token = None
        user.save(update_fields=["telegram_chat_id", "telegram_link_token"])

        return Response(
            {"detail": "Hisobingiz muvaffaqiyatli bog'landi!"},
            status=status.HTTP_200_OK,
        )
