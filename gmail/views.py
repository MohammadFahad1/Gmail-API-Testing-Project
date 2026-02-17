from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from .services import *
from .models import GmailToken, GmailAccount
from rest_framework.permissions import IsAuthenticated
from .services import get_gmail_service

class GmailAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        auth_url = get_auth_url()
        return redirect(auth_url)

class GmailCallbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        credentials = get_tokens_from_code(request.build_absolute_uri())

        # Get user's Gmail email
        service = build("gmail", "v1", credentials=credentials)
        profile = service.users().getProfile(userId="me").execute()

        gmail_email = profile.get("emailAddress")

        GmailAccount.objects.update_or_create(
            user=request.user,
            defaults={
                "email": gmail_email,
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry,
            }
        )

        return Response({"message": "Gmail connected successfully"})


class FetchEmailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        gmail_account = GmailAccount.objects.get(user=request.user)
        service = get_gmail_service(gmail_account)

        results = service.users().messages().list(
            userId="me",
            maxResults=5
        ).execute()

        messages = results.get("messages", [])

        email_list = []

        for msg in messages:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"]
            ).execute()

            email_list.append({
                "id": message["id"],
                "snippet": message["snippet"]
            })

        return Response(email_list)


class SendEmailView(APIView):

    def post(self, request):
        token = GmailToken.objects.get(user=request.user)

        to = request.data.get("to")
        subject = request.data.get("subject")
        body = request.data.get("body")

        send_email(token, to, subject, body)

        return Response({"message": "Email sent successfully"})
