#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""OpenCASCADE and Netgen build methods."""

import os
import shutil
import sys


class OcctBuilder:
    """Mixin for building OpenCASCADE and Netgen."""

    def _get_vtk_include_path(self) -> str:
        """
        OpenCASCADE needs a manually-set include path for VTK (the find_package script provided by VTK does not provide
        the include file path, and OpenCASCADE has not been updated to handle this, as of June 2024).
        """
        start_crawl_at = os.path.join(self.install_dir, "include")
        contents = [
            f for f in os.listdir(start_crawl_at) if os.path.isdir(os.path.join(start_crawl_at, f))
        ]
        for item in contents:
            if item.startswith("vtk-"):
                return os.path.join(start_crawl_at, item)
        raise RuntimeError("Could not find VTK include directory for OpenCASCADE")

    def build_opencascade(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "cmake", "OpenCASCADEConfig.cmake")):
                print("  Not rebuilding OpenCASCADE, it is already in the LibPack")
                return
        extra_args = [
            f"-D CMAKE_MODULE_PATH={self.install_dir}/lib/cmake;{self.install_dir}/share/cmake;{self.install_dir}",
            f"-D TCL_DIR={self.install_dir}/include",
            f"-D TK_DIR={self.install_dir}/include",
            f"-D FREETYPE_DIR={self.install_dir}/lib/cmake",
            f"-D VTK_DIR={self.install_dir}/lib/cmake",
            f"-D 3RDPARTY_VTK_INCLUDE_DIRS={self._get_vtk_include_path()}",
            f"-D EIGEN_DIR={self.install_dir}/share/eigen3/cmake",
            "-D USE_VTK=On",
            "-D USE_FREETYPE=On",
            "-D USE_RAPIDJSON=On",
            "-D USE_EIGEN=On",
            "-D BUILD_CPP_STANDARD=C++17",
            "-D BUILD_RELEASE_DISABLE_EXCEPTIONS=OFF",
            "-D INSTALL_DIR_BIN=bin",
            "-D INSTALL_DIR_LIB=lib",
            "-D CMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]
        if self.mode.name == "DEBUG":
            extra_args.append("-D BUILD_SHARED_LIBRARY_NAME_POSTFIX=d")
        cwd = os.getcwd()
        self._cmake_create_build_dir()
        self._cmake_configure(extra_args)
        self._cmake_build(parallel=False)
        if self.mode.name == "DEBUG" and sys.platform.startswith("win32"):
            # On Windows OpenCASCADE is looking in the wrong location for these files (as of 7.7.1) -- just copy them
            # TODO - Don't hardcode the path
            shutil.copytree(
                os.path.join("win64", "vc14", "bind"), os.path.join("win64", "vc14", "bin")
            )
        self._cmake_install()

        os.chdir(cwd)

        # TODO - something is getting messed up in the CMake config output (note the quotes around 26812): for now just
        # drop the line entirely
        # set (OpenCASCADE_CXX_FLAGS    "[...] /wd"26812" /MP /W4")
        with open(
            os.path.join(self.install_dir, "cmake", "OpenCASCADEConfig.cmake"),
            "r",
            encoding="utf-8",
        ) as f:
            occt_cmake_contents = f.readlines()
        with open(
            os.path.join(self.install_dir, "cmake", "OpenCASCADEConfig.cmake"),
            "w",
            encoding="utf-8",
        ) as f:
            for line in occt_cmake_contents:
                if "OpenCASCADE_CXX_FLAGS" not in line:
                    f.write(line + "\n")

    def build_netgen(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "share", "netgen")):
                print("  Not rebuilding netgen, it is already in the LibPack")
                return
        extra_args = [
            f"-D CMAKE_FIND_ROOT_PATH={self.install_dir}",
            "-D USE_SUPERBUILD=OFF",
            "-D USE_GUI=OFF",
            "-D USE_INTERNAL_TCL=OFF",
            f"-D TCL_DIR={self.install_dir}",
            f"-D TK_DIR={self.install_dir}",
            "-D USE_OCC=On",
            f"-D OpenCASCADE_ROOT={self.install_dir}",
            f"-D USE_PYTHON=OFF",
            f"-D CMAKE_CXX_FLAGS='-D_USE_MATH_DEFINES /EHsc'",
        ]
        self._build_standard_cmake(extra_args=extra_args)

