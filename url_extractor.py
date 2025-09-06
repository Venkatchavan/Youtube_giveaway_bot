"""
URL-based data extraction for YouTube videos without API access.
This module provides functionality to work with YouTube URLs directly.
"""
import re
import requests
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from models import Participant


class YouTubeURLExtractor:
    """Handles YouTube URL processing without API requirements."""
    
    def __init__(self):
        """Initialize the URL extractor."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
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
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_info(self, video_id: str) -> Tuple[bool, Dict]:
        """
        Get basic video information without API.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (success, video_info_dict)
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}"}
            
            html_content = response.text
            
            # Extract basic info from HTML
            info = {
                "video_id": video_id,
                "url": url,
                "title": self._extract_title(html_content),
                "channel": self._extract_channel(html_content),
                "is_live": self._check_if_live(html_content),
                "has_chat": self._check_has_chat(html_content)
            }
            
            return True, info
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def _extract_title(self, html_content: str) -> str:
        """Extract video title from HTML."""
        patterns = [
            r'<title>([^<]+)</title>',
            r'"title":"([^"]+)"',
            r'<meta property="og:title" content="([^"]*)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                title = match.group(1)
                # Clean up title
                title = title.replace(' - YouTube', '').strip()
                if title:
                    return title
        
        return "Unknown Title"
    
    def _extract_channel(self, html_content: str) -> str:
        """Extract channel name from HTML."""
        patterns = [
            r'"ownerChannelName":"([^"]+)"',
            r'"author":"([^"]+)"',
            r'<meta property="og:video:tag" content="([^"]*)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                channel = match.group(1)
                if channel and channel != "YouTube":
                    return channel
        
        return "Unknown Channel"
    
    def _check_if_live(self, html_content: str) -> bool:
        """Check if video is currently live."""
        live_indicators = [
            '"isLiveContent":true',
            '"isLive":true',
            'LIVE</span>',
            'live-stream',
            '"broadcastStatus":"LIVE"'
        ]
        
        return any(indicator in html_content for indicator in live_indicators)
    
    def _check_has_chat(self, html_content: str) -> bool:
        """Check if video has chat enabled."""
        chat_indicators = [
            'live_chat',
            'liveChatRenderer',
            'chatFrame',
            '"hasLiveChat":true'
        ]
        
        return any(indicator in html_content for indicator in chat_indicators)
    
    def generate_demo_participants(self, video_info: Dict, count: int = 20) -> Dict[str, Participant]:
        """
        Generate demo participants for URL-only mode.
        This simulates what would be fetched from live chat.
        
        Args:
            video_info: Video information dict
            count: Number of demo participants to generate
            
        Returns:
            Dictionary of demo participants
        """
        demo_usernames = [
            "ChatFan2024", "StreamViewer", "GiveawayHunter", "LiveWatcher",
            "YouTubeFan", "StreamLover", "ChatMaster", "ViewerPro",
            "LiveChatUser", "StreamSupporter", "YouTubeViewer", "ChatBuddy",
            "StreamingFan", "LiveViewer", "ChatExpert", "StreamWatcher",
            "YouTubeExplorer", "LiveStreamFan", "ChatEnthusiast", "ViewerElite",
            "StreamAddict", "ChatChampion", "LiveBroadcastFan", "StreamingPro",
            "YouTubeRegular", "ChatStar", "LiveContentFan", "StreamFollower"
        ]
        
        demo_messages = [
            "Great stream!", "Love this content!", "Keep it up!",
            "Amazing video!", "This is awesome!", "Thanks for streaming!",
            "Best channel ever!", "Loving the content!", "Great work!",
            "This is so cool!", "Fantastic stream!", "Really enjoying this!",
            "Awesome content!", "Love watching this!", "Great job!",
            "This is amazing!", "Best stream ever!", "Really good content!",
            "Love this channel!", "Great video!", "This is fun!",
            "Enjoying the stream!", "Really cool!", "Love it!",
            "This is great!", "Amazing work!", "Best content!"
        ]
        
        giveaway_messages = [
            "I want to win!", "Count me in!", "Pick me!", "Hope I win!",
            "Entering the giveaway!", "This is exciting!", "I'm participating!",
            "Thanks for the giveaway!", "Fingers crossed!", "Let's go!",
            "I'm in!", "Hope to win something!", "Giveaway time!",
            "Really want to win!", "Participating!", "This is awesome!",
            "Count me in for the giveaway!", "Hoping to be chosen!",
            "Giveaway entry!", "Want to participate!", "Let me win!"
        ]
        
        participants = {}
        
        # Use a subset of demo usernames
        selected_usernames = demo_usernames[:count]
        
        for i, username in enumerate(selected_usernames):
            username_key = username.lower()
            participant = Participant(
                username=username,
                first_seen=datetime.now()
            )
            
            # Generate 1-5 messages per participant
            import random
            random.seed(42 + i)  # Consistent randomness
            num_messages = random.randint(1, 5)
            
            for j in range(num_messages):
                if j == 0 and random.random() < 0.7:  # 70% chance of giveaway message
                    message = random.choice(giveaway_messages)
                else:
                    message = random.choice(demo_messages)
                
                participant.add_message(message)
            
            participants[username_key] = participant
        
        return participants
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate if a URL is a valid YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not url or not url.strip():
            return False, "URL cannot be empty"
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return False, "Invalid YouTube URL format"
        
        # Try to fetch video info
        success, info = self.get_video_info(video_id)
        if not success:
            return False, f"Cannot access video: {info.get('error', 'Unknown error')}"
        
        return True, f"Valid YouTube video: {info.get('title', 'Unknown')}"
    
    def get_supported_url_formats(self) -> List[str]:
        """Get list of supported URL formats."""
        return [
            "https://www.youtube.com/watch?v=VIDEO_ID",
            "https://youtu.be/VIDEO_ID",
            "https://www.youtube.com/live/VIDEO_ID",
            "https://www.youtube.com/embed/VIDEO_ID",
            "https://www.youtube.com/shorts/VIDEO_ID",
            "VIDEO_ID (11 character ID only)"
        ]
