"""
Composant de carte KPI
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPalette, QLinearGradient, QPainter, QBrush
import ui.app_theme as Theme


class KPICard(QWidget):
    """Widget de carte KPI avec animations"""
    
    def __init__(self, title: str, value: str, color: str = Theme.AppTheme.PRIMARY, 
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.icon = icon
        self._animation_value = 0
        
        self.init_ui()
        self.setup_animation()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # En-tête avec icône
        header_layout = QHBoxLayout()
        
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setStyleSheet(f"font-size: 24px; color: {self.color};")
            header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        # Titre
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(Theme.AppTheme.get_label_style("subtitle"))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        if self.icon:
            # Espaceur pour équilibrer
            header_layout.addWidget(QLabel(""))
        
        layout.addLayout(header_layout)
        
        # Valeur
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet(f"""
            {Theme.AppTheme.get_label_style("title")}
            color: {self.color};
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Sous-titre (optionnel)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(Theme.AppTheme.get_label_style("normal"))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setVisible(False)
        layout.addWidget(self.subtitle_label)
        
        # Barre de progression (optionnelle)
        self.progress_layout = QHBoxLayout()
        self.progress_layout.setContentsMargins(0, 10, 0, 0)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(Theme.AppTheme.get_label_style("info"))
        
        self.progress_layout.addStretch()
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addStretch()
        
        layout.addLayout(self.progress_layout)
        
        self.setLayout(layout)
        
        # Style de la carte
        self.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 2px solid {Theme.AppTheme.LIGHT_DARK};
                border-radius: 12px;
                {Theme.AppTheme.create_shadow_css()}
            }}
            QWidget:hover {{
                border: 2px solid {self.color};
                {Theme.AppTheme.create_shadow_css(color=self.color, blur=15)}
            }}
        """)
        
        # Effet de survol
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setup_animation(self):
        """Configure les animations"""
        self.animation = QPropertyAnimation(self, b"animationValue")
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def set_value(self, value: str, animate: bool = True):
        """Définit la valeur avec animation optionnelle"""
        self.value = value
        
        if animate:
            self.animation.setStartValue(0)
            self.animation.setEndValue(100)
            self.animation.start()
        else:
            self.value_label.setText(value)
    
    def set_subtitle(self, text: str):
        """Définit un sous-titre"""
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))
    
    def set_progress(self, current: float, total: float, unit: str = "%"):
        """Définit une barre de progression"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_label.setText(f"{percentage:.1f}{unit}")
            self.progress_label.setVisible(True)
            
            # Changer la couleur selon le pourcentage
            if percentage >= 80:
                color = Theme.AppTheme.SUCCESS
            elif percentage >= 50:
                color = Theme.AppTheme.WARNING
            else:
                color = Theme.AppTheme.DANGER
            
            self.progress_label.setStyleSheet(f"""
                {Theme.AppTheme.get_label_style("normal")}
                color: {color};
                font-weight: bold;
            """)
        else:
            self.progress_label.setVisible(False)
    
    def paintEvent(self, event):
        """Dessine un effet de dégradé pendant l'animation"""
        if self._animation_value > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Créer un dégradé transparent
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(self.color))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            # Ajuster l'opacité selon l'animation
            alpha = int(30 * (self._animation_value / 100))
            gradient.setColorAt(0, QColor(self.color).lighter(150))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 10, 10)
        
        super().paintEvent(event)
    
    def get_animation_value(self):
        return self._animation_value

    def set_animation_value(self, value):
        self._animation_value = value
        # Mettre à jour l'affichage pendant l'animation
        self.value_label.setText(self.value)
        self.update()

    animationValue = pyqtProperty(float, get_animation_value, set_animation_value)
