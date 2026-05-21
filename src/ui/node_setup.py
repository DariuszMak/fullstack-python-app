import platform
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path

import structlog

from src import STATIC_CATALOGUE_NAME

logger = structlog.get_logger(__name__)

REACT_DIR = Path(__file__).parent / "ui" / "react_ui"
FRONTEND_DIR: Path = REACT_DIR / "frontend"
STATIC_DIR: Path = REACT_DIR / STATIC_CATALOGUE_NAME
DIST_DIR: Path = FRONTEND_DIR / "dist"

NPM_CMD: str = "npm.cmd" if platform.system() == "Windows" else "npm"


def run_command(command: list[str], cwd: Path | None = None) -> str:
    log = logger.bind(command=" ".join(command), cwd=str(cwd))
    log.info("executing_command")

    if not cwd or not Path(cwd).exists():
        log.error("directory_not_found")
        raise NotADirectoryError(f"Directory does not exist: {cwd}")

    process = subprocess.run(command, cwd=cwd, capture_output=True, text=True)  # noqa: S603

    if process.returncode != 0:
        log.error(
            "command_failed",
            exit_code=process.returncode,
            stdout=process.stdout.strip(),
            stderr=process.stderr.strip(),
        )
        raise RuntimeError(f"Command {' '.join(command)} failed")

    return process.stdout


def install_dependencies() -> None:
    node_modules: Path = FRONTEND_DIR / "node_modules"

    if node_modules.exists():
        logger.info("skip_install", reason="node_modules_exists", path=str(node_modules))
        return

    run_command([NPM_CMD, "install"], cwd=FRONTEND_DIR)


def build_frontend() -> None:
    run_command([NPM_CMD, "run", "build"], cwd=FRONTEND_DIR)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_directory_contents(source: Path, destination_root: Path) -> None:
    for sub_item in source.rglob("*"):
        target_path: Path = destination_root / sub_item.relative_to(DIST_DIR)

        if sub_item.is_dir():
            ensure_directory(target_path)
        else:
            shutil.copy2(sub_item, target_path)


def copy_item(item: Path, destination: Path) -> None:
    if item.is_dir():
        if destination.exists():
            copy_directory_contents(item, STATIC_DIR)
        else:
            shutil.copytree(item, destination)
        return

    shutil.copy2(item, destination)


def copy_dist_to_static() -> None:
    log = logger.bind(source=str(DIST_DIR), target=str(STATIC_DIR))
    log.info("syncing_dist_to_static")

    if not DIST_DIR.exists():
        log.error("dist_missing", detail="Ensure 'npm run build' completed successfully")
        return

    for item in DIST_DIR.iterdir():
        copy_item(item, STATIC_DIR / item.name)

    log.info("sync_complete")


def build_react_frontend() -> None:
    log = logger.bind(pipeline="react_frontend_build")

    try:
        install_dependencies()
        build_frontend()
        copy_dist_to_static()
        log.info("build_pipeline_success")
    except Exception as e:
        log.exception("build_pipeline_failed", error_message=str(e))
        sys.exit(1)


if __name__ == "__main__":
    build_react_frontend()
