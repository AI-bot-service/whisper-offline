' ============================================================
'  Установщик voice2text
'  Делает всё сам: проверяет Python 3.11, создаёт venv в корне
'  проекта, ставит зависимости, создаёт ярлык на рабочем столе.
'  Запуск: двойной клик по install.vbs
' ============================================================

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)   ' ...\voice2text
root      = fso.GetParentFolderName(scriptDir)                ' ...\whisper-offline
reqFile   = root & "\requirements.txt"
venvDir   = root & "\venv"
launcher  = scriptDir & "\voice2text.vbs"

If Not fso.FileExists(reqFile) Then
    MsgBox "Не найден requirements.txt в корне проекта:" & vbCrLf & reqFile, _
           vbCritical, "voice2text — установка"
    WScript.Quit
End If

answer = MsgBox("Установить voice2text?" & vbCrLf & vbCrLf & _
    "Будет создано окружение Python в:" & vbCrLf & venvDir & vbCrLf & vbCrLf & _
    "Требуется установленный Python 3.11 и интернет." & vbCrLf & _
    "Установка займёт несколько минут (~1.5 ГБ).", _
    vbOKCancel + vbInformation, "voice2text — установка")
If answer <> vbOK Then WScript.Quit

' --- собираем временный .bat для видимого прогресса установки ---
batPath = fso.GetSpecialFolder(2) & "\voice2text_install.bat"   ' %TEMP%
Set bat = fso.CreateTextFile(batPath, True)
bat.WriteLine "@echo off"
bat.WriteLine "chcp 65001 >nul"
bat.WriteLine "cd /d """ & root & """"
bat.WriteLine "echo === Проверка Python 3.11 ==="
bat.WriteLine "py -3.11 --version || (echo. & echo [ОШИБКА] Python 3.11 не найден. Установи с python.org & echo. & pause & exit /b 1)"
bat.WriteLine "if not exist ""venv"" ("
bat.WriteLine "  echo === Создаю виртуальное окружение ==="
bat.WriteLine "  py -3.11 -m venv venv || (echo [ОШИБКА] не удалось создать venv & pause & exit /b 1)"
bat.WriteLine ") else ( echo venv уже существует, пропускаю )"
bat.WriteLine "call venv\Scripts\activate"
bat.WriteLine "echo === Обновляю pip ==="
bat.WriteLine "python -m pip install --upgrade pip"
bat.WriteLine "echo === Ставлю зависимости (несколько минут) ==="
bat.WriteLine "pip install -r requirements.txt || (echo [ОШИБКА] установка зависимостей не удалась & pause & exit /b 1)"
bat.WriteLine "echo."
bat.WriteLine "echo === Установка зависимостей завершена ==="
bat.Close

' --- запускаем установку в видимом окне, ждём завершения ---
rc = sh.Run("""" & batPath & """", 1, True)

On Error Resume Next
fso.DeleteFile batPath
On Error Goto 0

If rc <> 0 Then
    MsgBox "Установка прервана (код " & rc & ")." & vbCrLf & _
           "Проверь, что установлен Python 3.11 и есть интернет.", _
           vbCritical, "voice2text — установка"
    WScript.Quit
End If

' --- ярлык на рабочем столе ---
desktop = sh.SpecialFolders("Desktop")
Set lnk = sh.CreateShortcut(desktop & "\voice2text.lnk")
lnk.TargetPath       = "wscript.exe"
lnk.Arguments        = """" & launcher & """"
lnk.WorkingDirectory = scriptDir
lnk.Description       = "voice2text — звук системы в текст"
lnk.Save

MsgBox "Готово!" & vbCrLf & vbCrLf & _
    "На рабочем столе создан ярлык 'voice2text'." & vbCrLf & _
    "Запуск — двойной клик по нему (без терминала).", _
    vbInformation, "voice2text — установка"
