"""
SubsystemSim GUI Application

A complete tool for FRC teams to simulate their robot subsystems with real CAD and code.

Features:
- Import CAD files (STEP, OBJ, STL)
- Create/edit subsystem configuration (joints, motors, sensors)
- Import robot code (Java, C++, Python)
- Run physics simulation with WebSocket bridge
- Real-time visualization with PyBullet
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, List
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class SubsystemSimApp:
    """Main GUI application for SubsystemSim."""

    def __init__(self, root):
        self.root = root
        self.root.title("SubsystemSim - FRC Subsystem Simulator")
        self.root.geometry("1200x800")

        # Application state
        self.cad_files: List[Path] = []
        self.robot_code_path: Optional[Path] = None
        self.config_data: Dict = self._default_config()
        self.config_file_path: Optional[Path] = None
        self.simulation_process: Optional[subprocess.Popen] = None

        # Build UI
        self._create_menu()
        self._create_main_layout()

        # Status
        self.status_var.set("Ready - Import CAD files to begin")

    def _default_config(self) -> Dict:
        """Create default configuration structure."""
        return {
            "name": "my_subsystem",
            "links": [],
            "joints": [],
            "motors": [],
            "sensors": []
        }

    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_command(label="Save Config As...", command=self.save_config_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Examples menu
        examples_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Examples", menu=examples_menu)
        examples_menu.add_command(label="Load Simple Arm Example", command=self.load_simple_arm_example)
        examples_menu.add_command(label="Download FRC CAD Resources", command=self.show_cad_resources)
        examples_menu.add_command(label="Download Java Robot Examples", command=self.show_java_examples)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)

    def _create_main_layout(self):
        """Create main application layout."""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: CAD Import
        self.cad_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cad_frame, text="1. CAD Import")
        self._create_cad_import_tab()

        # Tab 2: Config Editor
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="2. Configuration")
        self._create_config_tab()

        # Tab 3: Robot Code
        self.code_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.code_frame, text="3. Robot Code")
        self._create_robot_code_tab()

        # Tab 4: Simulation
        self.sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_frame, text="4. Run Simulation")
        self._create_simulation_tab()

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_cad_import_tab(self):
        """Create CAD import interface."""
        # Instructions
        instructions = ttk.Label(self.cad_frame, text=
            "Import your FRC subsystem CAD files (OBJ, STL)\n"
            "Each mesh file will become a link in your mechanism.\n"
            "For STEP files, use 'Convert STEP Online' button (free, 30 seconds).",
            justify=tk.LEFT, padding=10)
        instructions.pack(anchor=tk.W)

        # Import button
        import_frame = ttk.Frame(self.cad_frame)
        import_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(import_frame, text="Import CAD Files (OBJ/STL)",
                   command=self.import_cad).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Convert STEP Online →",
                   command=self.open_step_converter).pack(side=tk.LEFT, padx=5)
        ttk.Button(import_frame, text="Clear All",
                   command=self.clear_cad).pack(side=tk.LEFT, padx=5)

        # File list
        list_frame = ttk.LabelFrame(self.cad_frame, text="Imported CAD Files", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrolled listbox
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.cad_listbox = tk.Listbox(list_frame, yscrollcommand=scroll.set, height=15)
        self.cad_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.cad_listbox.yview)

        # Auto-generate config button
        ttk.Button(self.cad_frame, text="Auto-Generate Config from CAD Files →",
                   command=self.auto_generate_config,
                   style='Accent.TButton').pack(pady=10)

    def _create_config_tab(self):
        """Create configuration editor interface."""
        # Instructions
        instructions = ttk.Label(self.config_frame, text=
            "Define your subsystem configuration (joints, motors, sensors)\n"
            "Edit the JSON directly or use the forms below.",
            justify=tk.LEFT, padding=10)
        instructions.pack(anchor=tk.W)

        # JSON editor
        editor_frame = ttk.LabelFrame(self.config_frame, text="Configuration JSON", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.config_text = scrolledtext.ScrolledText(editor_frame, height=25, width=80)
        self.config_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(self.config_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="Load from File",
                   command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save to File",
                   command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Validate",
                   command=self.validate_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Default",
                   command=self.reset_config).pack(side=tk.LEFT, padx=5)

        # Load default config into editor
        self._update_config_display()

    def _create_robot_code_tab(self):
        """Create robot code import interface."""
        # Instructions
        instructions = ttk.Label(self.code_frame, text=
            "Select your robot code project folder\n"
            "Supports Java (Gradle), C++ (Gradle), and Python projects.",
            justify=tk.LEFT, padding=10)
        instructions.pack(anchor=tk.W)

        # Path selection
        path_frame = ttk.LabelFrame(self.code_frame, text="Robot Code Path", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=10)

        self.code_path_var = tk.StringVar(value="No robot code selected")
        ttk.Label(path_frame, textvariable=self.code_path_var,
                  relief=tk.SUNKEN, width=80).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="Browse...",
                   command=self.browse_robot_code).pack(side=tk.LEFT, padx=5)

        # Detected info
        info_frame = ttk.LabelFrame(self.code_frame, text="Project Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.code_info_text = scrolledtext.ScrolledText(info_frame, height=20, width=80)
        self.code_info_text.pack(fill=tk.BOTH, expand=True)
        self.code_info_text.insert('1.0', "No robot code loaded.\n\nSelect a robot code folder to see project details.")
        self.code_info_text.config(state=tk.DISABLED)

    def _create_simulation_tab(self):
        """Create simulation control interface."""
        # Instructions
        instructions = ttk.Label(self.sim_frame, text=
            "Run the simulation with your CAD, config, and robot code\n"
            "The WebSocket bridge will connect your robot code to the physics simulation.",
            justify=tk.LEFT, padding=10)
        instructions.pack(anchor=tk.W)

        # Control buttons
        control_frame = ttk.LabelFrame(self.sim_frame, text="Simulation Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.start_sim_btn = ttk.Button(control_frame, text="▶ Start Simulation",
                                         command=self.start_simulation,
                                         style='Accent.TButton')
        self.start_sim_btn.pack(side=tk.LEFT, padx=5)

        self.stop_sim_btn = ttk.Button(control_frame, text="⏹ Stop Simulation",
                                        command=self.stop_simulation,
                                        state=tk.DISABLED)
        self.stop_sim_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Open Config Folder",
                   command=self.open_config_folder).pack(side=tk.LEFT, padx=5)

        # Status and logs
        log_frame = ttk.LabelFrame(self.sim_frame, text="Simulation Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.sim_log = scrolledtext.ScrolledText(log_frame, height=25, width=80)
        self.sim_log.pack(fill=tk.BOTH, expand=True)
        self.sim_log.insert('1.0', "Simulation not started.\n\nClick 'Start Simulation' to begin.")

        # Instructions at bottom
        instructions_text = (
            "\n"
            "How to run:\n"
            "1. Load CAD files and create configuration\n"
            "2. Select robot code folder (Java/C++/Python project)\n"
            "3. Click 'Start Simulation' - Everything runs automatically!\n"
            "\n"
            "SubsystemSim will:\n"
            "- Start your robot code (compiles if needed)\n"
            "- Launch PyBullet physics window\n"
            "- Connect them via WebSocket\n"
            "- Your code controls the simulation in real-time!\n"
        )
        ttk.Label(self.sim_frame, text=instructions_text,
                  justify=tk.LEFT, padding=10).pack()

    # ==================== CAD Import Methods ====================

    def import_cad(self):
        """Import CAD files (OBJ, STL)."""
        files = filedialog.askopenfilenames(
            title="Select CAD Mesh Files",
            filetypes=[
                ("Mesh Files", "*.obj *.stl"),
                ("OBJ Files", "*.obj"),
                ("STL Files", "*.stl"),
                ("All Files", "*.*")
            ]
        )

        if files:
            for file_path in files:
                path = Path(file_path)
                if path not in self.cad_files:
                    self.cad_files.append(path)
                    self.cad_listbox.insert(tk.END, f"{path.stem} ({path.suffix})")

            self.status_var.set(f"Imported {len(files)} CAD file(s)")

    def open_step_converter(self):
        """Open online STEP to OBJ converter."""
        result = messagebox.showinfo(
            "STEP to OBJ Conversion",
            "SubsystemSim works with OBJ and STL mesh files.\n\n"
            "To convert STEP files:\n\n"
            "1. Click OK to open free online converter\n"
            "2. Upload your STEP file\n"
            "3. Download converted OBJ file(s)\n"
            "4. Import OBJ files using 'Import CAD Files' button\n\n"
            "Conversion takes ~30 seconds and requires no software installation.",
            icon='info'
        )

        # Open online converter
        self._open_url("https://convert3d.org/step-to-obj")

    def convert_step_to_obj_freecad(self):
        """Convert STEP files to OBJ using FreeCAD."""
        from subsystemsim.cad import check_freecad_available, convert_step_to_obj, get_freecad_install_instructions

        # Check if FreeCAD is available
        is_available, message = check_freecad_available()

        if not is_available:
            result = messagebox.askyesno(
                "FreeCAD Not Found",
                f"{message}\n\n"
                "FreeCAD is required for STEP to OBJ conversion.\n\n"
                "Would you like to see installation instructions?"
            )

            if result:
                # Show installation instructions
                instructions = get_freecad_install_instructions()
                window = tk.Toplevel(self.root)
                window.title("Install FreeCAD")
                window.geometry("600x500")

                text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text.insert('1.0', instructions)
                text.config(state=tk.DISABLED)

                # Add online converter alternative
                ttk.Button(
                    window,
                    text="Open Online Converter (Alternative)",
                    command=lambda: self._open_url("https://convert3d.org/step-to-obj")
                ).pack(pady=10)

            return

        # FreeCAD is available, proceed with conversion
        step_files = filedialog.askopenfilenames(
            title="Select STEP Files to Convert",
            filetypes=[
                ("STEP Files", "*.step *.stp"),
                ("All Files", "*.*")
            ]
        )

        if not step_files:
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(
            title="Select Output Directory for OBJ Files"
        )

        if not output_dir:
            return

        output_path = Path(output_dir)

        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Converting STEP to OBJ")
        progress_window.geometry("500x300")
        progress_window.transient(self.root)
        progress_window.grab_set()

        ttk.Label(
            progress_window,
            text="Converting STEP files to OBJ...\nThis may take a moment.",
            padding=10
        ).pack()

        log_text = scrolledtext.ScrolledText(progress_window, height=15, width=60)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Redirect print output to log window
        class GUILogger:
            def write(self, message):
                log_text.insert(tk.END, message)
                log_text.see(tk.END)
                progress_window.update()

            def flush(self):
                pass

        old_stdout = sys.stdout
        sys.stdout = GUILogger()

        try:
            # Convert all STEP files
            from subsystemsim.cad import batch_convert_step_files

            obj_files = batch_convert_step_files(
                [Path(f) for f in step_files],
                output_path
            )

            # Restore stdout
            sys.stdout = old_stdout

            if obj_files:
                # Ask if user wants to import the converted files
                result = messagebox.askyesno(
                    "Conversion Complete",
                    f"Successfully converted {len(step_files)} STEP file(s) to {len(obj_files)} OBJ file(s).\n\n"
                    f"Output directory: {output_path}\n\n"
                    "Would you like to import the OBJ files now?"
                )

                progress_window.destroy()

                if result:
                    # Import the converted OBJ files
                    for obj_file in obj_files:
                        if obj_file not in self.cad_files:
                            self.cad_files.append(obj_file)
                            self.cad_listbox.insert(tk.END, f"{obj_file.stem} (.obj)")

                    self.status_var.set(f"Converted and imported {len(obj_files)} OBJ file(s)")
            else:
                sys.stdout = old_stdout
                progress_window.destroy()
                messagebox.showerror("Conversion Failed", "No OBJ files were created. Check the log for errors.")

        except Exception as e:
            sys.stdout = old_stdout
            progress_window.destroy()
            messagebox.showerror("Conversion Error", f"Error during conversion:\n{e}")

    def _open_url(self, url: str):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)

    def clear_cad(self):
        """Clear all imported CAD files."""
        if messagebox.askyesno("Clear CAD Files", "Remove all imported CAD files?"):
            self.cad_files.clear()
            self.cad_listbox.delete(0, tk.END)
            self.status_var.set("Cleared all CAD files")

    def auto_generate_config(self):
        """Auto-generate configuration from CAD files."""
        if not self.cad_files:
            messagebox.showwarning("No CAD Files", "Import CAD files first!")
            return

        # Create config with links from CAD files
        config = {
            "name": "my_subsystem",
            "links": [],
            "joints": [],
            "motors": [],
            "sensors": []
        }

        # Add each CAD file as a link
        for i, cad_file in enumerate(self.cad_files):
            link = {
                "name": cad_file.stem,
                "mesh": str(cad_file.absolute()),
                "mass": 1.0,
                "center_of_mass": [0.0, 0.0, 0.0],
                "inertia": None
            }
            config["links"].append(link)

            # If not first link, create a joint to previous link
            if i > 0:
                joint = {
                    "name": f"joint_{i}",
                    "type": "revolute",
                    "parent": config["links"][i-1]["name"],
                    "child": link["name"],
                    "axis": [0.0, 0.0, 1.0],
                    "origin": [0.0, 0.0, 0.1],
                    "limits": None,
                    "velocity_limit": 1000.0,
                    "effort_limit": 100.0
                }
                config["joints"].append(joint)

                # Add motor for each joint
                motor = {
                    "name": f"motor_{i}",
                    "type": "neo",
                    "joint": joint["name"],
                    "gear_ratio": 60.0,
                    "hal_port": i-1,
                    "inverted": False
                }
                config["motors"].append(motor)

                # Add encoder for each joint
                sensor = {
                    "name": f"encoder_{i}",
                    "type": "encoder",
                    "joint": joint["name"],
                    "hal_ports": [2*(i-1), 2*(i-1)+1],
                    "ticks_per_rev": 2048,
                    "offset": 0.0
                }
                config["sensors"].append(sensor)

        self.config_data = config
        self._update_config_display()
        self.notebook.select(1)  # Switch to config tab
        self.status_var.set("Auto-generated configuration - please review and edit")

        messagebox.showinfo(
            "Config Generated",
            f"Generated configuration with:\n"
            f"- {len(config['links'])} links\n"
            f"- {len(config['joints'])} joints\n"
            f"- {len(config['motors'])} motors\n"
            f"- {len(config['sensors'])} sensors\n\n"
            f"Please review and edit the configuration in the Config tab."
        )

    # ==================== Config Methods ====================

    def _update_config_display(self):
        """Update config editor with current config data."""
        self.config_text.delete('1.0', tk.END)
        self.config_text.insert('1.0', json.dumps(self.config_data, indent=2))

    def load_config(self):
        """Load configuration from file."""
        file_path = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.config_data = json.load(f)
                self.config_file_path = Path(file_path)
                self._update_config_display()
                self.status_var.set(f"Loaded config: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config:\n{e}")

    def save_config(self):
        """Save configuration to file."""
        if self.config_file_path:
            self._save_config_to_file(self.config_file_path)
        else:
            self.save_config_as()

    def save_config_as(self):
        """Save configuration to new file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if file_path:
            self._save_config_to_file(Path(file_path))

    def _save_config_to_file(self, file_path: Path):
        """Save config data to file."""
        try:
            # Parse current text in editor
            config_text = self.config_text.get('1.0', tk.END)
            self.config_data = json.loads(config_text)

            # Save to file
            with open(file_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)

            self.config_file_path = file_path
            self.status_var.set(f"Saved config: {file_path.name}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Configuration has invalid JSON:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{e}")

    def validate_config(self):
        """Validate configuration JSON."""
        try:
            config_text = self.config_text.get('1.0', tk.END)
            config = json.loads(config_text)

            # Basic validation
            required_keys = ["name", "links", "joints", "motors", "sensors"]
            missing = [k for k in required_keys if k not in config]

            if missing:
                messagebox.showwarning("Validation Warning",
                    f"Missing required keys: {', '.join(missing)}")
            else:
                messagebox.showinfo("Validation Success",
                    "Configuration is valid!\n\n"
                    f"Links: {len(config['links'])}\n"
                    f"Joints: {len(config['joints'])}\n"
                    f"Motors: {len(config['motors'])}\n"
                    f"Sensors: {len(config['sensors'])}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Configuration has invalid JSON:\n{e}")

    def reset_config(self):
        """Reset configuration to default."""
        if messagebox.askyesno("Reset Config", "Reset configuration to default?"):
            self.config_data = self._default_config()
            self._update_config_display()
            self.status_var.set("Reset to default configuration")

    # ==================== Robot Code Methods ====================

    def browse_robot_code(self):
        """Browse for robot code folder."""
        folder_path = filedialog.askdirectory(title="Select Robot Code Folder")

        if folder_path:
            self.robot_code_path = Path(folder_path)
            self.code_path_var.set(str(self.robot_code_path))
            self._analyze_robot_code()
            self.status_var.set(f"Loaded robot code: {self.robot_code_path.name}")

    def _analyze_robot_code(self):
        """Analyze robot code folder and display information."""
        if not self.robot_code_path:
            return

        info = []
        info.append(f"Robot Code Path: {self.robot_code_path}\n")
        info.append("="*60 + "\n\n")

        # Detect project type
        if (self.robot_code_path / "build.gradle").exists():
            info.append("Project Type: Java/C++ (Gradle)\n")
            info.append("Build System: Gradle\n\n")
            info.append("To run simulation:\n")
            info.append("  cd " + str(self.robot_code_path) + "\n")
            info.append("  gradlew simulateJava -Phalsim    (for Java)\n")
            info.append("  gradlew simulateNative -Phalsim  (for C++)\n\n")
        elif (self.robot_code_path / "robot.py").exists():
            info.append("Project Type: Python (RobotPy)\n\n")
            info.append("To run simulation:\n")
            info.append("  cd " + str(self.robot_code_path) + "\n")
            info.append("  python robot.py sim\n\n")
        else:
            info.append("Project Type: Unknown\n")
            info.append("Could not detect Java, C++, or Python robot code.\n\n")

        # List important files
        info.append("Project Files:\n")
        for pattern in ["*.java", "*.cpp", "*.py", "*.json", "build.gradle"]:
            files = list(self.robot_code_path.rglob(pattern))
            if files:
                info.append(f"\n{pattern} files: ({len(files)})\n")
                for f in files[:5]:  # Show first 5
                    info.append(f"  - {f.relative_to(self.robot_code_path)}\n")
                if len(files) > 5:
                    info.append(f"  ... and {len(files)-5} more\n")

        # Update display
        self.code_info_text.config(state=tk.NORMAL)
        self.code_info_text.delete('1.0', tk.END)
        self.code_info_text.insert('1.0', ''.join(info))
        self.code_info_text.config(state=tk.DISABLED)

    # ==================== Simulation Methods ====================

    def start_simulation(self):
        """Start the simulation with robot code and WebSocket bridge."""
        # Validate we have config
        if not self.config_file_path:
            result = messagebox.askyesno(
                "No Config Saved",
                "Configuration not saved to file. Save now?"
            )
            if result:
                self.save_config_as()
                if not self.config_file_path:
                    return
            else:
                return

        # Validate we have robot code
        if not self.robot_code_path:
            messagebox.showerror(
                "No Robot Code",
                "Please select robot code folder in the 'Robot Code' tab first."
            )
            self.notebook.select(2)  # Switch to Robot Code tab
            return

        try:
            self.sim_log.delete('1.0', tk.END)
            self.sim_log.insert(tk.END, "Starting Simulation...\n\n")

            # Detect project type and prepare robot code command
            robot_cmd = self._get_robot_command()
            if not robot_cmd:
                messagebox.showerror(
                    "Unsupported Project",
                    "Could not detect project type.\n\n"
                    "Supported:\n"
                    "- Java: Gradle project with build.gradle\n"
                    "- C++: Gradle project with build.gradle\n"
                    "- Python: robot.py file"
                )
                return

            self.sim_log.insert(tk.END, f"Robot code command: {' '.join(robot_cmd)}\n")
            self.sim_log.insert(tk.END, "Starting robot code...\n\n")

            # Start robot code process (it will create WebSocket server)
            self.robot_process = subprocess.Popen(
                robot_cmd,
                cwd=str(self.robot_code_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Start robot code log reader
            self.robot_log_thread = threading.Thread(
                target=self._read_robot_output,
                daemon=True
            )
            self.robot_log_thread.start()

            # Wait a moment for robot code to start WebSocket server
            self.sim_log.insert(tk.END, "Waiting for robot code to initialize...\n")
            self.root.after(3000, self._start_websocket_bridge)  # Wait 3 seconds

            # Update UI
            self.start_sim_btn.config(state=tk.DISABLED)
            self.stop_sim_btn.config(state=tk.NORMAL)
            self.status_var.set("Simulation starting...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start simulation:\n{e}")
            self.sim_log.insert(tk.END, f"\nERROR: {e}\n")

    def _get_robot_command(self):
        """Determine robot code command based on project type."""
        if not self.robot_code_path:
            return None

        # Check for Gradle project (Java/C++)
        build_gradle = self.robot_code_path / "build.gradle"
        gradlew = self.robot_code_path / "gradlew.bat"  # Windows
        gradlew_unix = self.robot_code_path / "gradlew"  # Linux/Mac

        if build_gradle.exists():
            # It's a Gradle project
            if gradlew.exists():
                # Java project (most common)
                return [str(gradlew), "simulateJava", "-Phalsim"]
            elif gradlew_unix.exists():
                return [str(gradlew_unix), "simulateJava", "-Phalsim"]
            else:
                # No gradlew wrapper, use system gradle
                return ["gradle", "simulateJava", "-Phalsim"]

        # Check for Python robot code
        robot_py = self.robot_code_path / "robot.py"
        if robot_py.exists():
            # Use --ws-server flag to enable HAL WebSocket extension
            return [sys.executable, "-m", "robotpy", "sim", "--ws-server"]

        return None

    def _start_websocket_bridge(self):
        """Start WebSocket bridge after robot code has initialized."""
        try:
            self.sim_log.insert(tk.END, "\nStarting WebSocket bridge...\n\n")

            cmd = [
                sys.executable, "-m", "subsystemsim.hal_bridge.websocket_bridge",
                "--config", str(self.config_file_path)
            ]

            self.simulation_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Start log reader thread
            self.log_thread = threading.Thread(target=self._read_simulation_output, daemon=True)
            self.log_thread.start()

            self.status_var.set("Simulation running")

        except Exception as e:
            self.sim_log.insert(tk.END, f"\nERROR starting bridge: {e}\n")

    def _read_robot_output(self):
        """Read robot code output in background thread."""
        if not self.robot_process:
            return

        for line in self.robot_process.stdout:
            self.sim_log.insert(tk.END, f"[ROBOT] {line}")
            self.sim_log.see(tk.END)

        # Process ended
        self.root.after(0, self._robot_ended)

    def _robot_ended(self):
        """Handle robot code process ending."""
        self.sim_log.insert(tk.END, "\n[ROBOT] Robot code stopped\n")
        if hasattr(self, 'simulation_process') and self.simulation_process:
            self.simulation_process.terminate()

    def _read_simulation_output(self):
        """Read simulation output in background thread."""
        if not self.simulation_process:
            return

        for line in self.simulation_process.stdout:
            self.sim_log.insert(tk.END, line)
            self.sim_log.see(tk.END)

        # Process ended
        self.root.after(0, self._simulation_ended)

    def _simulation_ended(self):
        """Handle simulation process ending."""
        self.start_sim_btn.config(state=tk.NORMAL)
        self.stop_sim_btn.config(state=tk.DISABLED)
        self.status_var.set("Simulation stopped")

    def stop_simulation(self):
        """Stop the simulation."""
        # Stop WebSocket bridge
        if hasattr(self, 'simulation_process') and self.simulation_process:
            self.simulation_process.terminate()
            self.simulation_process = None

        # Stop robot code
        if hasattr(self, 'robot_process') and self.robot_process:
            self.robot_process.terminate()
            self.robot_process = None

        self.sim_log.insert(tk.END, "\n\nSimulation stopped by user.\n")
        self.status_var.set("Simulation stopped")

    def open_config_folder(self):
        """Open the folder containing the config file."""
        if self.config_file_path:
            folder = self.config_file_path.parent
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])
        else:
            messagebox.showinfo("No Config", "Save configuration first!")

    # ==================== Menu Methods ====================

    def new_project(self):
        """Start a new project."""
        if messagebox.askyesno("New Project", "Clear all data and start new project?"):
            self.cad_files.clear()
            self.cad_listbox.delete(0, tk.END)
            self.robot_code_path = None
            self.code_path_var.set("No robot code selected")
            self.config_data = self._default_config()
            self.config_file_path = None
            self._update_config_display()
            self.status_var.set("New project created")

    def show_docs(self):
        """Show documentation."""
        doc_text = """
SubsystemSim Documentation

1. CAD IMPORT
   - Import OBJ/STL files (meshes for your subsystem parts)
   - For STEP files, convert to OBJ first using online tools
   - Each mesh becomes a "link" in your mechanism

2. CONFIGURATION
   - Define joints between links (revolute, prismatic, fixed)
   - Assign motors to joints (NEO, CIM, Falcon, etc.)
   - Add sensors (encoders)
   - Match HAL ports to your robot code

3. ROBOT CODE
   - Point to your Java/C++/Python robot project
   - Code should use standard WPILib motor controllers and sensors

4. SIMULATION
   - Start simulation (launches WebSocket bridge)
   - Run your robot code with -Phalsim flag
   - Robot code connects and controls the physics simulation

For more help, see WEBSOCKET_BRIDGE_GUIDE.md
"""

        window = tk.Toplevel(self.root)
        window.title("Documentation")
        window.geometry("600x500")

        text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', doc_text)
        text.config(state=tk.DISABLED)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About SubsystemSim",
            "SubsystemSim\n"
            "FRC Subsystem Simulator\n\n"
            "Version 1.0\n\n"
            "Simulates FRC robot subsystems using:\n"
            "- PyBullet physics engine\n"
            "- WPILib HAL WebSocket bridge\n"
            "- Real robot code (Java/C++/Python)\n\n"
            "Supports importing CAD and running\n"
            "unmodified robot code."
        )

    # ==================== Examples Methods ====================

    def load_simple_arm_example(self):
        """Load the built-in simple arm example."""
        try:
            # Load CAD files
            example_dir = project_root / "examples" / "simple_arm"
            meshes_dir = example_dir / "meshes"

            if not meshes_dir.exists():
                messagebox.showerror("Example Not Found",
                    "Simple arm example meshes not found.\n"
                    "Expected location: examples/simple_arm/meshes/")
                return

            # Clear current data
            self.cad_files.clear()
            self.cad_listbox.delete(0, tk.END)

            # Load mesh files
            for mesh_file in meshes_dir.glob("*.obj"):
                self.cad_files.append(mesh_file)
                self.cad_listbox.insert(tk.END, f"{mesh_file.stem} (.obj)")

            # Load config
            config_file = example_dir / "arm_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config_data = json.load(f)
                self.config_file_path = config_file
                self._update_config_display()

            # Load robot code path
            robot_file = example_dir / "robot.py"
            if robot_file.exists():
                self.robot_code_path = example_dir
                self.code_path_var.set(str(self.robot_code_path))
                self._analyze_robot_code()

            self.status_var.set("Loaded simple arm example")
            messagebox.showinfo(
                "Example Loaded",
                "Simple Arm Example Loaded!\n\n"
                "- 2 CAD meshes (base, arm)\n"
                "- 1 revolute joint\n"
                "- 1 NEO motor (60:1 ratio)\n"
                "- 1 encoder (2048 ticks/rev)\n"
                "- Python robot code\n\n"
                "You can now test the simulation!"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load example:\n{e}")

    def show_cad_resources(self):
        """Show links to download FRC CAD resources."""
        resources_text = """
FRC CAD Resources - Download Links

1. GRABCAD - FRC CAD Library
   https://grabcad.com/library?query=frc
   - Thousands of FRC robot CAD models
   - Arms, elevators, intakes, drivetrains
   - Filter by year (2020-2024)
   - Download as STEP files

2. Chief Delphi - CAD Resources Forum
   https://www.chiefdelphi.com/c/technical/cad/15
   - Community-shared designs
   - Well-documented mechanisms
   - STEP and SLDPRT formats

3. WCP (West Coast Products) - CAD Downloads
   https://www.wcproducts.com/
   - Professional FRC components
   - Greyt Elevator, Greyt Arm
   - STEP files available

4. Everybot CAD
   https://www.robowranglers148.com/uploads/1/0/5/4/10542658/2024_everybot_cad.zip
   - Simple, well-documented arm
   - Perfect for testing
   - SLDASM format (can export STEP)

5. Online STEP to OBJ Converter
   https://convert3d.org/step-to-obj
   - Convert STEP → OBJ for SubsystemSim
   - Free, no account needed

INSTRUCTIONS:
1. Download STEP file from any source above
2. Convert to OBJ using online converter
3. Import OBJ files in SubsystemSim CAD Import tab
4. Auto-generate configuration
5. Test with simulation!
"""

        window = tk.Toplevel(self.root)
        window.title("FRC CAD Resources")
        window.geometry("700x600")

        text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', resources_text)
        text.config(state=tk.DISABLED)

    def show_java_examples(self):
        """Show links to download Java robot code examples."""
        examples_text = """
Java Robot Code Examples - Download Links

1. WPILib Example Projects (OFFICIAL)
   https://github.com/wpilibsuite/allwpilib/tree/main/wpilibjExamples
   - Official WPILib Java examples
   - Motor control, encoders, PID
   - Clone with: git clone https://github.com/wpilibsuite/allwpilib.git
   - Examples in: wpilibjExamples/src/main/java/edu/wpi/first/wpilibj/examples/

2. Simple Arm Example (Recommended for Testing)
   https://github.com/wpilibsuite/allwpilib/tree/main/wpilibjExamples/src/main/java/edu/wpi/first/wpilibj/examples/armbot
   - Single-joint arm with PID control
   - Uses PWM motor and encoder
   - Perfect match for simple arm CAD

3. Elevator Example
   https://github.com/wpilibsuite/allwpilib/tree/main/wpilibjExamples/src/main/java/edu/wpi/first/wpilibj/examples/elevatorbot
   - Vertical motion (prismatic joint)
   - Trapezoidal motion profiling

4. FRC 2024 Robot Code Examples (Chief Delphi)
   https://www.chiefdelphi.com/t/2024-robot-code-repositories/450816
   - Real team code from 2024 season
   - Production-quality examples
   - Various subsystem designs

5. Create New Java Robot Project
   Run in terminal:
   > wpilib create project
   - Creates new Java robot project
   - Includes Gradle build files
   - Ready for simulation

QUICK START FOR TESTING:
1. Download ArmBot example from link #2
2. Extract to a folder
3. In SubsystemSim, go to "Robot Code" tab
4. Browse to the extracted folder
5. In terminal: gradlew simulateJava -Phalsim
6. Robot code connects to SubsystemSim!

PORT MAPPING:
Make sure robot code motor/sensor ports match your SubsystemSim config:
- Motor: PWMSparkMax(PORT) → config: "hal_port": PORT
- Encoder: Encoder(PORT_A, PORT_B) → config: "hal_ports": [PORT_A, PORT_B]
"""

        window = tk.Toplevel(self.root)
        window.title("Java Robot Code Examples")
        window.geometry("800x650")

        text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert('1.0', examples_text)
        text.config(state=tk.DISABLED)


def main():
    """Entry point for GUI application."""
    root = tk.Tk()
    app = SubsystemSimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
