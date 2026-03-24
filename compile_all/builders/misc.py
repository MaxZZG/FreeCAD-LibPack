#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Miscellaneous library build methods."""

import os
import platform
import shutil
import subprocess
import sys

from ..core import to_exe


class MiscBuilder:
    """Mixin for building miscellaneous libraries."""

    def build_gmsh(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "gmsh" + to_exe())):
                print("  Not rebuilding gmsh, it is already in the LibPack")
                return
        extra_args = []
        if sys.platform.startswith("win32"):
            extra_args = [
                "-D ENABLE_OPENMP=No",
                "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            ]  # Build fails if OpenMP is enabled
        self._build_standard_cmake(extra_args)

    def build_pycxx(self, _: None):
        """PyCXX does not use a cMake-based build system"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "Lib", "site-packages", "CXX")):
                print("  Not rebuilding PyCXX, it is already in the LibPack")
                return
        path_to_python = self.python_exe()
        args = [path_to_python, "setup.py", "install"]
        try:
            subprocess.run(args, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to build PyCXX using its custom build script")
            print(e.output.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(1)

    def build_icu(self, _: None):
        """ICU does not use cMake, but has projects for various OSes"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "unicode")):
                print("  Not rebuilding ICU, it is already in the LibPack")
                return

        os.chdir(os.path.join("icu4c", "source"))
        if platform.machine() == "ARM64":
            arch = "ARM64"
        else:
            arch = "x64"
        if sys.platform.startswith("win32"):
            os.chdir("allinone")
            target = self._get_latest_windows_target_platform_version()
            args = [
                self.init_script,
                "&",
                "msbuild",
                f"/p:Configuration={str(self.mode).lower()}",
                "/t:Build",
                f"/p:Platform={arch}",
                f"/p:WindowsTargetPlatformVersion={target}",
                "/p:SkipUWP=true",
                "allinone.sln",
            ]
            try:
                subprocess.run(args, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print("ERROR: Failed to build ICU using its custom build script")
                print(e.output.decode("utf-8"))
                if e.stderr:
                    print(e.stderr.decode("utf-8"))
                exit(1)
            os.chdir(os.path.join("..", ".."))
            bin_dir = os.path.join(self.install_dir, "bin")
            lib_dir = os.path.join(self.install_dir, "lib")
            inc_dir = os.path.join(self.install_dir, "include")
            if sys.platform.startswith("win32"):
                if platform.machine() == "ARM64":
                    shutil.copytree(f"binARM64", bin_dir, dirs_exist_ok=True)
                    shutil.copytree(f"libARM64", lib_dir, dirs_exist_ok=True)
                else:
                    shutil.copytree(f"bin64", bin_dir, dirs_exist_ok=True)
                    shutil.copytree(f"lib64", lib_dir, dirs_exist_ok=True)
            shutil.copytree(f"include", inc_dir, dirs_exist_ok=True)
        else:
            raise NotImplemented("Non-Windows compilation of ICU is not implemented yet")

    def build_xercesc(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "xercesc")):
                print("  Not rebuilding xerces-c, it is already in the LibPack")
                return
        extra_args = [
            f"-D ICU_INCLUDE_DIR={self.install_dir}/include",
            f"-D ICU_ROOT={self.install_dir}",
            f"-D ICU_UC_DIR={self.install_dir}",
        ]
        self._build_standard_cmake(extra_args)

    def build_libfmt(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "fmt")):
                print("  Not rebuilding libfmt, it is already in the LibPack")
                return
        extra_args = ["-D FMT_TEST=OFF", "-D FMT_DOC=OFF"]
        self._build_standard_cmake(extra_args)

    def build_eigen3(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "eigen3")):
                print("  Not rebuilding Eigen3, it is already in the LibPack")
                return
        self._build_standard_cmake()

    def build_yamlcpp(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "yaml-cpp")):
                print("  Not rebuilding yaml-cpp, it is already in the LibPack")
                return
        extra_args = ["-D YAML_BUILD_SHARED_LIBS=ON", "-D CMAKE_POLICY_VERSION_MINIMUM=3.5"]
        self._build_standard_cmake(extra_args)

    def build_rapidjson(self, _):
        if os.path.exists(os.path.join(self.install_dir, "include", "rapidjson")):
            if self.skip_existing:
                print("  Not re-copying RapidJSON, it is already in the LibPack")
                return
            shutil.rmtree(os.path.join(self.install_dir, "include", "rapidjson"))
        shutil.copytree("include", os.path.join(self.install_dir, "include"), dirs_exist_ok=True)

    def build_pybind11(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "pybind11")):
                print("  Not rebuilding pybind11, it is already in the LibPack")
                return
        self._build_standard_cmake()
