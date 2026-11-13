import math
import random
import time
from typing import List
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
)
from argon_bug.config import (
    BugState,
    COLOR_BG_DARK,
    COLOR_BG_CARD,
    COLOR_NEON_PURPLE,
    COLOR_NEON_VIOLET,
    COLOR_NEON_CYAN,
    COLOR_SPARK_YELLOW,
    COLOR_MUTED_GRAY,
    COLOR_TEXT,
    COLOR_GREEN,
    COLOR_HEART_RED,
    detect_system_language,
    get_phrases_for_lang,
    PET_PHRASES,
)

# Minecraft Axolotl Pixel Palette
COLOR_AXO_L = QColor("#FAD2E1")  # L: Светло-розовый лоб и верх головы
COLOR_AXO_P = QColor("#F497B6")  # P: Основной нежно-розовый тон мордочки
COLOR_AXO_S = QColor("#D87093")  # S: Тёмный пыльно-розовый оттенок для объёма по бокам и снизу
COLOR_AXO_G = QColor("#E01E5A")  # G: Ярко-малиновый/вишнёвый цвет для жабр и лапок
COLOR_AXO_D = QColor("#A4133C")  # D: Тёмно-малиновая тень на жабрах и кончиках лапок
COLOR_AXO_E = QColor("#2B193D")  # E: Тёмно-фиолетовые, почти чёрные квадратные глаза
COLOR_AXO_M = QColor("#DF5780")  # M: Розовый горизонтальный ротик посередине между глаз

# Спецэффекты и аксессуары
COLOR_GILL_LIT = QColor("#FF7597")      # Светло-малиновая подсветка кончиков D в режиме THINKING
COLOR_GILL_DIM = QColor("#6E1430")      # Приглушённые жабры в режиме LIMIT / ERROR
COLOR_GOGGLES_CYAN = QColor("#00F5D4")  # Голубые защитные очки в режиме TESTING
COLOR_GOGGLES_GLINT = QColor("#FFFFFF") # Белый блик на очках
COLOR_PIXEL_SPARK = QColor("#FFD166")   # Жёлтые квадратные искры в режиме WORKING
COLOR_PIXEL_MUG = QColor("#24283B")     # Корпус кружки в IDLE
COLOR_PIXEL_STEAM = QColor(250, 210, 225, 190) # Пиксельный парок над кружкой
COLOR_SWEAT_DROP = QColor("#38BDF8")    # Капля пота в режиме ERROR
COLOR_WOOD_SIGN = QColor("#B45309")     # Ручка лупы
COLOR_MAG_RIM = QColor("#F59E0B")       # Оправа лупы в SEARCHING
COLOR_MAG_GLASS = QColor(56, 189, 248, 170) # Стекло лупы

# 16x11 Minecraft Axolotl Matrix (Строго симметричная относительно центра cols 7-8)
BASE_SPRITE = [
    "...D........D...",  # Row 0: Кончики верхних жабр (col 3 и col 12)
    "..DG.LLLLLL.GD..",  # Row 1: Верхние жабры и светлый лоб (cols 5..10)
    ".DGGLLLLLLLLGGD.",  # Row 2: Верхние/средние жабры и лоб (cols 4..11)
    "..GSPPPPPPPPSG..",  # Row 3: Основание верхних жабр и верх мордочки (cols 4..11)
    "DGGSPEPPPPEPSGGD",  # Row 4: Боковые жабры, СИММЕТРИЧНЫЕ глаза E (col 5 и col 10!)
    ".GGSPPPMMPPPSGG.",  # Row 5: Боковые жабры, ротик MM по центру (col 7, 8)
    "...SPPPPPPPPS...",  # Row 6: Щёчки и низ мордочки (cols 4..11)
    "....SSSSSSSS....",  # Row 7: Нижний контур подбородка (cols 4..11)
    "...DG......GD...",  # Row 8: Симметричные лапки (cols 3,4 и 11,12)
    "..DGGD....DGGD..",  # Row 9: Средняя широкая часть лапок (cols 2..5 и 10..13)
    "...DG......GD...",  # Row 10: Нижняя часть лапок (cols 3,4 и 11,12)
]


