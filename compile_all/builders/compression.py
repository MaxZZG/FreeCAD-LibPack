#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Compression library build methods (zlib, bzip2, pcre2)."""

import os
import shutil
import subprocess
import sys


class CompressionBuilder:
    """Mixin for building compression libraries."""

    def build_zlib(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "zlib.h")):
                print("  Not rebuilding zlib, it is already in the LibPack")
                return
        self._build_standard_cmake()
        # Qt really wants to find these under an alternate name, so just make copies...
        name_mapping = [
            (os.path.join("lib", "zlib.lib"), os.path.join("lib", "zlib1.lib")),
            (os.path.join("bin", "zlib.dll"), os.path.join("bin", "zlib1.dll")),
        ]
        for name1, name2 in name_mapping:
            full_name1 = os.path.join(self.install_dir, name1)
            full_name2 = os.path.join(self.install_dir, name2)
            if os.path.exists(full_name1) and not os.path.exists(full_name2):
                shutil.copy(full_name1, full_name2)
            elif os.path.exists(full_name2) and not os.path.exists(full_name1):
                shutil.copy(full_name2, full_name1)

    def build_bzip2(self, _=None):
        """The version of BZip2 in widespread use (1.0.8, the most recent official release) do not yet use cMake"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "bzlib.h")):
                print("  Not rebuilding bzip2, it is already in the LibPack")
                return
        if sys.platform.startswith("win32"):
            args = [self.init_script, "&", "nmake", "/f", "makefile.msc"]
            try:
                subprocess.run(args, check=True, capture_output=True)
                shutil.copyfile("libbz2.lib", os.path.join(self.install_dir, "lib", "libbz2.lib"))
                shutil.copyfile("bzlib.h", os.path.join(self.install_dir, "include", "bzlib.h"))
                shutil.copyfile(
                    "bzlib_private.h", os.path.join(self.install_dir, "include", "bzlib_private.h")
                )
            except subprocess.CalledProcessError as e:
                print("ERROR: Failed to build bzip2 using nmake")
                print(e.output.decode("utf-8"))
                if e.stderr:
                    print(e.stderr.decode("utf-8"))
                exit(1)
        else:
            raise NotImplemented("Non-Windows compilation of bzip2 is not implemented yet")

    def build_pcre2(self, _=None):
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "pcre2.h")):
                print("  Not rebuilding pcre2, it is already in the LibPack")
                return
        self._build_standard_cmake()
