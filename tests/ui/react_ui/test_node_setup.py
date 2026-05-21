import platform
from importlib import reload
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ui.node_setup import (
    NPM_CMD,
    build_frontend,
    build_react_frontend,
    copy_dist_to_static,
    install_dependencies,
    run_command,
)


def test_run_command_success(tmp_path: Path) -> None:
    with patch("src.ui.react_ui.node_setup.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success",
            stderr="",
        )

        output = run_command(["echo", "test"], cwd=tmp_path)

        assert output == "success"
        mock_run.assert_called_once()


def test_run_command_invalid_cwd() -> None:
    with pytest.raises(NotADirectoryError):
        run_command(["echo", "test"], cwd=Path("/does/not/exist"))


def test_run_command_failure(tmp_path: Path) -> None:
    with patch("src.ui.react_ui.node_setup.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="out",
            stderr="err",
        )

        with pytest.raises(RuntimeError, match=r"Command .* failed"):
            run_command(["bad", "cmd"], cwd=tmp_path)


def test_install_dependencies_skips_when_node_modules_exists(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    node_modules = frontend / "node_modules"
    node_modules.mkdir(parents=True)

    with patch("src.ui.react_ui.node_setup.FRONTEND_DIR", frontend), patch("src.ui.react_ui.node_setup.run_command") as mock_run:
        install_dependencies()
        mock_run.assert_not_called()


def test_install_dependencies_runs_npm_install(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()

    with patch("src.ui.react_ui.node_setup.FRONTEND_DIR", frontend), patch("src.ui.react_ui.node_setup.run_command") as mock_run:
        install_dependencies()
        mock_run.assert_called_once_with([NPM_CMD, "install"], cwd=frontend)


def test_build_frontend_runs_npm_build(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()

    with patch("src.ui.react_ui.node_setup.FRONTEND_DIR", frontend), patch("src.ui.react_ui.node_setup.run_command") as mock_run:
        build_frontend()
        mock_run.assert_called_once_with([NPM_CMD, "run", "build"], cwd=frontend)


def test_copy_dist_to_static_copies_files_and_dirs(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    static = tmp_path / "static"

    dist.mkdir()
    static.mkdir()

    file = dist / "index.html"
    file.write_text("html")

    assets = dist / "assets"
    assets.mkdir()
    nested = assets / "app.js"
    nested.write_text("js")

    with patch("src.ui.react_ui.node_setup.DIST_DIR", dist), patch("src.ui.react_ui.node_setup.STATIC_DIR", static):
        copy_dist_to_static()

    assert (static / "index.html").read_text() == "html"
    assert (static / "assets" / "app.js").read_text() == "js"


def test_copy_dist_to_static_merges_existing_directory(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    static = tmp_path / "static"

    dist.mkdir()
    static.mkdir()

    src_dir = dist / "assets"
    src_dir.mkdir()
    (src_dir / "new.js").write_text("new")

    dest_dir = static / "assets"
    dest_dir.mkdir()
    (dest_dir / "old.js").write_text("old")

    with patch("src.ui.react_ui.node_setup.DIST_DIR", dist), patch("src.ui.react_ui.node_setup.STATIC_DIR", static):
        copy_dist_to_static()

    assert (static / "assets" / "old.js").exists()
    assert (static / "assets" / "new.js").exists()


def test_build_react_frontend_calls_all_steps() -> None:
    with (
        patch("src.ui.react_ui.node_setup.install_dependencies") as mock_install,
        patch("src.ui.react_ui.node_setup.build_frontend") as mock_build,
        patch("src.ui.react_ui.node_setup.copy_dist_to_static") as mock_copy,
    ):
        build_react_frontend()

        mock_install.assert_called_once()
        mock_build.assert_called_once()
        mock_copy.assert_called_once()


def test_npm_cmd_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    import src.ui.node_setup as module

    reload(module)

    assert module.NPM_CMD == "npm.cmd"
