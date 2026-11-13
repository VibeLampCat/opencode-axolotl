from enum import Enum
import json
import locale
import os
from typing import Dict, List


class BugState(str, Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    SEARCHING = "SEARCHING"
    WORKING = "WORKING"
    TESTING = "TESTING"
    ASKING = "ASKING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    LIMIT = "LIMIT"


# UDP Socket Bridge Configuration
UDP_HOST = "127.0.0.1"
UDP_PORT = 51515

# Argon Color Palette
COLOR_BG_DARK = "#16161E"
COLOR_BG_CARD = "#24283B"
COLOR_NEON_PURPLE = "#9D4EDD"
COLOR_NEON_VIOLET = "#7B2CBF"
COLOR_NEON_CYAN = "#00B4D8"
COLOR_SPARK_YELLOW = "#FFD166"
COLOR_MUTED_GRAY = "#3B3B4F"
COLOR_TEXT = "#E0E2EE"
COLOR_GREEN = "#06D6A0"
COLOR_HEART_RED = "#FF3366"

# Config Path for Preferences
CONFIG_DIR = os.path.expanduser("~/.opencode")
CONFIG_FILE = os.path.join(CONFIG_DIR, "argon_config.json")


def detect_system_language() -> str:
    """Detects active language: ENV > config file > Windows locale > default 'en'."""
    env_lang = os.environ.get("OPENCODE_ARGON_LANG", "").lower().strip()
    if env_lang in ("ru", "en"):
        return env_lang

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "").lower()
                if lang in ("ru", "en"):
                    return lang
        except Exception:
            pass

    try:
        loc = None
        try:
            loc = locale.getlocale()[0]
        except Exception:
            pass
        if not loc:
            loc = locale.getdefaultlocale()[0]
        if loc and loc.lower().startswith("ru"):
            return "ru"
    except Exception:
        pass

    return "en"


def save_language_preference(lang: str) -> None:
    """Persists user language choice to ~/.opencode/argon_config.json."""
    if lang not in ("ru", "en"):
        return
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}
        config_data["language"] = lang
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception:
        pass


# Localized Phrases: Russian
PHRASES_RU: Dict[BugState, List[str]] = {
    BugState.IDLE: [
        "Жду ТЗ от босса",
        "Пью чай, не отвлекай",
        "Вайбкодим в тишине...",
    ],
    BugState.THINKING: [
        "Argon думает, тихо...",
        "Просчитываю архитектуру",
        "Нейроны кипят...",
    ],
    BugState.SEARCHING: [
        "Вынюхиваю баги в файлах...",
        "Листаю древние мануалы...",
        "Сканирую проект...",
    ],
    BugState.WORKING: [
        "Flash пилит код!",
        "Фиксим баги на скорости света",
        "Искры из лапок!",
    ],
    BugState.TESTING: [
        "Запускаю .exe, держим кулачки",
        "Проверяю, не упало ли",
        "Тесты идут полным ходом",
    ],
    BugState.ASKING: [
        "Босс, глянь в консоль, есть вопросик!",
        "Разрешите выполнить?",
        "Твоё слово — закон!",
    ],
    BugState.SUCCESS: [
        "Красота, всё работает!",
        "Миссия выполнена! ✨",
        "Релиз готов, взлетаем!",
    ],
    BugState.ERROR: [
        "Что-то пошло не так...",
        "Ой-ой, синтаксический конфуз",
        "Кажется, баг проскочил 💧",
    ],
    BugState.LIMIT: [
        "Жук лимитает... Ждём 5 часов",
        "Квота всё, иди спать",
        "Отдыхаем, пока квоты спят",
    ],
}

# Localized Phrases: English
PHRASES_EN: Dict[BugState, List[str]] = {
    BugState.IDLE: [
        "Sipping tea, awaiting specs",
        "No tasks? Tea time!",
        "Ready for the next prompt",
    ],
    BugState.THINKING: [
        "Argon is thinking, shh...",
        "Cooking up solutions",
        "Planning the architecture...",
    ],
    BugState.SEARCHING: [
        "Sniffing out bugs in codebase...",
        "Consulting sacred docs...",
        "Inspecting project files...",
    ],
    BugState.WORKING: [
        "Flash is cranking out code!",
        "Fast edits in progress!",
        "Sparks are flying!",
    ],
    BugState.TESTING: [
        "Safety goggles on. Running tests!",
        "Testing build, fingers crossed",
        "Verifying outputs...",
    ],
    BugState.ASKING: [
        "Awaiting your green light, boss!",
        "Need your permission in console!",
        "Shall we proceed?",
    ],
    BugState.SUCCESS: [
        "Mission accomplished! Everything works!",
        "Ship it! Pure gold ✨",
        "Tests passed! Great vibe!",
    ],
    BugState.ERROR: [
        "Wait, that's illegal...",
        "Something went wrong 💧",
        "Caught an error, debugging...",
    ],
    BugState.LIMIT: [
        "Quota reached. Catching z Z z...",
        "Rate limited! Nap time",
        "Cooling down API limits",
    ],
}

PET_PHRASES: Dict[str, List[str]] = {
    "ru": [
        "Муррр... Люблю вайбкодинг! ❤️",
        "Погладили аксолотля (+100 к удаче) ❤️",
        "Спасибо, босс! ❤️",
    ],
    "en": [
        "Purr... Vibe coding is life! ❤️",
        "Axolotl petted (+100 luck) ❤️",
        "Thanks, boss! ❤️",
    ],
}


def get_phrases_for_lang(lang: str) -> Dict[BugState, List[str]]:
    return PHRASES_RU if lang == "ru" else PHRASES_EN


# Backwards compatibility map
STATE_PHRASES = PHRASES_RU
