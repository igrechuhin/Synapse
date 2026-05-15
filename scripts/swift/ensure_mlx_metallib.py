#!/usr/bin/env python3
"""Ensure MLX metallib artifacts exist for TradeWing build and test runs.

MLX loads ``mlx.metallib`` colocated with the test host binary (``current_binary_dir()``),
then SwiftPM bundles, then ``default.metallib`` relative to the process working directory.
Tests that call ``FileManager.changeCurrentDirectoryPath`` break the cwd-relative fallback,
so this script installs ``mlx.metallib`` beside SwiftPM ``*.xctest`` hosts and copies
``default.metallib`` at the repository root.

Configuration:
    METALLIB_BUILD_TIMEOUT: CMake build timeout in seconds (default: 900)
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root

from swift_toolchain import ensure_developer_dir_for_swiftpm

METALLIB_BUILD_TIMEOUT = get_config_int("METALLIB_BUILD_TIMEOUT", 900)
_MLX_CHECKOUT_REL = Path(".build/checkouts/mlx-swift/Source/Cmlx/mlx")
_BUILT_METALLIB_REL = Path("mlx/backend/metal/kernels/mlx.metallib")
_CACHE_ROOT_REL = Path(".build/mlx-metallib-cache")


def _fingerprint_inputs(project_root: Path) -> str:
    """Hash inputs that should invalidate a cached metallib build."""
    parts: list[bytes] = []
    resolved = project_root / "Package.resolved"
    if resolved.is_file():
        parts.append(resolved.read_bytes())
    parts.append(os.environ.get("DEVELOPER_DIR", "").encode())
    digest = hashlib.sha256(b"".join(parts)).hexdigest()[:16]
    return digest


def _mlx_source_root(project_root: Path) -> Path:
    """Return the mlx CMake source tree from the SwiftPM checkout."""
    return (project_root / _MLX_CHECKOUT_REL).resolve()


def _resolve_mlx_checkout(project_root: Path, swift: str) -> Path:
    """Return mlx source path, running ``swift package resolve`` when the checkout is missing."""
    mlx_root = _mlx_source_root(project_root)
    if (mlx_root / "CMakeLists.txt").is_file():
        return mlx_root
    print("mlx-swift checkout missing; running swift package resolve...", file=sys.stderr)
    proc = subprocess.run(
        [swift, "package", "resolve"],
        cwd=project_root,
        check=False,
        timeout=600,
        env=os.environ,
    )
    if proc.returncode != 0:
        print("❌ swift package resolve failed (required for MLX metallib).", file=sys.stderr)
        sys.exit(1)
    if not (mlx_root / "CMakeLists.txt").is_file():
        print(f"❌ MLX source not found at {mlx_root}", file=sys.stderr)
        sys.exit(1)
    return mlx_root


def _copy_is_fresh(target: Path, built_metallib: Path) -> bool:
    """Return whether ``target`` exists and is at least as new as ``built_metallib``."""
    if not target.is_file() or not built_metallib.is_file():
        return False
    return target.stat().st_mtime >= built_metallib.stat().st_mtime


def _colocated_metallib_dirs(project_root: Path) -> list[Path]:
    """Return MacOS directories for SwiftPM test bundles that may load MLX."""
    build_root = project_root / ".build"
    if not build_root.is_dir():
        return []
    dirs: list[Path] = []
    for xctest in build_root.glob("**/debug/*.xctest"):
        macos_dir = xctest / "Contents" / "MacOS"
        if macos_dir.is_dir():
            dirs.append(macos_dir)
    return sorted(set(dirs))


def _install_metallib_copy(built_metallib: Path, target: Path) -> None:
    """Copy ``built_metallib`` to ``target`` when stale or missing."""
    if _copy_is_fresh(target, built_metallib):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_metallib, target)


def _sync_metallib_installs(project_root: Path, built_metallib: Path) -> None:
    """Install root and colocated metallib copies for MLX runtime loading."""
    root_default = project_root / "default.metallib"
    _install_metallib_copy(built_metallib, root_default)
    print(f"✅ Installed MLX default metallib at {root_default}")

    for macos_dir in _colocated_metallib_dirs(project_root):
        colocated_mlx = macos_dir / "mlx.metallib"
        _install_metallib_copy(built_metallib, colocated_mlx)
        print(f"✅ Installed MLX colocated metallib at {colocated_mlx}")


def _run_cmake_metallib_build(mlx_root: Path, build_dir: Path) -> Path:
    """Configure and build the ``mlx-metallib`` CMake target."""
    build_dir.mkdir(parents=True, exist_ok=True)
    configure = [
        "cmake",
        str(mlx_root),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DMLX_BUILD_METAL=ON",
    ]
    print(f"Running: {' '.join(configure)}", file=sys.stderr)
    subprocess.run(
        configure,
        cwd=build_dir,
        check=True,
        timeout=METALLIB_BUILD_TIMEOUT,
        env=os.environ,
    )
    build = ["cmake", "--build", ".", "--target", "mlx-metallib", "-j", str(os.cpu_count() or 4)]
    print(f"Running: {' '.join(build)}", file=sys.stderr)
    subprocess.run(
        build,
        cwd=build_dir,
        check=True,
        timeout=METALLIB_BUILD_TIMEOUT,
        env=os.environ,
    )
    built = build_dir / _BUILT_METALLIB_REL
    if not built.is_file():
        print(f"❌ Expected metallib at {built}", file=sys.stderr)
        sys.exit(1)
    return built


def ensure_default_metallib(project_root: Path, swift: str | None = None) -> None:
    """Build (if needed) and install ``default.metallib`` for MLX runtime loading."""
    if sys.platform != "darwin":
        return
    ensure_developer_dir_for_swiftpm(project_root)
    if shutil.which("cmake") is None:
        print("❌ cmake not found; required to build MLX default.metallib.", file=sys.stderr)
        sys.exit(1)

    if swift is None:
        from swift_toolchain import find_swift

        swift = find_swift()

    mlx_root = _resolve_mlx_checkout(project_root, swift)
    cache_dir = project_root / _CACHE_ROOT_REL / _fingerprint_inputs(project_root)
    built_metallib = cache_dir / _BUILT_METALLIB_REL

    if not built_metallib.is_file():
        print(f"Building MLX metallib in {cache_dir}...", file=sys.stderr)
        built = _run_cmake_metallib_build(mlx_root, cache_dir)
        built_metallib = built

    root_default = project_root / "default.metallib"
    colocated_targets = [
        macos_dir / "mlx.metallib" for macos_dir in _colocated_metallib_dirs(project_root)
    ]
    all_targets = [root_default, *colocated_targets]
    if all_targets and all(_copy_is_fresh(target, built_metallib) for target in all_targets):
        print("✅ MLX metallib installs are up to date")
        return

    _sync_metallib_installs(project_root, built_metallib)


def main() -> None:
    """CLI entry point."""
    project_root = get_project_root(Path(__file__))
    ensure_default_metallib(project_root)


if __name__ == "__main__":
    main()
