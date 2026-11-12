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
    STATE_PHRASES,
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
COLOR_GILL_DIM = QColor("#6E1430")      # Приглушённые жабры в режиме LIMIT
COLOR_GOGGLES_CYAN = QColor("#00F5D4")  # Голубые защитные очки в режиме TESTING
COLOR_GOGGLES_GLINT = QColor("#FFFFFF") # Белый блик на очках
COLOR_PIXEL_SPARK = QColor("#FFD166")   # Жёлтые квадратные искры в режиме WORKING
COLOR_PIXEL_MUG = QColor("#24283B")     # Корпус кружки в IDLE
COLOR_PIXEL_STEAM = QColor(250, 210, 225, 190) # Пиксельный парок над кружкой

# 16x11 Minecraft Axolotl Matrix
BASE_SPRITE = [
    "...D........D...",  # Row 0: Верхние кончики жабр
    "..DG.LLLLLL.GD..",  # Row 1: Верхние жабры и светлый лоб
    ".DGGLLLLLLLLGGD.",  # Row 2: Верхние/средние жабры и лоб
    "..GSPPPPPPPPSG..",  # Row 3: Основание верхних жабр и верх мордочки
    "DGGSPEPPPPPESGGD",  # Row 4: Боковые жабры, глаза E (col 5 и col 10)
    ".GGSPPPMMPPPSGG.",  # Row 5: Боковые жабры, ротик MM по центру (col 7, 8)
    "...SPPPPPPPPS...",  # Row 6: Щёчки и низ мордочки
    "....SSSSSSSS....",  # Row 7: Нижний контур головы (подбородок)
    "...DG......GD...",  # Row 8: Верхняя часть лапок-крестиков
    "..DGGD....DGGD..",  # Row 9: Средняя широкая часть лапок-крестиков
    "...DG......GD...",  # Row 10: Нижняя часть лапок-крестиков
]


class SparkParticle:
    def __init__(self, x: float, y: float, side: int):
        self.x = x
        self.y = y
        self.vx = side * random.uniform(2.0, 4.2)
        self.vy = random.uniform(-2.5, 1.5)
        self.life = 1.0
        self.decay = random.uniform(0.05, 0.09)
        self.size = random.choice([4.0, 6.0])  # Strict square pixel sizes

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


