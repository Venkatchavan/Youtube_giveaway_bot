"""
Main GUI application using tkinter.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import List, Dict
from datetime import datetime
from pathlib import Path

from models import Participant, Winner, GiveawaySession
from filters import ParticipantFilter
from selector import WinnerSelector
from exporter import DataExporter
from datasource import DataSourceManager
from youtube_api import YouTubeAPI
from oauth import YouTubeOAuth


class YouTubeGiveawayApp:
    """Main application class for YouTube Chat Giveaway."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the application.
        
        Args:
            root: Root tkinter window
        """
        self.root = root
        self.root.title("YouTube Chat Giveaway")
        self.root.geometry("1200x800")
        
        # Core components
        self.filter = ParticipantFilter()
        self.selector = WinnerSelector()
        self.exporter = DataExporter()
        self.datasource = DataSourceManager()
        
        # YouTube API components
        self.oauth = YouTubeOAuth()
        self.youtube_api = YouTubeAPI(self.oauth)
        self.datasource.set_youtube_api(self.youtube_api)
        
        # Application state
        self.participants: Dict[str, Participant] = {}
        self.eligible_usernames: List[str] = []
        self.winners: List[Winner] = []
        self.current_session = GiveawaySession()
        
        # UI variables
        self.youtube_url_var = tk.StringVar()
        self.keyword_var = tk.StringVar()
        self.min_messages_var = tk.IntVar(value=1)
        self.num_winners_var = tk.IntVar(value=1)
        self.weighted_selection_var = tk.BooleanVar()
        
        # UI components
        self.status_label = None
        self.participants_listbox = None
        self.winners_listbox = None
        self.blacklist_text = None
        self.participants_count_label = None
        self.eligible_count_label = None
        
        # Setup callbacks
        self.datasource.set_callbacks(
            on_participants_updated=self._on_participants_updated,
            on_status_changed=self._on_status_changed,
            on_error=self._on_error
        )
        
        # Initialize UI
        self._create_ui()
        self._update_youtube_api_status()
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_ui(self) -> None:
        """Create the user interface."""
        # Create main frames
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the top toolbar."""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # YouTube URL input
        ttk.Label(toolbar_frame, text="YouTube URL/ID:").pack(side=tk.LEFT)
        url_entry = ttk.Entry(toolbar_frame, textvariable=self.youtube_url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # YouTube controls
        ttk.Button(toolbar_frame, text="Resolve URL", 
                  command=self._resolve_url).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Import from URL", 
                  command=self._import_from_url).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Live API controls (may not work without credentials)
        self.resolve_live_btn = ttk.Button(toolbar_frame, text="Resolve Live", 
                                         command=self._resolve_live_chat)
        self.resolve_live_btn.pack(side=tk.LEFT, padx=2)
        self.start_fetch_btn = ttk.Button(toolbar_frame, text="Start Live Fetch", 
                                         command=self._start_live_fetch)
        self.start_fetch_btn.pack(side=tk.LEFT, padx=2)
        self.stop_fetch_btn = ttk.Button(toolbar_frame, text="Stop Live Fetch", 
                                        command=self._stop_live_fetch, state=tk.DISABLED)
        self.stop_fetch_btn.pack(side=tk.LEFT, padx=2)
        
        # File operations
        ttk.Button(toolbar_frame, text="Import File...", 
                  command=self._import_file).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(toolbar_frame, text="Clear All", 
                  command=self._clear_all).pack(side=tk.LEFT, padx=2)
        
        # Authentication (for API features)
        ttk.Button(toolbar_frame, text="Auth Setup", 
                  command=self._show_auth_setup).pack(side=tk.RIGHT, padx=2)
    
    def _resolve_url(self) -> None:
        """Resolve and validate YouTube URL (no API required)."""
        url = self.youtube_url_var.get().strip()
        if not url:
            self._set_status("Please enter a YouTube URL or video ID")
            return
        
        def resolve_thread():
            is_valid, message = self.datasource.url_extractor.validate_url(url)
            if is_valid:
                self._set_status(f"✓ Valid URL: {message}")
            else:
                self._set_status(f"✗ Invalid URL: {message}")
        
        threading.Thread(target=resolve_thread, daemon=True).start()
    
    def _import_from_url(self) -> None:
        """Import participants from YouTube URL (demo mode)."""
        url = self.youtube_url_var.get().strip()
        if not url:
            self._set_status("Please enter a YouTube URL or video ID")
            return
        
        # Show info dialog about URL-only mode
        response = messagebox.askyesno(
            "URL-Only Mode", 
            "This will generate demo participants based on the YouTube URL.\n\n"
            "Since no API credentials are configured, this simulates what would be "
            "collected from live chat.\n\n"
            "Continue with demo participants?"
        )
        
        if response:
            success = self.datasource.import_from_url(url, demo_mode=True)
            if success:
                self._apply_filters()  # Auto-apply filters after import
    
    def _create_main_content(self) -> None:
        """Create the main content area."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Filters
        self._create_filters_panel(main_frame)
        
        # Center panel - Participants
        self._create_participants_panel(main_frame)
        
        # Right panel - Winners
        self._create_winners_panel(main_frame)
    
    def _create_filters_panel(self, parent: ttk.Frame) -> None:
        """Create the filters panel."""
        filters_frame = ttk.LabelFrame(parent, text="Filters", width=300)
        filters_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        filters_frame.pack_propagate(False)
        
        # Keyword filter
        ttk.Label(filters_frame, text="Keyword (optional):").pack(anchor=tk.W, padx=5, pady=(5, 0))
        ttk.Entry(filters_frame, textvariable=self.keyword_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Minimum messages
        ttk.Label(filters_frame, text="Minimum Messages:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        min_msg_frame = ttk.Frame(filters_frame)
        min_msg_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Spinbox(min_msg_frame, from_=0, to=100, textvariable=self.min_messages_var, 
                   width=10).pack(side=tk.LEFT)
        
        # Blacklist
        ttk.Label(filters_frame, text="Blacklist (one username per line):").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.blacklist_text = scrolledtext.ScrolledText(filters_frame, height=8, width=30)
        self.blacklist_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Apply filters button
        ttk.Button(filters_frame, text="Apply Filters", 
                  command=self._apply_filters).pack(pady=(10, 5))
        
        # Counts
        self.participants_count_label = ttk.Label(filters_frame, text="Total: 0")
        self.participants_count_label.pack(pady=2)
        self.eligible_count_label = ttk.Label(filters_frame, text="Eligible: 0")
        self.eligible_count_label.pack(pady=2)
    
    def _create_participants_panel(self, parent: ttk.Frame) -> None:
        """Create the participants panel."""
        participants_frame = ttk.LabelFrame(parent, text="Participants")
        participants_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Participants listbox with scrollbar
        listbox_frame = ttk.Frame(participants_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.participants_listbox = tk.Listbox(listbox_frame)
        scrollbar_v = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.participants_listbox.yview)
        scrollbar_h = ttk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL, command=self.participants_listbox.xview)
        
        self.participants_listbox.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.participants_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_winners_panel(self, parent: ttk.Frame) -> None:
        """Create the winners panel."""
        winners_frame = ttk.LabelFrame(parent, text="Winners", width=300)
        winners_frame.pack(side=tk.RIGHT, fill=tk.Y)
        winners_frame.pack_propagate(False)
        
        # Number of winners
        winners_controls = ttk.Frame(winners_frame)
        winners_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(winners_controls, text="Number of Winners:").pack(anchor=tk.W)
        ttk.Spinbox(winners_controls, from_=1, to=100, textvariable=self.num_winners_var, 
                   width=10).pack(anchor=tk.W, pady=2)
        
        # Weighted selection option
        ttk.Checkbutton(winners_controls, text="Weight by message count", 
                       variable=self.weighted_selection_var).pack(anchor=tk.W, pady=2)
        
        # Pick winners button
        self.pick_winners_btn = ttk.Button(winners_controls, text="Pick Winners", 
                                          command=self._pick_winners)
        self.pick_winners_btn.pack(pady=(10, 5))
        
        # Winners listbox
        self.winners_listbox = tk.Listbox(winners_frame)
        self.winners_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Export buttons
        export_frame = ttk.Frame(winners_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Export Winners CSV", 
                  command=self._export_winners).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="Export All CSV", 
                  command=self._export_all).pack(fill=tk.X, pady=2)
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _resolve_live_chat(self) -> None:
        """Resolve live chat for the given YouTube URL."""
        url = self.youtube_url_var.get().strip()
        if not url:
            self._set_status("Please enter a YouTube URL or video ID")
            return
        
        if not self.youtube_api.is_authenticated():
            if not self._authenticate_youtube():
                return
        
        def resolve_thread():
            video_id = self.youtube_api.extract_video_id(url)
            if not video_id:
                self._set_status("Invalid YouTube URL or video ID")
                return
            
            success, result = self.youtube_api.get_live_chat_id(video_id)
            if success:
                self._set_status(f"Live chat resolved: {result}")
            else:
                self._set_status(f"Failed to resolve live chat: {result}")
        
        threading.Thread(target=resolve_thread, daemon=True).start()
    
    def _start_live_fetch(self) -> None:
        """Start live fetching."""
        url = self.youtube_url_var.get().strip()
        if not url:
            self._set_status("Please enter a YouTube URL or video ID")
            return
        
        if not self.youtube_api.is_authenticated():
            if not self._authenticate_youtube():
                return
        
        success = self.datasource.start_live_fetch(url)
        if success:
            self.start_fetch_btn.config(state=tk.DISABLED)
            self.stop_fetch_btn.config(state=tk.NORMAL)
            self.pick_winners_btn.config(state=tk.DISABLED)
        
    def _stop_live_fetch(self) -> None:
        """Stop live fetching."""
        self.datasource.stop_live_fetch()
        self.start_fetch_btn.config(state=tk.NORMAL)
        self.stop_fetch_btn.config(state=tk.DISABLED)
        self.pick_winners_btn.config(state=tk.NORMAL)
    
    def _import_file(self) -> None:
        """Import participants from file."""
        file_path = filedialog.askopenfilename(
            title="Select chat file",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            success = self.datasource.import_from_file(file_path)
            if success:
                self._apply_filters()  # Auto-apply filters after import
    
    def _clear_all(self) -> None:
        """Clear all participants and reset the application."""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all participants and winners?"):
            self.datasource.clear_participants()
            self.participants.clear()
            self.eligible_usernames.clear()
            self.winners.clear()
            self._update_ui()
    
    def _apply_filters(self) -> None:
        """Apply current filters to participants."""
        # Get current participants
        self.participants = self.datasource.get_participants()
        
        # Update filter settings
        self.filter.set_keyword_filter(self.keyword_var.get())
        self.filter.set_minimum_messages(self.min_messages_var.get())
        
        # Get blacklist
        blacklist_text = self.blacklist_text.get(1.0, tk.END).strip()
        blacklist = [line.strip() for line in blacklist_text.split('\n') if line.strip()]
        self.filter.set_blacklist(blacklist)
        
        # Apply filters
        self.eligible_usernames = self.filter.apply_filters(self.participants)
        
        # Update UI
        self._update_ui()
        
        # Update status
        filter_summary = self.filter.get_filter_summary()
        self._set_status(
            f"Filters applied. {len(self.eligible_usernames)} of {len(self.participants)} participants eligible"
        )
    
    def _pick_winners(self) -> None:
        """Pick random winners from eligible participants."""
        if not self.eligible_usernames:
            messagebox.showwarning("No Eligible Participants", 
                                 "No eligible participants found. Please check your filters.")
            return
        
        num_winners = self.num_winners_var.get()
        if num_winners > len(self.eligible_usernames):
            messagebox.showerror("Too Many Winners", 
                               f"Cannot select {num_winners} winners from {len(self.eligible_usernames)} eligible participants.")
            return
        
        try:
            # Prepare message counts for weighted selection
            message_counts = {username: self.participants[username.lower()].message_count 
                            for username in self.eligible_usernames}
            
            # Pick winners
            self.winners = self.selector.pick_winners(
                self.eligible_usernames,
                num_winners,
                self.weighted_selection_var.get(),
                message_counts
            )
            
            # Update UI
            self._update_winners_display()
            
            # Update session
            self.current_session.winners = self.winners
            
            self._set_status(f"Selected {len(self.winners)} winners")
            
        except Exception as e:
            messagebox.showerror("Error Picking Winners", f"Error selecting winners: {str(e)}")
    
    def _export_winners(self) -> None:
        """Export winners to CSV."""
        if not self.winners:
            messagebox.showwarning("No Winners", "No winners to export. Please pick winners first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Winners",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if file_path:
            success = self.exporter.export_winners(self.winners, file_path, self.current_session)
            if success:
                self._set_status(f"Winners exported to {file_path}")
                messagebox.showinfo("Export Successful", f"Winners exported to {file_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to export winners")
    
    def _export_all(self) -> None:
        """Export all participants to CSV."""
        if not self.participants:
            messagebox.showwarning("No Participants", "No participants to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export All Participants",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if file_path:
            filter_summary = self.filter.get_filter_summary()
            success = self.exporter.export_all_participants(
                self.participants, self.winners, file_path, 
                self.current_session, self.eligible_usernames, filter_summary
            )
            if success:
                self._set_status(f"All participants exported to {file_path}")
                messagebox.showinfo("Export Successful", f"All participants exported to {file_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to export participants")
    
    def _show_auth_setup(self) -> None:
        """Show authentication setup dialog."""
        auth_window = tk.Toplevel(self.root)
        auth_window.title("YouTube API Authentication")
        auth_window.geometry("700x500")
        auth_window.transient(self.root)
        auth_window.grab_set()
        
        # Mode selection frame
        mode_frame = ttk.LabelFrame(auth_window, text="Usage Modes")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        mode_text = tk.Text(mode_frame, height=6, wrap=tk.WORD)
        mode_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        mode_info = """
