#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Compiler base class with CMake helper methods."""

import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
from typing import List, Optional

from .core import (
    BuildMode,
    libpack_dir,
    patch_files,
    remove_readonly,
    to_exe,
    to_static,
)


class CompilerBase:
    """Base class for all package builders. Provides CMake helpers and common functionality."""

    def __init__(
        self, config, bison_path, skip_existing: bool = False, mode: BuildMode = BuildMode.RELEASE
    ):
        self.config = config
        self.bison_path = bison_path
        self.base_dir = os.getcwd()
        self.skip_existing = skip_existing
        self.install_dir = libpack_dir(config, mode)
        self.init_script = None
        self.mode = mode
        self.strict_mode = True

        # Right now there are two packages where the version number gets coded into the path when: Boost and Coin:
        # store those two separately from all the other paths we have to track
        self.boost_include_path: Optional[str] = None
        self.coin_cmake_path: Optional[str] = None

    def get_cmake_options(self) -> List[str]:
        """Get a comprehensive list of cMake options that can be used in any cMake build. Not all options apply
        to all builds, but none conflict."""
        pcre_lib = self.install_dir + "/lib/pcre2-8"
        if self.mode == BuildMode.DEBUG:
            pcre_lib += "d"
        pcre_lib += to_static()

        base = [
            "-D CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=FALSE",
            "-D CMAKE_FIND_PACKAGE_NO_SYSTEM_PACKAGE_REGISTRY=TRUE",
            "-D CMAKE_CXX_STANDARD=20",
            f"-D BISON_EXECUTABLE={self.bison_path}",
            f"-D BOOST_ROOT={self.install_dir}",
            "-D BUILD_DOC=No",
            "-D BUILD_DOCS=No",
            "-D BUILD_EXAMPLES=No",
            "-D BUILD_SHARED=Yes",
            "-D BUILD_SHARED_LIB=Yes",
            "-D BUILD_SHARED_LIBS=Yes",
            "-D BUILD_TEST=No",
            "-D BUILD_TESTS=No",
            "-D BUILD_TESTING=No",
            f"-D BZIP2_DIR={self.install_dir}/lib/cmake/",
            f"-D Boost_INCLUDE_DIRS={self.install_dir}/include",
            f"-D CMAKE_BUILD_TYPE={self.mode}",
            f"-D CMAKE_INSTALL_PATH={self.install_dir}",
            f"-D CMAKE_INSTALL_PREFIX={self.install_dir}",
            f"-D HarfBuzz_DIR={self.install_dir}/lib/cmake/",
            f"-D HDF5_DIR={self.install_dir}/share/cmake/",
            f"-D HDF5_LIBRARY_DEBUG={self.install_dir}/lib/hdf5d.lib",
            f"-D HDF5_LIBRARY_RELEASE={self.install_dir}/lib/hdf5.lib",
            f"-D HDF5_DIFF_EXECUTABLE={self.install_dir}/bin/hdf5diff" + to_exe(),
            f"-D INSTALL_DIR={self.install_dir}",
            f"-D PCRE2_LIBRARY={pcre_lib}",
            "-D PIVY_USE_QT6=Yes",
            f"-D pybind11_DIR={self.install_dir}/share/cmake/pybind11",
            f"-D Python_ROOT_DIR={self.install_dir}/bin",
            f"-D Python_DIR={self.install_dir}/bin",
            f"-D Python3_ROOT_DIR={self.install_dir}/bin",
            f"-D Python3_DIR={self.install_dir}/bin",
            "-D Python_FIND_REGISTRY=NEVER",
            f"-D Qt6_DIR={self.install_dir}/lib/cmake/Qt6",
            f"-D SWIG_EXECUTABLE={self.install_dir}/bin/swig" + to_exe(),
            f"-D ZLIB_DIR={self.install_dir}/lib/cmake/",
            f"-D ZLIB_INCLUDE_DIR={self.install_dir}/include",
            f"-D ZLIB_LIBRARY_RELEASE={self.install_dir}/lib/zlib" + to_static(),
            f"-D ZLIB_LIBRARY_DEBUG={self.install_dir}/lib/zlibd" + to_static(),
            "-D CMAKE_DISABLE_FIND_PACKAGE_SoQt=True",
        ]
        if self.boost_include_path:
            base.append(f"-D Boost_INCLUDE_DIR={self.boost_include_path}")
        if self.coin_cmake_path:
            base.append(f"-D Coin_DIR={self.coin_cmake_path}")
        if sys.platform.startswith("win32"):
            if platform.machine() == "ARM64":
                base.append("-A ARM64")
            inc_path = self.install_dir.replace("\\", "/")
            cxx_flags = f"/I{inc_path}/include /EHsc  /DWIN32 /DWIN64"
            if self.strict_mode:
                # NOTE: /permissive- is required with Qt6 but could be disabled for anything that doesn't link against
                # Qt. The same is true for /Zc:__cplusplus /std:c++20
                cxx_flags += " /Zc:__cplusplus /std:c++20 /permissive-"
        else:
            cxx_flags = f"-I{self.install_dir}/include"
        base.append(f"-D CMAKE_CXX_FLAGS={cxx_flags}")
        return base

    def compile_all(self):
        for item in self.config["content"]:
            # All build methods are named using "build_XXX" where XXX is the name of the package in the config file
            os.chdir(item["name"])
            build_function_name = "build_" + item["name"]
            if hasattr(self, build_function_name):
                print(f"Building {item['name']}")
                build_function = getattr(self, build_function_name)
                build_function(item)
                if item["name"].lower() == "python":
                    # Check these even if we didn't actually have to build Python
                    self._build_pip()
                    if "requirements" in item:
                        self._install_python_requirements(item["requirements"])
            else:
                print(
                    f"No '{build_function_name}' found in compile_all "
                    "did you forget to add one when adding a dependency?"
                )
                exit(2)
            os.chdir(self.base_dir)

    def build_nonexistent(self, _=None):
        """Used for automated testing to allow easy Mock injection."""

    def python_exe(self) -> str:
        if self.mode == BuildMode.RELEASE:
            return os.path.join(self.install_dir, "bin", "python") + to_exe()
        return os.path.join(self.install_dir, "bin", "python_d") + to_exe()

    # ==================== CMake Helper Methods ====================

    def _cmake_create_build_dir(self):
        build_dir = "build-" + str(self.mode).lower()
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir, onerror=remove_readonly)
        os.mkdir(build_dir)
        os.chdir(build_dir)

    def _run_cmake(self, args: List[str]):
        cmake_setup_options = [self.init_script, "&", "cmake"]
        cmake_setup_options.extend(args)
        try:
            process = subprocess.run(cmake_setup_options, check=True, capture_output=True)
            with open("build_log.txt", "a", encoding="utf-8") as f:
                f.write(process.stdout.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            print("ERROR: cMake failed!")
            print(f"Command: {' '.join(cmake_setup_options)}")
            print(e.stdout.decode("utf-8"))
            if e.stderr:
                print(e.stderr.decode("utf-8"))
            exit(e.returncode)

    def _cmake_configure(self, extra_args: List[str] = None):
        options = self.get_cmake_options()
        if extra_args:
            options.extend(extra_args)
        options.append(
            ".."
        )  # Because the source code is located one directory up from our build location
        self._run_cmake(options)

    def _cmake_build(self, parallel: bool = True):
        cmake_build_options = ["--build", ".", "--config", str(self.mode).lower(), "--verbose"]
        if parallel:
            cmake_build_options.append("--parallel")
        self._run_cmake(cmake_build_options)

    def _cmake_install(self):
        cmake_install_options = ["--install", ".", "--config", str(self.mode).lower()]
        self._run_cmake(cmake_install_options)

    def _build_standard_cmake(self, extra_args: List[str] = None):
        self._cmake_create_build_dir()
        self._cmake_configure(extra_args)
        self._cmake_build()
        self._cmake_install()

    def force_copy(self, src_components: List[str], dst_components: List[str]):
        full_src = self.install_dir
        for src in src_components:
            full_src = os.path.join(full_src, src)
        full_dst = self.install_dir
        for dst in dst_components:
            full_dst = os.path.join(full_dst, dst)
        if not os.path.exists(full_src):
            print(f"    (Can't rename {full_src}, no such file or directory)")
            return
        if os.path.exists(full_dst):
            os.unlink(full_dst)
        shutil.copyfile(full_src, full_dst)

    @staticmethod
    def _get_latest_windows_target_platform_version(self) -> Optional[str]:
        base_path = r"C:\Program Files (x86)\Windows Kits\10\Lib"
        if not os.path.exists(base_path):
            return None

        version_dirs = []
        version_pattern = re.compile(r"^\d+\.\d+\.\d+\.\d+$")

        for name in os.listdir(base_path):
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path) and version_pattern.match(name):
                version_dirs.append(name)

        if not version_dirs:
            return None

        def version_key(v):
            return [int(x) for x in v.split(".")]

        latest_version = sorted(version_dirs, key=version_key)[-1]
        return latest_version
