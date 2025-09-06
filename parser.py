"""
Data parser for importing participant data from various file formats.
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from models import Participant


class DataParser:
    """Handles parsing of participant data from files."""
    
    def __init__(self):
        """Initialize the parser."""
        self.supported_extensions = {'.txt', '.csv'}
    
    def parse_file(self, file_path: str) -> Dict[str, Participant]:
        """
        Parse a file and extract participants.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary mapping username to Participant objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        try:
            if path.suffix.lower() == '.csv':
                return self._parse_csv(file_path)
            else:
                return self._parse_txt(file_path)
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")
    
    def _parse_csv(self, file_path: str) -> Dict[str, Participant]:
        """
        Parse CSV file with columns for author and text.
        
        Expected CSV format:
        - author,text
        - username,message content
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dictionary mapping username to Participant objects
        """
        participants = {}
        
        with open(file_path, 'r', encoding='utf-8', newline='') as file:
            # Try to detect if file has headers
            sample = file.read(1024)
            file.seek(0)
            
            has_header = csv.Sniffer().has_header(sample)
            reader = csv.reader(file)
            
            if has_header:
                headers = next(reader)
                # Find author and text columns (case-insensitive)
                author_col = self._find_column_index(headers, ['author', 'username', 'user', 'name'])
                text_col = self._find_column_index(headers, ['text', 'message', 'content', 'msg'])
                
                if author_col is None or text_col is None:
                    raise ValueError("CSV must contain 'author' and 'text' columns (or similar)")
            else:
                # Assume first column is author, second is text
                author_col = 0
                text_col = 1
            
            for row_num, row in enumerate(reader, start=2 if has_header else 1):
                if len(row) < max(author_col + 1, text_col + 1):
                    continue  # Skip incomplete rows
                
                username = row[author_col].strip()
                message = row[text_col].strip()
                
                if not username or not message:
                    continue  # Skip empty entries
                
                # Normalize username (case-insensitive deduplication)
                username_key = username.lower()
                
                if username_key not in participants:
                    participants[username_key] = Participant(
                        username=username,  # Keep original case
                        first_seen=datetime.now()
                    )
                
                participants[username_key].add_message(message)
        
        return participants
    
    def _parse_txt(self, file_path: str) -> Dict[str, Participant]:
        """
        Parse text file with one message per line.
        
        Expected formats:
        - "username: message content"
        - "username - message content"
        - "username | message content"
        - Just "username" (if no separator found)
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary mapping username to Participant objects
        """
        participants = {}
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                
                username, message = self._parse_chat_line(line)
                
                if not username:
                    continue  # Skip lines we couldn't parse
                
                # Normalize username (case-insensitive deduplication)
                username_key = username.lower()
                
                if username_key not in participants:
                    participants[username_key] = Participant(
                        username=username,  # Keep original case
                        first_seen=datetime.now()
                    )
                
                participants[username_key].add_message(message or line)
        
        return participants
    
    def _parse_chat_line(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a single chat line to extract username and message.
        
        Args:
            line: Raw chat line
            
        Returns:
            Tuple of (username, message) or (username, None) if no separator found
        """
        # Try different separator patterns
        patterns = [
            r'^([^:]+):\s*(.+)$',    # username: message
            r'^([^-]+)-\s*(.+)$',    # username - message
            r'^([^|]+)\|\s*(.+)$',   # username | message
            r'^([^>]+)>\s*(.+)$',    # username > message
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                username = match.group(1).strip()
                message = match.group(2).strip()
                return username, message
        
        # If no separator found, treat entire line as username
        # This handles cases where file just contains usernames
        return line.strip(), None
    
    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """
        Find the index of a column with one of the possible names (case-insensitive).
        
        Args:
            headers: List of column headers
            possible_names: List of possible column names to look for
            
        Returns:
            Index of the matching column, or None if not found
        """
        headers_lower = [h.lower() for h in headers]
        
        for name in possible_names:
            if name.lower() in headers_lower:
                return headers_lower.index(name.lower())
        
        return None
    
    def validate_file_format(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a file can be parsed successfully.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            participants = self.parse_file(file_path)
            if not participants:
                return False, "No valid participants found in file"
            return True, f"Successfully parsed {len(participants)} participants"
        except Exception as e:
            return False, str(e)
