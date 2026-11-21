from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Event, Registration


class EventShortSerializer(serializers.ModelSerializer):
    """Short event representation embedded in registrations."""

    class Meta:
        model = Event
        fields = ("id", "title", "start_at", "location")


class EventListSerializer(serializers.ModelSerializer):
    available_seats = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "event_type",
            "location",
            "start_at",
            "capacity",
            "available_seats",
            "status",
            "is_registered",
        )

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_available_seats(self, obj):
        return obj.get_available_seats()

    @extend_schema_field(serializers.BooleanField())
    def get_is_registered(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        if hasattr(obj, "user_is_registered"):
            return bool(obj.user_is_registered)
        return obj.registrations.filter(user=user, status=Registration.Status.ACTIVE).exists()


class EventDetailSerializer(serializers.ModelSerializer):
    registered_count = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    is_finished = serializers.BooleanField(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "event_type",
            "location",
            "start_at",
            "end_at",
            "capacity",
            "registered_count",
            "available_seats",
            "status",
            "is_finished",
            "is_registered",
            "created_at",
        )

    @extend_schema_field(serializers.IntegerField())
    def get_registered_count(self, obj):
        return obj.get_registered_count()

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_available_seats(self, obj):
        return obj.get_available_seats()

    @extend_schema_field(serializers.BooleanField())
    def get_is_registered(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        return obj.registrations.filter(user=user, status=Registration.Status.ACTIVE).exists()


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "description",
            "event_type",
            "location",
            "start_at",
            "end_at",
            "capacity",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at")

    def validate_capacity(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Joylar soni kamida 1 bo'lishi kerak.")
        return value

    def validate(self, attrs):
        start_at = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end_at = attrs.get("end_at", getattr(self.instance, "end_at", None))
        capacity = attrs.get("capacity", getattr(self.instance, "capacity", None))

        # BR-8: Yangi tadbir o'tgan sanaga yaratilmaydi
        if not self.instance and start_at and start_at <= timezone.now():
            raise serializers.ValidationError(
                {"start_at": "Yangi tadbir o'tgan sanaga yaratilmaydi."}
            )

        # BR-7: end_at har doim start_at dan keyin bo'lishi kerak
        if start_at and end_at and end_at <= start_at:
            raise serializers.ValidationError(
                {"end_at": "Tugash vaqti boshlanish vaqtidan keyin bo‘lishi kerak."}
            )

        # BR-9: capacity ni hozirgi faol qatnashuvchilar sonidan kamaytirib bo'lmaydi
        if self.instance and capacity is not None:
            active_count = self.instance.registrations.filter(
                status=Registration.Status.ACTIVE
            ).count()
            if capacity < active_count:
                raise serializers.ValidationError(
                    {
                        "capacity": "Joylar soni hozirgi faol qatnashuvchilar sonidan kam bo‘lishi mumkin emas."
                    }
                )

        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user if self.context.get("request") else None
        validated_data["created_by"] = user
        return super().create(validated_data)


class RegistrationResponseSerializer(serializers.ModelSerializer):
    event = EventShortSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ("id", "event", "status", "created_at")


class ParticipantSerializer(serializers.Serializer):
    registration_id = serializers.IntegerField(source="id")
    user_id = serializers.IntegerField(source="user.id")
    full_name = serializers.CharField(source="user.full_name")
    email = serializers.EmailField(source="user.email")
    phone_number = serializers.CharField(source="user.phone_number")
    registered_at = serializers.DateTimeField(source="created_at")
