from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from .services import *
from .models import GmailToken

class GmailAuthView(APIView):

    def get(self, request):
        auth_url = get_auth_url()
        return redirect(auth_url)

class GmailCallbackView(APIView):

    def get(self, request):

        credentials = get_tokens_from_code(
            request.build_absolute_uri()
        )

        GmailToken.objects.update_or_create(
            user=request.user,
            defaults={
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry
            }
        )

        return Response({"message": "Gmail connected successfully"})


class FetchEmailsView(APIView):

    def get(self, request):
        token = GmailToken.objects.get(user=request.user)
        emails = fetch_emails(token)
        return Response(emails)


class SendEmailView(APIView):

    def post(self, request):
        token = GmailToken.objects.get(user=request.user)

        to = request.data.get("to")
        subject = request.data.get("subject")
        body = request.data.get("body")

        send_email(token, to, subject, body)

        return Response({"message": "Email sent successfully"})
