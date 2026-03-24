#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""CAM-related build methods (OpenCAMLib, CalculiX)."""

import os
import shutil


class CamBuilder:
    """Mixin for building CAM-related packages."""

    def build_opencamlib(self, _: None):
        if self.skip_existing:
            if os.path.exists(
                os.path.join(self.install_dir, "bin", "Lib", "site-packages", "opencamlib")
            ):
                print("  Not rebuilding opencamlib, it is already in the LibPack")
                return
        extra_args = [
            "-D BUILD_CXX_LIB=OFF",
            "-D BUILD_PY_LIB=ON",
            "-D BUILD_DOC=OFF",
            "-D Boost_USE_STATIC_LIBS=OFF",
        ]
        self._build_standard_cmake(extra_args)

    def build_calculix(self, _: None):
        """Cannot currently build Calculix (it's in Fortran, and we only support MSVC toolchain right now).
        Extract the relevant files from the downloaded zipfile and copy them."""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "bin", "ccx.exe")):
                print("  Not rebuilding Calculix, it is already in the LibPack")
                return
        path_to_ccx_bin = os.path.join(os.getcwd(), "CL35-win64", "bin", "ccx", "218")
        if not os.path.exists(path_to_ccx_bin):
            raise RuntimeError("Could not locate Calculix")
        shutil.copytree(path_to_ccx_bin, os.path.join(self.install_dir, "bin"), dirs_exist_ok=True)
        # The download we use calls the executable ccx218.exe, but FreeCAD would prefer it be called ccx.exe for
        # automatic location of the executable
        shutil.move(
            os.path.join(self.install_dir, "bin", "ccx218.exe"),
            os.path.join(self.install_dir, "bin", "ccx.exe"),
        )
