' ============================================================
'  video2text installer
'  Checks Python 3.11, creates venv in project root,
'  installs dependencies, creates a desktop shortcut.
'  Run: double-click install.vbs
' ============================================================

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)   ' ...\video2text
root      = fso.GetParentFolderName(scriptDir)                ' ...\whisper-offline
reqFile   = scriptDir & "\requirements.txt"   ' video2text deps only
venvDir   = root & "\venv"
launcher  = scriptDir & "\video2text.vbs"

If Not fso.FileExists(reqFile) Then
    MsgBox "requirements.txt not found:" & vbCrLf & reqFile, _
           vbCritical, "video2text setup"
    WScript.Quit
End If

answer = MsgBox("Install video2text?" & vbCrLf & vbCrLf & _
    "Python environment will be created in:" & vbCrLf & venvDir & vbCrLf & vbCrLf & _
    "Requires installed Python 3.11 and internet." & vbCrLf & _
    "deno is also needed for YouTube (winget install denoland.deno)." & vbCrLf & _
    "Takes a few minutes (~1.5 GB).", _
    vbOKCancel + vbInformation, "video2text setup")
If answer <> vbOK Then WScript.Quit

' --- temp .bat (ASCII only), run visibly ---
batPath = fso.GetSpecialFolder(2) & "\video2text_install.bat"   ' %TEMP%
Set bat = fso.CreateTextFile(batPath, True)
bat.WriteLine "@echo off"
bat.WriteLine "cd /d """ & root & """"
bat.WriteLine "echo === Check Python 3.11 ==="
bat.WriteLine "py -3.11 --version || (echo. & echo [ERROR] Python 3.11 not found. Install from python.org & echo. & pause & exit /b 1)"
bat.WriteLine "if not exist ""venv"" ("
bat.WriteLine "  echo === Creating virtual environment ==="
bat.WriteLine "  py -3.11 -m venv venv || (echo [ERROR] venv creation failed & pause & exit /b 1)"
bat.WriteLine ") else ( echo venv already exists, skipping )"
bat.WriteLine "call venv\Scripts\activate"
bat.WriteLine "echo === Upgrading pip ==="
bat.WriteLine "python -m pip install --upgrade pip"
bat.WriteLine "echo === Installing video2text dependencies (a few minutes) ==="
bat.WriteLine "pip install -r """ & reqFile & """ || (echo [ERROR] dependency install failed & pause & exit /b 1)"
bat.WriteLine "where deno >nul 2>&1 || (echo. & echo [WARNING] deno not found - needed for YouTube. Install: winget install denoland.deno)"
bat.WriteLine "echo."
bat.WriteLine "echo === Done. You can close this window. ==="
bat.Close

rc = sh.Run("""" & batPath & """", 1, True)

On Error Resume Next
fso.DeleteFile batPath
On Error Goto 0

If rc <> 0 Then
    MsgBox "Setup aborted (code " & rc & ")." & vbCrLf & _
           "Make sure Python 3.11 is installed and internet is available.", _
           vbCritical, "video2text setup"
    WScript.Quit
End If

' --- desktop shortcut ---
desktop = sh.SpecialFolders("Desktop")
Set lnk = sh.CreateShortcut(desktop & "\video2text.lnk")
lnk.TargetPath       = "wscript.exe"
lnk.Arguments        = """" & launcher & """"
lnk.WorkingDirectory = scriptDir
lnk.Description       = "video2text - YouTube to text"
lnk.Save

MsgBox "Done!" & vbCrLf & vbCrLf & _
    "Desktop shortcut 'video2text' created." & vbCrLf & _
    "Double-click it to run (no terminal)." & vbCrLf & vbCrLf & _
    "For YouTube: log in to YouTube in Firefox (or put cookies.txt in video2text folder).", _
    vbInformation, "video2text setup"
