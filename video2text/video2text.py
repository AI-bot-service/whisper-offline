import sys, os, re, subprocess

# === НАСТРОЙКИ ===
BROWSER      = "firefox"        # firefox работает; chrome/edge — нет (шифрование куки)
COOKIES_FILE = "cookies.txt"    # если файл рядом — юзается он; иначе браузер
MODEL        = "deepdml/faster-whisper-large-v3-turbo-ct2"

# кэш моделей на D + больший таймаут скачивания + тише варнинги
os.environ["HF_HOME"] = r"D:\huggingface_cache"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# консоль в utf-8 (кириллица без кракозябр)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# подключаем cudnn/cublas DLL из venv (GPU)
base = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..",
                                    "Lib", "site-packages", "nvidia"))
for sub in ("cudnn", "cublas"):
    p = os.path.join(base, sub, "bin")
    if os.path.isdir(p):
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

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
lang = sys.argv[2] if len(sys.argv) > 2 else None   # "ru","en" или пусто=авто

EJS = ["--remote-components", "ejs:github"]
if COOKIES_FILE and os.path.exists(COOKIES_FILE):
    YTDLP = [sys.executable, "-m", "yt_dlp", *EJS, "--cookies", COOKIES_FILE]
else:
    YTDLP = [sys.executable, "-m", "yt_dlp", *EJS, "--cookies-from-browser", BROWSER]

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

# 2. транскрипция на GPU (turbo)
model = WhisperModel(MODEL, device="cuda", compute_type="float16")
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
