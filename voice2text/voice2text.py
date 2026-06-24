import sys, os, threading
from collections import deque
import numpy as np
import tkinter as tk

# === НАСТРОЙКИ ===
HOTKEY      = "ctrl+space"
LANG        = "ru"
MODEL       = "deepdml/faster-whisper-large-v3-turbo-ct2"
SAMPLE_RATE = 16000

# кэш моделей + GPU DLL
os.environ["HF_HOME"] = r"D:\huggingface_cache"
base = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..",
                                    "Lib", "site-packages", "nvidia"))
for sub in ("cudnn", "cublas"):
    p = os.path.join(base, sub, "bin")
    if os.path.isdir(p):
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

import soundcard as sc
import keyboard
import pyperclip
from faster_whisper import WhisperModel

# === ЦВЕТА ===
BG, CARD, EDGE = "#0f1115", "#191c22", "#272b34"
TXT, SUB       = "#e7e9ee", "#7c828d"
ACCENT, REC, OK = "#5b8cff", "#ff4d57", "#37d39a"
IDLE_BAR        = "#2c313b"

# === СОСТОЯНИЕ ===
recording = False
frames = []
level = 0.0
model = None
NBARS = 42
hist = deque([0.0] * NBARS, maxlen=NBARS)


# === АУДИО-ПОТОК (loopback звука системы) ===
def record_loop():
    global level
    spk = sc.default_speaker()
    lb = sc.get_microphone(spk.name, include_loopback=True)
    with lb.recorder(samplerate=SAMPLE_RATE) as rec:
        while True:
            chunk = rec.record(numframes=1024)
            mono = chunk.mean(axis=1) if chunk.ndim > 1 else chunk
            level = float(np.sqrt(np.mean(mono ** 2)))
            if recording:
                frames.append(chunk)


# === ЛОГИКА ===
def toggle():
    global recording, frames
    if model is None:
        set_status("модель грузится...", SUB); return
    if not recording:
        frames = []
        recording = True
        set_status("● запись звука системы...", REC)
    else:
        recording = False
        set_status("распознаю...", ACCENT)
        threading.Thread(target=transcribe, daemon=True).start()
    draw_button()


def transcribe():
    if not frames:
        root.after(0, lambda: set_status("пусто", SUB)); return
    audio = np.concatenate(frames, axis=0)
    audio = (audio.mean(axis=1) if audio.ndim > 1 else audio).astype(np.float32)
    segs, info = model.transcribe(audio, language=LANG,
                                  vad_filter=True, condition_on_previous_text=False)
    text = " ".join(s.text.strip() for s in segs).strip()
    if text:
        pyperclip.copy(text)
        root.after(0, lambda: (show_text(text),
                               set_status("✓ скопировано в буфер  ·  Ctrl+V", OK)))
    else:
        root.after(0, lambda: set_status("речь не распознана", SUB))


def load_model():
    global model
    model = WhisperModel(MODEL, device="cuda", compute_type="float16")
    root.after(0, lambda: set_status(f"готов  ·  {HOTKEY.upper()}", SUB))


# === GUI ===
root = tk.Tk()
root.title("Voice → Text")
root.configure(bg=BG)
root.resizable(False, False)
root.attributes("-topmost", True)

# окно снизу по центру, над панелью задач
W, H = 440, 150
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x = (sw - W) // 2
y = sh - H - 70
root.geometry(f"{W}x{H}+{x}+{y}")

top = tk.Frame(root, bg=BG)
top.pack(fill="x", padx=16, pady=(16, 8))

# --- квадратная кнопка записи (слева) ---
BSZ = 72
btn = tk.Canvas(top, width=BSZ, height=BSZ, bg=CARD, highlightthickness=1,
                highlightbackground=EDGE, cursor="hand2")
btn.pack(side="left")
btn.bind("<Button-1>", lambda e: toggle())


def draw_button():
    btn.delete("all")
    c = BSZ // 2
    if recording:
        btn.create_rectangle(c - 13, c - 13, c + 13, c + 13, fill=REC, width=0)  # стоп
    else:
        btn.create_oval(c - 16, c - 16, c + 16, c + 16, outline=EDGE, width=2)
        btn.create_oval(c - 9, c - 9, c + 9, c + 9, fill=REC, width=0)            # запись


# --- звуковая дорожка (справа) ---
WW, WH = 320, BSZ
wave = tk.Canvas(top, width=WW, height=WH, bg=CARD, highlightthickness=1,
                 highlightbackground=EDGE)
wave.pack(side="left", padx=(12, 0))

# --- инфо-строки (снизу) ---
status = tk.Label(root, text="загрузка модели...", bg=BG, fg=SUB,
                  font=("Segoe UI", 9), anchor="w")
status.pack(fill="x", padx=18)

txt = tk.Label(root, text="", bg=BG, fg=TXT, font=("Segoe UI", 9),
               wraplength=410, justify="left", anchor="w")
txt.pack(fill="x", padx=18, pady=(2, 0))


def set_status(s, color=SUB):
    status.config(text=s, fg=color)


def show_text(s):
    txt.config(text=(s[:120] + "…") if len(s) > 120 else s)


# --- анимация дорожки ---
def update_wave():
    hist.append(min(level * 8, 1.0))
    wave.delete("bar")
    bw = WW / NBARS
    for i, v in enumerate(hist):
        h = max(2, v * (WH - 16))
        x0 = i * bw + 1; x1 = (i + 1) * bw - 1
        y0 = (WH - h) / 2; y1 = (WH + h) / 2
        c = REC if recording else (IDLE_BAR if v < 0.02 else ACCENT)
        wave.create_rectangle(x0, y0, x1, y1, fill=c, width=0, tags="bar")
    root.after(40, update_wave)


# === СТАРТ ===
draw_button()
threading.Thread(target=record_loop, daemon=True).start()
threading.Thread(target=load_model, daemon=True).start()
keyboard.add_hotkey(HOTKEY, lambda: root.after(0, toggle))
update_wave()
root.mainloop()
