; Script Inno Setup para o instalador do Sistema de Gestão Empresarial (Dimensão do Logus)
; Compile com o Inno Setup Compiler (https://jrsoftware.org/isinfo.php)
;
; IMPORTANTE: execute o PyInstaller ANTES de compilar este instalador:
;   pyinstaller build.spec
; Ou use o script: build_installer.bat

#define MyAppName "Dimensão do Logus"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Dimensão do Logus"
#define MyAppExeName "SistemaGestao.exe"
#define MyAppURL "https://dimensaologus.local"

; Caminho absoluto do executável (relativo ao diretório deste .iss)
#define DistDir AddBackslash(SourcePath) + "dist"
#define DistExe DistDir + "\" + MyAppExeName

; Valida se o PyInstaller já foi executado
#if FileExists(DistExe)
#else
#pragma error "Arquivo nao encontrado: " DistExe ". Execute 'pyinstaller build.spec' (ou build_installer.bat) antes de compilar o instalador."
#endif

[Setup]
AppId={{7C4F1A62-9E38-4B5D-9A21-D3F6B7C80851}
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
OutputDir={#SourcePath}\installer_output
OutputBaseFilename=DimensaoLogus_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Executável gerado pelo PyInstaller (modo onefile)
Source: "{#DistExe}"; DestDir: "{app}"; Flags: ignoreversion
; Manual básico exibido no menu iniciar
Source: "{#SourcePath}\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Manual de Utilização"; Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; A pasta data (banco SQLite) e backups ficam em {app} e sao removidas com a desinstalacao.
; Faca backup pela tela de Configuracoes antes de desinstalar, se precisar preservar os dados.
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\backups"
Type: filesandordirs; Name: "{app}\assets"
