"""
Data models for the YouTube Chat Giveaway application.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class Participant:
    """Represents a participant in the giveaway."""
    username: str
    message_count: int = 0
    messages: List[str] = None
    first_seen: datetime = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.first_seen is None:
            self.first_seen = datetime.now()
    
    def add_message(self, message: str) -> None:
        """Add a message to this participant's message list."""
        self.messages.append(message)
        self.message_count += 1


@dataclass
class Winner:
    """Represents a selected winner."""
    username: str
    draw_order: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class GiveawaySession:
    """Represents a complete giveaway session."""
    youtube_video_id: Optional[str] = None
    mode: str = "offline"  # "live" or "offline"
    participants: Dict[str, Participant] = None
    winners: List[Winner] = None
    filters_applied: Dict = None
    timestamp_created: datetime = None
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = {}
        if self.winners is None:
            self.winners = []
        if self.filters_applied is None:
            self.filters_applied = {}
        if self.timestamp_created is None:
            self.timestamp_created = datetime.now()
