import os
import subprocess  # noqa: S404
from enum import StrEnum

import structlog

logger = structlog.get_logger(__name__)


class UiExtensions(StrEnum):
    UI = ".ui"
    QRC = ".qrc"


def create_moc(dir_path: str, file_name: str, extension: UiExtensions) -> None:
    input_file = os.path.join(dir_path, file_name)
    output_file = None

    if extension == UiExtensions.UI:
        output_file = os.path.join(dir_path, f"moc_{os.path.splitext(file_name)[0]}.py")
    elif extension == UiExtensions.QRC:
        output_file = os.path.join(dir_path, f"{os.path.splitext(file_name)[0]}_rc.py")

    log = logger.bind(input_file=input_file, output_file=output_file, extension=extension)

    if os.path.isfile(output_file):
        ui_file_modification_time = os.path.getmtime(input_file)
        moc_file_modification_time = os.path.getmtime(output_file)
        if moc_file_modification_time > ui_file_modification_time:
            log.info("skipping_moc_generation", reason="output_newer_than_input")
            return

    try:
        if os.path.exists(output_file):
            log.info("removing_old_moc_file")
            os.remove(output_file)
    except OSError as e:
        log.warning("failed_to_remove_old_file", error=str(e))

    if extension == UiExtensions.UI:
        command = ["pyside6-uic", "--from-imports", input_file, "-o", output_file]
    elif extension == UiExtensions.QRC:
        command = ["pyside6-rcc", input_file, "-o", output_file]

    log.info("generating_moc_file", command=command)
    process = subprocess.run(  # noqa: S603
        command, capture_output=True, text=True
    )

    if process.returncode != 0:
        log.error("moc_generation_failed", stdout=process.stdout, stderr=process.stderr, return_code=process.returncode)
        raise Exception(f"Mocking UI file failed! ({file_name})")


def create_mocs() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info("starting_moc_discovery", root_dir=root_dir)

    for root, _dirs, files in os.walk(root_dir):
        for file in files:
            for extension in UiExtensions:
                if file.endswith(extension):
                    create_moc(root, file, extension)

    logger.info("moc_processing_finished")


if __name__ == "__main__":
    create_mocs()
