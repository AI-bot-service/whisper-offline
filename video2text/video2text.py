import sys, os, re, subprocess, threading

# настройки из корневого config.py + подготовка окружения (кэш + GPU DLL)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
import config
config.setup()

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from faster_whisper import WhisperModel

# === ПУТИ ===
OUT_BASE    = os.path.join(SCRIPT_DIR, "out")
COOKIE_PATH = os.path.join(SCRIPT_DIR, config.COOKIES_FILE) if config.COOKIES_FILE else ""

# === yt-dlp база (куки + EJS) ===
def ytdlp_base():
    ejs = ["--remote-components", "ejs:github"]
    if COOKIE_PATH and os.path.exists(COOKIE_PATH):
        auth = ["--cookies", COOKIE_PATH]
    else:
        auth = ["--cookies-from-browser", config.BROWSER]
    return [sys.executable, "-m", "yt_dlp", *ejs, *auth]


def fmt(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace('.', ',')


def safe_name(s):
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:120] or "video"


class Cancelled(Exception):
    pass


# ленивая загрузка модели (общая на процесс)
_model = None
_current_proc = None

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(config.MODEL, device=config.DEVICE,
                              compute_type=config.COMPUTE_TYPE)
    return _model


def process(url, progress_cb, status_cb, cancel_cb, lang=None):
    """Скачивает аудио и транскрибирует. Файлы → out/{title}/{title}.(wav|txt|srt)."""
    global _current_proc
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    YT = ytdlp_base()

    # 0. имя видео
    status_cb("получаю название видео...")
    title = subprocess.run(
        YT + ["--print", "title", "--skip-download", url],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env).stdout.strip()
    name = safe_name(title)
    outdir = os.path.join(OUT_BASE, name)
    os.makedirs(outdir, exist_ok=True)
    audio = os.path.join(outdir, name + ".wav")

    # 1. скачивание (0..50%)
    if os.path.exists(audio):
        status_cb("аудио уже скачано, пропускаю")
        progress_cb(0.5)
    else:
        status_cb("скачивание аудио...")
        proc = subprocess.Popen(
            YT + ["--newline", "-x", "--audio-format", "wav",
                  "-o", os.path.join(outdir, name + ".%(ext)s"), url],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", env=env)
        _current_proc = proc
        for line in proc.stdout:
            if cancel_cb():
                proc.terminate()
                raise Cancelled()
            m = re.search(r'(\d+\.\d+)%', line)
            if m:
                progress_cb(float(m.group(1)) / 100 * 0.5)
        proc.wait()
        _current_proc = None
        if proc.returncode != 0:
            raise RuntimeError("yt-dlp ошибка скачивания (код %s)" % proc.returncode)

    if cancel_cb():
        raise Cancelled()

    # 2. транскрипция (50..100%)
    status_cb("загрузка модели...")
    model = get_model()
    status_cb("транскрипция...")
    segments, info = model.transcribe(audio, language=lang or config.LANG,
                                      vad_filter=True, condition_on_previous_text=False)
    dur = getattr(info, "duration", 0) or 0

    txt_path = os.path.join(outdir, name + ".txt")
    srt_path = os.path.join(outdir, name + ".srt")
    with open(txt_path, "w", encoding="utf-8") as ft, \
         open(srt_path, "w", encoding="utf-8") as fs:
        for i, seg in enumerate(segments, 1):
            if cancel_cb():
                raise Cancelled()
            t = seg.text.strip()
            ft.write(t + "\n")
            fs.write(f"{i}\n{fmt(seg.start)} --> {fmt(seg.end)}\n{t}\n\n")
            if dur:
                progress_cb(0.5 + 0.5 * min(seg.end / dur, 1.0))
    progress_cb(1.0)
    status_cb("готово")
    return outdir


def cancel_proc():
    """Прибить текущий yt-dlp при остановке."""
    global _current_proc
    if _current_proc:
        try:
            _current_proc.terminate()
        except Exception:
            pass


# ======================= CLI =======================
def run_cli(url, lang):
    out = process(url,
                  progress_cb=lambda p: None,
                  status_cb=lambda s: print(s),
                  cancel_cb=lambda: False,
                  lang=lang)
    print("файлы:", out)


# ======================= GUI =======================
def run_gui():
    import tkinter as tk

    BG, CARD, EDGE = "#0f1115", "#191c22", "#272b34"
    TXT, SUB       = "#e7e9ee", "#7c828d"
    ACCENT, REC, OK = "#5b8cff", "#ff4d57", "#37d39a"

    running = {"on": False}
    cancel  = {"flag": False}

    root = tk.Tk()
    root.title("Video → Text")
    root.configure(bg=BG)
    root.resizable(False, False)
    root.attributes("-topmost", True)

    W, H = 500, 230
    sw = root.winfo_screenwidth(); sh = root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw - W)//2}+{(sh - H)//2}")

    tk.Label(root, text="VIDEO → TEXT", bg=BG, fg=TXT,
             font=("Segoe UI Semibold", 13)).pack(pady=(18, 2))
    tk.Label(root, text="вставь ссылку на YouTube-видео", bg=BG, fg=SUB,
             font=("Segoe UI", 9)).pack()

    entry = tk.Entry(root, bg=CARD, fg=TXT, insertbackground=TXT,
                     relief="flat", font=("Segoe UI", 10),
                     highlightthickness=1, highlightbackground=EDGE,
                     highlightcolor=ACCENT)
    entry.pack(fill="x", padx=20, ipady=7, pady=(12, 8))

    btn = tk.Button(root, text="СТАРТ", bg=ACCENT, fg="white",
                    font=("Segoe UI Semibold", 12), relief="flat", bd=0,
                    activebackground=ACCENT, cursor="hand2", height=2)
    btn.pack(fill="x", padx=20)

    PW, PH = W - 40, 10
    prog = tk.Canvas(root, width=PW, height=PH, bg=CARD, highlightthickness=0)
    prog.pack(padx=20, pady=(14, 6))
    fill = prog.create_rectangle(0, 0, 0, PH, fill=ACCENT, width=0)

    status = tk.Label(root, text="загрузка модели...", bg=BG, fg=SUB,
                      font=("Segoe UI", 9))
    status.pack()

    def ui(fn, *a):
        root.after(0, lambda: fn(*a))

    def set_progress(p):
        prog.coords(fill, 0, 0, int(PW * p), PH)
        prog.itemconfig(fill, fill=(REC if running["on"] else OK) if p >= 1 else ACCENT)

    def set_status(s, color=SUB):
        status.config(text=s, fg=color)

    def to_idle():
        running["on"] = False
        btn.config(text="СТАРТ", bg=ACCENT)
        entry.config(state="normal")

    def to_running():
        running["on"] = True
        cancel["flag"] = False
        btn.config(text="СТОП", bg=REC)
        entry.config(state="disabled")
        set_progress(0)

    def worker(url):
        try:
            out = process(url,
                          progress_cb=lambda p: ui(set_progress, p),
                          status_cb=lambda s: ui(set_status, s, SUB),
                          cancel_cb=lambda: cancel["flag"])
            ui(set_status, "✓ готово: out\\" + os.path.basename(out), OK)
        except Cancelled:
            ui(set_status, "остановлено", SUB)
            ui(set_progress, 0)
        except Exception as e:
            ui(set_status, "ошибка: " + str(e)[:80], REC)
        finally:
            ui(to_idle)

    def on_click():
        if running["on"]:
            cancel["flag"] = True
            cancel_proc()
            set_status("останавливаю...", SUB)
            return
        url = entry.get().strip()
        if not url:
            set_status("вставь ссылку", REC); return
        to_running()
        threading.Thread(target=worker, args=(url,), daemon=True).start()

    btn.config(command=on_click)

    # прогрев модели в фоне
    def warm():
        get_model()
        ui(set_status, "готов · вставь ссылку и жми СТАРТ", SUB)
    threading.Thread(target=warm, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        run_gui()
