from enum import Enum


class BugState(str, Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    WORKING = "WORKING"
    TESTING = "TESTING"
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

# Default Phrases
STATE_PHRASES = {
    BugState.IDLE: [
        "Жду ТЗ от босса",
        "Пью чай, не отвлекай",
    ],
    BugState.THINKING: [
        "Argon думает, тихо...",
        "Просчитываю архитектуру",
    ],
    BugState.WORKING: [
        "Flash пилит код!",
        "Фиксим баги на скорости света",
    ],
    BugState.TESTING: [
        "Запускаю .exe, держим кулачки",
        "Проверяю, не упало ли",
    ],
    BugState.LIMIT: [
        "Жук лимитает... Ждём 5 часов",
        "Квота всё, иди спать",
    ],
}
