from django.db.models import Count, Q, Exists, OuterRef
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin, IsAdminOrReadOnly
from .filters import EventFilter
from .models import Event, Registration
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    RegistrationResponseSerializer,
    ParticipantSerializer,
)
from .services import register_for_event, unregister_from_event, close_event


class EventListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = EventFilter
    search_fields = ["title", "description"]
    ordering_fields = ["start_at", "created_at"]
    ordering = ["start_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Event.objects.all().annotate(
            annotated_registered_count=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.ACTIVE),
                distinct=True,
            )
        )
        if user.is_authenticated:
            user_reg_subquery = Registration.objects.filter(
                event=OuterRef("pk"),
                user=user,
                status=Registration.Status.ACTIVE,
            )
            qs = qs.annotate(user_is_registered=Exists(user_reg_subquery))
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EventCreateUpdateSerializer
        return EventListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        output_serializer = EventDetailSerializer(event, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Event.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = EventDetailSerializer(instance, context=self.get_serializer_context())
        return Response(output_serializer.data)


class EventCloseView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=["Events"],
        summary="Tadbirni yopish (Admin)",
        description="Tadbirni yopadi, shundan so'ng hech kim unga yozila olmaydi.",
        request=None,
        responses={
            200: inline_serializer(
                name="EventCloseResponse",
                fields={
                    "detail": serializers.CharField(),
                    "status": serializers.CharField(),
                },
            )
        },
    )
    def post(self, request, pk):
        event = close_event(pk)
        return Response(
            {"detail": "Tadbir muvaffaqiyatli yopildi.", "status": event.status},
            status=status.HTTP_200_OK,
        )


class EventParticipantsView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = ParticipantSerializer
    queryset = Registration.objects.none()

    @extend_schema(
        tags=["Events"],
        summary="Qatnashuvchilar ro'yxati (Admin)",
        description="Tadbirning barcha faol qatnashuvchilari ro'yxatini qaytaradi.",
    )
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Registration.objects.none()
        event_id = self.kwargs.get("pk")
        return (
            Registration.objects.filter(
                event_id=event_id,
                status=Registration.Status.ACTIVE,
            )
            .select_related("user")
            .order_by("created_at")
        )


class EventRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Registrations"],
        summary="Tadbirga yozilish",
        description="Foydalanuvchini tadbirga yozadi. Cheklangan joylar, status va boshlanish vaqti tekshiriladi.",
        request=None,
        responses={
            201: RegistrationResponseSerializer,
            400: OpenApiResponse(description="Biznes qoida xatosi (event_full, event_closed, already_registered va h.k.)"),
        },
    )
    def post(self, request, pk):
        registration = register_for_event(request.user, pk)
        serializer = RegistrationResponseSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventUnregisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Registrations"],
        summary="Tadbirdan chiqish",
        description="Foydalanuvchini tadbirdan chiqaradi (status=cancelled). Boshlangan tadbirdan chiqib bo'lmaydi.",
        request=None,
        responses={
            200: inline_serializer(
                name="EventUnregisterResponse",
                fields={"detail": serializers.CharField()},
            ),
            400: OpenApiResponse(description="Biznes qoida xatosi (event_started, not_registered)."),
        },
    )
    def post(self, request, pk):
        unregister_from_event(request.user, pk)
        return Response(
            {"detail": "Tadbirdan muvaffaqiyatli chiqildi."},
            status=status.HTTP_200_OK,
        )


class MyRegistrationsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegistrationResponseSerializer
    queryset = Registration.objects.none()

    @extend_schema(
        tags=["Registrations"],
        summary="O'zim yozilgan tadbirlar",
        description="Foydalanuvchi o'zi yozilgan tadbirlar ro'yxatini ko'radi. ?status=active yoki ?status=cancelled bo'yicha filtrlanadi.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Registration holati: active yoki cancelled",
                required=False,
                type=str,
            ),
        ],
    )
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Registration.objects.none()
        qs = (
            Registration.objects.filter(user=self.request.user)
            .select_related("event")
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        if status_param in [Registration.Status.ACTIVE, Registration.Status.CANCELLED]:
            qs = qs.filter(status=status_param)
        return qs