class SparkParticle:
    def __init__(self, x: float, y: float, side: int):
        self.x = x
        self.y = y
        self.vx = side * random.uniform(2.0, 4.2)
        self.vy = random.uniform(-2.5, 1.5)
        self.life = 1.0
        self.decay = random.uniform(0.05, 0.09)
        self.size = random.choice([4.0, 6.0])

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0


class SleepZParticle:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.startY = y
        self.life = 1.0
        self.decay = 0.025
        self.phase = random.uniform(0, 6.28)
        self.scale = random.choice([1, 2])

    def update(self) -> bool:
        self.y -= 0.8
        self.x += math.sin(self.phase + (self.startY - self.y) * 0.1) * 0.5
        self.life -= self.decay
        return self.life > 0


class CelebrationParticle:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-4.0, -1.5)
        self.gravity = 0.12
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.04)
        self.size = random.choice([3.0, 5.0])
        self.color = random.choice([
            QColor(COLOR_SPARK_YELLOW),
            QColor(COLOR_NEON_CYAN),
            QColor(COLOR_GREEN),
            QColor(COLOR_AXO_G),
            QColor("#F43F5E"),
        ])

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay
        return self.life > 0


class HeartParticle:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.life = 1.0
        self.decay = 0.028

    def update(self) -> bool:
        self.y -= 1.2
        self.life -= self.decay
        return self.life > 0


