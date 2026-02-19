from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect, get_object_or_404
from .services import *
from .models import GmailToken, GmailAccount
from rest_framework.permissions import IsAuthenticated
from googleapiclient.discovery import build # Ensure this is imported
from django.utils import timezone

class GmailAuthView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        auth_url = get_auth_url()
        return redirect(auth_url)

class GmailCallbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Handle "Access Denied" or Cancelled login from Google
        if 'error' in request.GET:
            return Response(
                {"error": f"Google Access Denied: {request.GET.get('error')}"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            credentials = get_tokens_from_code(request.build_absolute_uri())
            
            # 2. Get user's Gmail email
            service = build("gmail", "v1", credentials=credentials)
            profile = service.users().getProfile(userId="me").execute()
            gmail_email = profile.get("emailAddress")

            # 3. Save to database
            GmailAccount.objects.update_or_create(
                user=request.user,
                defaults={
                    "email": gmail_email,
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    # Ensure the expiry datetime is timezone-aware
                    "token_expiry": timezone.make_aware(credentials.expiry) if timezone.is_naive(credentials.expiry) else credentials.expiry,
                }
            )
            return Response({"message": f"Successfully connected {gmail_email}"})
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FetchEmailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 4. Handle "DoesNotExist" gracefully
        try:
            gmail_account = GmailAccount.objects.get(user=request.user)
        except GmailAccount.DoesNotExist:
            return Response(
                {"error": "No Gmail account linked. Please visit /api/gmail/login/ first."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        service = get_gmail_service(gmail_account)
        results = service.users().messages().list(userId="me", maxResults=5).execute()
        messages = results.get("messages", [])

        email_list = []
        for msg in messages:
            message = service.users().messages().get(userId="me", id=msg["id"]).execute()
            email_list.append({
                "id": message["id"],
                "snippet": message["snippet"]
            })

        return Response(email_list)

class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Get the account object, not just the token string
        gmail_account = get_object_or_404(GmailAccount, user=request.user)

        to = request.data.get("to")
        subject = request.data.get("subject")
        body = request.data.get("body")

        # 2. Pass the WHOLE account object to your service
        send_email(gmail_account, to, subject, body)

        return Response({"message": "Email sent successfully"})
