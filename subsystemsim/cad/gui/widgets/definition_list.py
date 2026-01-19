"""
DefinitionListWidget - QListWidget with hover signals for 3D highlighting.
"""

from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt


class DefinitionListWidget(QListWidget):
    """
    List widget that emits signals when items are hovered or double-clicked.
    Used for highlighting corresponding 3D parts when hovering over definitions.
    """

    # Emitted when mouse enters an item (passes the definition name)
    itemHovered = pyqtSignal(str)

    # Emitted when mouse leaves all items
    hoverCleared = pyqtSignal()

    # Emitted when an item is double-clicked (passes the definition name)
    itemEditRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._last_hovered_item = None

        # Connect double-click to edit signal
        self.itemDoubleClicked.connect(self._on_double_click)

        # Style the list
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }
        """)

    def mouseMoveEvent(self, event):
        """Detect which item is under cursor and emit hover signal."""
        item = self.itemAt(event.pos())

        if item != self._last_hovered_item:
            self._last_hovered_item = item
            if item:
                # Get the definition name stored in item data
                name = item.data(Qt.UserRole)
                if name:
                    self.itemHovered.emit(name)
            else:
                self.hoverCleared.emit()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Clear hover when mouse leaves widget."""
        self._last_hovered_item = None
        self.hoverCleared.emit()
        super().leaveEvent(event)

    def addDefinition(self, name: str, display_text: str = None):
        """
        Add a definition item to the list.

        Args:
            name: The unique name of the definition (stored in UserRole)
            display_text: Text to display (defaults to name if not provided)
        """
        item = QListWidgetItem(display_text or name)
        item.setData(Qt.UserRole, name)
        self.addItem(item)
        return item

    def removeDefinition(self, name: str):
        """Remove a definition by name."""
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.UserRole) == name:
                self.takeItem(i)
                return True
        return False

    def clear(self):
        """Clear all items and reset hover state."""
        self._last_hovered_item = None
        super().clear()

    def getSelectedNames(self):
        """Get list of names for all selected items."""
        names = []
        for item in self.selectedItems():
            name = item.data(Qt.UserRole)
            if name:
                names.append(name)
        return names

    def _on_double_click(self, item):
        """Handle double-click on an item."""
        if item:
            name = item.data(Qt.UserRole)
            if name:
                self.itemEditRequested.emit(name)
