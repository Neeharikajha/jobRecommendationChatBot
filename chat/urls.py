from django.urls import path
from .views import UploadView, ChatView

urlpatterns = [
    path("upload/", UploadView.as_view()),
    path("chat/", ChatView.as_view()),
]