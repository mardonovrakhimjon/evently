import django_filters
from django.utils import timezone
from .models import Event


class EventFilter(django_filters.FilterSet):
    upcoming = django_filters.BooleanFilter(method="filter_upcoming")
    event_type = django_filters.ChoiceFilter(choices=Event.EventType.choices)
    status = django_filters.ChoiceFilter(choices=Event.Status.choices)

    class Meta:
        model = Event
        fields = ["event_type", "status", "upcoming"]

    def filter_upcoming(self, queryset, name, value):
        if value:
            return queryset.filter(start_at__gt=timezone.now())
        return queryset
