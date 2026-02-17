from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from django.conf import settings


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

def get_auth_url():

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    print("AUTH URL:", auth_url)

    return auth_url



def get_gmail_service(gmail_account):

    creds = Credentials(
        token=gmail_account.access_token,
        refresh_token=gmail_account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    # Auto refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        # Save new access token
        gmail_account.access_token = creds.token
        gmail_account.save()

    service = build("gmail", "v1", credentials=creds)

    return service


# Exchange code for tokens
def get_tokens_from_code(authorization_response):

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials


# Build gmail service from saved tokens
def build_gmail_service(user_token):
    creds = Credentials(
        token=user_token.access_token,
        refresh_token=user_token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    return build('gmail', 'v1', credentials=creds)

# Fetch emails
def fetch_emails(user_token):
    service = build_gmail_service(user_token)

    results = service.users().messages().list(
        userId='me',
        maxResults=10
    ).execute()

    return results

# Send emails
def send_email(user_token, to, subject, body):

    service = build_gmail_service(user_token)

    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()
