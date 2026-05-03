; Inno Setup script for JS8Spotter-Subspace
;
; Build with Inno Setup 6+ (https://jrsoftware.org/isdl.php).
;
; Default usage from the installer/ directory:
;     iscc js8spotter-subspace.iss
;   (expects the deployment folder at ..\..\js8spotter-300_win10 -- adjust if needed)
;
; Override the source folder explicitly:
;     iscc /DSourceDir=C:\path\to\js8spotter-300_win10 js8spotter-subspace.iss
;
; Output: js8spotter-subspace-<version>-setup.exe in the current directory.

#ifndef SourceDir
  #define SourceDir "..\..\js8spotter-300_win10"
#endif

#define MyAppName        "JS8Spotter-Subspace"
#define MyAppVersion     "3.0.1"
#define MyAppPublisher   "Andy van Tol WM8Q"
#define MyAppURL         "https://github.com/avantol/js8spotter-subspace"
#define MyAppExeName     "js8spotter.exe"

[Setup]
; AppId is a stable UUID; do NOT change between releases or upgrades will be treated as a fresh install
AppId={{8AD5BBFF-5C69-5E09-82E5-AD8ABD8C6D4E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoVersion={#MyAppVersion}

; Per-user install -- no admin / UAC required, lives under %LOCALAPPDATA%\Programs
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=auto
UsePreviousAppDir=yes

LicenseFile={#SourceDir}\LICENSE.txt
SetupIconFile={#SourceDir}\js8spotter.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

OutputDir=.
OutputBaseFilename=js8spotter-subspace-{#MyAppVersion}-setup

; The .exe inside is 32-bit but happily runs on x64 under WoW64
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; User database: install on first run only, and never delete on upgrade or uninstall
Source: "{#SourceDir}\js8spotter.db"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

; Everything else: replace freely. Exclude the user db (handled above) and any stale Linux pyc cache
Source: "{#SourceDir}\*"; DestDir: "{app}"; Excludes: "js8spotter.db,__pycache__\*,*.cpython-312.pyc"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";              Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\js8spotter.ico"
Name: "{group}\Uninstall {#MyAppName}";    Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";        Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\js8spotter.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
