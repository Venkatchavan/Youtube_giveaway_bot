"""
CSV export functionality for participants and winners.
"""
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from models import Participant, Winner, GiveawaySession


class DataExporter:
    """Handles exporting participant and winner data to CSV files."""
    
    def __init__(self):
        """Initialize the exporter."""
        pass
    
    def export_winners(self, winners: List[Winner], file_path: str, 
                      session: GiveawaySession = None) -> bool:
        """
        Export winners to CSV file.
        
        Args:
            winners: List of Winner objects
            file_path: Path where to save the CSV file
            session: Optional session data for additional context
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write header
                headers = [
                    'timestamp_iso',
                    'youtube_video_id',
                    'mode',
                    'username',
                    'draw_order',
                    'selected_as_winner'
                ]
                writer.writerow(headers)
                
                # Write winner data
                for winner in winners:
                    row = [
                        winner.timestamp.isoformat() if winner.timestamp else datetime.now().isoformat(),
                        session.youtube_video_id if session else '',
                        session.mode if session else 'unknown',
                        winner.username,
                        winner.draw_order,
                        True
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting winners: {e}")
            return False
    
    def export_all_participants(self, participants: Dict[str, Participant], 
                               winners: List[Winner], file_path: str,
                               session: GiveawaySession = None,
                               eligible_usernames: List[str] = None,
                               filter_summary: Dict = None) -> bool:
        """
        Export all participants to CSV file with detailed information.
        
        Args:
            participants: Dictionary of all participants
            winners: List of winners
            file_path: Path where to save the CSV file
            session: Optional session data
            eligible_usernames: List of usernames that passed filters
            filter_summary: Summary of applied filters
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Create sets for faster lookup
            winner_usernames = {winner.username.lower() for winner in winners}
            winner_draw_order = {winner.username.lower(): winner.draw_order for winner in winners}
            eligible_set = set(eligible_usernames) if eligible_usernames else set()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write header
                headers = [
                    'timestamp_iso',
                    'youtube_video_id',
                    'mode',
                    'username',
                    'message_count',
                    'first_seen',
                    'keyword_used',
                    'blacklisted',
                    'eligible',
                    'selected_as_winner',
                    'draw_order'
                ]
                writer.writerow(headers)
                
                # Get filter info for keyword detection
                keyword = filter_summary.get('keyword', '') if filter_summary else ''
                blacklisted_users = set(filter_summary.get('blacklisted_users', [])) if filter_summary else set()
                
                # Write participant data
                for username_key, participant in participants.items():
                    # Check if participant has keyword in messages
                    has_keyword = False
                    if keyword:
                        for message in participant.messages:
                            if keyword.lower() in message.lower():
                                has_keyword = True
                                break
                    
                    # Check if blacklisted
                    is_blacklisted = username_key in blacklisted_users
                    
                    # Check if eligible
                    is_eligible = username_key in eligible_set
                    
                    # Check if winner
                    is_winner = username_key in winner_usernames
                    draw_order = winner_draw_order.get(username_key, '') if is_winner else ''
                    
                    row = [
                        session.timestamp_created.isoformat() if session and session.timestamp_created else datetime.now().isoformat(),
                        session.youtube_video_id if session else '',
                        session.mode if session else 'unknown',
                        participant.username,
                        participant.message_count,
                        participant.first_seen.isoformat() if participant.first_seen else '',
                        has_keyword,
                        is_blacklisted,
                        is_eligible,
                        is_winner,
                        draw_order
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting participants: {e}")
            return False
    
    def export_session(self, session: GiveawaySession, file_path: str) -> bool:
        """
        Export complete session data to CSV file.
        
        Args:
            session: GiveawaySession object containing all data
            file_path: Path where to save the CSV file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write session metadata header
                writer.writerow(['# Session Metadata'])
                writer.writerow(['timestamp_created', session.timestamp_created.isoformat()])
                writer.writerow(['youtube_video_id', session.youtube_video_id or ''])
                writer.writerow(['mode', session.mode])
                writer.writerow(['total_participants', len(session.participants)])
                writer.writerow(['total_winners', len(session.winners)])
                writer.writerow(['filters_applied', str(session.filters_applied)])
                writer.writerow([])  # Empty row
                
                # Write participants header
                writer.writerow(['# Participants'])
                headers = [
                    'username',
                    'message_count',
                    'first_seen',
                    'selected_as_winner',
                    'draw_order'
                ]
                writer.writerow(headers)
                
                # Create winner lookup
                winner_data = {w.username.lower(): w for w in session.winners}
                
                # Write participant data
                for username_key, participant in session.participants.items():
                    winner = winner_data.get(username_key)
                    row = [
                        participant.username,
                        participant.message_count,
                        participant.first_seen.isoformat() if participant.first_seen else '',
                        bool(winner),
                        winner.draw_order if winner else ''
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting session: {e}")
            return False
    
    def create_export_filename(self, base_name: str, export_type: str = "participants") -> str:
        """
        Create a timestamped filename for exports.
        
        Args:
            base_name: Base name for the file
            export_type: Type of export (e.g., "participants", "winners", "session")
            
        Returns:
            Formatted filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{export_type}_{timestamp}.csv"
    
    def validate_export_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that the export path is writable.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            # Check if directory exists and is writable
            if not path.parent.exists():
                return False, f"Directory does not exist: {path.parent}"
            
            # Try to create a test file
            test_path = path.parent / f"test_write_{datetime.now().timestamp()}.tmp"
            try:
                test_path.touch()
                test_path.unlink()  # Delete test file
                return True, "Path is valid and writable"
            except PermissionError:
                return False, f"No write permission for directory: {path.parent}"
            
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
