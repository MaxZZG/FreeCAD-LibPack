#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Python build methods."""

import io
import os
import pathlib
import platform
import requests
import shutil
import subprocess
import sys
import zipfile
from typing import List, Optional

from ..core import BuildMode, to_exe


class PythonBuilder:
    """Mixin for building Python and related packages."""

    def build_python(self, args=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "DLLs")):
                print("  Not rebuilding Python, it is already in the LibPack")
                return
        if sys.platform.startswith("win32"):
            expected_exe_path = self.python_exe()
            arch = "x64" if platform.machine() == "AMD64" else "ARM64"
            path = "amd64" if platform.machine() == "AMD64" else "arm64"
            try:
                subprocess.run(
                    [
                        self.init_script,
                        "&",
                        "PCbuild\\build.bat",
                        "-p",
                        arch,
                        "-c",
                        str(self.mode),
                        "-e",
                    ],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                print("Python build failed")
                print(e.stdout.decode("utf-8"))
                if e.stderr:
                    print(e.stderr.decode("utf-8"))
                exit(e.returncode)
            except FileNotFoundError as e:
                print(f"Could not find file: {e}")
                exit(-1)
            bin_dir = os.path.join(self.install_dir, "bin")
            dll_dir = os.path.join(bin_dir, "DLLs")
            lib_dir = os.path.join(bin_dir, "Lib")
            libs_dir = os.path.join(bin_dir, "libs")
            inc_dir = os.path.join(bin_dir, "Include")
            tools_dir = os.path.join(bin_dir, "Tools")
            os.makedirs(bin_dir, exist_ok=True)
            os.makedirs(dll_dir, exist_ok=True)
            os.makedirs(lib_dir, exist_ok=True)
            os.makedirs(libs_dir, exist_ok=True)
            os.makedirs(bin_dir, exist_ok=True)
            os.makedirs(tools_dir, exist_ok=True)
            tools_subs = ["i18n", "scripts"]
            for sub in tools_subs:
                os.makedirs(os.path.join(tools_dir, sub), exist_ok=True)

            # NOTES:
            # When installed via the Python installer, the top-level Python folder contains:
            #   python.exe
            #   python.pdb
            #   python3.dll
            #   python3xx.dll
            #   python3xx.pdb
            #   python3xx_d.dll
            #   python3xx_d.pdb
            #   python3_d.dll
            #   pythonw.exe
            #   pythonw.pdb
            #   pythonw_d.exe
            #   pythonw_d.pdb
            #   python_d.exe
            #   python_d.pdb
            #   vcruntime140.dll
            #   vcruntime140_1.dll
            # It also contains 5 subdirectories: DLLs, include, Lib, libs, and Tools, plus LICENSE.txt
            #    DLLS folder contains *.pyd, *.pdb, and *.dll
            #    include contains the header file directory tree
            #    Lib contains the Python standard libraries
            #    libs contains the actual Python *.lib files (python3.lib and python3xx.lib and their debug equivalents
            #    Tools contains a number of subdirectories with Python scripts: i18n, scripts, and demo
            # Finally, we also need the file "pyconfig.h" which is in yet another directory of the Python build, "PC"

            shutil.copytree(f"PCBuild\\{path}", dll_dir, dirs_exist_ok=True)
            shutil.copytree(f"Lib", lib_dir, dirs_exist_ok=True)
            shutil.copytree(f"Include", inc_dir, dirs_exist_ok=True)
            for sub in tools_subs:
                shutil.copytree(f"Tools\\{sub}", os.path.join(tools_dir, sub), dirs_exist_ok=True)

            # Figure out what version of Python we just built:
            major, minor = self.get_python_version(
                os.path.join("PCBuild", path, "python.exe")
            ).split(".")

            # Construct the list of files we expect to exist that need to be placed in the toplevel directory, or in
            # libs:
            move_to_bin = ["vcruntime"]
            for base in ["python", f"python{major}", f"python{major}{minor}", "pythonw"]:
                final = base
                if self.mode == BuildMode.DEBUG:
                    final += "_d"
                move_to_bin.append(final)
            # They are all in the DLLs subdirectory now: move the ones that match:
            for file in pathlib.Path(dll_dir).iterdir():
                if file.is_file():
                    if file.stem in move_to_bin:
                        if file.suffix == ".lib":
                            target = os.path.join(libs_dir, file.name)
                        elif file.suffix in [".dll", ".exe", ".pdb"]:
                            target = os.path.join(bin_dir, file.name)
                        else:
                            continue
                        if os.path.exists(target):
                            os.unlink(target)
                        file.rename(target)
            pyconfig = os.path.join("PCBuild", path.lower(), "pyconfig.h")
            target = os.path.join(inc_dir, "pyconfig.h")
            if not os.path.exists(pyconfig):
                print("ERROR: Could not locate pyconfig.h, cannot complete installation of Python")
                exit(1)
            if os.path.exists(target):
                os.unlink(target)
            print(f"Copying {pyconfig} to {target}")
            shutil.copyfile(pyconfig, target)
        else:
            raise NotImplemented("Non-Windows compilation of Python is not implemented yet")

    def get_python_version(self, exe: str = None) -> str:
        if exe is None:
            path_to_python = self.python_exe()
        else:
            path_to_python = exe
        try:
            result = subprocess.run([path_to_python, "--version"], capture_output=True, check=True)
            _, _, version_number = result.stdout.decode("utf-8").strip().partition(" ")
            components = version_number.split(".")
            python_version = f"{components[0]}.{components[1]}"
            return python_version
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to run LibPack's Python executable")
            print(e.stdout.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)

    def _build_pip(self, _=None):
        print("  Installing the latest pip")
        path_to_python = self.python_exe()
        try:
            subprocess.run(
                [path_to_python, "-m", "ensurepip", "--upgrade"], capture_output=True, check=True
            )
            subprocess.run(
                [path_to_python, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to run LibPack's Python executable")
            print(e.stdout.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)

    def _install_python_requirements(self, requirements):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "Lib", "site-packages", "PIL")):
                print("  Not re-installing Python requirements, they are already in the LibPack")
                return
        if platform.machine() == "ARM64" and sys.platform == "win32":
            print("Detected Windows-on-ARM, downloading fallback wheels...")
            fallback_wheels = self._get_windows_on_arm_fallback_wheels()
        else:
            fallback_wheels = None
        print("  Installing the following requirements (and their dependencies) using pip:")
        final_requirements = []
        for req in requirements:
            fallback = False
            if fallback_wheels is not None:
                new_req = self._get_fallback_wheel(req, fallback_wheels)
                if new_req is not None:
                    fallback = True
                    final_requirements.append(new_req)
                    print("    " + req + " (using ARM64 fallback wheel)")
            if not fallback:
                final_requirements.append(req)
                print("    " + req)
        path_to_python = self.python_exe()
        call_args = [
            path_to_python,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--ignore-installed",
            "--no-warn-script-location",
        ]
        call_args.extend(final_requirements)
        try:
            subprocess.run(
                call_args,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to pip install requirements")
            print(e.output.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)

    def _get_windows_on_arm_fallback_wheels(self) -> str:
        """As of May 2025 SciPy does not yet provide a WOA wheel, so we have to use an "unofficial" build from
        https://github.com/cgohlke/win_arm64-wheels"""
        wheel_dir = os.path.join(self.base_dir, "woa-fallback-wheel")
        if os.path.exists(wheel_dir):
            if self.skip_existing:
                print("Already downloaded Windows-on-ARM fallback wheels")
                return wheel_dir
            else:
                shutil.rmtree(wheel_dir)
        os.makedirs(wheel_dir)
        zip_url = "https://github.com/cgohlke/win_arm64-wheels/releases/download/v2025.3.31/2025.3.31-experimental-cp313-win_arm64.whl.zip"
        response = requests.get(zip_url)
        if response.status_code != 200:
            print("Failed to download Windows-on-ARM fallback Python requirements")
            exit(1)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_data:
            for content_item in zip_data.infolist():
                if content_item.is_dir():
                    continue
                filename = str(os.path.basename(content_item.filename))
                if not filename:
                    continue
                target_path = os.path.join(wheel_dir, filename)
                with open(target_path, "wb") as target_file:
                    target_file.write(zip_data.read(content_item))
            zip_data.extractall(path=wheel_dir)
        return wheel_dir

    @staticmethod
    def _get_fallback_wheel(req: str, fallback_wheels: str) -> Optional[str]:
        """See if a given requirement has a wheel in our fallback directory, and if so return
        it. If not, just return the original requirement"""
        package_name, _, version = req.partition("==")
        filename = next(
            (
                f
                for f in os.listdir(fallback_wheels)
                if f.startswith(package_name) and f.endswith(".whl")
            ),
            None,
        )
        if filename is None:
            return None
        return os.path.join(fallback_wheels, filename)

    def _pip_install(self, requirement: str) -> None:
        path_to_python = self.python_exe()
        package_name = requirement.split("==")[0]
        try:
            # Get rid of any version that's already there.
            subprocess.run(
                [path_to_python, "-m", "pip", "uninstall", "--yes", package_name],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"{package_name} was not uninstalled... continuing")
            pass
        try:
            subprocess.run(
                [path_to_python, "-m", "pip", "install", "--ignore-installed", requirement],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to pip install {requirement}")
            print(e.output.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)

    def _build_with_pip(self, options: dict):
        if "pip-install" not in options:
            print(
                f"ERROR: No pip-install provided in config of {options['name']}, so version cannot be determined"
            )
            exit(1)
        self._pip_install(options["pip-install"])
