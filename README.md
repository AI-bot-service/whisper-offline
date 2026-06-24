# whisper-offline

Локальная транскрибация речи в текст на GPU (NVIDIA, CUDA) — бесплатно, офлайн, на базе [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Два инструмента в одном репозитории:

| Подпроект | Что делает |
|---|---|
| **[voice2text](voice2text/)** | Настольное окно с горячей клавишей: захват **звука системы** → распознавание → текст в буфер обмена. |
| **[video2text](video2text/)** | Ссылка на **YouTube** → транскрипт: чистый текст + субтитры с таймингами (SRT). |

Модель по умолчанию: `large-v3-turbo`. Перевод EN→RU в проект не входит (добавляется отдельно при необходимости).

---

## Требования

- Windows 10 / 11
- **NVIDIA GPU** (GeForce RTX / GTX) + свежий драйвер (`nvidia-smi` должен работать)
- **Python 3.11** — [скачать](https://www.python.org/downloads/release/python-3119/) (на 3.12 / 3.13 ломается сборка зависимостей)
- **deno** — только для video2text (`winget install denoland.deno`)

---

## Установка (рекомендуется) — один клик

1. Установи **Python 3.11** (галка «Add to PATH» при установке).
2. Склонируй репозиторий:
   ```powershell
   git clone https://github.com/AI-bot-service/whisper-offline
   ```
3. Запусти установщик нужного инструмента двойным кликом:
   - **`voice2text/install.vbs`** — для voice2text
   - **`video2text/install.vbs`** — для video2text

Установщик сам проверит Python, создаст venv в корне, поставит зависимости (прогресс
виден в окне) и создаст **ярлык на рабочем столе**. Дальше запуск — двойным кликом по ярлыку.

> venv общий для обоих инструментов. Поставив один — второй доустановит только свои
> зависимости. Модель (~1.6 ГБ) скачается при первом запуске.

---

## voice2text — звук системы в текст

Запуск: ярлык **voice2text** на рабочем столе (или `voice2text/voice2text.vbs`) — окно без терминала.

- Окно появляется внизу по центру экрана, поверх всех окон.
- **Ctrl+Space** (или клик по квадратной кнопке) → старт записи звука системы.
- Повторное нажатие → стоп, распознавание на GPU, текст копируется в **буфер обмена**.
- Вставляешь сам куда нужно: **Ctrl+V**.
- Справа — живая звуковая дорожка, снизу — статус и распознанный текст.

Звук берётся с **динамика по умолчанию** (loopback) — видео/созвон должны играть через него.

---

## video2text — YouTube в текст

Запуск: ярлык **video2text** на рабочем столе (или `video2text/video2text.vbs`) — окно без терминала.

**Подготовка:** залогинься в YouTube в **Firefox** (Chrome / Edge не работают —
App-Bound шифрование куки). Альтернатива: положи `cookies.txt` в папку `video2text/`
(расширение «Get cookies.txt LOCALLY»).

> **Где берутся куки Firefox.** yt-dlp читает их напрямую из профиля, ничего
> экспортировать не надо — файл `cookies.sqlite`:
> ```
> %APPDATA%\Mozilla\Firefox\Profiles\<профиль>.default-release\cookies.sqlite
> ```
> Профиль находится автоматически. Firefox не шифрует куки (в отличие от Chrome/Edge),
> поэтому работает «на лету» — главное быть залогиненным в YouTube.

В окне: вставь ссылку → выбери **язык** (авто/ru/en) → **СТАРТ** (превращается в **СТОП**)
→ снизу шкала прогресса (скачивание 0–50 %, транскрипция 50–100 %). После готовности —
кнопка **«Открыть папку»** с результатом.

Результат → **`video2text/out/{название видео}/`**:
- `{название}.wav` — аудио (повторно не качается, если уже есть)
- `{название}.txt` — чистый текст
- `{название}.srt` — фразы с таймингами

---

## Ручная установка и запуск (по желанию)

Если не хочешь установщик `.vbs` — то же самое руками.

```powershell
# внешние утилиты
winget install ffmpeg
winget install denoland.deno      # нужен только для video2text

# клон
git clone https://github.com/AI-bot-service/whisper-offline
cd whisper-offline

# общий venv
py -3.11 -m venv venv
venv\Scripts\activate

# зависимости: оба сразу...
pip install -r requirements.txt
# ...или по отдельности:
pip install -r voice2text\requirements.txt
pip install -r video2text\requirements.txt

# проверка GPU
nvidia-smi
```

Запуск из терминала:

```powershell
venv\Scripts\activate

# voice2text — окно
python voice2text\voice2text.py

# video2text — окно
python video2text\video2text.py

# video2text — без окна, сразу по ссылке (CLI)
python video2text\video2text.py "https://youtube.com/watch?v=..."        # авто-язык
python video2text\video2text.py "https://youtube.com/watch?v=..." ru     # форс язык
```

Ярлык вручную: ПКМ по `*.vbs` → **Отправить → Рабочий стол**.

---

## Структура

```
whisper-offline/
├── config.py             # ВСЕ настройки (модель, кэш, язык, хоткей, куки)
├── voice2text/
│   ├── voice2text.py        # GUI: звук системы → текст в буфер (Ctrl+Space)
│   ├── voice2text.vbs       # запуск без терминала (для ярлыка)
│   ├── install.vbs          # установщик: venv + зависимости + ярлык
│   └── requirements.txt     # зависимости только voice2text
├── video2text/
│   ├── video2text.py        # GUI: YouTube → out/{название}/.wav/.txt/.srt
│   ├── video2text.vbs       # запуск без терминала (для ярлыка)
│   ├── install.vbs          # установщик: venv + зависимости + ярлык
│   ├── out/                 # результаты (создаётся сам, в .gitignore)
│   └── requirements.txt     # зависимости только video2text
├── requirements.txt      # мета: ставит оба (для разработки)
├── .gitignore
└── README.md
```

Оба инструмента используют **один общий venv** в корне и **один кэш моделей** — модель скачивается единожды. Зависимости разнесены по подпроектам (voice2text не тянет `yt-dlp`, video2text не тянет GUI-библиотеки).

---

## Настройки — всё в `config.py`

Один файл в корне, оба инструмента берут параметры оттуда:

| Параметр | Назначение |
|---|---|
| `MODEL` | модель Whisper (`...turbo-ct2` / `large-v3`) |
| `HF_HOME` | папка кэша моделей (по умолч. `D:\cache\huggingface_cache`) |
| `LANG` | язык (`"ru"`, `"en"`, `None` = авто) |
| `DEVICE` / `COMPUTE_TYPE` | `cuda`+`float16` (GPU) или `cpu`+`int8` |
| `HOTKEY` | горячая клавиша (voice2text) |
| `BROWSER` / `COOKIES_FILE` | источник куки YouTube (video2text) |

Меняешь значение в `config.py` — применяется к обоим. Функция `config.setup()` готовит
кэш и GPU-библиотеки (вызывается скриптами автоматически).

---

## Безопасность

- `cookies.txt` содержит **авторизационные куки YouTube** — он в `.gitignore`, никогда не коммить.
- venv, модели и результаты (`*.wav/.txt/.srt`) тоже игнорируются — большие и личные.

---

## Лицензия

MIT
