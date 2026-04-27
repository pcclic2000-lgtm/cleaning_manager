; ═══════════════════════════════════════════════════════════════════════════
; create_installer.iss — Script Inno Setup 6
; Clean Manager ERP — Installateur Windows professionnel
;
; Prereq : Inno Setup 6 — https://jrsoftware.org/isinfo.php
; Compiler : Ctrl+F9 dans l'IDE Inno Setup, ou :
;            iscc.exe "build_tools\create_installer.iss"
;
; Produit : dist\installer\CleanManagerERP_Setup_1.1.0.exe
; ═══════════════════════════════════════════════════════════════════════════

#define MyAppName      "Clean Manager ERP"
#define MyAppVersion   "1.1.0"
#define MyAppPublisher "Clean Manager SARL"
#define MyAppURL       "https://www.entsnet.com"
#define MyAppExeName   "CleanManagerERP.exe"
#define MyAppId        "{A3F7B2D1-4E8C-4F9A-B6D3-2E1A5C8D0F4B}"
#define MyAppMutex     "CleanManagerERP_SingleInstance"

[Setup]
AppId={{#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\dist\installer
OutputBaseFilename=CleanManagerERP_Setup_{#MyAppVersion}
SetupIconFile=..\assets\logo-entreprise.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
WizardImageFile=..\assets\wizard_side.bmp
WizardSmallImageFile=..\assets\wizard_small.bmp
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Logiciel ERP pour entreprises de nettoyage
VersionInfoCopyright=Copyright 2025 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
AppMutex={#MyAppMutex}
CloseApplications=yes
CloseApplicationsFilter=*{#MyAppExeName}
RestartApplications=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[CustomMessages]
french.CreateDesktopIcon=Creer un raccourci sur le Bureau
french.CreateStartupShortcut=Lancer automatiquement au demarrage de Windows

[Tasks]
Name: "desktopicon";  Description: "{cm:CreateDesktopIcon}";     GroupDescription: "Raccourcis :"; Flags: checkedonce
Name: "startupentry"; Description: "{cm:CreateStartupShortcut}"; GroupDescription: "Options :";   Flags: unchecked

[Files]
Source: "..\dist\CleanManagerERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";              Filename: "{app}\{#MyAppExeName}"; Comment: "Lancer Clean Manager ERP"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";        Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Clean Manager ERP"
Name: "{userstartup}\{#MyAppName}";        Filename: "{app}\{#MyAppExeName}"; Tasks: startupentry

[Dirs]
Name: "{app}\database"; Permissions: users-modify
Name: "{app}\logs";     Permissions: users-modify
Name: "{app}\exports";  Permissions: users-modify
Name: "{app}\reports";  Permissions: users-modify

[Registry]
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version";     ValueData: "{#MyAppVersion}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName} maintenant"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\exports"
Type: filesandordirs; Name: "{app}\reports"
Type: files;          Name: "{app}\*.pyc"

[Code]

// Verifie si c'est une mise a jour (installation precedente detectee)
function IsUpgrade(): Boolean;
var
  PrevVersion: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\{#MyAppPublisher}\{#MyAppName}', 'Version', PrevVersion)
            and (PrevVersion <> '');
end;

// Sauvegarde la base de donnees avant une mise a jour
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  DBSource, DBBackup, Timestamp: String;
begin
  Result := '';

  if not IsUpgrade() then
    Exit;

  DBSource := ExpandConstant('{app}\database\cleaning_manager.db');
  if not FileExists(DBSource) then
    Exit;

  Timestamp := GetDateTimeString('yyyymmdd_hhnnss', #0, #0);
  DBBackup  := ExpandConstant('{app}\database\cleaning_manager_backup_') + Timestamp + '.db';

  if FileCopy(DBSource, DBBackup, False) then
    Log('Sauvegarde DB creee : ' + DBBackup)
  else
    Log('AVERT : Impossible de creer la sauvegarde DB');
end;

// Actions post-installation
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // init_db() dans main.py cree les tables manquantes au premier lancement
    Log('Installation terminee — init_db() gerera la migration au demarrage');
  end;
end;

// Initialisation de la desinstallation
function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

