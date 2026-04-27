# views/rapport_widget.py
"""
Widget pour la génération de rapports
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from views.invoices.rapport_dialog import RapportDialog


class RapportWidget(QWidget):
    """Widget pour la génération de rapports"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("📋 RAPPORTS DE GESTION")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            border-left: 5px solid #9b59b6;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Zone de contenu
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Carte de rapport principal
        rapport_card = self.create_rapport_card(
            "📊 Rapport complet de gestion",
            "Génère un rapport PDF complet avec toutes les sections : Employés, Clients, Salaires, Banque, Dépenses, Factures",
            "#9b59b6"
        )
        content_layout.addWidget(rapport_card)
        
        # Autres types de rapports (optionnel)
        # ...
        
        content_layout.addStretch()
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def create_rapport_card(self, title, description, color):
        """Crée une carte pour un type de rapport"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #e3e8ee;
                border-radius: 12px;
                border-left: 5px solid {color};
                padding: 15px;
            }}
            QFrame:hover {{
                background: #f8f9fa;
            }}
        """)
        
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(15)
        
        # Contenu
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color};")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        text_layout.addWidget(desc_label)
        
        card_layout.addLayout(text_layout, 1)
        
        # Bouton
        btn = QPushButton("Générer")
        btn.setFixedSize(100, 40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #8e44ad;
            }}
        """)
        btn.clicked.connect(self.open_rapport_dialog)
        
        card_layout.addWidget(btn)
        
        return card
    
    def open_rapport_dialog(self):
        """Ouvre le dialogue de rapport"""
        dialog = RapportDialog(self)
        dialog.exec()