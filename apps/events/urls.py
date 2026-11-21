from django.urls import path
from .views import (
    EventListCreateView,
    EventDetailView,
    EventCloseView,
    EventParticipantsView,
    EventRegisterView,
    EventUnregisterView,
    MyRegistrationsView,
)

urlpatterns = [
    # Events CRUD
    path("events/", EventListCreateView.as_view(), name="event-list-create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("events/<int:pk>/close/", EventCloseView.as_view(), name="event-close"),
    path(
        "events/<int:pk>/participants/",
        EventParticipantsView.as_view(),
        name="event-participants",
    ),
    # Event Registration
    path("events/<int:pk>/register/", EventRegisterView.as_view(), name="event-register"),
    path(
        "events/<int:pk>/unregister/",
        EventUnregisterView.as_view(),
        name="event-unregister",
    ),
    # My Registrations
    path("me/registrations/", MyRegistrationsView.as_view(), name="my-registrations"),
]
