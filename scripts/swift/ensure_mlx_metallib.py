#!/usr/bin/env python3
"""Ensure MLX metallib artifacts exist for TradeWing build and test runs.

MLX searches loaded bundles for ``mlx-swift_Cmlx.bundle/default.metallib``
via each bundle's resource URL, before its working-directory fallback. Install
that resource bundle inside test hosts' Resources directories, never their
code-signed MacOS directories, and retain the repository-root fallback.

Configuration:
    METALLIB_BUILD_TIMEOUT: CMake build timeout in seconds (default: 900)
"""

from __future__ import annotations

# cspell:ignore BNDL

import hashlib
import os
import plistlib
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
BUILT_METALLIB_REL = Path("mlx/backend/metal/kernels/mlx.metallib")
_CACHE_ROOT_REL = Path(".build/mlx-metallib-cache")
# Match mlx-swift's JIT backend while retaining its precompiled base kernels.
CMAKE_METALLIB_OPTIONS = (
    "-DCMAKE_BUILD_TYPE=Release",
    "-DMLX_BUILD_METAL=ON",
    "-DMLX_METAL_JIT=ON",
)


def metallib_cache_fingerprint(project_root: Path) -> str:
    """Hash inputs that should invalidate a cached metallib build."""
    parts: list[bytes] = ["\0".join(CMAKE_METALLIB_OPTIONS).encode()]
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
    print(
        "mlx-swift checkout missing; running swift package resolve...", file=sys.stderr
    )
    proc = subprocess.run(
        [swift, "package", "resolve"],
        cwd=project_root,
        check=False,
        timeout=600,
        env=os.environ,
    )
    if proc.returncode != 0:
        print(
            "❌ swift package resolve failed (required for MLX metallib).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not (mlx_root / "CMakeLists.txt").is_file():
        print(f"❌ MLX source not found at {mlx_root}", file=sys.stderr)
        sys.exit(1)
    return mlx_root


def copy_is_fresh(target: Path, built_metallib: Path) -> bool:
    """Return whether ``target`` exists and is at least as new as ``built_metallib``."""
    if not target.is_file() or not built_metallib.is_file():
        return False
    return target.stat().st_mtime >= built_metallib.stat().st_mtime


def xctest_metallib_resource_dirs(project_root: Path) -> list[Path]:
    """Return MLX resource directories for native and SwiftBuild debug tests."""
    build_root = project_root / ".build"
    if not build_root.is_dir():
        return []
    dirs: list[Path] = []
    for xctest in build_root.rglob("*.xctest"):
        if xctest.parent.name.lower() != "debug":
            continue
        if (xctest / "Contents" / "MacOS").is_dir():
            dirs.append(
                xctest
                / "Contents"
                / "Resources"
                / "mlx-swift_Cmlx.bundle"
                / "Contents"
                / "Resources"
            )
    return sorted(set(dirs))


def _install_metallib_copy(built_metallib: Path, target: Path) -> None:
    """Copy ``built_metallib`` to ``target`` when stale or missing."""
    if copy_is_fresh(target, built_metallib):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copy2(built_metallib, target)


def sync_metallib_installs(project_root: Path, built_metallib: Path) -> None:
    """Install root and resource-bundle copies for MLX runtime loading."""
    root_default = project_root / "default.metallib"
    _install_metallib_copy(built_metallib, root_default)
    print(f"✅ Installed MLX default metallib at {root_default}")

    for resource_dir in xctest_metallib_resource_dirs(project_root):
        target = resource_dir / "default.metallib"
        _install_metallib_copy(built_metallib, target)
        info = resource_dir.parent / "Info.plist"
        if not info.is_file():
            _ = info.write_bytes(
                plistlib.dumps(
                    {
                        "CFBundleIdentifier": "mlx-swift.Cmlx.resources",
                        "CFBundleName": "mlx-swift_Cmlx",
                        "CFBundlePackageType": "BNDL",
                        "CFBundleInfoDictionaryVersion": "6.0",
                    }
                )
            )
        print(f"✅ Installed MLX resource metallib at {target}")


def build_cmake_metallib(mlx_root: Path, build_dir: Path) -> Path:
    """Configure and build the ``mlx-metallib`` CMake target."""
    build_dir.mkdir(parents=True, exist_ok=True)
    configure = [
        "cmake",
        str(mlx_root),
        *CMAKE_METALLIB_OPTIONS,
    ]
    print(f"Running: {' '.join(configure)}", file=sys.stderr)
    _ = subprocess.run(
        configure,
        cwd=build_dir,
        check=True,
        timeout=METALLIB_BUILD_TIMEOUT,
        env=os.environ,
    )
    build = [
        "cmake",
        "--build",
        ".",
        "--target",
        "mlx-metallib",
        "-j",
        str(os.cpu_count() or 4),
    ]
    print(f"Running: {' '.join(build)}", file=sys.stderr)
    _ = subprocess.run(
        build,
        cwd=build_dir,
        check=True,
        timeout=METALLIB_BUILD_TIMEOUT,
        env=os.environ,
    )
    built = build_dir / BUILT_METALLIB_REL
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
        print(
            "❌ cmake not found; required to build MLX default.metallib.",
            file=sys.stderr,
        )
        sys.exit(1)

    if swift is None:
        from swift_toolchain import find_swift

        swift = find_swift()

    mlx_root = _resolve_mlx_checkout(project_root, swift)
    cache_dir = (
        project_root / _CACHE_ROOT_REL / metallib_cache_fingerprint(project_root)
    )
    built_metallib = cache_dir / BUILT_METALLIB_REL

    if not built_metallib.is_file():
        print(f"Building MLX metallib in {cache_dir}...", file=sys.stderr)
        built = build_cmake_metallib(mlx_root, cache_dir)
        built_metallib = built

    root_default = project_root / "default.metallib"
    resource_dirs = xctest_metallib_resource_dirs(project_root)
    all_targets = [
        root_default,
        *(directory / "default.metallib" for directory in resource_dirs),
    ]
    if all(
        directory.parent.joinpath("Info.plist").is_file() for directory in resource_dirs
    ) and all(copy_is_fresh(target, built_metallib) for target in all_targets):
        print("✅ MLX metallib installs are up to date")
        return

    sync_metallib_installs(project_root, built_metallib)


def main() -> None:
    """CLI entry point."""
    project_root = get_project_root(Path(__file__))
    ensure_default_metallib(project_root)


if __name__ == "__main__":
    main()
