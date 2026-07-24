; Script de Inno Setup para "Gestión de Taller".
;
; Requiere: haber corrido antes "pyinstaller packaging/TallerMotos.spec"
; desde la raíz del proyecto, de forma que exista dist/TallerMotos/.
;
; Compilar con el compilador de Inno Setup (ISCC.exe) o abriendo este
; archivo en la aplicación Inno Setup Compiler.
;
; IMPORTANTE: el AppId debe mantenerse IGUAL en todas las versiones futuras
; para que las actualizaciones se instalen encima en vez de duplicar la app.

#define MyAppName "Gestión de Taller"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tu empresa"
#define MyAppExeName "TallerMotos.exe"

[Setup]
AppId={{D592874B-F099-4508-B478-51024D61C19D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\TallerMotos
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=TallerMotosSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\app.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\dist\TallerMotos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

; No borramos %LOCALAPPDATA%\TallerMotos al desinstalar: ahí vive la base de
; datos, la licencia y los respaldos del cliente. Si se reinstala o
; actualiza, sus datos siguen intactos.
[UninstallDelete]
; (intencionalmente vacío — ver comentario arriba)

[Code]
const
  WebView2RegKey = 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function WebView2Instalado(): Boolean;
begin
  Result := RegKeyExists(HKLM, WebView2RegKey) or RegKeyExists(HKCU, WebView2RegKey);
end;

procedure InitializeWizard();
begin
  if not WebView2Instalado() then
  begin
    MsgBox(
      'Este programa necesita "Microsoft Edge WebView2 Runtime", que normalmente ya viene ' +
      'instalado en Windows 10/11. Si la aplicación no abre después de instalarla, descarga ' +
      'el runtime desde el sitio oficial de Microsoft ("Microsoft Edge WebView2 Runtime") ' +
      'e instálalo.',
      mbInformation, MB_OK
    );
  end;
end;
