; Instalador do Windows. Instala só para o usuário atual, sem pedir administrador.
; Compile com: iscc /DVersao=1.0.0 empacotar\rato-alarme.iss

[Setup]
AppId={{6E2D9B1E-5B3C-4E57-9C6B-7A1F3D2C8E10}
AppName=Rato-Alarme
AppVersion={#Versao}
AppPublisher=Artur Henrique
DefaultDirName={localappdata}\Programs\Rato-Alarme
DefaultGroupName=Rato-Alarme
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Rato-Alarme-Windows
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
UninstallDisplayIcon={app}\Rato-Alarme.exe

[Files]
Source: "..\dist\Rato-Alarme\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Rato-Alarme"; Filename: "{app}\Rato-Alarme.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "RatoAlarme"; Flags: uninsdeletevalue dontcreatekey

[Run]
Filename: "{app}\Rato-Alarme.exe"; Description: "Abrir o Rato-Alarme"; Flags: nowait postinstall

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM Rato-Alarme.exe"; Flags: runhidden; RunOnceId: "FecharRato"
