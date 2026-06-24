' Launch video2text GUI without a terminal window.
' Relative paths: venv is expected in the project root (one level up).
' Make a shortcut to this file - double-click runs the app with no console.

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)   ' ...\video2text
root      = fso.GetParentFolderName(scriptDir)                ' ...\whisper-offline
pythonw   = root & "\venv\Scripts\pythonw.exe"
app       = scriptDir & "\video2text.py"

If Not fso.FileExists(pythonw) Then
    MsgBox "venv not found: " & pythonw & vbCrLf & _
           "Create it: py -3.11 -m venv venv (in project root), then pip install -r video2text\requirements.txt", _
           vbCritical, "video2text"
    WScript.Quit
End If

sh.CurrentDirectory = scriptDir
' 0 = hidden window, False = do not wait
sh.Run """" & pythonw & """ """ & app & """", 0, False
