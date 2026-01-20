"""
Simulation screen for SimpleSim.

Runs the physics simulation and displays real-time information
in a sidebar with Log, Analytics, and Warnings tabs.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import sys
import threading
import socket
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, Any
from queue import Queue, Empty

from .base_screen import BaseScreen
from simplesim.theming import Colors

if TYPE_CHECKING:
    from simplesim.app import SimpleSimApp


class SimulationScreen(BaseScreen):
    """
    Simulation screen with control and monitoring sidebar.

    Features:
    - Start/Stop simulation controls
    - Log tab: Real-time simulation output
    - Analytics tab: Joint positions, motor commands, sensor readings
    - Warnings tab: Active simulation warnings
    """

    TITLE = "Simulation"
    HAS_BACK_BUTTON = False  # Use custom Stop button instead

    def __init__(self, app: 'SimpleSimApp', container: tk.Frame):
        super().__init__(app, container)

        # Process handles
        self.robot_process: Optional[subprocess.Popen] = None
        self.bridge_process: Optional[subprocess.Popen] = None

        # Threads
        self.robot_log_thread: Optional[threading.Thread] = None
        self.bridge_log_thread: Optional[threading.Thread] = None
        self.analytics_thread: Optional[threading.Thread] = None

        # State
        self._running = False
        self._analytics_socket: Optional[socket.socket] = None
        self._analytics_data: Dict[str, Any] = {}
        self._log_queue: Queue = Queue()
        self._warnings: list = []
        self._start_time: float = 0.0
        self._message_count: int = 0

        # UI elements (initialized in build())
        self._status_label = None
        self._log_text = None
        self._stats_labels: Dict[str, Any] = {}
        self._analytics_frame = None
        self._analytics_widgets: Dict[str, Any] = {}
        self._warnings_frame = None

    def build(self):
        """Build the simulation screen UI."""
        project = self.app.current_project

        # Custom navigation bar with Stop button
        nav_frame = tk.Frame(self.frame, bg=Colors.BG_SECONDARY, height=60)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)

        nav_inner = tk.Frame(nav_frame, bg=Colors.BG_SECONDARY)
        nav_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Stop button (replaces back button)
        stop_btn = ttk.Button(
            nav_inner,
            text="\u25A0 Stop Simulation",
            style="Danger.TButton",
            command=self._stop_simulation
        )
        stop_btn.pack(side=tk.LEFT)

        # Title
        title_label = ttk.Label(
            nav_inner,
            text=f"Simulation - {project.name}",
            style="Header.TLabel"
        )
        title_label.pack(side=tk.LEFT, padx=(20, 0))

        # Status indicator
        self._status_label = ttk.Label(
            nav_inner,
            text="Starting...",
            style="Muted.TLabel"
        )
        self._status_label.pack(side=tk.RIGHT)

        # Main content: split between info and sidebar
        main_content = tk.Frame(self.frame, bg=Colors.BG_PRIMARY)
        main_content.pack(fill=tk.BOTH, expand=True)

        # Left side: Instructions and status
        left_panel = tk.Frame(main_content, bg=Colors.BG_PRIMARY)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._create_left_panel(left_panel)

        # Right side: Tabbed sidebar
        right_panel = tk.Frame(main_content, bg=Colors.BG_SECONDARY, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0), pady=0)
        right_panel.pack_propagate(False)

        self._create_sidebar(right_panel)

    def _create_left_panel(self, parent):
        """Create the left information panel."""
        # Instructions
        info_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        info_frame.pack(fill=tk.X, pady=(0, 20))

        info_inner = tk.Frame(info_frame, bg=Colors.BG_SECONDARY)
        info_inner.pack(fill=tk.X, padx=20, pady=15)

        info_title = tk.Label(
            info_inner,
            text="\U0001F4A1 Simulation Running",
            font=("Segoe UI", 14, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY
        )
        info_title.pack(anchor=tk.W)

        info_text = tk.Label(
            info_inner,
            text="The PyBullet physics window should open separately.\n"
                 "Use your robot code's driver station or gamepad to control the simulation.\n"
                 "Monitor the sidebar for real-time data and warnings.",
            font=("Segoe UI", 10),
            fg=Colors.TEXT_SECONDARY,
            bg=Colors.BG_SECONDARY,
            justify=tk.LEFT,
            anchor=tk.W
        )
        info_text.pack(anchor=tk.W, pady=(10, 0))

        # Quick stats
        stats_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        stats_frame.pack(fill=tk.X)

        stats_inner = tk.Frame(stats_frame, bg=Colors.BG_SECONDARY)
        stats_inner.pack(fill=tk.X, padx=20, pady=15)

        stats_title = tk.Label(
            stats_inner,
            text="Quick Stats",
            font=("Segoe UI", 12, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY
        )
        stats_title.pack(anchor=tk.W, pady=(0, 10))

        # Stats will be updated dynamically
        self._stats_labels = {}
        for stat_name in ["Simulation Time", "Messages Received", "Active Warnings"]:
            row = tk.Frame(stats_inner, bg=Colors.BG_SECONDARY)
            row.pack(fill=tk.X, pady=2)

            name_label = tk.Label(
                row,
                text=f"{stat_name}:",
                font=("Segoe UI", 10),
                fg=Colors.TEXT_SECONDARY,
                bg=Colors.BG_SECONDARY
            )
            name_label.pack(side=tk.LEFT)

            value_label = tk.Label(
                row,
                text="--",
                font=("Segoe UI", 10, "bold"),
                fg=Colors.TEXT_PRIMARY,
                bg=Colors.BG_SECONDARY
            )
            value_label.pack(side=tk.RIGHT)

            self._stats_labels[stat_name] = value_label

    def _create_sidebar(self, parent):
        """Create the tabbed sidebar."""
        # Notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Log tab
        log_frame = tk.Frame(notebook, bg=Colors.BG_PRIMARY)
        notebook.add(log_frame, text="Log")
        self._create_log_tab(log_frame)

        # Analytics tab
        analytics_frame = tk.Frame(notebook, bg=Colors.BG_PRIMARY)
        notebook.add(analytics_frame, text="Analytics")
        self._create_analytics_tab(analytics_frame)

        # Warnings tab
        warnings_frame = tk.Frame(notebook, bg=Colors.BG_PRIMARY)
        notebook.add(warnings_frame, text="Warnings")
        self._create_warnings_tab(warnings_frame)

    def _create_log_tab(self, parent):
        """Create the log tab content."""
        # Log text area
        self._log_text = scrolledtext.ScrolledText(
            parent,
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_PRIMARY,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self._log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure tags for colored output
        self._log_text.tag_configure("robot", foreground=Colors.INFO)
        self._log_text.tag_configure("bridge", foreground=Colors.SUCCESS)
        self._log_text.tag_configure("warning", foreground=Colors.WARNING)
        self._log_text.tag_configure("error", foreground=Colors.ERROR)
        self._log_text.tag_configure("physics", foreground=Colors.TEXT_SECONDARY)

    def _create_analytics_tab(self, parent):
        """Create the analytics tab content."""
        # Scrollable frame for analytics
        canvas = tk.Canvas(parent, bg=Colors.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner_frame = tk.Frame(canvas, bg=Colors.BG_PRIMARY)
        canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)

        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", configure_scroll)

        # Store reference
        self._analytics_frame = inner_frame
        self._analytics_widgets = {}

        # Will be populated when simulation starts
        placeholder = tk.Label(
            inner_frame,
            text="Analytics data will appear here\nwhen the simulation starts",
            font=("Segoe UI", 10),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_PRIMARY,
            justify=tk.CENTER
        )
        placeholder.pack(pady=50)
        self._analytics_placeholder = placeholder

    def _create_warnings_tab(self, parent):
        """Create the warnings tab content."""
        # Warnings list
        self._warnings_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        self._warnings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Placeholder
        self._warnings_placeholder = tk.Label(
            self._warnings_frame,
            text="No warnings",
            font=("Segoe UI", 10),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_PRIMARY
        )
        self._warnings_placeholder.pack(pady=50)

    def _log(self, message: str, tag: str = None):
        """Add message to log."""
        self._log_queue.put((message, tag))

    def _process_log_queue(self):
        """Process queued log messages (called from main thread)."""
        if not self._log_text:
            # UI not built yet, reschedule
            if self._running:
                self.frame.after(100, self._process_log_queue)
            return

        try:
            while True:
                message, tag = self._log_queue.get_nowait()
                self._log_text.configure(state=tk.NORMAL)
                if tag:
                    self._log_text.insert(tk.END, message + "\n", tag)
                else:
                    self._log_text.insert(tk.END, message + "\n")
                self._log_text.see(tk.END)
                self._log_text.configure(state=tk.DISABLED)
        except Empty:
            pass

        if self._running:
            self.frame.after(100, self._process_log_queue)

    def _start_simulation(self):
        """Start the simulation."""
        project = self.app.current_project
        if not project:
            return

        self._running = True
        self._start_time = time.time()
        self._message_count = 0

        # Start log processing
        self.frame.after(100, self._process_log_queue)

        # Start stats update
        self.frame.after(1000, self._update_stats)

        # Log start
        self._log("=" * 50)
        self._log(f"Starting simulation for: {project.name}")
        self._log("=" * 50)

        # Start robot code
        self._start_robot_code(project)

        # Wait a bit for robot code to initialize, then start bridge
        self.frame.after(3000, lambda: self._start_bridge(project))

    def _start_robot_code(self, project):
        """Start the robot code subprocess."""
        robot_path = Path(project.robot_code_path)

        # Determine command based on project type
        cmd = self._get_robot_command(robot_path)
        if not cmd:
            self._log("ERROR: Could not determine robot code type", "error")
            return

        self._log(f"Robot code command: {' '.join(cmd)}", "robot")

        try:
            self.robot_process = subprocess.Popen(
                cmd,
                cwd=str(robot_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Start log reader thread
            self.robot_log_thread = threading.Thread(
                target=self._read_robot_output,
                daemon=True
            )
            self.robot_log_thread.start()

            self._log("Robot code started", "robot")
            if self._status_label:
                self._status_label.configure(text="Robot code running...")

        except Exception as e:
            self._log(f"ERROR starting robot code: {e}", "error")

    def _get_robot_command(self, robot_path: Path):
        """Determine the command to run robot code."""
        # Check for Gradle (Java/C++)
        if (robot_path / "build.gradle").exists():
            gradlew = "gradlew.bat" if sys.platform == "win32" else "gradlew"
            gradlew_path = robot_path / gradlew
            if gradlew_path.exists():
                return [str(gradlew_path), "simulateJava", "-Phalsim"]

        # Check for Python (robotpy)
        if (robot_path / "robot.py").exists():
            return [sys.executable, "-m", "robotpy", "sim", "--ws-server"]

        return None

    def _read_robot_output(self):
        """Read robot code output in background thread."""
        if not self.robot_process:
            return

        for line in self.robot_process.stdout:
            line = line.rstrip()
            if line:
                self._log(f"[ROBOT] {line}", "robot")

    def _start_bridge(self, project):
        """Start the WebSocket bridge subprocess."""
        if not self._running:
            return

        self._log("Starting WebSocket bridge...", "bridge")

        try:
            cmd = [
                sys.executable, "-u",
                "-m", "subsystemsim.hal_bridge.websocket_bridge",
                "--config", str(project.config_path)
            ]

            self.bridge_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Start log reader thread
            self.bridge_log_thread = threading.Thread(
                target=self._read_bridge_output,
                daemon=True
            )
            self.bridge_log_thread.start()

            if self._status_label:
                self._status_label.configure(text="Simulation running")
            self._log("WebSocket bridge started", "bridge")

        except Exception as e:
            self._log(f"ERROR starting bridge: {e}", "error")

    def _read_bridge_output(self):
        """Read bridge output in background thread."""
        if not self.bridge_process:
            return

        for line in self.bridge_process.stdout:
            line = line.rstrip()
            if line:
                self._message_count += 1

                # Color code different message types
                if "[PHYSICS]" in line:
                    self._log(line, "physics")
                    self._parse_physics_line(line)
                elif "[WARNING]" in line:
                    self._log(line, "warning")
                    self._add_warning(line)
                elif "[ERROR]" in line or "Error" in line:
                    self._log(line, "error")
                else:
                    self._log(line, "bridge")

    def _parse_physics_line(self, line: str):
        """Parse physics debug output for analytics."""
        # Format: [PHYSICS] pos=0.500m, vel=0.100m/s, cmd=0.250, force=50.0N
        try:
            parts = line.split("]")[1].strip().split(",")
            for part in parts:
                part = part.strip()
                if "=" in part:
                    key, value = part.split("=", 1)
                    self._analytics_data[key.strip()] = value.strip()
        except Exception:
            pass

    def _add_warning(self, line: str):
        """Add a warning to the warnings list."""
        self._warnings.append({
            "time": time.time(),
            "message": line
        })

        # Update warnings tab (schedule in main thread)
        self.frame.after(0, self._update_warnings_display)

    def _update_warnings_display(self):
        """Update the warnings tab display."""
        # Clear placeholder
        if hasattr(self, '_warnings_placeholder') and self._warnings_placeholder.winfo_exists():
            self._warnings_placeholder.destroy()

        # Show last 20 warnings
        recent = self._warnings[-20:]

        # Clear existing
        for child in self._warnings_frame.winfo_children():
            child.destroy()

        if not recent:
            self._warnings_placeholder = tk.Label(
                self._warnings_frame,
                text="No warnings",
                font=("Segoe UI", 10),
                fg=Colors.TEXT_MUTED,
                bg=Colors.BG_PRIMARY
            )
            self._warnings_placeholder.pack(pady=50)
            return

        for warning in reversed(recent):
            warning_frame = tk.Frame(self._warnings_frame, bg=Colors.BG_SECONDARY)
            warning_frame.pack(fill=tk.X, pady=2)

            # Warning icon
            icon = tk.Label(
                warning_frame,
                text="\u26A0",
                font=("Segoe UI", 12),
                fg=Colors.WARNING,
                bg=Colors.BG_SECONDARY
            )
            icon.pack(side=tk.LEFT, padx=5, pady=5)

            # Message
            msg = tk.Label(
                warning_frame,
                text=warning["message"][:80],
                font=("Segoe UI", 9),
                fg=Colors.TEXT_PRIMARY,
                bg=Colors.BG_SECONDARY,
                anchor=tk.W
            )
            msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

    def _update_stats(self):
        """Update quick stats display."""
        if not self._running:
            return

        # Check if stats labels are ready
        if not self._stats_labels or "Simulation Time" not in self._stats_labels:
            # UI not fully built yet, reschedule
            self.frame.after(1000, self._update_stats)
            return

        # Simulation time
        elapsed = time.time() - self._start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self._stats_labels["Simulation Time"].configure(text=f"{minutes}:{seconds:02d}")

        # Messages
        self._stats_labels["Messages Received"].configure(text=str(self._message_count))

        # Warnings
        self._stats_labels["Active Warnings"].configure(text=str(len(self._warnings)))

        # Schedule next update
        self.frame.after(1000, self._update_stats)

    def _stop_simulation(self):
        """Stop the simulation and navigate back."""
        self._running = False
        if self._status_label:
            self._status_label.configure(text="Stopping...")

        # Terminate processes
        if self.bridge_process:
            try:
                self.bridge_process.terminate()
                self.bridge_process.wait(timeout=5)
            except Exception:
                try:
                    self.bridge_process.kill()
                except Exception:
                    pass
            self.bridge_process = None

        if self.robot_process:
            try:
                self.robot_process.terminate()
                self.robot_process.wait(timeout=5)
            except Exception:
                try:
                    self.robot_process.kill()
                except Exception:
                    pass
            self.robot_process = None

        self._log("Simulation stopped")

        # Navigate back
        self.navigate_back()

    def on_enter(self):
        """Start simulation when screen becomes visible."""
        self._start_simulation()

    def on_exit(self):
        """Clean up when leaving screen."""
        if self._running:
            self._running = False

            # Terminate processes
            if self.bridge_process:
                try:
                    self.bridge_process.terminate()
                except Exception:
                    pass

            if self.robot_process:
                try:
                    self.robot_process.terminate()
                except Exception:
                    pass
