from django.urls import path
from .views import TelegramLinkView, TelegramConfirmView

urlpatterns = [
    path("link/", TelegramLinkView.as_view(), name="telegram-link"),
    path("confirm/", TelegramConfirmView.as_view(), name="telegram-confirm"),
]
