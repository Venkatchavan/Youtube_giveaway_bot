"""
Simple test script to validate core functionality.
Run this to test the application components without the GUI.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Participant, Winner
from filters import ParticipantFilter
from selector import WinnerSelector
from file_parser import DataParser
from exporter import DataExporter
from url_extractor import YouTubeURLExtractor
from datetime import datetime


def test_file_parsing():
    """Test file parsing functionality."""
    print("Testing file parsing...")
    
    parser = DataParser()
    
    # Test sample CSV
    try:
        participants = parser.parse_file("sample_chat.csv")
        print(f"✓ Parsed {len(participants)} participants from CSV")
        
        # Show first few participants
        for i, (username_key, participant) in enumerate(list(participants.items())[:3]):
            print(f"  - {participant.username}: {participant.message_count} messages")
    except Exception as e:
        print(f"✗ CSV parsing failed: {e}")
    
    # Test sample TXT
    try:
        participants = parser.parse_file("sample_chat.txt")
        print(f"✓ Parsed {len(participants)} participants from TXT")
    except Exception as e:
        print(f"✗ TXT parsing failed: {e}")


def test_filtering():
    """Test participant filtering."""
    print("\nTesting participant filtering...")
    
    # Create test participants
    participants = {
        "user1": Participant("User1", message_count=3, messages=["hello", "giveaway", "win"]),
        "user2": Participant("User2", message_count=1, messages=["hi"]),
        "user3": Participant("User3", message_count=2, messages=["giveaway", "cool"]),
        "spammer": Participant("Spammer", message_count=10, messages=["spam"] * 10),
    }
    
    filter_obj = ParticipantFilter()
    
    # Test no filters
    eligible = filter_obj.apply_filters(participants)
    print(f"✓ No filters: {len(eligible)} eligible participants")
    
    # Test keyword filter
    filter_obj.set_keyword_filter("giveaway")
    eligible = filter_obj.apply_filters(participants)
    print(f"✓ Keyword 'giveaway': {len(eligible)} eligible participants")
    
    # Test minimum messages
    filter_obj.set_keyword_filter("")  # Clear keyword
    filter_obj.set_minimum_messages(2)
    eligible = filter_obj.apply_filters(participants)
    print(f"✓ Min 2 messages: {len(eligible)} eligible participants")
    
    # Test blacklist
    filter_obj.set_minimum_messages(1)  # Reset
    filter_obj.set_blacklist(["spammer"])
    eligible = filter_obj.apply_filters(participants)
    print(f"✓ Blacklist 'spammer': {len(eligible)} eligible participants")


def test_winner_selection():
    """Test winner selection."""
    print("\nTesting winner selection...")
    
    eligible_usernames = ["user1", "user2", "user3", "user4", "user5"]
    selector = WinnerSelector(seed=42)  # Use seed for reproducible results
    
    # Test normal selection
    try:
        winners = selector.pick_winners(eligible_usernames, 3)
        print(f"✓ Selected {len(winners)} winners:")
        for winner in winners:
            print(f"  {winner.draw_order}. {winner.username}")
    except Exception as e:
        print(f"✗ Winner selection failed: {e}")
    
    # Test error case - too many winners
    try:
        winners = selector.pick_winners(eligible_usernames, 10)
        print("✗ Should have failed with too many winners")
    except ValueError as e:
        print(f"✓ Correctly caught error: {e}")


def test_csv_export():
    """Test CSV export functionality."""
    print("\nTesting CSV export...")
    
    # Create test data
    participants = {
        "user1": Participant("User1", message_count=3),
        "user2": Participant("User2", message_count=1),
        "user3": Participant("User3", message_count=2),
    }
    
    winners = [
        Winner("User1", 1),
        Winner("User3", 2),
    ]
    
    exporter = DataExporter()
    
    # Test winners export
    try:
        success = exporter.export_winners(winners, "test_winners.csv")
        if success:
            print("✓ Winners export successful")
        else:
            print("✗ Winners export failed")
    except Exception as e:
        print(f"✗ Winners export error: {e}")
    
    # Test all participants export
    try:
        eligible = ["user1", "user3"]
        success = exporter.export_all_participants(
            participants, winners, "test_all.csv", 
            eligible_usernames=eligible
        )
        if success:
            print("✓ All participants export successful")
        else:
            print("✗ All participants export failed")
    except Exception as e:
        print(f"✗ All participants export error: {e}")


def test_url_extraction():
    """Test URL-only mode functionality."""
    print("\nTesting URL extraction...")
    
    extractor = YouTubeURLExtractor()
    
    # Test URL validation
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
        "invalid-url"
    ]
    
    for url in test_urls:
        video_id = extractor.extract_video_id(url)
        if video_id:
            print(f"✓ Extracted video ID from '{url}': {video_id}")
        else:
            print(f"✗ Could not extract video ID from '{url}'")
    
    # Test demo participant generation
    try:
        demo_info = {"title": "Test Video", "channel": "Test Channel"}
        participants = extractor.generate_demo_participants(demo_info, 10)
        print(f"✓ Generated {len(participants)} demo participants")
        
        # Show first few participants
        for i, (username_key, participant) in enumerate(list(participants.items())[:3]):
            print(f"  - {participant.username}: {participant.message_count} messages")
    except Exception as e:
        print(f"✗ Demo participant generation failed: {e}")


def run_all_tests():
    """Run all tests."""
    print("YouTube Chat Giveaway - Component Tests")
    print("=" * 50)
    
    test_file_parsing()
    test_filtering()
    test_winner_selection()
    test_csv_export()
    test_url_extraction()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("\nTo run the full application, use: python main.py")
    print("Try the new URL-only mode with 'Resolve URL' and 'Import from URL' buttons!")


if __name__ == "__main__":
    run_all_tests()
