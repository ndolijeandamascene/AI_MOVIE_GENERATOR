"""
YouTube API Service for AI Movie Generator
Phase 2 Feature: Auto-upload to YouTube via OAuth integration
"""

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from django.conf import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

def upload_video_to_youtube(video_path, title, description, tags=None, category_id="1", user=None):
    """
    Upload a compiled video to YouTube securely using the Google API Python Client.
    Integrates with django-allauth to fetch the multi-tenant authenticated Google
    SocialToken for the user, bypassing the global token.json requirement.
    """
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    api_service_name = "youtube"
    api_version = "v3"
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")
        
    credentials = None
    
    # Check for allauth SocialToken
    if user:
        try:
            from allauth.socialaccount.models import SocialToken
            token_obj = SocialToken.objects.filter(account__user=user, app__provider='google').first()
            if token_obj:
                app = token_obj.app
                credentials = Credentials(
                    token=token_obj.token,
                    refresh_token=token_obj.token_secret,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=app.client_id,
                    client_secret=app.secret,
                    scopes=SCOPES
                )
        except Exception as e:
            print(f"Failed to fetch SocialToken: {e}")

    # Fallback to local token.json
    if not credentials:
        token_file = os.path.join(settings.BASE_DIR, "token.json")
        client_secrets_file = os.path.join(settings.BASE_DIR, "client_secrets.json")
        if os.path.exists(token_file):
            credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
        else:
            raise Exception("No Youtube authorization found. Please login via Google or provide token.json.")

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            # Note: in a production app we would update the SocialToken object here!
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    tags = tags or ["AI Movie", "Generated"]
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": category_id,
            "description": description,
            "title": title,
            "tags": tags
          },
          "status": {
            "privacyStatus": "private"  # Uploaded as private by default
          }
        },
        media_body=MediaFileUpload(video_path, resumable=True)
    )
    
    response = request.execute()
    return response.get('id')

def fetch_youtube_channel_metadata(user):
    """
    Fetch the YouTube channel name connected to a user's google SocialAccount.
    Used during initial signup/login signals to track their active channel.
    """
    from allauth.socialaccount.models import SocialToken
    try:
        token_obj = SocialToken.objects.filter(account__user=user, app__provider='google').first()
        if not token_obj:
            return None
            
        app = token_obj.app
        credentials = Credentials(
            token=token_obj.token,
            refresh_token=token_obj.token_secret,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=app.client_id,
            client_secret=app.secret,
            scopes=SCOPES
        )
        
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        request = youtube.channels().list(part="snippet", mine=True)
        response = request.execute()
        
        if response.get("items"):
            channel = response["items"][0]
            return {
                "channel_id": channel["id"],
                "title": channel["snippet"]["title"]
            }
    except Exception as e:
        print(f"Metadata fetch failed: {e}")
        
    return None
