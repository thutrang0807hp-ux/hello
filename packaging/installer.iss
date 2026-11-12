[Setup]
AppId={{45F21EEB-FA7B-44A3-8255-89C62AC0567F}
AppName=Freelance Desk
AppVersion=1.2.1
DefaultDirName={localappdata}\Programs\FreelanceDesk
DefaultGroupName=Freelance Desk
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=FreelanceDesk-Setup
SetupIconFile=..\public\desktop.ico
UninstallDisplayIcon={app}\FreelanceDesk.exe
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
WizardStyle=modern

[Files]
Source: "..\dist\FreelanceDesk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\repair-webview2-windows.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\repair-webview2-windows.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Freelance Desk"; Filename: "{app}\FreelanceDesk.exe"
Name: "{userdesktop}\Freelance Desk"; Filename: "{app}\FreelanceDesk.exe"
Name: "{group}\Chan doan Freelance Desk"; Filename: "{app}\FreelanceDesk.exe"; Parameters: "--diagnose"

Name: "{group}\Dừng dịch vụ Freelance Desk"; Filename: "{app}\FreelanceDesk.exe"; Parameters: "--stop-server"

[Run]
Filename: "{app}\FreelanceDesk.exe"; Description: "Mo Freelance Desk"; Flags: nowait postinstall skipifsilent

; No AppData deletion: SQLite, settings, Gmail tokens and WebView profile survive uninstall.
