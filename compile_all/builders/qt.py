#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Qt build methods."""

import os
import platform
import shutil
import subprocess
import sys


class QtBuilder:
    """Mixin for building Qt."""

    def _build_qt_from_source(self, options: dict):
        """Actually build Qt from source."""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "metatypes")):
                print("Not building Qt from source, it already seems to be in the LibPack")
                return

        build_dir = os.path.join(os.getcwd(), f"build-{str(self.mode).lower()}")
        if len(build_dir) > 20:
            print(
                "  WARNING: Qt uses incredibly long path names which end up right at the very edge of what\n"
                "  can be supported. In order to build successfully it might be necessary to use a very short\n"
                '  path name for the actual build directory (e.g., "C:\\temp").\n'
            )
            if "fallback-build-dir" in options:
                print(f"  Using fallback build directory {options['fallback-build-dir']}")
                build_dir = options["fallback-build-dir"]
            else:
                print(
                    f"  Attempting to use default path {build_dir}. \n\nIf the build fails, consider making a temp directory to work in.\n"
                )

        os.makedirs(build_dir, exist_ok=True)
        old_cwd = os.getcwd()
        os.chdir(build_dir)

        # Qt needs access to zlib and libpng, and assumes they are installed at the system level. We want to
        # use the LibPack versions. The easiest thing to do is just copy the DLLs:
        files = ["zlib.dll", "zlib1.dll", "libpng16.dll"]
        source = os.path.join(self.install_dir, "bin")
        destination = os.path.join(build_dir, "qtbase", "bin")
        os.makedirs(destination, exist_ok=True)
        for f in files:
            shutil.copy(os.path.join(source, f), destination)

        submodules = ["qtbase", "qtsvg", "qtdeclarative", "qttools"]
        init_command = [
            self.init_script,
            "&",
            os.path.join(old_cwd, "configure.bat"),
            "-opensource",
            "-init-submodules",
            "-submodules",
            ",".join(submodules),
            "-feature-opengl",
            "-prefix",
            self.install_dir,
            "-opengl",
            "desktop",
        ]
        try:
            process = subprocess.run(init_command, check=True, capture_output=True)
            with open("configure_log.txt", "a", encoding="utf-8") as f:
                f.write(process.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            print("ERROR: Qt configure failed!")
            print(f"Command: {' '.join(init_command)}")
            print(e.stdout.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(e.returncode)

        self._cmake_build()
        self._cmake_install()
        os.chdir(old_cwd)

    def build_qt(self, options: dict):
        """Doesn't really 'build' Qt, just copies the pre-compiled libraries from the configured path,
        unless running in Windows-on-ARM, in which case we *have* to build Qt from source in order to get
        the OpenGL module"""

        if (
            "install-directory" not in options
            or not os.path.exists(options["install-directory"])
            or platform.machine() == "ARM64"
        ):
            self._build_qt_from_source(options)
            return
        qt_dir = options["install-directory"]
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "metatypes")):
                print(
                    "  Not re-copying, instead just using existing Qt in the LibPack installation path"
                )
                return
        if not os.path.exists(qt_dir):
            print(f"Error: specified Qt installation path does not exist ({qt_dir})")
            exit(1)
        print("  (Note that Qt isn't really 'built,' it is just copied from a local installation)")
        shutil.copytree(qt_dir, self.install_dir, dirs_exist_ok=True)

    def build_libclang(self, _=None):
        """libclang is provided as a platform-specific download by Qt."""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "clang")):
                print("  Not copying libclang, it is already in the LibPack")
                return
        print("  (not really building libclang, just copying from a build provided by Qt)")
        shutil.copytree("libclang", self.install_dir, dirs_exist_ok=True)
