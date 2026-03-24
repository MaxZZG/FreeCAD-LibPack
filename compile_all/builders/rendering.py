#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Rendering library build methods (VTK, HarfBuzz, libpng, FreeType)."""

import os
import shutil
import sys


class RenderingBuilder:
    """Mixin for building rendering libraries."""

    def build_vtk(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "share", "licenses", "VTK")):
                print("  Not rebuilding VTK, it is already in the LibPack")
                return
        extra_args = [
            "-D VTK_WRAP_PYTHON=YES",
            "-D VTK_MODULE_ENABLE_VTK_WrappingPythonCore=YES",
            "-D VTK_PYTHON_SITE_PACKAGES_SUFFIX=bin/Lib/site-packages/",
        ]
        if sys.platform.startswith("win32"):
            extra_args.append(
                "-D VTK_MODULE_ENABLE_VTK_IOIOSS=NO",
            )
            extra_args.append(
                "-D VTK_MODULE_ENABLE_VTK_ioss=NO",
            )
            extra_args.append("-D CMAKE_CXX_MP_FLAG=YES")

        print("  (VTK is big, this will take some time)")

        old_strict_mode = self.strict_mode
        self.strict_mode = False
        self._build_standard_cmake(extra_args)
        self.strict_mode = old_strict_mode

    def build_harfbuzz(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "harfbuzz")):
                print("  Not rebuilding harfbuzz, it is already in the LibPack")
                return
        self._build_standard_cmake()

    def build_libpng(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "lib", "libpng")):
                print("  Not rebuilding libpng, it is already in the LibPack")
                return
        self._build_standard_cmake()

    def build_freetype(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "freetype2")):
                print("  Not rebuilding freetype, it is already in the LibPack")
                return
        self._build_standard_cmake()
        if self.mode.name == "DEBUG":
            # OCCT *really* wants these libraries named like this:
            shutil.copyfile(
                f"{self.install_dir}/bin/freetyped.dll", f"{self.install_dir}/bin/freetype.dll"
            )
            shutil.copyfile(
                f"{self.install_dir}/lib/freetyped.lib", f"{self.install_dir}/lib/freetype.lib"
            )
