"""
Dark theme stylesheet for CAD Editor.

Matches SimpleSim's color scheme:
- Background: #1e1e1e (primary), #2d2d2d (secondary), #3d3d3d (tertiary)
- Accent Red: #B22234
- Text: #FFFFFF (primary), #B0B0B0 (secondary)
"""

# Color constants
BG_PRIMARY = "#1e1e1e"
BG_SECONDARY = "#2d2d2d"
BG_TERTIARY = "#3d3d3d"
BG_INPUT = "#3d3d3d"
BORDER_COLOR = "#4d4d4d"
ACCENT_RED = "#B22234"
ACCENT_RED_HOVER = "#CC3344"
ACCENT_RED_PRESSED = "#992233"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0B0B0"
TEXT_MUTED = "#808080"
SUCCESS = "#4CAF50"
WARNING = "#FFA726"
ERROR = "#EF5350"

# Dark theme stylesheet for PyQt5
DARK_STYLESHEET = f"""
/* Main Window */
QMainWindow {{
    background-color: {BG_PRIMARY};
}}

/* Central Widget and generic QWidget */
QWidget {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 2px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
}}

QMenuBar::item:selected {{
    background-color: {ACCENT_RED};
}}

QMenuBar::item:pressed {{
    background-color: {ACCENT_RED_PRESSED};
}}

/* Menus */
QMenu {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 30px 8px 20px;
    background-color: transparent;
}}

QMenu::item:selected {{
    background-color: {ACCENT_RED};
}}

QMenu::separator {{
    height: 1px;
    background-color: {BORDER_COLOR};
    margin: 4px 10px;
}}

QMenu::item:disabled {{
    color: {TEXT_MUTED};
}}

/* Status Bar */
QStatusBar {{
    background-color: {BG_SECONDARY};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
}}

/* Labels */
QLabel {{
    color: {TEXT_PRIMARY};
    background-color: transparent;
}}

/* Push Buttons */
QPushButton {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 8px 16px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {ACCENT_RED};
    border-color: {ACCENT_RED};
}}

QPushButton:pressed {{
    background-color: {ACCENT_RED_PRESSED};
}}

QPushButton:disabled {{
    background-color: {BG_SECONDARY};
    color: {TEXT_MUTED};
    border-color: {BG_TERTIARY};
}}

/* Line Edit */
QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {ACCENT_RED};
}}

QLineEdit:focus {{
    border-color: {ACCENT_RED};
}}

QLineEdit:disabled {{
    background-color: {BG_SECONDARY};
    color: {TEXT_MUTED};
}}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {ACCENT_RED};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {BG_TERTIARY};
    border: none;
    width: 16px;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {ACCENT_RED};
}}

/* Combo Box */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px;
    min-width: 80px;
}}

QComboBox:hover {{
    border-color: {ACCENT_RED};
}}

QComboBox::drop-down {{
    background-color: {BG_TERTIARY};
    border: none;
    width: 24px;
}}

QComboBox::drop-down:hover {{
    background-color: {ACCENT_RED};
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_RED};
}}

/* Check Box */
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 3px;
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_RED};
    border-color: {ACCENT_RED};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT_RED};
}}

/* Radio Button */
QRadioButton {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 9px;
}}

QRadioButton::indicator:checked {{
    background-color: {ACCENT_RED};
    border-color: {ACCENT_RED};
}}

/* Group Box */
QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {TEXT_PRIMARY};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background-color: {BG_PRIMARY};
}}

QTabBar::tab {{
    background-color: {BG_SECONDARY};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT_RED};
}}

QTabBar::tab:hover:!selected {{
    background-color: {BG_TERTIARY};
}}

/* List Widget */
QListWidget {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
}}

QListWidget::item {{
    padding: 6px;
}}

QListWidget::item:selected {{
    background-color: {ACCENT_RED};
}}

QListWidget::item:hover:!selected {{
    background-color: {BG_TERTIARY};
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background-color: {BG_SECONDARY};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {BG_TERTIARY};
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_MUTED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {BG_SECONDARY};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {BG_TERTIARY};
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_MUTED};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {BORDER_COLOR};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Dialog Buttons */
QDialogButtonBox {{
    button-layout: 0;
}}

/* Message Box */
QMessageBox {{
    background-color: {BG_SECONDARY};
}}

/* Tool Tips */
QToolTip {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    padding: 4px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {BG_TERTIARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {ACCENT_RED};
    border-radius: 3px;
}}
"""


def apply_dark_theme(app_or_widget):
    """Apply the dark theme stylesheet to a QApplication or QWidget."""
    app_or_widget.setStyleSheet(DARK_STYLESHEET)
