import curses
import time
import subprocess
from datetime import datetime

class OnyxUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(1)  # Show cursor
        self.stdscr.nodelay(True) # Non-blocking input
        self.stdscr.timeout(100) # 100ms timeout for getch

        # Colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # Matrix style
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Info
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning/System
        
        self.messages = []
        self.input_buffer = []
        self.user_count = 0
        self.connection_status = "Connecting..."
        self.commands = [] # List of available commands for autocomplete
        
        self.version = self.get_version() # Cache version once at startup

        self.setup_windows()
        self.redraw_all() # Draw interface immediately at startup
        
    def get_version(self):
        try:
            # We assume CWD is the project root (where .git is)
            commit_count = int(subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip())
            
            major = commit_count // 100
            minor = (commit_count % 100) // 10
            patch = commit_count % 10
            return f"v{major}.{minor}.{patch}"
        except:
            return "v1.0.0"

    def setup_windows(self):
        """Calculates window sizes and positions."""
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Header: Top 1 line
        self.header_win = curses.newwin(1, self.width, 0, 0)
        
        # Input: Bottom 3 lines (Border + Input)
        self.input_height = 3
        self.input_win = curses.newwin(self.input_height, self.width, self.height - self.input_height, 0)
        
        # Messages: Remaining middle area
        self.msg_height = self.height - 1 - self.input_height
        self.msg_win = curses.newwin(self.msg_height, self.width, 1, 0)
        self.msg_win.scrollok(True)

    def redraw_all(self):
        self.stdscr.refresh() # Refresh background first
        self.draw_header()
        self.draw_messages()
        self.draw_input()
        curses.doupdate()

    def resize(self):
        curses.update_lines_cols()
        self.setup_windows()
        self.redraw_all()

    def draw_header(self):
        self.header_win.erase()
        self.header_win.bkgd(' ', curses.color_pair(2) | curses.A_REVERSE)
        
        # Use cached version to avoid subprocess lag
        title = f" OnyxNet {self.version} "
        status = f" Status: {self.connection_status} | Users: {self.user_count} "
        
        # Left align title
        self.header_win.addstr(0, 0, title, curses.A_BOLD)
        
        # Right align status
        if len(status) < self.width:
            try:
                # Ensure we don't write to the very last character of the line/window
                # if the window width exactly matches, writing to the last char might move cursor out of bounds
                x_pos = self.width - len(status)
                if x_pos >= 0:
                    # Truncate if somehow larger (though the if checks simple length)
                    self.header_win.addstr(0, x_pos, status[:self.width-1])
            except curses.error:
                pass
        
        self.header_win.noutrefresh()

    def draw_messages(self):
        self.msg_win.erase()
        
        # Keep last N messages that fit
        # Simple rendering: just reprint the last (height) messages
        # Actual scrolling logic would need an offset, but let's stick to "tail" for now.
        lines_to_draw = self.messages[-self.msg_height:]
        
        for i, (timestamp, sender, text) in enumerate(lines_to_draw):
            try:
                # Format: [HH:MM] <Sender> Message
                time_str = f"[{timestamp}] "
                self.msg_win.addstr(i, 0, time_str, curses.color_pair(2))
                
                sender_str = f"<{sender}> "
                self.msg_win.addstr(sender_str, curses.color_pair(1) | curses.A_BOLD)
                
                self.msg_win.addstr(text + "\n")
            except curses.error:
                pass 
                
        self.msg_win.box() # Optional box
        self.msg_win.noutrefresh()

    def draw_input(self):
        self.input_win.erase()
        self.input_win.box()
        
        prompt = "> "
        self.input_win.addstr(1, 1, prompt, curses.color_pair(1) | curses.A_BOLD)
        
        input_str = "".join(self.input_buffer)
        self.input_win.addstr(1, 1 + len(prompt), input_str)
        
        self.input_win.noutrefresh()

    def add_message(self, sender, text, system=False):
        timestamp = datetime.now().strftime("%H:%M")
        self.messages.append((timestamp, sender, text))
        self.draw_messages()
        curses.doupdate()

    def autocomplete(self):
        """Simple autocomplete for commands."""
        current_input = "".join(self.input_buffer)
        if not current_input.startswith('/'):
            return
            
        matches = [cmd for cmd in self.commands if cmd.startswith(current_input)]
        
        if len(matches) == 1:
            # Complete the command
            completed = matches[0] + " " # Add space for convenience
            self.input_buffer = list(completed)
            self.draw_input()
            curses.doupdate()
        elif len(matches) > 1:
            # Maybe list options in system message?
            # For now, just do common prefix? 
            # Let's keep it simple: do nothing if multiple, or maybe show hints.
            pass

    def show_popup(self, title, text):
        """Displays a modal popup window."""
        h, w = 12, 60
        y = (self.height - h) // 2
        x = (self.width - w) // 2
        
        # Ensure dimensions fit
        if y < 0: y = 0
        if x < 0: x = 0
        
        popup = curses.newwin(h, w, y, x)
        popup.box()
        popup.bkgd(' ', curses.color_pair(3)) # Yellow background/text style
        
        popup.addstr(1, 2, title, curses.A_BOLD)
        
        # Wrap text manually or just print lines
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 3 + i < h - 2:
                popup.addstr(3 + i, 2, line[:w-4])
        
        popup.addstr(h-2, 2, "Press any key to close...", curses.A_DIM)
        popup.refresh()
        
        # Block until keypress
        old_nodelay = self.stdscr.nodelay(False) # Disable non-blocking
        self.stdscr.getch()
        self.stdscr.nodelay(True) # Restore non-blocking
        
        del popup
        self.redraw_all()

    async def get_input(self):
        """Async wrapper to poll for input."""
        try:
            # Check for resize event (KEY_RESIZE)
            key = self.stdscr.getch()
            
            if key == curses.KEY_RESIZE:
                self.resize()
                return None
            
            if key == -1:
                return None
            
            if key == 9: # TAB
                self.autocomplete()
                return None
                
            if key in (10, 13): # Enter
                msg = "".join(self.input_buffer)
                self.input_buffer = []
                self.draw_input()
                curses.doupdate()
                if msg:
                    return msg
                return None
                
            if key in (8, 127, curses.KEY_BACKSPACE): # Backspace
                if self.input_buffer:
                    self.input_buffer.pop()
                    self.draw_input()
                    curses.doupdate()
                return None
            
            if 32 <= key <= 126: # Printable chars
                self.input_buffer.append(chr(key))
                self.draw_input()
                curses.doupdate()
                return None
                
        except curses.error:
            pass
            
        return None
