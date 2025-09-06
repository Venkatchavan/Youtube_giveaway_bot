"""
YouTube Data API v3 integration for live chat monitoring.
"""
import re
import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import GoogleAuthError
from oauth import YouTubeOAuth
from models import Participant


class YouTubeAPI:
    """Handles YouTube Data API v3 operations for live chat monitoring."""
    
    def __init__(self, oauth_handler: YouTubeOAuth):
        """
        Initialize YouTube API client.
        
        Args:
            oauth_handler: Configured OAuth handler
        """
        self.oauth_handler = oauth_handler
        self.youtube = None
        self.live_chat_id = None
        self.next_page_token = None
        self.polling_interval = 3  # seconds
        self.last_poll_time = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            credentials = self.oauth_handler.get_credentials()
            if not credentials:
                return False
            
            self.youtube = build('youtube', 'v3', credentials=credentials)
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def extract_video_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL or return ID if already provided.
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            Video ID if valid, None otherwise
        """
        # If it's already a video ID (11 characters, alphanumeric + _ -)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        # Extract from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/live/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    def get_live_chat_id(self, video_id: str) -> Tuple[bool, str]:
        """
        Get live chat ID for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (success, live_chat_id_or_error_message)
        """
        if not self.youtube:
            return False, "Not authenticated"
        
        try:
            # Get video details
            video_response = self.youtube.videos().list(
                part='liveStreamingDetails',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return False, "Video not found"
            
            video = video_response['items'][0]
            
            if 'liveStreamingDetails' not in video:
                return False, "Video is not a live stream"
            
            live_details = video['liveStreamingDetails']
            
            if 'activeLiveChatId' not in live_details:
                return False, "Live chat is not available for this stream"
            
            self.live_chat_id = live_details['activeLiveChatId']
            return True, self.live_chat_id
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            reason = error_details.get('reason', 'Unknown error')
            
            if e.resp.status == 403:
                return False, f"Access denied: {reason}"
            elif e.resp.status == 404:
                return False, "Video not found"
            else:
                return False, f"API error: {reason}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def fetch_live_chat_messages(self) -> Tuple[bool, List[Dict], str]:
        """
        Fetch new live chat messages.
        
        Returns:
            Tuple of (success, messages_list, error_message)
        """
        if not self.youtube or not self.live_chat_id:
            return False, [], "Not properly initialized"
        
        try:
            # Respect polling interval
            current_time = time.time()
            if self.last_poll_time and (current_time - self.last_poll_time) < self.polling_interval:
                return True, [], "Polling too frequent"
            
            # Fetch messages
            request = self.youtube.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part='snippet,authorDetails',
                pageToken=self.next_page_token
            )
            
            response = request.execute()
            
            # Update polling info
            self.next_page_token = response.get('nextPageToken')
            self.polling_interval = response.get('pollingIntervalMillis', 3000) // 1000
            self.last_poll_time = current_time
            
            # Extract messages
            messages = []
            for item in response.get('items', []):
                snippet = item['snippet']
                author = item['authorDetails']
                
                # Skip system messages and deleted messages
                if snippet['type'] != 'textMessageEvent':
                    continue
                
                message_data = {
                    'id': item['id'],
                    'username': author['displayName'],
                    'message': snippet['displayMessage'],
                    'timestamp': snippet['publishedAt'],
                    'author_channel_id': author.get('channelId'),
                    'is_verified': author.get('isVerified', False),
                    'is_chat_owner': author.get('isChatOwner', False),
                    'is_chat_moderator': author.get('isChatModerator', False),
                    'is_chat_sponsor': author.get('isChatSponsor', False)
                }
                messages.append(message_data)
            
            return True, messages, ""
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            reason = error_details.get('reason', 'Unknown error')
            
            if e.resp.status == 403:
                if 'quota' in reason.lower():
                    return False, [], f"API quota exceeded: {reason}"
                else:
                    return False, [], f"Access denied: {reason}"
            elif e.resp.status == 404:
                return False, [], "Live chat no longer available"
            else:
                return False, [], f"API error: {reason}"
        except Exception as e:
            return False, [], f"Unexpected error: {str(e)}"
    
    def process_chat_messages(self, messages: List[Dict], 
                            participants: Dict[str, Participant]) -> int:
        """
        Process chat messages and update participants dictionary.
        
        Args:
            messages: List of message dictionaries from API
            participants: Dictionary to update with new participants
            
        Returns:
            Number of new messages processed
        """
        new_messages = 0
        
        for message_data in messages:
            username = message_data['username']
            message_text = message_data['message']
            
            # Normalize username for deduplication (case-insensitive)
            username_key = username.lower()
            
            # Create participant if doesn't exist
            if username_key not in participants:
                participants[username_key] = Participant(
                    username=username,  # Keep original case
                    first_seen=datetime.now()
                )
            
            # Add message
            participants[username_key].add_message(message_text)
            new_messages += 1
        
        return new_messages
    
    def is_authenticated(self) -> bool:
        """Check if API is authenticated and ready."""
        return self.youtube is not None
    
    def get_polling_interval(self) -> int:
        """Get current polling interval in seconds."""
        return self.polling_interval
    
    def reset_chat_session(self) -> None:
        """Reset the chat session (clear tokens and chat ID)."""
        self.live_chat_id = None
        self.next_page_token = None
        self.last_poll_time = None
    
    def test_api_connection(self) -> Tuple[bool, str]:
        """
        Test the API connection by making a simple request.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.youtube:
            return False, "Not authenticated"
        
        try:
            # Simple test request - get channel info
            response = self.youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if response['items']:
                channel_name = response['items'][0]['snippet']['title']
                return True, f"Connected as: {channel_name}"
            else:
                return False, "No channel found for authenticated user"
                
        except HttpError as e:
            return False, f"API test failed: {e}"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
