"""
OAuth 2.0 authentication handler for YouTube Data API.
"""
import os
import json
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class YouTubeOAuth:
    """Handles OAuth 2.0 authentication for YouTube Data API."""
    
    # YouTube Data API scope for read-only access
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
    
    def __init__(self, credentials_file: str = 'client_secret.json', 
                 token_file: str = 'token.json'):
        """
        Initialize OAuth handler.
        
        Args:
            credentials_file: Path to client credentials JSON file
            token_file: Path to store access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.credentials = None
    
    def has_credentials_file(self) -> bool:
        """Check if client credentials file exists."""
        return Path(self.credentials_file).exists()
    
    def has_valid_token(self) -> bool:
        """Check if a valid token file exists."""
        if not Path(self.token_file).exists():
            return False
        
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            return creds and creds.valid
        except Exception:
            return False
    
    def get_credentials(self) -> Optional[Credentials]:
        """
        Get valid credentials, refreshing or re-authenticating as needed.
        
        Returns:
            Valid Credentials object or None if authentication fails
        """
        creds = None
        
        # Load existing token if available
        if Path(self.token_file).exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            except Exception as e:
                print(f"Error loading token file: {e}")
                # Delete invalid token file
                try:
                    os.remove(self.token_file)
                except:
                    pass
        
        # If credentials are not valid, refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Try to refresh
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            # If refresh failed or no credentials, re-authenticate
            if not creds:
                creds = self._authenticate()
        
        # Save credentials for next time
        if creds and creds.valid:
            try:
                self._save_credentials(creds)
                self.credentials = creds
                return creds
            except Exception as e:
                print(f"Error saving credentials: {e}")
        
        return None
    
    def _authenticate(self) -> Optional[Credentials]:
        """
        Perform OAuth 2.0 authentication flow.
        
        Returns:
            Valid Credentials object or None if authentication fails
        """
        if not self.has_credentials_file():
            print(f"Credentials file not found: {self.credentials_file}")
            print("Please download client credentials from Google Cloud Console")
            return None
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.SCOPES
            )
            
            # Run the OAuth flow
            # This will open a browser window for user authentication
            creds = flow.run_local_server(port=0)
            
            return creds
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None
    
    def _save_credentials(self, creds: Credentials) -> None:
        """
        Save credentials to token file.
        
        Args:
            creds: Credentials object to save
        """
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Error saving token: {e}")
            raise
    
    def revoke_credentials(self) -> bool:
        """
        Revoke and delete stored credentials.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Revoke the credentials if possible
            if self.credentials and self.credentials.valid:
                try:
                    self.credentials.revoke(Request())
                except Exception as e:
                    print(f"Error revoking credentials: {e}")
            
            # Delete token file
            if Path(self.token_file).exists():
                os.remove(self.token_file)
            
            self.credentials = None
            return True
            
        except Exception as e:
            print(f"Error revoking credentials: {e}")
            return False
    
    def get_auth_status(self) -> dict:
        """
        Get detailed authentication status.
        
        Returns:
            Dictionary with authentication status information
        """
        status = {
            'has_credentials_file': self.has_credentials_file(),
            'has_token_file': Path(self.token_file).exists(),
            'has_valid_token': False,
            'is_authenticated': False,
            'user_info': None,
            'error': None
        }
        
        if not status['has_credentials_file']:
            status['error'] = f"Missing credentials file: {self.credentials_file}"
            return status
        
        try:
            if status['has_token_file']:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                if creds and creds.valid:
                    status['has_valid_token'] = True
                    status['is_authenticated'] = True
                    
                    # Try to get user info from token
                    try:
                        token_info = json.loads(creds.to_json())
                        status['user_info'] = {
                            'client_id': token_info.get('client_id'),
                            'expires_at': token_info.get('expiry')
                        }
                    except:
                        pass
                elif creds and creds.expired and creds.refresh_token:
                    status['error'] = "Token expired but can be refreshed"
                else:
                    status['error'] = "Invalid token file"
            else:
                status['error'] = "No token file found - authentication required"
                
        except Exception as e:
            status['error'] = f"Error checking authentication: {str(e)}"
        
        return status
    
    def setup_instructions(self) -> str:
        """
        Get setup instructions for OAuth configuration.
        
        Returns:
            Formatted setup instructions
        """
        return """
YouTube API OAuth Setup Instructions:

1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the YouTube Data API v3
4. Go to 'Credentials' and create OAuth 2.0 Client ID
5. Select 'Desktop Application' as application type
6. Download the credentials JSON file
7. Save it as 'client_secret.json' in the application directory
8. Run the application and click 'Authenticate' to complete setup

Required file: client_secret.json
Token file (auto-generated): token.json

Scopes required:
- https://www.googleapis.com/auth/youtube.readonly
        """.strip()
