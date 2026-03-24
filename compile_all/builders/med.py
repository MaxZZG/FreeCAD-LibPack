#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""MED file format build methods (HDF5, medfile)."""

import os


class MedBuilder:
    """Mixin for building HDF5 and medfile."""

    def build_hdf5(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "hdf5.h")):
                print("  Not rebuilding hdf5, it is already in the LibPack")
                return
        # HDF5 is VERY picky about how you specify the location of zlib: you must actually set the precise path to the
        # library file itself. TODO future work to internally detect that library name and path and fill them here
        extra_args = [
            f"-D ZLIB_INCLUDE_DIR={self.install_dir}/include",
            f"-D ZLIB_LIBRARY={self.install_dir}/lib/zlib.lib",
        ]
        self._build_standard_cmake(extra_args)

    def build_medfile(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "medfile.h")):
                print("  Not rebuilding medfile, it is already in the LibPack")
                return
        extra_args = ["-D MEDFILE_USE_UNICODE=On", "-D MEDFILE_BUILD_TESTS=OFF"]
        old_strict_mode = self.strict_mode
        self.strict_mode = False
        self._build_standard_cmake(extra_args)
        self.strict_mode = old_strict_mode
