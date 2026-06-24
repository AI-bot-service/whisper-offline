"""Общие настройки проекта whisper-offline.

Меняй значения здесь — оба инструмента (voice2text, video2text) берут их отсюда.
"""
import sys, os

# ===== ОБЩЕЕ =====
HF_HOME      = r"D:\huggingface_cache"                       # папка кэша моделей
MODEL        = "deepdml/faster-whisper-large-v3-turbo-ct2"   # модель Whisper
LANG         = "ru"          # язык: "ru", "en" или None = автоопределение
DEVICE       = "cuda"        # "cuda" = GPU, "cpu" = без видеокарты
COMPUTE_TYPE = "float16"     # float16 (GPU) / int8 (CPU)

# ===== voice2text (звук системы → текст) =====
HOTKEY      = "ctrl+space"   # горячая клавиша старт/стоп
SAMPLE_RATE = 16000

# ===== video2text (YouTube → текст) =====
BROWSER      = "firefox"      # откуда брать куки (firefox; chrome/edge не работают)
COOKIES_FILE = "cookies.txt"  # если файл есть рядом — юзается вместо браузера


def setup():
    """Готовит окружение: кэш моделей + GPU-библиотеки. Вызывать ДО импорта faster_whisper."""
    os.environ["HF_HOME"] = HF_HOME
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    # подключаем cudnn/cublas DLL из venv (нужно ctranslate2 для GPU)
    base = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..",
                                        "Lib", "site-packages", "nvidia"))
    for sub in ("cudnn", "cublas"):
        p = os.path.join(base, sub, "bin")
        if os.path.isdir(p):
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
