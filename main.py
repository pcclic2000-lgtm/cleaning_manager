# main.py — CLEAN MANAGER ERP
"""
Point d'entrée unique de l'application.

Ordre de démarrage :
  1. Logging (en tout premier, avant tout import tiers)
  2. Environnement (dossiers runtime)
  3. Base de données (init SQLAlchemy + seed données par défaut)
  4. Interface PyQt6 (splash → MainWindow → boucle événements)
"""

import sys
import os
import traceback

# ── 1. Logging — doit être le tout premier import applicatif ────────────────
from config.logging_config import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)

# ── Imports PyQt6 ───────────────────────────────────────────────────────────
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# ── Chemin racine dans sys.path ─────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ── Version centralisée
try:
    from __version__ import __version__
except ImportError:
    __version__ = "1.0.0"

# ── Résolution des chemins (dev + exe PyInstaller)
def resource_path(relative: str) -> str:
    """Retourne le chemin absolu vers une ressource.

    En développement : chemin relatif à ROOT_DIR.
    Dans l'exe PyInstaller : chemin relatif à sys._MEIPASS (dossier temp extrait).
    """
    base = getattr(sys, "_MEIPASS", ROOT_DIR)
    return os.path.join(base, relative)


def setup_environment() -> bool:
    """Crée les dossiers runtime nécessaires."""
    logger.info("Vérification de l'environnement...")
    for d in ["database", "assets", "reports", "exports", "logs"]:
        os.makedirs(os.path.join(ROOT_DIR, d), exist_ok=True)
    return True


def initialize_database() -> bool:
    """Initialise la base SQLite via init_db() puis insère les données par défaut."""
    logger.info("Initialisation de la base de données...")
    try:
        from database.db import init_db, DATABASE_PATH
        logger.info("%s : %s", "Base existante" if os.path.exists(DATABASE_PATH) else "Nouvelle base", DATABASE_PATH)
        if not init_db():
            logger.error("init_db() a échoué")
            return False
        _seed_company_defaults()
        return True
    except Exception as exc:
        logger.critical("Échec init base de données : %s", exc, exc_info=True)
        return False


def _seed_company_defaults() -> None:
    """Insère les paramètres entreprise par défaut si la base est vierge."""
    try:
        from database.db import get_session
        from models.company import CompanyInfo, CompanySettings

        with get_session() as session:
            if session.query(CompanyInfo).count() == 0:
                session.add(CompanyInfo(
                    nom="Votre Entreprise",
                    adresse="123 Rue Principale",
                    ville="Alger",
                    telephone="0550 00 00 00",
                    email="contact@entreprise.dz",
                    devise="DA",
                    pays="Algérie",
                ))
                logger.info("Données entreprise par défaut créées")

            if session.query(CompanySettings).count() == 0:
                session.add(CompanySettings(
                    prefix_facture="FAC",
                    prochain_numero_facture=1,
                    taux_tva=19,
                    conditions_paiement="Paiement à 30 jours",
                    auto_sauvegarde=True,
                    frequence_sauvegarde=7,
                    session_timeout=30,
                ))
                logger.info("Paramètres par défaut créés")

            session.commit()

    except ImportError as exc:
        logger.warning("Modèle company introuvable, seed ignoré : %s", exc)
    except Exception as exc:
        logger.warning("Erreur seed données entreprise : %s", exc)


def _load_stylesheet(app: QApplication) -> None:
    qss_path = resource_path(os.path.join("assets", "styles.qss"))
    if os.path.exists(qss_path):
        try:
            with open(qss_path, encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            logger.debug("Feuille de style chargée")
            return
        except OSError as exc:
            logger.warning("Impossible de lire styles.qss : %s", exc)
    app.setStyleSheet("""
        QMainWindow  { background-color: #f5f7fa; }
        QPushButton  { background-color: #3498db; color: white; border: none;
                       padding: 8px 15px; border-radius: 4px; font-weight: bold; }
        QPushButton:hover { background-color: #2980b9; }
        QLineEdit, QTextEdit, QComboBox { padding: 8px; border: 1px solid #ddd;
                       border-radius: 4px; font-size: 14px; }
        QLineEdit:focus, QTextEdit:focus { border-color: #3498db; }
    """)


def _make_splash() -> QSplashScreen:
    pix = QPixmap(600, 400)
    pix.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(pix)
    splash.showMessage(
        "🧹  Clean Manager ERP\nInitialisation en cours...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.darkGray,
    )
    splash.show()
    return splash


def _splash_msg(splash: QSplashScreen, app: QApplication, msg: str) -> None:
    splash.showMessage(msg, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
    app.processEvents()


def launch_ui() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Clean Manager ERP")
    app.setApplicationVersion(__version__)

    splash = _make_splash()
    app.processEvents()

    _splash_msg(splash, app, "Initialisation de la base de données...")
    if not initialize_database():
        splash.close()
        QMessageBox.critical(None, "Erreur fatale", "Impossible d'initialiser la base de données.\nConsultez logs/app.log pour le détail.")
        return 1

    _splash_msg(splash, app, "Chargement de l'interface...")
    _load_stylesheet(app)

    _splash_msg(splash, app, "Chargement de la fenêtre principale...")
    try:
        from views.main_window import MainWindow
        window = MainWindow()
        logger.info("Fenêtre principale créée avec succès")
    except Exception as exc:
        splash.close()
        logger.critical("Impossible de créer MainWindow : %s", exc, exc_info=True)
        QMessageBox.critical(None, "Erreur de démarrage", f"Impossible de charger l'interface principale :\n{exc}\n\nConsultez logs/app.log pour le détail complet.")
        return 1

    splash.finish(window)
    window.show()
    logger.info("Application démarrée — version %s", __version__)
    return app.exec()


def main() -> int:
    try:
        setup_environment()
        return launch_ui()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
        return 0
    except Exception as exc:
        logger.critical("Erreur critique non gérée : %s", exc, exc_info=True)
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            box = QMessageBox()
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle("Erreur critique")
            box.setText("Une erreur inattendue s'est produite.")
            box.setDetailedText(traceback.format_exc())
            box.setStandardButtons(QMessageBox.StandardButton.Close)
            box.exec()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
