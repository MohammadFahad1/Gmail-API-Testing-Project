from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.conf import settings
import base64
from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

# Generate OAuth Url
def get_auth_url():
    print(settings.GOOGLE_REDIRECT_URI)
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    print("AUTH URL:", auth_url)  # 👈 ADD THIS

    return auth_url

# Exchange code for tokens
def get_tokens_from_code(authorization_response):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

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
