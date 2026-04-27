# Guide de compilation — Clean Manager ERP

## Prérequis

| Outil | Version | Téléchargement |
|---|---|---|
| Python | 3.11 ou 3.12 **(64-bit)** | https://python.org |
| Inno Setup | 6.x | https://jrsoftware.org/isinfo.php |
| UPX (optionnel) | 4.x | https://upx.github.io |

> ⚠️ **Python 64-bit obligatoire** — PyQt6 ne fonctionne pas en 32-bit.  
> ⚠️ Cochez **"Add Python to PATH"** pendant l'installation de Python.

---

## Compilation en une seule commande

Depuis la racine du projet, double-cliquez sur :

```
build_tools\build.bat
```

Le script gère tout automatiquement et produit :

```
dist\
├── CleanManagerERP\              ← Dossier portable (zip et distribuez)
│   ├── CleanManagerERP.exe
│   ├── assets\
│   ├── config\
│   ├── templates\
│   ├── database\   (vide — créé au 1er lancement)
│   ├── logs\
│   ├── exports\
│   └── reports\
└── installer\
    └── CleanManagerERP_Setup_1.1.0.exe   ← Si Inno Setup installé
```

---

## Étapes détaillées du build.bat

| Étape | Action |
|---|---|
| 1 | Vérifie Python 64-bit ≥ 3.11 |
| 2 | Installe/met à jour PyInstaller + dépendances |
| 3 | Vérifie les fichiers requis (assets, config, templates) |
| 4 | Nettoie les anciens builds |
| 5 | Lance PyInstaller avec clean_manager.spec |
| 6 | Crée les dossiers runtime + copie LICENSE |
| 7 | Lance Inno Setup si `iscc.exe` est trouvé |

---

## Créer l'installateur .exe (Inno Setup)

Si Inno Setup n'est pas installé au moment du build :

1. Téléchargez **Inno Setup 6** : https://jrsoftware.org/isinfo.php
2. Ouvrez `build_tools\create_installer.iss`
3. Menu **Build → Compile** (ou `Ctrl+F9`)
4. Résultat : `dist\installer\CleanManagerERP_Setup_1.1.0.exe`

### Ce que fait l'installateur Inno Setup

- Installe dans `C:\Program Files\Clean Manager ERP\`
- Crée un raccourci Bureau (optionnel, coché par défaut)
- Option démarrage automatique Windows (non coché par défaut)
- **Sauvegarde automatique de la base de données** lors d'une mise à jour
  → `database\cleaning_manager_backup_YYYYMMDD_HHMMSS.db`
- Crée les dossiers `database\`, `logs\`, `exports\`, `reports\` avec permissions en écriture
- Enregistre le chemin d'installation dans la registry Windows
- Gère la désinstallation propre (supprime logs/exports, **conserve** la base)

---

## Résolution des problèmes courants

### `ModuleNotFoundError: No module named 'X'` au lancement de l'exe

Le module `X` n'a pas été détecté par PyInstaller. Ajoutez-le dans `clean_manager.spec` :

```python
hiddenimports = [
    ...
    "nom.du.module.manquant",
]
```

Puis recompilez.

### L'exe ne trouve pas les assets (logo, styles, templates)

Vérifiez que tous les chemins utilisent `resource_path()` :

```python
# main.py expose déjà cette fonction
from main import resource_path   # ou recopiez ce pattern :

import sys, os
def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

logo = resource_path("assets/logo-entreprise.jpg")
```

### L'antivirus bloque l'exe

Faux positif courant avec PyInstaller. Solutions :
- **Court terme** : ajoutez une exclusion dans votre antivirus pour le dossier `dist\`
- **Long terme** : signez le binaire avec un certificat code-signing EV

### La compression UPX produit un exe corrompu

Certaines DLLs Qt6 se corrompent à la compression. Les DLLs problématiques sont
déjà exclues dans `clean_manager.spec` (`upx_exclude`). Si d'autres DLLs posent
problème, désactivez UPX complètement :

```python
# Dans clean_manager.spec
exe = EXE(..., upx=False, ...)
coll = COLLECT(..., upx=False, ...)
```

### Réduire la taille de l'exe

1. Installez **UPX 4.x** et ajoutez son dossier au PATH Windows
2. Utilisez un **virtualenv propre** avec uniquement les dépendances requises :
   ```bat
   python -m venv venv_build
   venv_build\Scripts\activate
   pip install -r requirements.txt
   build_tools\build.bat
   ```
3. Vérifiez la liste `excludes` dans le `.spec` et ajoutez tout module inutile

---

## Mise à jour d'une version existante

L'installateur Inno Setup détecte automatiquement une installation existante.
Il **sauvegarde la base de données** avant d'écraser les fichiers, puis l'application
exécute `init_db()` au démarrage qui ajoute les colonnes manquantes sans supprimer
les données.

Pour une migration manuelle de la base :
```bat
cd dist\CleanManagerERP
CleanManagerERP.exe --migrate   REM (si cette option est implémentée)
REM ou directement :
python tools\migrate.py
```