🌐 URL-Only Mode (No API Required):
• Use "Resolve URL" and "Import from URL" buttons
• Generate demo participants based on any YouTube URL
• Perfect for testing and demonstrations
• No Google account or API setup needed

🔴 Live API Mode (Requires Authentication):
• Monitor real YouTube live chat in real-time
• Requires Google Cloud Console setup and API credentials
• Use "Resolve Live" and live fetch buttons
        """.strip()
        
        mode_text.insert(1.0, mode_info)
        mode_text.config(state=tk.DISABLED)
        
        # Status frame
        status_frame = ttk.LabelFrame(auth_window, text="API Authentication Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        auth_status = self.oauth.get_auth_status()
        status_text = tk.Text(status_frame, height=6, wrap=tk.WORD)
        status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        status_info = f"""
Credentials File: {'✓' if auth_status['has_credentials_file'] else '✗'} {self.oauth.credentials_file}
Token File: {'✓' if auth_status['has_token_file'] else '✗'} {self.oauth.token_file}
Valid Token: {'✓' if auth_status['has_valid_token'] else '✗'}
Authenticated: {'✓' if auth_status['is_authenticated'] else '✗'}

{auth_status.get('error', 'No errors')}
        """.strip()
        
        status_text.insert(1.0, status_info)
        status_text.config(state=tk.DISABLED)
        
        # Instructions frame
        instructions_frame = ttk.LabelFrame(auth_window, text="Setup Instructions")
        instructions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instructions_text = tk.Text(instructions_frame, wrap=tk.WORD)
        instructions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        instructions_text.insert(1.0, self.oauth.setup_instructions())
        instructions_text.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = ttk.Frame(auth_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def authenticate():
            auth_window.destroy()
            self._authenticate_youtube()
        
        def revoke():
            if messagebox.askyesno("Revoke Authentication", "Are you sure you want to revoke authentication?"):
                self.oauth.revoke_credentials()
                self._update_youtube_api_status()
                auth_window.destroy()
        
        ttk.Button(buttons_frame, text="Authenticate", command=authenticate).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Revoke", command=revoke).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Close", command=auth_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _authenticate_youtube(self) -> bool:
        """Authenticate with YouTube API."""
        if not self.oauth.has_credentials_file():
            messagebox.showerror("Missing Credentials", 
                               f"Please place your client_secret.json file in the application directory.\n\n"
                               f"See Auth Setup for detailed instructions.")
            return False
        
        self._set_status("Authenticating with YouTube...")
        
        def auth_thread():
            success = self.youtube_api.authenticate()
            if success:
                # Test connection
                test_success, test_msg = self.youtube_api.test_api_connection()
                if test_success:
                    self._set_status(f"Authentication successful. {test_msg}")
                else:
                    self._set_status(f"Authentication completed but test failed: {test_msg}")
            else:
                self._set_status("Authentication failed")
            
            self._update_youtube_api_status()
        
        threading.Thread(target=auth_thread, daemon=True).start()
        return True
    
    def _update_youtube_api_status(self) -> None:
        """Update UI based on YouTube API authentication status."""
        if self.youtube_api.is_authenticated():
            self.root.title("YouTube Chat Giveaway - ✓ API Authenticated")
        else:
            self.root.title("YouTube Chat Giveaway - 🌐 URL-Only Mode")
    
    def _update_ui(self) -> None:
        """Update the entire UI with current data."""
        self._update_participants_display()
        self._update_counts()
        self._update_winners_display()
    
    def _update_participants_display(self) -> None:
        """Update the participants listbox."""
        self.participants_listbox.delete(0, tk.END)
        
        for username in sorted(self.eligible_usernames):
            participant = self.participants.get(username.lower())
            if participant:
                display_text = f"{participant.username} ({participant.message_count})"
                self.participants_listbox.insert(tk.END, display_text)
    
    def _update_counts(self) -> None:
        """Update participant counts."""
        total_count = len(self.participants)
        eligible_count = len(self.eligible_usernames)
        
        self.participants_count_label.config(text=f"Total: {total_count}")
        self.eligible_count_label.config(text=f"Eligible: {eligible_count}")
    
    def _update_winners_display(self) -> None:
        """Update the winners listbox."""
        self.winners_listbox.delete(0, tk.END)
        
        for winner in self.winners:
            display_text = f"{winner.draw_order}. {winner.username}"
            self.winners_listbox.insert(tk.END, display_text)
    
    def _set_status(self, message: str) -> None:
        """Set status bar message."""
        if self.status_label:
            self.status_label.config(text=message)
    
    # Callback methods for data source
    def _on_participants_updated(self) -> None:
        """Called when participants are updated from data source."""
        # Update UI in main thread
        self.root.after(0, lambda: self._apply_filters())
    
    def _on_status_changed(self, status: str) -> None:
        """Called when status changes from data source."""
        self.root.after(0, lambda: self._set_status(status))
    
    def _on_error(self, error: str) -> None:
        """Called when error occurs in data source."""
        self.root.after(0, lambda: self._set_status(f"Error: {error}"))
    
    def _on_closing(self) -> None:
        """Handle application closing."""
        # Stop any live fetching
        self.datasource.stop_live_fetch()
        
        # Clean up resources
        self.datasource.cleanup()
        
        # Close the window
        self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = YouTubeGiveawayApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
