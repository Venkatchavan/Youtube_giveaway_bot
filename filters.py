"""
Filtering logic for participants based on various criteria.
"""
from typing import List, Dict, Set, Any
from models import Participant


class ParticipantFilter:
    """Handles filtering of participants based on various criteria."""
    
    def __init__(self):
        """Initialize the filter with default settings."""
        self.keyword: str = ""
        self.min_messages: int = 1
        self.blacklist: Set[str] = set()
        self.case_sensitive: bool = False
    
    def set_keyword_filter(self, keyword: str, case_sensitive: bool = False) -> None:
        """
        Set keyword filter for messages.
        
        Args:
            keyword: Keyword that must appear in at least one message
            case_sensitive: Whether keyword matching is case sensitive
        """
        self.keyword = keyword.strip()
        self.case_sensitive = case_sensitive
    
    def set_minimum_messages(self, min_count: int) -> None:
        """
        Set minimum message count requirement.
        
        Args:
            min_count: Minimum number of messages required to be eligible
        """
        self.min_messages = max(0, min_count)
    
    def set_blacklist(self, blacklisted_usernames: List[str]) -> None:
        """
        Set list of blacklisted usernames.
        
        Args:
            blacklisted_usernames: List of usernames to exclude
        """
        # Convert to lowercase for case-insensitive matching
        self.blacklist = {username.lower().strip() for username in blacklisted_usernames if username.strip()}
    
    def apply_filters(self, participants: Dict[str, Participant]) -> List[str]:
        """
        Apply all filters and return list of eligible usernames.
        
        Args:
            participants: Dictionary mapping username to Participant objects
            
        Returns:
            List of usernames that pass all filters
        """
        eligible = []
        
        for username, participant in participants.items():
            if self._is_eligible(participant):
                eligible.append(username)
        
        return eligible
    
    def _is_eligible(self, participant: Participant) -> bool:
        """
        Check if a participant meets all filter criteria.
        
        Args:
            participant: Participant object to check
            
        Returns:
            True if participant is eligible, False otherwise
        """
        # Check blacklist (case-insensitive)
        if participant.username.lower() in self.blacklist:
            return False
        
        # Check minimum message count
        if participant.message_count < self.min_messages:
            return False
        
        # Check keyword filter (if set)
        if self.keyword:
            has_keyword = False
            search_keyword = self.keyword if self.case_sensitive else self.keyword.lower()
            
            for message in participant.messages:
                search_message = message if self.case_sensitive else message.lower()
                if search_keyword in search_message:
                    has_keyword = True
                    break
            
            if not has_keyword:
                return False
        
        return True
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current filter settings.
        
        Returns:
            Dictionary with current filter settings
        """
        return {
            "keyword": self.keyword,
            "case_sensitive": self.case_sensitive,
            "min_messages": self.min_messages,
            "blacklist_count": len(self.blacklist),
            "blacklisted_users": list(self.blacklist)
        }
    
    def is_participant_eligible(self, participant: Participant) -> bool:
        """
        Public method to check if a single participant is eligible.
        
        Args:
            participant: Participant to check
            
        Returns:
            True if eligible, False otherwise
        """
        return self._is_eligible(participant)
    
    def get_ineligible_reasons(self, participant: Participant) -> List[str]:
        """
        Get list of reasons why a participant is ineligible.
        
        Args:
            participant: Participant to check
            
        Returns:
            List of string reasons for ineligibility
        """
        reasons = []
        
        if participant.username.lower() in self.blacklist:
            reasons.append("Username is blacklisted")
        
        if participant.message_count < self.min_messages:
            reasons.append(f"Message count ({participant.message_count}) below minimum ({self.min_messages})")
        
        if self.keyword:
            has_keyword = False
            search_keyword = self.keyword if self.case_sensitive else self.keyword.lower()
            
            for message in participant.messages:
                search_message = message if self.case_sensitive else message.lower()
                if search_keyword in search_message:
                    has_keyword = True
                    break
            
            if not has_keyword:
                reasons.append(f"No messages contain required keyword: '{self.keyword}'")
        
        return reasons
