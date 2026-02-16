from django.urls import path
from .views import *

urlpatterns = [
    path("auth/", GmailAuthView.as_view()),
    path("callback/", GmailCallbackView.as_view()),
    path("emails/", FetchEmailsView.as_view()),
    path("send/", SendEmailView.as_view()),
]
