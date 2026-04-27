"""
Gestionnaire de thème cohérent pour l'application
"""
# CORRECTION : imports regroupés en blocs cohérents, symboles inutilisés supprimés
# Supprimés : QColor, QPalette, QFont, Qt, QTableWidgetItem (jamais utilisés)
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QTableWidget, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QLabel, QProgressBar, QScrollArea, QMenu
)


class AppTheme:
    """Classe pour la gestion des thèmes et styles"""

    # Couleurs principales
    PRIMARY = "#3498db"
    PRIMARY_DARK = "#2980b9"
    SECONDARY = "#2ecc71"
    SECONDARY_DARK = "#27ae60"
    DANGER = "#e74c3c"
    DANGER_DARK = "#c0392b"
    WARNING = "#f39c12"
    WARNING_DARK = "#d35400"
    INFO = "#9b59b6"
    INFO_DARK = "#8e44ad"
    SUCCESS = "#1abc9c"
    SUCCESS_DARK = "#16a085"

    # Couleurs neutres
    DARK = "#2c3e50"
    DARK_DARK = "#1a252f"
    LIGHT = "#ecf0f1"
    LIGHT_DARK = "#bdc3c7"
    GRAY = "#95a5a6"
    GRAY_DARK = "#7f8c8d"

    # Couleurs de texte
    TEXT_PRIMARY = "#2c3e50"
    TEXT_SECONDARY = "#34495e"
    TEXT_LIGHT = "#ecf0f1"

    @staticmethod
    def get_button_style(color: str, hover_color: str = None,
                         padding: str = "10px 20px",
                         radius: str = "8px") -> str:
        """
        Génère un style CSS pour un bouton

        Args:
            color: Couleur de fond
            hover_color: Couleur au survol (optionnel)
            padding: Padding CSS
            radius: Rayon des bordures

        Returns:
            Style CSS
        """
        hover = hover_color or AppTheme._darken_color(color, 20)

        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: {padding};
                border-radius: {radius};
                font-weight: bold;
                font-size: 13px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton:pressed {{
                background: {AppTheme._darken_color(color, 30)};
            }}
            QPushButton:disabled {{
                background: {AppTheme.GRAY};
                color: {AppTheme.GRAY_DARK};
            }}
            QPushButton:focus {{
                outline: 2px solid {AppTheme._lighten_color(color, 40)};
                outline-offset: 2px;
            }}
        """

    @staticmethod
    def get_table_style() -> str:
        """Style pour les tables"""
        return f"""
            QTableWidget {{
                border: 1px solid {AppTheme.LIGHT_DARK};
                border-radius: 8px;
                background: white;
                gridline-color: {AppTheme.LIGHT_DARK};
                selection-background-color: {AppTheme.PRIMARY};
                selection-color: white;
            }}
            QHeaderView::section {{
                background: {AppTheme.DARK};
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {AppTheme.LIGHT};
            }}
            QTableWidget::item:selected {{
                background: {AppTheme.PRIMARY};
                color: white;
            }}
            QTableWidget QTableCornerButton::section {{
                background: {AppTheme.DARK};
                border: none;
            }}
        """

    @staticmethod
    def get_card_style() -> str:
        """Style pour les cartes/groupes"""
        return f"""
            QGroupBox {{
                border: 2px solid {AppTheme.LIGHT_DARK};
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 14px;
                color: {AppTheme.TEXT_PRIMARY};
                background: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background: {AppTheme.LIGHT};
                border-radius: 5px;
            }}
        """

    @staticmethod
    def get_input_style() -> str:
        """Style pour les champs de saisie"""
        return f"""
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                border: 2px solid {AppTheme.LIGHT_DARK};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background: white;
                selection-background-color: {AppTheme.PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {AppTheme.PRIMARY};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled,
            QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background: {AppTheme.LIGHT};
                color: {AppTheme.GRAY_DARK};
            }}
        """

    @staticmethod
    def get_tab_style() -> str:
        """Style pour les onglets"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {AppTheme.LIGHT_DARK};
                border-radius: 8px;
                background: white;
            }}
            QTabBar::tab {{
                background: {AppTheme.LIGHT};
                border: 1px solid {AppTheme.LIGHT_DARK};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 2px;
                font-weight: bold;
                color: {AppTheme.TEXT_SECONDARY};
            }}
            QTabBar::tab:selected {{
                background: white;
                border-bottom: 2px solid {AppTheme.PRIMARY};
                color: {AppTheme.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background: {AppTheme._lighten_color(AppTheme.LIGHT, 10)};
            }}
        """

    @staticmethod
    def get_label_style(label_type: str = "normal") -> str:
        """
        Style pour les labels

        Args:
            label_type: Type de label (normal, title, subtitle, success, error, warning, info)

        Returns:
            Style CSS
        """
        # CORRECTION : paramètre renommé de 'type' (builtin Python) en 'label_type'
        styles = {
            "normal": f"color: {AppTheme.TEXT_PRIMARY}; font-size: 13px;",
            "title": f"""
                color: {AppTheme.DARK};
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            """,
            "subtitle": f"""
                color: {AppTheme.TEXT_SECONDARY};
                font-size: 15px;
                font-weight: bold;
                padding: 5px 0;
            """,
            "success": f"""
                color: {AppTheme.SUCCESS};
                font-size: 13px;
                font-weight: bold;
            """,
            "error": f"""
                color: {AppTheme.DANGER};
                font-size: 13px;
                font-weight: bold;
            """,
            "warning": f"""
                color: {AppTheme.WARNING};
                font-size: 13px;
                font-weight: bold;
            """,
            "info": f"""
                color: {AppTheme.INFO};
                font-size: 13px;
                font-weight: bold;
            """
        }

        return styles.get(label_type, styles["normal"])

    @staticmethod
    def get_progress_bar_style() -> str:
        """Style pour les barres de progression"""
        return f"""
            QProgressBar {{
                border: 2px solid {AppTheme.LIGHT_DARK};
                border-radius: 6px;
                text-align: center;
                background: white;
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background: {AppTheme.PRIMARY};
                border-radius: 4px;
            }}
        """

    @staticmethod
    def get_scroll_area_style() -> str:
        """Style pour les zones de défilement"""
        return f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {AppTheme.LIGHT};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {AppTheme.GRAY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {AppTheme.GRAY_DARK};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
        """

    @staticmethod
    def get_menu_style() -> str:
        """Style pour les menus"""
        return f"""
            QMenu {{
                background: white;
                border: 1px solid {AppTheme.LIGHT_DARK};
                border-radius: 6px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 30px 8px 20px;
                border-radius: 4px;
                color: {AppTheme.TEXT_PRIMARY};
            }}
            QMenu::item:selected {{
                background: {AppTheme.PRIMARY};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: {AppTheme.LIGHT_DARK};
                margin: 5px 10px;
            }}
        """

    @staticmethod
    def get_tooltip_style() -> str:
        """Style pour les infobulles"""
        return f"""
            QToolTip {{
                background: {AppTheme.DARK};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """

    @staticmethod
    def apply_global_style(widget):
        """
        Applique le style global à un widget et ses enfants

        Args:
            widget: Widget à styliser
        """
        for child in widget.findChildren(QWidget):
            if isinstance(child, QPushButton):
                text = child.text().lower()
                obj_name = child.objectName().lower()

                if "supprimer" in text or "delete" in text or "danger" in obj_name:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.DANGER, AppTheme.DANGER_DARK))
                elif "enregistrer" in text or "save" in text or "success" in obj_name:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.SUCCESS, AppTheme.SUCCESS_DARK))
                elif "annuler" in text or "cancel" in text or "warning" in obj_name:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.WARNING, AppTheme.WARNING_DARK))
                elif "nouveau" in text or "new" in text or "primary" in obj_name:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.PRIMARY, AppTheme.PRIMARY_DARK))
                elif "info" in obj_name:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.INFO, AppTheme.INFO_DARK))
                else:
                    child.setStyleSheet(AppTheme.get_button_style(AppTheme.SECONDARY, AppTheme.SECONDARY_DARK))

            elif isinstance(child, QTableWidget):
                child.setStyleSheet(AppTheme.get_table_style())

            elif isinstance(child, QGroupBox):
                child.setStyleSheet(AppTheme.get_card_style())

            elif isinstance(child, (QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                child.setStyleSheet(AppTheme.get_input_style())

            elif isinstance(child, QTabWidget):
                child.setStyleSheet(AppTheme.get_tab_style())

            elif isinstance(child, QLabel):
                obj_name = child.objectName().lower()
                if "title" in obj_name:
                    child.setStyleSheet(AppTheme.get_label_style("title"))
                elif "subtitle" in obj_name:
                    child.setStyleSheet(AppTheme.get_label_style("subtitle"))
                elif any(word in obj_name for word in ["error", "danger", "erreur"]):
                    child.setStyleSheet(AppTheme.get_label_style("error"))
                elif any(word in obj_name for word in ["success", "succes"]):
                    child.setStyleSheet(AppTheme.get_label_style("success"))
                elif any(word in obj_name for word in ["warning", "avertissement"]):
                    child.setStyleSheet(AppTheme.get_label_style("warning"))
                elif "info" in obj_name:
                    child.setStyleSheet(AppTheme.get_label_style("info"))

            elif isinstance(child, QProgressBar):
                child.setStyleSheet(AppTheme.get_progress_bar_style())

            elif isinstance(child, QScrollArea):
                child.setStyleSheet(AppTheme.get_scroll_area_style())

            elif isinstance(child, QMenu):
                child.setStyleSheet(AppTheme.get_menu_style())

        widget.setStyleSheet(widget.styleSheet() + AppTheme.get_tooltip_style())

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        """Convertit une couleur hex en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb):
        """Convertit RGB en hex"""
        return '#%02x%02x%02x' % rgb

    @staticmethod
    def _darken_color(hex_color: str, percent: int):
        """
        Assombrit une couleur

        Args:
            hex_color: Couleur hex
            percent: Pourcentage d'assombrissement (0-100)

        Returns:
            Couleur assombrie en hex
        """
        rgb = AppTheme._hex_to_rgb(hex_color)
        factor = 1 - percent / 100
        darkened = tuple(int(c * factor) for c in rgb)
        return AppTheme._rgb_to_hex(darkened)

    @staticmethod
    def _lighten_color(hex_color: str, percent: int):
        """
        Éclaircit une couleur

        Args:
            hex_color: Couleur hex
            percent: Pourcentage d'éclaircissement (0-100)

        Returns:
            Couleur éclaircie en hex
        """
        rgb = AppTheme._hex_to_rgb(hex_color)
        factor = 1 + percent / 100
        lightened = tuple(min(255, int(c * factor)) for c in rgb)
        return AppTheme._rgb_to_hex(lightened)

    @staticmethod
    def create_gradient_css(start_color: str, end_color: str, direction: str = "to right"):
        """
        Crée un dégradé CSS Qt linéaire

        Args:
            start_color: Couleur de départ
            end_color: Couleur de fin
            direction: 'to right' (horizontal) ou 'to bottom' (vertical)

        Returns:
            Déclaration CSS de dégradé
        """
        # CORRECTION : le paramètre 'direction' est maintenant utilisé
        if direction == "to bottom":
            coords = "x1: 0, y1: 0, x2: 0, y2: 1"
        else:  # to right (défaut)
            coords = "x1: 0, y1: 0, x2: 1, y2: 0"

        return f"""
            background: qlineargradient(
                {coords},
                stop: 0 {start_color},
                stop: 1 {end_color}
            );
        """

    @staticmethod
    def create_shadow_css(color: str = None, blur: int = 10,
                          offset_x: int = 0, offset_y: int = 4):
        """
        Crée une ombre CSS Qt approximative via bordure colorée.

        Note: Qt ne supporte pas box-shadow natif. Pour une vraie ombre,
        utiliser QGraphicsDropShadowEffect programmatiquement.

        Args:
            color: Couleur de l'ombre
            blur: Flou (non supporté en CSS Qt — ignoré)
            offset_x: Décalage horizontal (non supporté en CSS Qt — ignoré)
            offset_y: Décalage vertical (non supporté en CSS Qt — ignoré)

        Returns:
            Déclaration CSS de bordure colorée (approximation)
        """
        # CORRECTION : paramètres documentés comme non supportés par Qt CSS
        # Pour une vraie ombre, préférer QGraphicsDropShadowEffect :
        #   effect = QGraphicsDropShadowEffect()
        #   effect.setBlurRadius(blur)
        #   effect.setOffset(offset_x, offset_y)
        #   effect.setColor(QColor(shadow_color))
        #   widget.setGraphicsEffect(effect)
        shadow_color = color or AppTheme._darken_color(AppTheme.DARK, 60)
        return f"""
            border: 1px solid {shadow_color};
        """

    @staticmethod
    def get_font(size: int = 13, weight: str = "normal",
                 family: str = "Segoe UI, Arial, sans-serif") -> str:
        """
        Génère une déclaration de police CSS

        Args:
            size: Taille de police
            weight: Épaisseur (normal, bold, etc.)
            family: Famille de police

        Returns:
            Déclaration CSS de police
        """
        return f"""
            font-family: {family};
            font-size: {size}px;
            font-weight: {weight};
        """