class ArgonBugRenderer:
    def __init__(self):
        self.state = BugState.IDLE
        self.language = detect_system_language()
        self.detail_text = ""
        self.tick = 0
        self.phrase_index = 0
        self.last_phrase_switch = time.time()
        self.sparks: List[SparkParticle] = []
        self.sleep_zs: List[SleepZParticle] = []
        self.confetti: List[CelebrationParticle] = []
        self.hearts: List[HeartParticle] = []
        self.pet_until = 0.0
        self.pixel_size = 7

    def set_language(self, lang: str):
        if lang in ("ru", "en"):
            self.language = lang
            self.phrase_index = 0

    def get_current_phrases(self) -> List[str]:
        phrases_map = get_phrases_for_lang(self.language)
        return phrases_map.get(self.state, [""])

    def trigger_petting(self):
        self.pet_until = time.time() + 2.5
        phrases = PET_PHRASES.get(self.language, PET_PHRASES["en"])
        self.detail_text = random.choice(phrases)
        self.hearts.append(HeartParticle(115.0, 24.0))

    def set_state(self, state: BugState, detail: str = ""):
        if self.state != state:
            self.state = state
            phrases = self.get_current_phrases()
            self.phrase_index = random.randint(0, max(0, len(phrases) - 1))
            self.last_phrase_switch = time.time()
        self.detail_text = detail

    def update_animation(self):
        self.tick += 1

        if self.pet_until > 0 and time.time() > self.pet_until:
            self.pet_until = 0.0
            if self.detail_text in PET_PHRASES.get("ru", []) + PET_PHRASES.get("en", []):
                self.detail_text = ""

        now = time.time()
        if now - self.last_phrase_switch > 6.0:
            self.last_phrase_switch = now
            phrases = self.get_current_phrases()
            if phrases:
                self.phrase_index = (self.phrase_index + 1) % len(phrases)

        if self.state == BugState.WORKING:
            if len(self.sparks) < 25 and random.random() < 0.7:
                side = -1 if random.random() < 0.5 else 1
                emit_x = 115.0 + side * 52.0
                emit_y = 52.0 + random.uniform(-10.0, 10.0)
                self.sparks.append(SparkParticle(emit_x, emit_y, side))
        self.sparks = [s for s in self.sparks if s.update()]

        if self.state == BugState.LIMIT:
            if len(self.sleep_zs) < 4 and self.tick % 32 == 0:
                self.sleep_zs.append(SleepZParticle(120.0, 32.0))
        self.sleep_zs = [z for z in self.sleep_zs if z.update()]

        if self.state == BugState.SUCCESS:
            if len(self.confetti) < 30 and random.random() < 0.8:
                emit_x = 115.0 + random.uniform(-40.0, 40.0)
                emit_y = 48.0
                self.confetti.append(CelebrationParticle(emit_x, emit_y))
        self.confetti = [c for c in self.confetti if c.update()]

        self.hearts = [h for h in self.hearts if h.update()]

    def render(self, painter: QPainter, width: int, height: int):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        cx = width / 2.0
        base_x = int(cx - (16 * self.pixel_size) / 2)
        base_y = 26

        frame_step = self.tick // 10

        jump_y = int(-abs(math.sin(self.tick * 0.25)) * 8) if self.state == BugState.SUCCESS else 0

        self._render_axolotl_sprite(painter, base_x, base_y + jump_y, frame_step)

        if self.state == BugState.IDLE:
            self._render_pixel_tea_mug(painter, base_x, base_y + jump_y, frame_step)
        elif self.state == BugState.THINKING:
            self._render_thinking_halo(painter, cx, base_y + jump_y)
        elif self.state == BugState.SEARCHING:
            self._render_magnifying_glass(painter, base_x, base_y + jump_y)
        elif self.state == BugState.TESTING:
            self._render_pixel_hud(painter, cx, base_y + jump_y)
        elif self.state == BugState.ASKING:
            self._render_question_bubble(painter, cx, base_y + jump_y)
        elif self.state == BugState.ERROR:
            self._render_sweat_drop(painter, base_x, base_y + jump_y)

        self._render_particles(painter)
        self._render_status_card(painter, width, height)

    def _render_axolotl_sprite(self, painter: QPainter, bx: int, by: int, frame_step: int):
        px = self.pixel_size
        painter.setPen(Qt.PenStyle.NoPen)

        is_petted = (self.pet_until > time.time())
        is_blinking = ((self.tick % 90) < 6) or is_petted
        is_idle_breathe = (frame_step % 2 == 1) if self.state in (BugState.IDLE, BugState.ASKING) else False
        active_group = (self.tick // 6) % 4 if self.state == BugState.THINKING else -1
        fast_step = (self.tick // 3) % 2 if self.state == BugState.WORKING else -1
        working_head_vibe = ((self.tick % 2) * 2) if self.state == BugState.WORKING else 0

        global_offset_y = (2 * px) if self.state in (BugState.LIMIT, BugState.ERROR) else 0

        for r in range(11):
            row_str = BASE_SPRITE[r]
            for c in range(16):
                ch = row_str[c]
                if ch == ".":
                    continue

                draw_r = r
                draw_c = c
                color = COLOR_AXO_P

                is_head = (r <= 7)
                is_paws = (r >= 8)

                if is_head:
                    head_offset_y = global_offset_y + working_head_vibe
                    if is_idle_breathe:
                        head_offset_y += px
                    elif self.state in (BugState.LIMIT, BugState.ERROR):
                        head_offset_y += px
                else:
                    head_offset_y = global_offset_y

                if is_paws and self.state == BugState.WORKING:
                    if fast_step == 0 and (2 <= c <= 5):
                        draw_r = r - 1
                    elif fast_step == 1 and (10 <= c <= 13):
                        draw_r = r - 1

                if ch in ("D", "G"):
                    if self.state in (BugState.LIMIT, BugState.ERROR):
                        color = COLOR_GILL_DIM
                    elif self.state == BugState.THINKING and ch == "D" and r <= 5:
                        is_lit = False
                        if active_group == 0 and ((r == 4 and c == 0) or (r == 2 and c == 1)):
                            is_lit = True
                        elif active_group == 1 and ((r == 0 and c == 3) or (r == 1 and c == 2)):
                            is_lit = True
                        elif active_group == 2 and ((r == 0 and c == 12) or (r == 1 and c == 13)):
                            is_lit = True
                        elif active_group == 3 and ((r == 2 and c == 14) or (r == 4 and c == 15)):
                            is_lit = True
                        color = COLOR_GILL_LIT if is_lit else COLOR_AXO_D
                    else:
                        color = COLOR_AXO_D if ch == "D" else COLOR_AXO_G

                    painter.setBrush(QBrush(color))
                    painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                    continue

                if self.state == BugState.TESTING and r == 4 and (4 <= c <= 11):
                    if c in (7, 8):
                        color = COLOR_AXO_E
                        painter.setBrush(QBrush(color))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                    else:
                        color = COLOR_GOGGLES_CYAN
                        painter.setBrush(QBrush(color))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                        if c in (4, 9):
                            painter.setBrush(QBrush(COLOR_GOGGLES_GLINT))
                            painter.drawRect(QRectF(bx + draw_c * px + 1, by + draw_r * px + head_offset_y + 1, 3, 3))
                    continue

                if ch == "E" and r == 4:
                    if self.state in (BugState.LIMIT, BugState.ERROR) or is_blinking:
                        painter.setBrush(QBrush(COLOR_AXO_P))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                        painter.setBrush(QBrush(COLOR_AXO_E))
                        if is_petted:
                            painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y + 2, px, 2))
                        else:
                            painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y + 3, px, 2))
                    else:
                        painter.setBrush(QBrush(COLOR_AXO_E))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                    continue

                if ch == "L":
                    color = COLOR_AXO_L
                elif ch == "P":
                    color = COLOR_AXO_P
                elif ch == "S":
                    color = COLOR_AXO_S
                elif ch == "M":
                    color = COLOR_AXO_M
                else:
                    color = COLOR_AXO_P

                painter.setBrush(QBrush(color))
                painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))

    def _render_pixel_tea_mug(self, painter: QPainter, bx: int, by: int, frame_step: int):
        px = self.pixel_size
        mug_x = bx + 14 * px
        mug_y = by + 7 * px

        painter.setBrush(QBrush(COLOR_PIXEL_MUG))
        painter.setPen(QPen(COLOR_AXO_P, 1.2))
        painter.drawRect(QRectF(mug_x, mug_y, 2 * px, 3 * px))
        painter.drawRect(QRectF(mug_x + 2 * px, mug_y + 0.5 * px, 0.8 * px, 1.8 * px))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(COLOR_PIXEL_STEAM))
        steam_step = (self.tick // 4) % 10
        for s in range(2):
            sy = mug_y - 4 - ((steam_step + s * 5) % 14) * 2
            x_wobble = 2 if ((frame_step + s) % 2 == 0) else -2
            sx = mug_x + 4 + s * 5 + x_wobble
            painter.drawRect(QRectF(sx, sy, 4.0, 4.0))

    def _render_thinking_halo(self, painter: QPainter, cx: float, by: int):
        px = 5.0
        phase = self.tick * 0.12
        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(3):
            ang = phase + i * (2.0 * math.pi / 3.0)
            dot_x = cx + math.cos(ang) * 22.0 - px / 2.0
            dot_y = by - 12.0 + math.sin(ang) * 5.0 - px / 2.0
            color = COLOR_AXO_G if (i % 2 == 0) else COLOR_AXO_L
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(dot_x, dot_y, px, px))

    def _render_magnifying_glass(self, painter: QPainter, bx: int, by: int):
        px = self.pixel_size
        bob_y = int(math.sin(self.tick * 0.2) * 2)
        glass_x = bx + 14 * px + 2
        glass_y = by + 5 * px + bob_y

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(COLOR_MAG_RIM))
        painter.drawRect(QRectF(glass_x, glass_y, 2.8 * px, 2.8 * px))
        painter.setBrush(QBrush(COLOR_MAG_GLASS))
        painter.drawRect(QRectF(glass_x + 3, glass_y + 3, 2.8 * px - 6, 2.8 * px - 6))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(QRectF(glass_x + 4, glass_y + 4, 3, 3))
        painter.setBrush(QBrush(COLOR_WOOD_SIGN))
        painter.drawRect(QRectF(glass_x + 2.2 * px, glass_y + 2.4 * px, 1.0 * px, 2.2 * px))

    def _render_question_bubble(self, painter: QPainter, cx: float, by: int):
        b_w = 28.0
        b_h = 18.0
        bob_y = math.sin(self.tick * 0.15) * 3.0
        b_x = cx - b_w / 2.0
        b_y = by - 16.0 + bob_y

        painter.setBrush(QBrush(QColor(COLOR_BG_CARD)))
        painter.setPen(QPen(QColor(COLOR_SPARK_YELLOW), 1.2))
        painter.drawRoundedRect(QRectF(b_x, b_y, b_w, b_h), 4, 4)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.setPen(QColor(COLOR_SPARK_YELLOW))
        painter.drawText(QRectF(b_x, b_y - 1, b_w, b_h), Qt.AlignmentFlag.AlignCenter, "?")

    def _render_sweat_drop(self, painter: QPainter, bx: int, by: int):
        px = self.pixel_size
        drop_x = bx + 12 * px
        drop_y = by + 2 * px + ((self.tick // 3) % 4) * 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(COLOR_SWEAT_DROP))
        painter.drawRect(QRectF(drop_x, drop_y, 4, 6))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(QRectF(drop_x + 1, drop_y + 1, 2, 2))

    def _render_pixel_hud(self, painter: QPainter, cx: float, by: int):
        hud_w = 44.0
        hud_h = 18.0
        hud_x = cx - hud_w / 2.0
        hud_y = by + 68.0

        painter.setBrush(QBrush(QColor(16, 22, 34, 235)))
        painter.setPen(QPen(QColor(COLOR_GREEN), 1.0))
        painter.drawRect(QRectF(hud_x, hud_y, hud_w, hud_h))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(COLOR_GREEN)))
        for i in range(2):
            line_y = hud_y + 3.0 + i * 5.0
            line_w = 6.0 + ((self.tick * 2 + i * 11) % 24)
            painter.drawRect(QRectF(hud_x + 3.0, line_y, line_w, 2.0))

        if (self.tick // 8) % 2 == 0:
            painter.setBrush(QBrush(QColor(COLOR_SPARK_YELLOW)))
            painter.drawRect(QRectF(hud_x + 34.0, hud_y + 11.0, 3.0, 3.0))

    def _render_particles(self, painter: QPainter):
        painter.setPen(Qt.PenStyle.NoPen)

        for s in self.sparks:
            color = QColor(COLOR_PIXEL_SPARK)
            color.setAlpha(int(255 * s.life))
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(s.x, s.y, s.size, s.size))

        if self.sleep_zs:
            for z in self.sleep_zs:
                alpha = int(220 * z.life)
                painter.setPen(QColor(224, 30, 90, alpha))
                painter.setFont(QFont("Consolas", 8 if z.scale == 1 else 11, QFont.Weight.Bold))
                painter.drawText(QPointF(z.x, z.y), "z" if z.scale == 1 else "Z")

        for c in self.confetti:
            col = QColor(c.color)
            col.setAlpha(int(255 * c.life))
            painter.setBrush(QBrush(col))
            painter.drawRect(QRectF(c.x, c.y, c.size, c.size))

        for h in self.hearts:
            self._render_single_heart(painter, h.x, h.y, h.life)

    def _render_single_heart(self, painter: QPainter, hx: float, hy: float, life: float):
        px = 2.5
        col = QColor(COLOR_HEART_RED)
        col.setAlpha(int(255 * life))
        painter.setBrush(QBrush(col))
        painter.setPen(Qt.PenStyle.NoPen)

        pattern = [
            ".XX.XX.",
            "XXXXXXX",
            ".XXXXX.",
            "..XXX..",
            "...X...",
        ]
        start_x = hx - 3.5 * px
        start_y = hy
        for r, row in enumerate(pattern):
            for c, char in enumerate(row):
                if char == "X":
                    painter.drawRect(QRectF(start_x + c * px, start_y + r * px, px, px))

    def _render_status_card(self, painter: QPainter, width: int, height: int):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        card_w = width - 16
        card_h = 36
        card_x = 8
        card_y = height - card_h - 8

        painter.setBrush(QBrush(QColor(22, 22, 30, 230)))

        border_c = QColor(COLOR_NEON_VIOLET)
        if self.state in (BugState.LIMIT, BugState.ERROR):
            border_c = QColor(COLOR_MUTED_GRAY)
        elif self.state == BugState.SUCCESS:
            border_c = QColor(COLOR_GREEN)
        elif self.state == BugState.ASKING:
            border_c = QColor(COLOR_SPARK_YELLOW)

        painter.setPen(QPen(border_c, 1.4))
        painter.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 8, 8)

        if self.detail_text:
            text = self.detail_text
        else:
            phrases = self.get_current_phrases()
            text = phrases[self.phrase_index % len(phrases)]

        painter.setPen(QColor(COLOR_TEXT))
        font = QFont("Segoe UI", 8, QFont.Weight.Medium)
        painter.setFont(font)

        text_rect = QRectF(card_x + 8, card_y + 4, card_w - 16, card_h - 8)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            text,
        )
