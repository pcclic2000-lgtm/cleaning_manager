"""
Composant de table avec pagination
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QPushButton, QLabel, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import ui.app_theme as Theme


class PaginatedTable(QWidget):
    """Widget de table avec pagination"""
    
    page_changed = pyqtSignal(int)
    
    def __init__(self, page_size=50, parent=None):
        super().__init__(parent)
        self.page_size = page_size
        self.current_page = 1
        self.total_items = 0
        self.total_pages = 1
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.table)
        
        # Barre de pagination
        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(10, 5, 10, 5)
        
        # Boutons de navigation
        self.btn_first = QPushButton("⏮️")
        self.btn_first.setToolTip("Première page")
        self.btn_first.setFixedWidth(40)
        self.btn_first.clicked.connect(self.go_to_first_page)
        
        self.btn_prev = QPushButton("◀️")
        self.btn_prev.setToolTip("Page précédente")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.clicked.connect(self.go_to_previous_page)
        
        # Informations de page
        self.page_label = QLabel("Page 1 sur 1")
        self.page_label.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        
        # Sélecteur de page
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setFixedWidth(60)
        self.page_spin.valueChanged.connect(self.go_to_page)
        
        # Sélecteur de taille de page
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "25", "50", "100", "Tous"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setFixedWidth(80)
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        
        # Boutons de navigation suivants
        self.btn_next = QPushButton("▶️")
        self.btn_next.setToolTip("Page suivante")
        self.btn_next.setFixedWidth(40)
        self.btn_next.clicked.connect(self.go_to_next_page)
        
        self.btn_last = QPushButton("⏭️")
        self.btn_last.setToolTip("Dernière page")
        self.btn_last.setFixedWidth(40)
        self.btn_last.clicked.connect(self.go_to_last_page)
        
        # Informations sur les éléments
        self.items_label = QLabel("0 éléments")
        self.items_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        # Ajouter les widgets
        pagination_layout.addWidget(self.btn_first)
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(QLabel("Page:"))
        pagination_layout.addWidget(self.page_spin)
        pagination_layout.addWidget(QLabel("sur"))
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(QLabel("Taille:"))
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addWidget(self.btn_last)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.items_label)
        
        pagination_widget.setLayout(pagination_layout)
        layout.addWidget(pagination_widget)
        
        self.setLayout(layout)
        
        # Appliquer les styles
        self.apply_styles()
        
        # Mettre à jour les boutons
        self.update_navigation_buttons()
    
    def apply_styles(self):
        """Applique les styles aux composants"""
        # Style pour les boutons de pagination
        button_style = Theme.AppTheme.get_button_style(
            Theme.AppTheme.GRAY, 
            Theme.AppTheme.GRAY_DARK,
            "5px 10px",
            "4px"
        )
        
        self.btn_first.setStyleSheet(button_style)
        self.btn_prev.setStyleSheet(button_style)
        self.btn_next.setStyleSheet(button_style)
        self.btn_last.setStyleSheet(button_style)
        
        # Style pour les autres widgets
        self.page_spin.setStyleSheet(Theme.AppTheme.get_input_style())
        self.page_size_combo.setStyleSheet(Theme.AppTheme.get_input_style())
    
    def set_total_items(self, total):
        """Définit le nombre total d'éléments"""
        self.total_items = total
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        
        # Mettre à jour les contrôles
        self.page_spin.setRange(1, self.total_pages)
        self.page_label.setText(f"sur {self.total_pages}")
        self.items_label.setText(f"{total} éléments")
        
        # Ajuster la page courante si nécessaire
        if self.current_page > self.total_pages:
            self.current_page = 1
        
        self.page_spin.setValue(self.current_page)
        self.update_navigation_buttons()
    
    def set_current_page(self, page):
        """Définit la page courante"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.page_spin.setValue(page)
            self.update_navigation_buttons()
            self.page_changed.emit(page)
    
    def go_to_page(self, page):
        """Va à une page spécifique"""
        self.set_current_page(page)
    
    def go_to_first_page(self):
        """Va à la première page"""
        self.set_current_page(1)
    
    def go_to_previous_page(self):
        """Va à la page précédente"""
        if self.current_page > 1:
            self.set_current_page(self.current_page - 1)
    
    def go_to_next_page(self):
        """Va à la page suivante"""
        if self.current_page < self.total_pages:
            self.set_current_page(self.current_page + 1)
    
    def go_to_last_page(self):
        """Va à la dernière page"""
        self.set_current_page(self.total_pages)
    
    def change_page_size(self, size_text):
        """Change la taille de la page"""
        if size_text == "Tous":
            self.page_size = self.total_items
        else:
            try:
                self.page_size = int(size_text)
            except:
                self.page_size = 50
        
        # Recalculer les pages
        self.set_total_items(self.total_items)
    
    def update_navigation_buttons(self):
        """Met à jour l'état des boutons de navigation"""
        self.btn_first.setEnabled(self.current_page > 1)
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)
        self.btn_last.setEnabled(self.current_page < self.total_pages)
        
        # Mettre à jour le label de page
        self.page_label.setText(f"Page {self.current_page} sur {self.total_pages}")
    
    def get_offset(self):
        """Retourne l'offset pour la requête SQL"""
        return (self.current_page - 1) * self.page_size
    
    def get_limit(self):
        """Retourne la limite pour la requête SQL"""
        return self.page_size