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
├── config.py             # ВСЕ настройки (модель, кэш, язык, хоткей, куки)
├── voice2text/
│   ├── voice2text.py        # GUI: звук системы → текст в буфер (Ctrl+Space)
│   ├── voice2text.vbs       # запуск без терминала (для ярлыка)
│   ├── install.vbs          # установщик: venv + зависимости + ярлык
│   └── requirements.txt     # зависимости только voice2text
├── video2text/
│   ├── video2text.py        # YouTube → .txt + .srt
│   └── requirements.txt     # зависимости только video2text
├── requirements.txt      # мета: ставит оба (для разработки)
├── .gitignore
└── README.md
```

Оба инструмента используют **один общий venv** в корне и **один кэш моделей** — модель скачивается единожды. Зависимости разнесены по подпроектам (voice2text не тянет `yt-dlp`, video2text не тянет GUI-библиотеки).

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
> Путь кэша задан в `config.py`: `D:\cache\huggingface_cache`. Поменяй на свой, если диск другой
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

### Быстрая установка (одним кликом)

В папке `voice2text/` есть установщик **`install.vbs`** — делает всё сам:

1. Клонируй репозиторий: `git clone https://github.com/AI-bot-service/whisper-offline`
2. Установи Python 3.11 (если ещё нет): https://www.python.org/downloads/release/python-3119/
3. Двойной клик по **`voice2text/install.vbs`**.

Установщик проверит Python, создаст venv в корне, поставит зависимости и сделает
**ярлык `voice2text` на рабочем столе**. Прогресс виден в окне, по окончании — сообщение.

### Запуск без терминала

Готовый запускатель **`voice2text/voice2text.vbs`** — стартует приложение полностью
без консоли (`pythonw.exe` из venv, скрытый режим). Пути относительные — после клона
работает без правок.

- Двойной клик по `voice2text.vbs` — окно без чёрного терминала.
- Ярлык создаёт `install.vbs`; вручную — ПКМ по `voice2text.vbs` → **Отправить → Рабочий стол**.

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

## Настройки — всё в `config.py`

Один файл в корне, оба инструмента берут параметры оттуда:

| Параметр | Назначение |
|---|---|
| `MODEL` | модель Whisper (`...turbo-ct2` / `large-v3`) |
| `HF_HOME` | папка кэша моделей |
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
