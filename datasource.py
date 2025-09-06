"""
Data source management for collecting participants from various sources.
"""
import threading
import time
from typing import Dict, Callable, Optional, Any
from datetime import datetime
from models import Participant
from youtube_api import YouTubeAPI
from file_parser import DataParser
from url_extractor import YouTubeURLExtractor


class DataSourceManager:
    """Manages data collection from live and offline sources."""
    
    def __init__(self):
        """Initialize the data source manager."""
        self.participants: Dict[str, Participant] = {}
        self.youtube_api: Optional[YouTubeAPI] = None
        self.url_extractor = YouTubeURLExtractor()
        self.file_parser = DataParser()
        
        # Live fetching state
        self.is_live_fetching = False
        self.live_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Callbacks for UI updates
        self.on_participants_updated: Optional[Callable] = None
        self.on_status_changed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Statistics
        self.total_messages_fetched = 0
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_errors = 0
    
    def set_callbacks(self, on_participants_updated: Callable = None,
                     on_status_changed: Callable = None,
                     on_error: Callable = None) -> None:
        """
        Set callback functions for UI updates.
        
        Args:
            on_participants_updated: Called when participants are updated
            on_status_changed: Called when status changes
            on_error: Called when an error occurs
        """
        self.on_participants_updated = on_participants_updated
        self.on_status_changed = on_status_changed
        self.on_error = on_error
    
    def set_youtube_api(self, youtube_api: YouTubeAPI) -> None:
        """
        Set the YouTube API instance.
        
        Args:
            youtube_api: Configured YouTube API instance
        """
        self.youtube_api = youtube_api
    
    def import_from_file(self, file_path: str) -> bool:
        """
        Import participants from a file.
        
        Args:
            file_path: Path to the file to import
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            self._notify_status("Importing participants from file...")
            
            # Parse the file
            new_participants = self.file_parser.parse_file(file_path)
            
            if not new_participants:
                self._notify_error("No valid participants found in file")
                return False
            
            # Merge with existing participants
            original_count = len(self.participants)
            for username_key, participant in new_participants.items():
                if username_key in self.participants:
                    # Merge messages from existing participant
                    existing = self.participants[username_key]
                    for message in participant.messages:
                        existing.add_message(message)
                else:
                    # Add new participant
                    self.participants[username_key] = participant
            
            new_count = len(self.participants)
            imported_count = len(new_participants)
            
            self._notify_status(f"Imported {imported_count} participants from file. Total: {new_count}")
            self._notify_participants_updated()
            
            return True
            
        except Exception as e:
            error_msg = f"Error importing file: {str(e)}"
            self._notify_error(error_msg)
            return False
    
    def import_from_url(self, url: str, demo_mode: bool = True) -> bool:
        """
        Import participants from a YouTube URL (URL-only mode).
        
        Args:
            url: YouTube video URL
            demo_mode: If True, generate demo participants; if False, attempt to extract real data
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            self._notify_status("Processing YouTube URL...")
            
            # Validate URL
            is_valid, message = self.url_extractor.validate_url(url)
            if not is_valid:
                self._notify_error(f"Invalid URL: {message}")
                return False
            
            # Get video info
            video_id = self.url_extractor.extract_video_id(url)
            success, video_info = self.url_extractor.get_video_info(video_id)
            
            if not success:
                self._notify_error(f"Cannot access video: {video_info.get('error', 'Unknown error')}")
                return False
            
            self._notify_status(f"Found video: {video_info.get('title', 'Unknown')}")
            
            if demo_mode:
                # Generate demo participants
                new_participants = self.url_extractor.generate_demo_participants(video_info, 25)
                self._notify_status("Generated demo participants for URL-only mode")
            else:
                # In future, could implement actual chat extraction
                # For now, use demo mode
                new_participants = self.url_extractor.generate_demo_participants(video_info, 15)
                self._notify_status("URL-only mode: Generated sample participants")
            
            # Merge with existing participants
            original_count = len(self.participants)
            for username_key, participant in new_participants.items():
                if username_key in self.participants:
                    # Merge messages from existing participant
                    existing = self.participants[username_key]
                    for message in participant.messages:
                        existing.add_message(message)
                else:
                    # Add new participant
                    self.participants[username_key] = participant
            
            new_count = len(self.participants)
            imported_count = len(new_participants)
            
            self._notify_status(f"Imported {imported_count} participants from URL. Total: {new_count}")
            self._notify_participants_updated()
            
            return True
            
        except Exception as e:
            error_msg = f"Error importing from URL: {str(e)}"
            self._notify_error(error_msg)
            return False
    
    def start_live_fetch(self, video_url_or_id: str) -> bool:
        """
        Start live fetching from YouTube chat.
        
        Args:
            video_url_or_id: YouTube video URL or ID
            
        Returns:
            True if started successfully, False otherwise
        """
        if not self.youtube_api:
            self._notify_error("YouTube API not configured")
            return False
        
        if self.is_live_fetching:
            self._notify_error("Live fetching already in progress")
            return False
        
        # Extract video ID and get live chat ID
        video_id = self.youtube_api.extract_video_id(video_url_or_id)
        if not video_id:
            self._notify_error("Invalid YouTube URL or video ID")
            return False
        
        self._notify_status(f"Resolving live chat for video: {video_id}")
        
        success, chat_id_or_error = self.youtube_api.get_live_chat_id(video_id)
        if not success:
            self._notify_error(f"Failed to get live chat: {chat_id_or_error}")
            return False
        
        # Start live fetching thread
        self.stop_event.clear()
        self.is_live_fetching = True
        self.live_thread = threading.Thread(target=self._live_fetch_loop, daemon=True)
        self.live_thread.start()
        
        self._notify_status(f"Started live fetching from chat: {chat_id_or_error}")
        return True
    
    def stop_live_fetch(self) -> None:
        """Stop live fetching."""
        if not self.is_live_fetching:
            return
        
        self._notify_status("Stopping live fetch...")
        self.stop_event.set()
        self.is_live_fetching = False
        
        if self.live_thread and self.live_thread.is_alive():
            self.live_thread.join(timeout=5)
        
        self._notify_status("Live fetch stopped")
    
    def _live_fetch_loop(self) -> None:
        """Main loop for live fetching (runs in separate thread)."""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while not self.stop_event.is_set():
            try:
                # Fetch new messages
                success, messages, error_msg = self.youtube_api.fetch_live_chat_messages()
                
                if success:
                    if messages:  # Only update if we got new messages
                        # Process messages
                        new_message_count = self.youtube_api.process_chat_messages(
                            messages, self.participants
                        )
                        
                        if new_message_count > 0:
                            self.total_messages_fetched += new_message_count
                            self.last_fetch_time = datetime.now()
                            
                            # Notify UI of updates
                            self._notify_participants_updated()
                            self._notify_status(
                                f"Live fetching... {len(self.participants)} participants, "
                                f"{self.total_messages_fetched} messages"
                            )
                    
                    consecutive_errors = 0
                    
                elif error_msg:
                    # Handle error
                    self.fetch_errors += 1
                    consecutive_errors += 1
                    
                    if consecutive_errors >= max_consecutive_errors:
                        self._notify_error(f"Too many consecutive errors. Stopping: {error_msg}")
                        break
                    else:
                        self._notify_error(f"Fetch error (attempt {consecutive_errors}): {error_msg}")
                
                # Wait for next poll (respect API polling interval)
                poll_interval = self.youtube_api.get_polling_interval()
                self.stop_event.wait(poll_interval)
                
            except Exception as e:
                self.fetch_errors += 1
                consecutive_errors += 1
                error_msg = f"Unexpected error in live fetch: {str(e)}"
                
                if consecutive_errors >= max_consecutive_errors:
                    self._notify_error(f"Too many errors. Stopping: {error_msg}")
                    break
                else:
                    self._notify_error(error_msg)
                
                # Wait before retrying
                self.stop_event.wait(5)
        
        # Clean up
        self.is_live_fetching = False
        if self.youtube_api:
            self.youtube_api.reset_chat_session()
    
    def clear_participants(self) -> None:
        """Clear all participants."""
        self.participants.clear()
        self.total_messages_fetched = 0
        self.last_fetch_time = None
        self.fetch_errors = 0
        self._notify_participants_updated()
        self._notify_status("Participants cleared")
    
    def get_participants(self) -> Dict[str, Participant]:
        """Get current participants dictionary."""
        return self.participants.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Dictionary with current statistics
        """
        return {
            'total_participants': len(self.participants),
            'total_messages': self.total_messages_fetched,
            'is_live_fetching': self.is_live_fetching,
            'last_fetch_time': self.last_fetch_time,
            'fetch_errors': self.fetch_errors,
            'youtube_api_connected': self.youtube_api and self.youtube_api.is_authenticated()
        }
    
    def _notify_participants_updated(self) -> None:
        """Notify that participants have been updated."""
        if self.on_participants_updated:
            try:
                self.on_participants_updated()
            except Exception as e:
                print(f"Error in participants updated callback: {e}")
    
    def _notify_status_changed(self, status: str) -> None:
        """Notify that status has changed."""
        if self.on_status_changed:
            try:
                self.on_status_changed(status)
            except Exception as e:
                print(f"Error in status changed callback: {e}")
    
    def _notify_status(self, status: str) -> None:
        """Notify status update."""
        self._notify_status_changed(status)
    
    def _notify_error(self, error: str) -> None:
        """Notify error."""
        if self.on_error:
            try:
                self.on_error(error)
            except Exception as e:
                print(f"Error in error callback: {e}")
        else:
            print(f"DataSource Error: {error}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_live_fetch()
        self.participants.clear()
