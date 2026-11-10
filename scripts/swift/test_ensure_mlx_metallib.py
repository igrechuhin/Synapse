#!/usr/bin/env python3
"""Tests for MLX metallib install helpers."""

from __future__ import annotations

import hashlib
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ensure_mlx_metallib as metallib
from ensure_mlx_metallib import xctest_metallib_resource_dirs, copy_is_fresh


class EnsureMlxMetallibTests(unittest.TestCase):
    """Validate MLX build configuration and signed-bundle-safe installation."""

    def test_resource_dirs_discovers_native_swiftpm_test_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            macos_dir = (
                root
                / ".build"
                / "arm64-apple-macosx"
                / "debug"
                / "TradeWingPackageTests.xctest"
                / "Contents"
                / "MacOS"
            )
            macos_dir.mkdir(parents=True)

            found = xctest_metallib_resource_dirs(root)

            self.assertEqual(
                found,
                [
                    macos_dir.parent
                    / "Resources"
                    / "mlx-swift_Cmlx.bundle"
                    / "Contents"
                    / "Resources"
                ],
            )

    def test_install_uses_resource_bundles_for_swiftbuild_without_touching_code(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            host = root / ".build" / "out" / "Products" / "Debug" / "Tests.xctest"
            macos = host / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            built = root / "built.metallib"
            _ = built.write_bytes(b"metal")
            metallib._sync_metallib_installs(root, built)
            resource = (
                host
                / "Contents"
                / "Resources"
                / "mlx-swift_Cmlx.bundle"
                / "Contents"
                / "Resources"
                / "default.metallib"
            )
            self.assertEqual(resource.read_bytes(), b"metal")
            self.assertEqual((root / "default.metallib").read_bytes(), b"metal")
            self.assertEqual(list(macos.iterdir()), [])
            info = plistlib.loads((resource.parent.parent / "Info.plist").read_bytes())
            self.assertEqual(info["CFBundlePackageType"], "BNDL")

    def test_copy_is_fresh_requires_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            built = root / "built.metallib"
            _ = built.write_bytes(b"metal")

            self.assertFalse(copy_is_fresh(root / "missing.metallib", built))

    def test_cmake_build_enables_metal_and_matches_swift_jit_backend(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            build = root / "build"
            built = build / metallib._BUILT_METALLIB_REL
            built.parent.mkdir(parents=True)
            _ = built.write_bytes(b"metal")

            with patch.object(metallib.subprocess, "run") as run:
                result = metallib._run_cmake_metallib_build(root / "mlx", build)

            self.assertEqual(result, built)
            self.assertEqual(run.call_count, 2)
            self.assertEqual(
                run.call_args_list[0].args[0],
                [
                    "cmake",
                    str(root / "mlx"),
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DMLX_BUILD_METAL=ON",
                    "-DMLX_METAL_JIT=ON",
                ],
            )
            self.assertEqual(
                run.call_args_list[1].args[0][:5],
                ["cmake", "--build", ".", "--target", "mlx-metallib"],
            )
            self.assertTrue(run.call_args_list[0].kwargs["check"])

    def test_fingerprint_invalidates_legacy_and_changed_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            _ = (root / "Package.resolved").write_bytes(b"resolved")
            with patch.dict(metallib.os.environ, {"DEVELOPER_DIR": "/xcode"}):
                current = metallib._fingerprint_inputs(root)
                legacy = hashlib.sha256(b"resolved/xcode").hexdigest()[:16]
                self.assertNotEqual(current, legacy)
                self.assertEqual(current, metallib._fingerprint_inputs(root))
                with patch.object(metallib, "_CMAKE_METALLIB_OPTIONS", ("changed",)):
                    self.assertNotEqual(current, metallib._fingerprint_inputs(root))

    def test_fingerprint_tracks_dependency_and_toolchain_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            resolved = root / "Package.resolved"
            _ = resolved.write_bytes(b"original")
            with patch.dict(metallib.os.environ, {"DEVELOPER_DIR": "/xcode"}):
                original = metallib._fingerprint_inputs(root)
                _ = resolved.write_bytes(b"updated")
                self.assertNotEqual(original, metallib._fingerprint_inputs(root))
                _ = resolved.write_bytes(b"original")
                with patch.dict(metallib.os.environ, {"DEVELOPER_DIR": "/other"}):
                    self.assertNotEqual(original, metallib._fingerprint_inputs(root))


if __name__ == "__main__":
    _ = unittest.main()
