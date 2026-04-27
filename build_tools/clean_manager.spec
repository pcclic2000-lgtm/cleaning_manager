# clean_manager.spec — Configuration PyInstaller pour Clean Manager ERP
#
# Usage depuis la RACINE du projet :
#   python -m PyInstaller build_tools\clean_manager.spec --noconfirm --clean
#
# Ou simplement : build_tools\build.bat

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT, "assets"),    "assets"),
    (os.path.join(ROOT, "config"),    "config"),
    (os.path.join(ROOT, "templates"), "templates"),
]
datas += collect_data_files("reportlab")
try:
    datas += collect_data_files("yaml")
except Exception:
    pass

hiddenimports = [
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "sqlalchemy.pool",
    "sqlalchemy.orm",
    "sqlalchemy.ext.declarative",
    "sqlalchemy.sql.sqltypes",
    "sqlalchemy.sql.default_comparator",
    "PyQt6.QtPrintSupport",
    "PyQt6.sip",
    "PyQt6.QtWidgets",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "reportlab.graphics.barcode",
    "reportlab.pdfbase._fontdata",
    "reportlab.pdfbase.cidfonts",
    "reportlab.pdfbase.ttfonts",
    "reportlab.platypus",
    "reportlab.platypus.tables",
    "PIL._imaging",
    "PIL.Image",
    "PIL.ImageQt",
    "decimal",
    "models.enums",
    "models.company",
    "models.employee",
    "models.client",
    "models.contrat",
    "models.tache",
    "models.affectation",
    "models.invoice",
    "models.payslip",
    "models.paye_globale",
    "models.cotisation",
    "models.expense",
    "models.bank",
    "models.relationships_config",
    "services.payslip_calculator",
    "services.payslip_builder",
    "services.payslip_pdf_service",
    "services.employee_status_service",
    "services.rapport_pdf_service",
    "services.certificat_pdf_service",
    "services.attestation_cnas_pdf",
    "services.attestation_pdf_service",
    "services.attestation_cnas_excel",
    "database.base",
    "database.db",
    "config.settings",
    "config.logging_config",
    "config.entreprise",
]
hiddenimports += collect_submodules("models")
hiddenimports += collect_submodules("views")
hiddenimports += collect_submodules("services")
hiddenimports += collect_submodules("utils")
hiddenimports += collect_submodules("config")
hiddenimports += collect_submodules("database")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "pandas", "scipy",
        "IPython", "jupyter", "notebook",
        "tkinter", "wx",
        "test", "unittest", "pytest",
        "docutils", "sphinx",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CleanManagerERP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, "assets", "logo-entreprise.ico"),
    version=os.path.join(ROOT, "build_tools", "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime140.dll", "python3*.dll", "Qt6*.dll"],
    name="CleanManagerERP",
)
