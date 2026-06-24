# whisper-offline

Локальная транскрибация речи в текст на GPU (NVIDIA, CUDA) — бесплатно, офлайн, на базе [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Два инструмента в одном репозитории:

| Подпроект | Что делает |
|---|---|
| **[voice2text](voice2text/)** | Настольное окно с горячей клавишей: захват **звука системы** → распознавание → текст в буфер обмена. |
| **[video2text](video2text/)** | Ссылка на **YouTube** → транскрипт: чистый текст + субтитры с таймингами (SRT). |

Модель по умолчанию: `large-v3-turbo`. Перевод EN→RU в проект не входит (добавляется отдельно при необходимости).

---

## Структура

```
whisper-offline/
├── voice2text/
│   └── voice2text.py     # GUI: звук системы → текст в буфер (хоткей Ctrl+Space)
├── video2text/
│   └── video2text.py     # YouTube → .txt + .srt
├── requirements.txt      # общие зависимости (один venv на оба)
├── .gitignore
└── README.md
```

Оба инструмента используют **один общий venv** в корне и **один кэш моделей** — модель скачивается единожды.

---

## Требования

- Windows 10 / 11
- **NVIDIA GPU** (GeForce RTX / GTX) + свежий драйвер (`nvidia-smi` должен работать)
- **Python 3.11** (на 3.12 / 3.13 ломается сборка зависимостей)
- **ffmpeg** в PATH
- **deno** — только для video2text (YouTube требует JS-движок)

---

## Установка

```powershell
# 1. внешние утилиты
winget install ffmpeg
winget install denoland.deno      # нужен только для video2text

# 2. клон репозитория
git clone https://github.com/AI-bot-service/whisper-offline
cd whisper-offline

# 3. общий venv + зависимости
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. проверка GPU
nvidia-smi
```

> Модель (~1.6 ГБ) скачается автоматически при первом запуске любого инструмента.
> Путь кэша задан в скриптах: `D:\huggingface_cache`. Поменяй на свой, если диск другой
> (переменная `HF_HOME` в начале каждого `.py`).

---

## voice2text — звук системы в текст

```powershell
venv\Scripts\activate
python voice2text\voice2text.py
```

- Окно появляется внизу по центру экрана, поверх всех окон.
- **Ctrl+Space** (или клик по квадратной кнопке) → старт записи звука системы.
- Повторное нажатие → стоп, распознавание на GPU, текст копируется в **буфер обмена**.
- Вставляешь сам куда нужно: **Ctrl+V**.
- Справа — живая звуковая дорожка, снизу — статус и распознанный текст.

Звук берётся с **динамика по умолчанию** (loopback) — видео/созвон должны играть через него.

### Запуск без терминала (ярлык на рабочем столе)

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$lnk = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\voice2text.lnk")
$lnk.TargetPath       = "C:\путь\к\whisper-offline\venv\Scripts\pythonw.exe"
$lnk.Arguments        = "C:\путь\к\whisper-offline\voice2text\voice2text.py"
$lnk.WorkingDirectory = "C:\путь\к\whisper-offline\voice2text"
$lnk.Save()
```

`pythonw.exe` запускает окно **без чёрной консоли**. Двойной клик по ярлыку — готово.
Подставь реальный путь к папке проекта.

---

## video2text — YouTube в текст

1. Залогинься в YouTube в **Firefox** (Chrome / Edge не работают — App-Bound шифрование куки).
   Альтернатива: положи рядом `cookies.txt` (расширение «Get cookies.txt LOCALLY»).
2. Запуск:
   ```powershell
   venv\Scripts\activate
   python video2text\video2text.py "https://youtube.com/watch?v=..."        # авто-язык
   python video2text\video2text.py "https://youtube.com/watch?v=..." ru     # форс язык
   ```
3. Рядом со скриптом появятся:
   - `{название видео}.wav` — аудио (повторно не качается, если уже есть)
   - `{название видео}.txt` — чистый текст
   - `{название видео}.srt` — фразы с таймингами

---

## Настройки (вверху каждого скрипта)

| Параметр | Где | Назначение |
|---|---|---|
| `MODEL` | оба | модель Whisper (`...turbo-ct2` / `large-v3`) |
| `HF_HOME` | оба | папка кэша моделей |
| `LANG` | оба | язык (`ru`, `en`, пусто = авто) |
| `HOTKEY` | voice2text | горячая клавиша |
| `BROWSER` / `COOKIES_FILE` | video2text | источник куки YouTube |

---

## Безопасность

- `cookies.txt` содержит **авторизационные куки YouTube** — он в `.gitignore`, никогда не коммить.
- venv, модели и результаты (`*.wav/.txt/.srt`) тоже игнорируются — большие и личные.

---

## Лицензия

MIT
