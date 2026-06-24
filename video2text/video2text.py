import sys, os, re, subprocess

# настройки из корневого config.py + подготовка окружения (кэш + GPU DLL)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
config.setup()

# консоль в utf-8 (кириллица без кракозябр)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from faster_whisper import WhisperModel


def fmt(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace('.', ',')


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:120] or "video"


if len(sys.argv) < 2:
    print("использование: python video2text.py \"<ссылка YouTube>\" [ru|en]")
    sys.exit(1)

url  = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else config.LANG   # CLI > config

EJS = ["--remote-components", "ejs:github"]
if config.COOKIES_FILE and os.path.exists(config.COOKIES_FILE):
    YTDLP = [sys.executable, "-m", "yt_dlp", *EJS, "--cookies", config.COOKIES_FILE]
else:
    YTDLP = [sys.executable, "-m", "yt_dlp", *EJS, "--cookies-from-browser", config.BROWSER]

# 0. имя видео (utf-8)
env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
title = subprocess.run(
    YTDLP + ["--print", "title", "--skip-download", url],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    env=env).stdout.strip()
name = safe_name(title)
print("видео:", title or "(заголовок не получен)")

audio = f"{name}.wav"

# 1. качаем аудио ТОЛЬКО если ещё нет
if os.path.exists(audio):
    print(f"аудио уже скачано, пропускаю: {audio}")
else:
    subprocess.run(
        YTDLP + ["-x", "--audio-format", "wav",
                 "-o", f"{name}.%(ext)s", url], check=True)

# 2. транскрипция на GPU
model = WhisperModel(config.MODEL, device=config.DEVICE, compute_type=config.COMPUTE_TYPE)
segments, info = model.transcribe(audio, language=lang,
                                  vad_filter=True, condition_on_previous_text=False)
print("язык:", info.language)

# 3. {имя}.txt (текст) + {имя}.srt (с таймингами)
with open(f"{name}.txt", "w", encoding="utf-8") as ft, \
     open(f"{name}.srt", "w", encoding="utf-8") as fs:
    for i, seg in enumerate(segments, 1):
        t = seg.text.strip()
        ft.write(t + "\n")
        fs.write(f"{i}\n{fmt(seg.start)} --> {fmt(seg.end)}\n{t}\n\n")
        print(f"[{fmt(seg.start)}] {t}")

print(f"\nготово: {name}.txt, {name}.srt, аудио: {audio}")
