# YouTube Chat Giveaway

A desktop application for conducting giveaways from YouTube live chat participants. Built with Python and Tkinter for cross-platform compatibility.

## Features

### Core Functionality
- **Live Mode**: Monitor YouTube live chat in real-time via YouTube Data API v3
- **Offline Mode**: Import chat data from text or CSV files
- **Smart Filtering**: Filter participants by keyword, message count, and blacklist
- **Random Selection**: Pick winners with optional message-count weighting
- **Data Export**: Export winners and participants to CSV with full audit trail

### User Interface
- **Live Chat Monitor**: Real-time participant tracking with status updates
- **Filter Panel**: Keyword filtering, minimum message requirements, blacklist management
- **Participant List**: View all eligible participants with message counts
- **Winner Selection**: Configure number of winners and selection method
- **Export Tools**: One-click CSV export for winners and all participants

## Requirements

- Python 3.10 or higher
- tkinter (usually included with Python)
- Google API credentials for YouTube Data API v3 (for live mode)

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd YT-Giveaway_software
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up YouTube API credentials (for live mode)**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing project
   - Enable the YouTube Data API v3
   - Create OAuth 2.0 Client ID credentials
   - Select "Desktop Application" as application type
   - Download the credentials JSON file
   - Save it as `client_secret.json` in the application directory

## Usage

### Starting the Application

```bash
python main.py
```

### Offline Mode (No API Setup Required)

1. **Import Chat Data**:
   - Click "Import File..." 
   - Select a text file (.txt) or CSV file (.csv)
   - Supported formats:
     - Text: `username: message` (one per line)
     - CSV: columns named `author,text` or `username,message`

2. **Apply Filters**:
   - Set keyword filter (optional)
   - Set minimum message count
   - Add usernames to blacklist (one per line)
   - Click "Apply Filters"

3. **Pick Winners**:
   - Set number of winners
   - Choose weighted selection (by message count) if desired
   - Click "Pick Winners"

4. **Export Results**:
   - Click "Export Winners CSV" for winners only
   - Click "Export All CSV" for complete participant data

### Live Mode (Requires YouTube API Setup)

1. **Authenticate**:
   - Click "Auth Setup" to check authentication status
   - Follow setup instructions if not authenticated
   - Click "Authenticate" to complete OAuth flow

2. **Monitor Live Chat**:
   - Paste YouTube live stream URL or video ID
   - Click "Resolve Live" to verify the stream has live chat
   - Click "Start Live Fetch" to begin monitoring
   - Participants will appear in real-time as they chat

3. **Manage Live Session**:
   - Use filters to update eligible participants
   - Click "Stop Live Fetch" when ready to pick winners
   - Follow same winner selection and export process as offline mode

## File Formats

### Input Files

**Text File (.txt)**:
```
username1: Hello this is my message
username2: I want to win!
username1: Another message from the same user
```

**CSV File (.csv)**:
```csv
author,text
username1,"Hello this is my message"
username2,"I want to win!"
username1,"Another message from the same user"
```

### Export CSV Schema

The exported CSV files contain the following columns:

- `timestamp_iso`: When the giveaway was conducted
- `youtube_video_id`: Video ID if from live mode
- `mode`: "live" or "offline"
- `username`: Participant's display name
- `message_count`: Number of messages from this participant
- `first_seen`: When participant first appeared
- `keyword_used`: Boolean - whether participant used required keyword
- `blacklisted`: Boolean - whether participant was blacklisted
- `eligible`: Boolean - whether participant passed all filters
- `selected_as_winner`: Boolean - whether participant was selected as winner
- `draw_order`: Order in which winner was selected (1, 2, 3...)

## YouTube API Setup Details

### Google Cloud Console Setup

1. **Create Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable YouTube Data API v3**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop application"
   - Download the JSON file as `client_secret.json`

4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Fill in required application information
   - Add your email as a test user (for development)

### Authentication Flow

1. Place `client_secret.json` in the application directory
2. Click "Auth Setup" in the application
3. Click "Authenticate" to start OAuth flow
4. Browser will open for Google authentication
5. Grant permissions to access YouTube data
6. Authentication token will be saved as `token.json`

## Troubleshooting

### Common Issues

**"Missing client_secret.json"**
- Download OAuth credentials from Google Cloud Console
- Save the file as `client_secret.json` in the application directory

**"API quota exceeded"**
- YouTube Data API has daily quotas
- Wait until the next day or request quota increase
- Each live chat message fetch counts toward quota

**"Live chat not available"**
- Ensure the video is actually a live stream
- Some streams may not have chat enabled
- Private or restricted streams may not be accessible

**"Authentication failed"**
- Check that OAuth consent screen is configured
- Ensure your email is added as a test user
- Try deleting `token.json` and re-authenticating

**"Import file failed"**
- Check file format matches expected structure
- Ensure file encoding is UTF-8
- Verify usernames don't contain special characters that break parsing

### Performance Notes

- Live chat polling respects YouTube's rate limiting (typically 2-4 seconds between requests)
- Large participant lists (>10,000) may slow the UI - consider filtering
- CSV export is optimized for large datasets

### Data Privacy

- Authentication tokens are stored locally in `token.json`
- No chat data is transmitted to external services
- All data processing happens locally on your machine

## File Structure

```
YT-Giveaway_software/
├── main.py              # Application entry point
├── ui.py                # Main GUI implementation
├── models.py            # Data models (Participant, Winner, etc.)
├── filters.py           # Participant filtering logic
├── selector.py          # Winner selection logic
├── exporter.py          # CSV export functionality
├── file_parser.py       # File import and parsing
├── youtube_api.py       # YouTube Data API integration
├── oauth.py             # OAuth authentication handler
├── datasource.py        # Data source management
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── client_secret.json  # OAuth credentials (you provide)
└── token.json          # OAuth token (auto-generated)
```

## License

This project is provided as-is for educational and personal use. Please ensure compliance with YouTube's Terms of Service and API usage policies when using the live chat features.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

---

**Note**: This application respects YouTube's API rate limits and Terms of Service. Use responsibly and ensure you have proper permissions for any streams you monitor.
