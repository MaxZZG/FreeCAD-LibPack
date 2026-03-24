#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""SWIG-related build methods (swig, pivy, pyside)."""

import os
import subprocess
import sys

from ..core import to_exe


class SwigBuilder:
    """Mixin for building SWIG and related packages."""

    def build_swig(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "swig") + to_exe()):
                print("  Not rebuilding SWIG, it is already in the LibPack")
                return
        self._build_standard_cmake()

    def build_pivy(self, _=None):
        if self.skip_existing:
            if os.path.exists(
                os.path.join(self.install_dir, "bin", "Lib", "site-packages", "pivy")
            ):
                print("  Not rebuilding pivy, it is already in the LibPack")
                return
        extra_args = []
        self._build_standard_cmake(extra_args)
        if self.mode.name == "DEBUG":
            base = os.path.join(self.install_dir, "bin", "Lib", "site-packages", "pivy")
            os.rename(os.path.join(base, "_coin.pyd"), os.path.join(base, "_coin_d.pyd"))

    def build_pyside(self, _=None):
        # Don't use a pip-install for this, we need the linkable libraries and include files for both PySide and
        # Shiboken, which won't get installed by pip, and it needs to be built against the right Python exe
        if self.skip_existing:
            if os.path.exists(
                os.path.join(self.install_dir, "bin", "Lib", "site-packages", "PySide6")
            ):
                print("  Not rebuilding PySide6, it is already in the LibPack")
                return
        python = self.python_exe()
        qtpaths = "--qtpaths=" + os.path.join(self.install_dir, "bin", "qtpaths6") + to_exe()
        clang = "CLANG_INSTALL_DIR=" + os.path.join(self.install_dir, "lib", "clang")
        vulkan = "VULKAN_SDK=None"
        parallel = "--parallel=16"
        if sys.platform.startswith("win32"):
            ssl = "--openssl=" + os.path.join(self.install_dir, "bin", "DLLs")
            args = [
                self.init_script,
                "&",
                "set",
                clang,
                "&",
                "set",
                vulkan,
                "&",
                python,
                "setup.py",
                "install",
                qtpaths,
                ssl,
                parallel,
            ]
            if self.mode.name == "DEBUG":
                args.append("--debug")
        else:
            ssl = "--openssl=" + os.path.join(self.install_dir, "bin", "DLLs")
            args = [clang, "&&", python, "setup.py", "install", qtpaths, ssl]
        try:
            subprocess.run(args, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to build Pyside and/or Shiboken")
            print(e.stdout.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)