class ArgonBugRenderer:
    def __init__(self):
        self.state = BugState.IDLE
        self.detail_text = ""
        self.tick = 0
        self.phrase_index = 0
        self.last_phrase_switch = time.time()
        self.sparks: List[SparkParticle] = []
        self.sleep_zs: List[SleepZParticle] = []
        self.pixel_size = 7  # 7x7 screen pixels per logical pixel

    def set_state(self, state: BugState, detail: str = ""):
        if self.state != state:
            self.state = state
            self.phrase_index = random.randint(0, len(STATE_PHRASES[state]) - 1)
            self.last_phrase_switch = time.time()
        self.detail_text = detail

    def update_animation(self):
        self.tick += 1

        # Cycle phrases periodically
        now = time.time()
        if now - self.last_phrase_switch > 6.0:
            self.last_phrase_switch = now
            phrases = STATE_PHRASES.get(self.state, [""])
            if phrases:
                self.phrase_index = (self.phrase_index + 1) % len(phrases)

        # Sparks generator for WORKING state
        if self.state == BugState.WORKING:
            if len(self.sparks) < 25 and random.random() < 0.7:
                side = -1 if random.random() < 0.5 else 1
                emit_x = 115.0 + side * 52.0
                emit_y = 52.0 + random.uniform(-10.0, 10.0)
                self.sparks.append(SparkParticle(emit_x, emit_y, side))
        self.sparks = [s for s in self.sparks if s.update()]

        # Sleep particles for LIMIT state
        if self.state == BugState.LIMIT:
            if len(self.sleep_zs) < 4 and self.tick % 32 == 0:
                self.sleep_zs.append(SleepZParticle(120.0, 32.0))
        self.sleep_zs = [z for z in self.sleep_zs if z.update()]

    def render(self, painter: QPainter, width: int, height: int):
        # Strict Pixel-Art: disable antialiasing for pixel rendering
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        cx = width / 2.0
        base_x = int(cx - (16 * self.pixel_size) / 2)
        base_y = 26

        frame_step = self.tick // 10  # ~330 ms cadence

        # 1. Render 16x11 Minecraft Axolotl Sprite
        self._render_axolotl_sprite(painter, base_x, base_y, frame_step)

        # 2. Render State Props & Overlays
        if self.state == BugState.IDLE:
            self._render_pixel_tea_mug(painter, base_x, base_y, frame_step)
        elif self.state == BugState.THINKING:
            self._render_thinking_halo(painter, cx, base_y)
        elif self.state == BugState.TESTING:
            self._render_pixel_hud(painter, cx, base_y)

        # 3. Render Strict Square Particles
        self._render_particles(painter)

        # 4. Render Translucent Status Banner at bottom (strictly preserved)
        self._render_status_card(painter, width, height)

    def _render_axolotl_sprite(self, painter: QPainter, bx: int, by: int, frame_step: int):
        px = self.pixel_size
        painter.setPen(Qt.PenStyle.NoPen)

        # State animations parameters
        is_blinking = (self.tick % 90) < 6
        is_idle_breathe = (frame_step % 2 == 1) if self.state == BugState.IDLE else False
        active_group = (self.tick // 6) % 4 if self.state == BugState.THINKING else -1
        fast_step = (self.tick // 3) % 2 if self.state == BugState.WORKING else -1
        working_head_vibe = ((self.tick % 2) * 2) if self.state == BugState.WORKING else 0

        # Global offset for LIMIT (whole sprite drops down)
        global_offset_y = (2 * px) if self.state == BugState.LIMIT else 0

        for r in range(11):
            row_str = BASE_SPRITE[r]
            for c in range(16):
                ch = row_str[c]
                if ch == ".":
                    continue

                draw_r = r
                draw_c = c
                color = COLOR_AXO_P

                # -----------------------------------------------------------
                # A. HEAD vs PAWS Y-OFFSETS
                # -----------------------------------------------------------
                is_head = (r <= 7)
                is_paws = (r >= 8)

                if is_head:
                    head_offset_y = global_offset_y + working_head_vibe
                    if is_idle_breathe:
                        # Head breathes down by 1 pixel to paws
                        head_offset_y += px
                    elif self.state == BugState.LIMIT:
                        # Head additionally presses +1 pixel closer to paws
                        head_offset_y += px
                else:
                    head_offset_y = global_offset_y

                # -----------------------------------------------------------
                # B. WORKING FAST STEP WITH CROSS-PAWS (rows 8..10)
                # -----------------------------------------------------------
                if is_paws and self.state == BugState.WORKING:
                    if fast_step == 0 and (2 <= c <= 5):
                        draw_r = r - 1
                    elif fast_step == 1 and (10 <= c <= 13):
                        draw_r = r - 1

                # -----------------------------------------------------------
                # C. GILL KINEMATICS & COLORING
                # -----------------------------------------------------------
                if ch in ("D", "G"):
                    # 1. LIMIT: upper gills drop by 1 px, all gills dim
                    if self.state == BugState.LIMIT:
                        if r in (0, 1, 2):
                            draw_r = r + 1
                        color = COLOR_GILL_DIM
                    # 2. IDLE: upper gill tips sway up on inhale
                    elif self.state == BugState.IDLE and is_idle_breathe:
                        if (r == 0 and c in (3, 12)) or (r == 2 and c in (1, 14)):
                            draw_r = r - 1
                        color = COLOR_AXO_D if ch == "D" else COLOR_AXO_G
                    # 3. THINKING: circular highlight on 4 groups of D tips
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

                # -----------------------------------------------------------
                # D. TESTING GOGGLES (row 4, columns 4..11)
                # -----------------------------------------------------------
                if self.state == BugState.TESTING and r == 4 and (4 <= c <= 11):
                    if c in (7, 8):
                        # Goggles bridge
                        color = COLOR_AXO_E
                        painter.setBrush(QBrush(color))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                    else:
                        # Cyan lenses
                        color = COLOR_GOGGLES_CYAN
                        painter.setBrush(QBrush(color))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                        # White glint at top-left of each lens
                        if c in (4, 9):
                            painter.setBrush(QBrush(COLOR_GOGGLES_GLINT))
                            painter.drawRect(QRectF(bx + draw_c * px + 1, by + draw_r * px + head_offset_y + 1, 3, 3))
                    continue

                # -----------------------------------------------------------
                # E. EYES & BLINKING (row 4, columns 5 and 10)
                # -----------------------------------------------------------
                if ch == "E" and r == 4:
                    if self.state == BugState.LIMIT or is_blinking:
                        # Base skin color
                        painter.setBrush(QBrush(COLOR_AXO_P))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                        # Closed horizontal line slit 2px high
                        painter.setBrush(QBrush(COLOR_AXO_E))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y + 3, px, 2))
                    else:
                        # Solid dark square eye
                        painter.setBrush(QBrush(COLOR_AXO_E))
                        painter.drawRect(QRectF(bx + draw_c * px, by + draw_r * px + head_offset_y, px, px))
                    continue

                # -----------------------------------------------------------
                # F. SKIN, FOREHEAD, CHEEKS, SMILE
                # -----------------------------------------------------------
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

        # Mug body: 2x3 logical pixels in #24283B with #F497B6 rim
        painter.setBrush(QBrush(COLOR_PIXEL_MUG))
        painter.setPen(QPen(COLOR_AXO_P, 1.2))
        painter.drawRect(QRectF(mug_x, mug_y, 2 * px, 3 * px))

        # Handle: 1x2 logical pixels on right
        painter.drawRect(QRectF(mug_x + 2 * px, mug_y + 0.5 * px, 0.8 * px, 1.8 * px))

        # Rising steam: 2 square pixels 4x4 px
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(COLOR_PIXEL_STEAM))
        steam_step = (self.tick // 4) % 10
        for s in range(2):
            sy = mug_y - 4 - ((steam_step + s * 5) % 14) * 2
            x_wobble = 2 if ((frame_step + s) % 2 == 0) else -2
            sx = mug_x + 4 + s * 5 + x_wobble
            painter.drawRect(QRectF(sx, sy, 4.0, 4.0))

    def _render_thinking_halo(self, painter: QPainter, cx: float, by: int):
        # 3 strict square dots (5x5 px) rotating above head
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

    def _render_pixel_hud(self, painter: QPainter, cx: float, by: int):
        # Mini pixel HUD terminal placed near paws
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

        # Blinking cursor
        if (self.tick // 8) % 2 == 0:
            painter.setBrush(QBrush(QColor(COLOR_SPARK_YELLOW)))
            painter.drawRect(QRectF(hud_x + 34.0, hud_y + 11.0, 3.0, 3.0))

    def _render_particles(self, painter: QPainter):
        painter.setPen(Qt.PenStyle.NoPen)

        # 1. Square yellow sparks for WORKING
        for s in self.sparks:
            color = QColor(COLOR_PIXEL_SPARK)
            color.setAlpha(int(255 * s.life))
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(s.x, s.y, s.size, s.size))

        # 2. Pixel sleep z / Z for LIMIT
        if self.sleep_zs:
            for z in self.sleep_zs:
                alpha = int(220 * z.life)
                painter.setPen(QColor(224, 30, 90, alpha))
                painter.setFont(QFont("Consolas", 8 if z.scale == 1 else 11, QFont.Weight.Bold))
                painter.drawText(QPointF(z.x, z.y), "z" if z.scale == 1 else "Z")

    def _render_status_card(self, painter: QPainter, width: int, height: int):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        card_w = width - 16
        card_h = 36
        card_x = 8
        card_y = height - card_h - 8

        # Background rounded rect (strictly preserved)
        painter.setBrush(QBrush(QColor(22, 22, 30, 230)))
        border_c = QColor(COLOR_NEON_VIOLET if self.state != BugState.LIMIT else COLOR_MUTED_GRAY)
        painter.setPen(QPen(border_c, 1.4))
        painter.drawRoundedRect(QRectF(card_x, card_y, card_w, card_h), 8, 8)

        # Determine display text
        if self.detail_text:
            text = self.detail_text
        else:
            phrases = STATE_PHRASES.get(self.state, [""])
            text = phrases[self.phrase_index % len(phrases)]

        # Text rendering
        painter.setPen(QColor(COLOR_TEXT))
        font = QFont("Segoe UI", 8, QFont.Weight.Medium)
        painter.setFont(font)

        text_rect = QRectF(card_x + 8, card_y + 4, card_w - 16, card_h - 8)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            text,
        )
