import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtWidgets import QApplication

from src.ui.pyside_ui.pyside_setup import UiExtensions, create_moc
from src.ui.pyside_ui.dialog_windows.main_window import MainWindow
from src.ui.pyside_ui.settings import MAINWINDOW_HEIGHT, MAINWINDOW_RESIZE_RANGE, MAINWINDOW_WIDTH


@pytest.fixture
def temp_dir(tmpdir: str) -> str:
    return str(tmpdir)


@pytest.fixture
def example_moc_content_ui() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>400</width>
    <height>300</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Form</string>
  </property>
 </widget>
 <resources/>
 <connections/>
</ui>
"""


@pytest.fixture
def example_moc_content_qrc() -> str:
    return """<RCC>
</RCC>
"""


@pytest.fixture(scope="session")
def app() -> QCoreApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(app: QApplication) -> Generator[MainWindow]:
    window = MainWindow()
    window.show()
    yield window
    window.close()


def test_create_moc_ui(temp_dir: str, example_moc_content_ui: str) -> None:
    input_file = os.path.join(temp_dir, "example.ui")
    with open(input_file, "w") as f:
        f.write(example_moc_content_ui)

    create_moc(temp_dir, "example.ui", UiExtensions.UI)

    moc_file = os.path.join(temp_dir, "moc_example.py")
    assert os.path.isfile(moc_file)


def test_create_moc_qrc(temp_dir: str, example_moc_content_qrc: str) -> None:
    input_file = os.path.join(temp_dir, "example.qrc")
    with open(input_file, "w") as f:
        f.write(example_moc_content_qrc)

    create_moc(temp_dir, "example.qrc", UiExtensions.QRC)

    moc_file = os.path.join(temp_dir, "example_rc.py")
    assert os.path.isfile(moc_file)


def test_create_moc_check_if_correctly_modified_existing_code(temp_dir: str, example_moc_content_ui: str) -> None:
    input_file = os.path.join(temp_dir, "example.ui")
    with open(input_file, "w") as f:
        f.write("Example UI content")

    moc_file = os.path.join(temp_dir, "moc_example.py")
    with open(moc_file, "w") as f:
        f.write(example_moc_content_ui)

    with patch("os.path.getmtime") as mock_getmtime:
        mock_getmtime.side_effect = [1, 2]
        create_moc(temp_dir, "example.ui", UiExtensions.UI)

    assert os.path.isfile(moc_file)
    assert mock_getmtime.call_count == 2


def test_create_moc_error_when_create_qrc_contnent_for_ui(temp_dir: str, example_moc_content_qrc: str) -> None:
    input_file = os.path.join(temp_dir, "example.ui")
    with open(input_file, "w") as f:
        f.write(example_moc_content_qrc)

    with pytest.raises(Exception, match=r"Mocking UI file failed!.*example\.ui"):
        create_moc(temp_dir, "example.ui", UiExtensions.UI)


def test_create_moc_error_when_create_ui_content_for_qrc(temp_dir: str, example_moc_content_ui: str) -> None:
    input_file = os.path.join(temp_dir, "example.ui")
    with open(input_file, "w") as f:
        f.write(example_moc_content_ui)

    with pytest.raises(Exception, match=r"Mocking UI file failed!.*example\.ui"):
        create_moc(temp_dir, "example.ui", UiExtensions.QRC)


def test_startup_size(main_window: MainWindow) -> None:
    assert main_window.width() == MAINWINDOW_WIDTH
    assert main_window.height() == MAINWINDOW_HEIGHT


def test_resize_event_enforces_minimum(main_window: MainWindow) -> None:
    min_width = MAINWINDOW_WIDTH - MAINWINDOW_RESIZE_RANGE
    min_height = MAINWINDOW_HEIGHT - MAINWINDOW_RESIZE_RANGE

    main_window.resize(100, 100)
    QApplication.processEvents()

    assert main_window.width() >= min_width
    assert main_window.height() >= min_height

    larger_size = QSize(MAINWINDOW_WIDTH + 200, MAINWINDOW_HEIGHT + 200)
    main_window.resize(larger_size)
    QApplication.processEvents()

    assert main_window.width() == larger_size.width()
    assert main_window.height() == larger_size.height()
