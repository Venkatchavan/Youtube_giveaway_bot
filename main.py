"""
YouTube Chat Giveaway Application
Main entry point for the desktop application.
"""
import sys
import tkinter as tk
from pathlib import Path

# Add current directory to path to ensure local imports work
sys.path.insert(0, str(Path(__file__).parent))

from ui import YouTubeGiveawayApp


def main():
    """Main entry point for the application."""
    try:
        # Create root window
        root = tk.Tk()
        
        # Set window icon (if available)
        try:
            # You can add an icon file here if desired
            # root.iconbitmap('icon.ico')
            pass
        except:
            pass
        
        # Create and run application
        app = YouTubeGiveawayApp(root)
        
        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Start the application
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
