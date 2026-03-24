#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Testing library build methods (Google Test, libE57Format)."""

import os
import sys


class TestingBuilder:
    """Mixin for building testing libraries."""

    def build_googletest(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "gtest")):
                print("  Not rebuilding googletest, it is already in the LibPack")
                return
        extra_args = []
        if sys.platform == "win32":
            extra_args.extend(["-D GTEST_FORCE_SHARED_CRT=ON", "-D GTEST_DISABLE_PTHREADS=ON"])
        self._build_standard_cmake(extra_args)

    def build_libE57Format(self, _: None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "E57Format")):
                print("  Not rebuilding libE57Format, it is already in the LibPack")
                return
        extra_args = ["-D E57_BUILD_TEST=OFF"]
        self._build_standard_cmake(extra_args)
