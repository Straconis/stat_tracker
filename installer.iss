#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName "Stat Tracker"
#define MyAppExeName "StatTracker.exe"

[Setup]
AppId={{C7BFF5B7-6991-4E88-BFB5-1FF55D64D680}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\Stat Tracker
DefaultGroupName=Stat Tracker
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=dist
OutputBaseFilename=StatTrackerSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
Uninstallable=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=stat_tracker.ico

[Files]
Source: "dist\StatTracker.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Stat Tracker"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Stat Tracker"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Stat Tracker"; Flags: nowait postinstall skipifsilent
