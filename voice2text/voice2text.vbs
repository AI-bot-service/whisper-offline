' Запуск voice2text без окна терминала.
' Пути относительные: venv ищется в корне проекта (на уровень выше этой папки).
' Сделай ярлык на этот файл — двойной клик запустит приложение без консоли.

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)   ' ...\voice2text
root      = fso.GetParentFolderName(scriptDir)                ' ...\whisper-offline
pythonw   = root & "\venv\Scripts\pythonw.exe"
app       = scriptDir & "\voice2text.py"

If Not fso.FileExists(pythonw) Then
    MsgBox "Не найден venv: " & pythonw & vbCrLf & _
           "Создай окружение: py -3.11 -m venv venv  (в корне проекта)", _
           vbCritical, "voice2text"
    WScript.Quit
End If

sh.CurrentDirectory = scriptDir
' 0 = скрытое окно, False = не ждать завершения
sh.Run """" & pythonw & """ """ & app & """", 0, False
