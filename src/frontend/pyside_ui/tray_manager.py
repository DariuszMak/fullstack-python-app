from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget


class TrayManager:
    def __init__(self, window: QWidget) -> None:
        self._window = window
        self._tray_icon = QSystemTrayIcon(window)

        icon = QIcon(":/logos/icons/images/program_icon.ico")
        self._tray_icon.setIcon(icon)

        self._menu = QMenu()

        self._restore_action = QAction("Restore")
        self._restore_action.triggered.connect(self.restore)

        self._quit_action = QAction("Quit")
        self._quit_action.triggered.connect(self.quit)

        self._menu.addAction(self._restore_action)
        self._menu.addSeparator()
        self._menu.addAction(self._quit_action)

        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.activated.connect(self.icon_activated)

        self._tray_icon.show()

    def restore(self) -> None:
        self._window.show()
        self._window.setWindowState(Qt.WindowState.WindowNoState)
        self._window.activateWindow()

    def hide(self) -> None:
        self._window.hide()

    def quit(self) -> None:
        self._tray_icon.hide()
        QApplication.quit()

    def icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._window.isVisible():
                self.hide()
            else:
                self.restore()

    def notify_hidden(self) -> None:
        self._tray_icon.showMessage(
            "Application",
            "Application minimized to tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )
