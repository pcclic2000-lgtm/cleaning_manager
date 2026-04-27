# widgets/status_notification_widget.py
"""
Widget pour afficher les notifications de changement de statut
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class StatusNotificationWidget(QWidget):
    """Widget de notification dans la barre d'outils"""
    
    closed = pyqtSignal()
    
    def __init__(self, message: str, notification_type: str = "info", parent=None):
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Style selon le type
        if self.notification_type == "success":
            style = "background: #d4edda; color: #155724; border: 1px solid #c3e6cb;"
            icon = "✅"
        elif self.notification_type == "warning":
            style = "background: #fff3cd; color: #856404; border: 1px solid #ffeaa7;"
            icon = "⚠️"
        elif self.notification_type == "error":
            style = "background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"
            icon = "❌"
        else:  # info
            style = "background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb;"
            icon = "ℹ️"
        
        # Message
        self.lbl_message = QLabel(f"{icon} {self.message}")
        self.lbl_message.setStyleSheet(f"""
            {style}
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
        """)
        layout.addWidget(self.lbl_message)
        
        # Bouton fermer
        btn_close = QPushButton("×")
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 18px;
                font-weight: bold;
                padding: 0;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                color: #333;
                background: rgba(0,0,0,0.1);
                border-radius: 10px;
            }
        """)
        btn_close.clicked.connect(self.close_notification)
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
    
    def close_notification(self):
        """Ferme la notification"""
        self.closed.emit()
        self.hide()
        self.deleteLater()