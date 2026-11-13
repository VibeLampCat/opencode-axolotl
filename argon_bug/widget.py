import sys
import time
from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPaintEvent,
    QMouseEvent,
    QContextMenuEvent,
    QIcon,
    QPixmap,
    QAction,
    QActionGroup,
)
from PySide6.QtWidgets import (
    QWidget,
    QMenu,
    QSystemTrayIcon,
    QApplication,
)
from argon_bug.config import (
    BugState,
    UDP_HOST,
    UDP_PORT,
    COLOR_NEON_CYAN,
    COLOR_NEON_PURPLE,
    COLOR_BG_DARK,
    save_language_preference,
)
from argon_bug.renderer import ArgonBugRenderer
from argon_bug.udp_listener import ArgonUDPListener


def create_tray_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Mini neon bug
    painter.setBrush(QColor(COLOR_BG_DARK))
    painter.setPen(QColor(COLOR_NEON_PURPLE))
    painter.drawEllipse(QRectF(6, 6, 20, 20))

    painter.setBrush(QColor(COLOR_NEON_CYAN))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(11, 11, 4, 4))
    painter.drawEllipse(QRectF(17, 11, 4, 4))

    painter.end()
    return QIcon(pixmap)


class ArgonBugWidget(QWidget):
    def __init__(self, listener: ArgonUDPListener, initial_lang: str = None):
        super().__init__()
        self.listener = listener
        self.renderer = ArgonBugRenderer()
        if initial_lang:
            self.renderer.set_language(initial_lang)

        self.drag_position = QPoint()
        self.press_pos = QPoint()
        self.press_time = 0.0
        self.is_dragging = False
        self.auto_mode = True

        self._setup_window()
        self._setup_tray()
        self._setup_signals()

        # 30 FPS Animation Timer (~33 ms)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_frame)
        self.anim_timer.start(33)

    def _setup_window(self):
        self.setFixedSize(230, 185)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("ArgonBug - OpenCode v2.2.7")

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.width() - self.width() - 40, geom.height() - self.height() - 40)

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self)
        self.tray_icon.setToolTip("ArgonBug - OpenCode Mascot")

        tray_menu = self._create_context_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _setup_signals(self):
        self.listener.state_received.connect(self.on_state_received)
        self.listener.parent_exited.connect(self.on_parent_exited)

    def _create_context_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16161E;
                color: #E0E2EE;
                border: 1px solid #7B2CBF;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #24283B;
                color: #00B4D8;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3B3B4F;
                margin: 4px 10px;
            }
        """)

        # 1. Connection status info
        is_ru = (self.renderer.language == "ru")
        status_label = f"🟢 Связь с OpenCode (UDP:{UDP_PORT})" if is_ru else f"🟢 OpenCode Core Synced (UDP:{UDP_PORT})"
        status_action = QAction(status_label, self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        menu.addSeparator()

        # 2. Language Selector
        lang_menu_label = "🌐 Язык / Language"
        lang_menu = menu.addMenu(lang_menu_label)
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)

        ru_action = QAction("🇷🇺 Русский", self)
        ru_action.setCheckable(True)
        ru_action.setChecked(self.renderer.language == "ru")
        ru_action.triggered.connect(lambda: self._set_language("ru"))
        lang_group.addAction(ru_action)
        lang_menu.addAction(ru_action)

        en_action = QAction("🇬🇧 English", self)
        en_action.setCheckable(True)
        en_action.setChecked(self.renderer.language == "en")
        en_action.triggered.connect(lambda: self._set_language("en"))
        lang_group.addAction(en_action)
        lang_menu.addAction(en_action)

        menu.addSeparator()

        # 3. Auto management toggle
        auto_label = "🔄 Авто-управление от ядра OpenCode" if is_ru else "🔄 Auto Sync with OpenCode Core"
        self.auto_action = QAction(auto_label, self)
        self.auto_action.setCheckable(True)
        self.auto_action.setChecked(self.auto_mode)
        self.auto_action.triggered.connect(self._toggle_auto_mode)
        menu.addAction(self.auto_action)
        menu.addSeparator()

        # 4. Manual state modes (9 states)
        manual_menu_label = "🎯 Выбрать состояние вручную" if is_ru else "🎯 Preview Animation State"
        manual_menu = menu.addMenu(manual_menu_label)
        manual_group = QActionGroup(self)
        manual_group.setExclusive(True)

        states = [
            (BugState.IDLE, "☕ IDLE (Пьёт чай / Sipping tea)"),
            (BugState.THINKING, "🧠 THINKING (Думает Argon)"),
            (BugState.SEARCHING, "🔍 SEARCHING (Читает код / Docs)"),
            (BugState.WORKING, "⚡ WORKING (Flash пилит код)"),
            (BugState.TESTING, "🧪 TESTING (Запуск и тесты)"),
            (BugState.ASKING, "❓ ASKING (Ждёт ответа / Question)"),
            (BugState.SUCCESS, "🎉 SUCCESS (Миссия выполнена)"),
            (BugState.ERROR, "💧 ERROR (Конфуз / Ошибка)"),
            (BugState.LIMIT, "💤 LIMIT (Жук лимитает)"),
        ]

        for state, label in states:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.renderer.state == state)
            action.setData(state)
            action.triggered.connect(lambda checked, s=state: self._set_manual_state(s))
            manual_group.addAction(action)
            manual_menu.addAction(action)

        menu.addSeparator()

        # 5. Quit
        quit_label = "❌ Скрыть / Закрыть Аргончика" if is_ru else "❌ Hide / Close Mascot"
        quit_action = QAction(quit_label, self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        return menu

    def _set_language(self, lang: str):
        self.renderer.set_language(lang)
        save_language_preference(lang)
        self.tray_icon.setContextMenu(self._create_context_menu())
        self.update()

    def _toggle_auto_mode(self, checked: bool):
        self.auto_mode = checked
        self.listener.set_manual_override(not checked)

    def _set_manual_state(self, state: BugState):
        self.auto_mode = False
        self.auto_action.setChecked(False)
        self.listener.set_manual_override(True)
        self.listener.set_current_state(state.value)
        self.renderer.set_state(state)
        self.update()

    def on_state_received(self, state_name: str, detail: str):
        if not self.auto_mode:
            return
        try:
            state = BugState(state_name)
            self.renderer.set_state(state, detail)
            self.update()
        except ValueError:
            pass

    def on_parent_exited(self):
        print("[ArgonBug] Parent OpenCode process exited. Closing widget...")
        self.close()

    def _on_animation_frame(self):
        self.renderer.update_animation()
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        self.renderer.render(painter, self.width(), self.height())
        painter.end()

    # Drag & Drop vs Petting / Click
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_pos = event.globalPosition().toPoint()
            self.press_time = time.time()
            self.is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            # If released quickly without moving (< 5px displacement) -> It's a pet/click!
            duration = time.time() - self.press_time
            displacement = (event.globalPosition().toPoint() - self.press_pos).manhattanLength()
            if duration < 0.35 and displacement < 6:
                self.renderer.trigger_petting()
                self.update()
            event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = self._create_context_menu()
        menu.exec(event.globalPos())
        event.accept()

    def closeEvent(self, event):
        self.anim_timer.stop()
        self.tray_icon.hide()
        self.listener.stop()
        event.accept()
        QApplication.quit()
