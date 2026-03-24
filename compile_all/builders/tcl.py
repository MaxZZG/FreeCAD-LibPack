#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Tcl/Tk build methods."""

import os
import subprocess
import sys


class TclBuilder:
    """Mixin for building Tcl and Tk."""

    def build_tcl(self, _=None):
        """tcl does not use cMake"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "tcl.h")):
                print("  Not rebuilding tcl, it is already in the LibPack")
                return
        if sys.platform.startswith("win32"):
            try:
                os.chdir("win")
                args = [self.init_script, "&", "nmake", "/f", "makefile.vc", "release"]
                if self.mode.name == "DEBUG":
                    args.append("OPTS=symbols")
                subprocess.run(args, check=True, capture_output=True)
                args = [
                    self.init_script,
                    "&",
                    "nmake",
                    "/f",
                    "makefile.vc",
                    "install",
                    f"INSTALLDIR={self.install_dir}",
                ]
                if self.mode.name == "DEBUG":
                    args.append("OPTS=symbols")
                subprocess.run(args, check=True, capture_output=True)
                if self.mode.name == "RELEASE":
                    self.force_copy(["bin", "tclsh86t.exe"], ["bin", "tclsh.exe"])
                    self.force_copy(["bin", "tcl86t.dll"], ["bin", "tcl86.dll"])
                    self.force_copy(["lib", "tcl86t.lib"], ["lib", "tcl86.lib"])
                else:
                    self.force_copy(["bin", "tclsh86tg.exe"], ["bin", "tclsh.exe"])
                    self.force_copy(["bin", "tcl86tg.dll"], ["bin", "tcl86.dll"])
                    self.force_copy(["lib", "tcl86tg.lib"], ["lib", "tcl86.lib"])
            except subprocess.CalledProcessError as e:
                print("ERROR: Failed to build tcl using nmake")
                print(e.stdout.decode("utf-8"))
                if e.stderr:
                    print(e.stderr.decode("utf-8"))
                exit(1)
        else:
            raise NotImplemented("Non-Windows compilation of tcl is not implemented yet")

    def build_tk(self, _=None):
        """tk does not use cMake"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "tk.h")):
                print("  Not rebuilding tk, it is already in the LibPack")
                return
        if sys.platform.startswith("win32"):
            try:
                os.chdir("win")
                args = [self.init_script, "&", "nmake", "/f", "makefile.vc", "release"]
                if self.mode.name == "DEBUG":
                    args.append("OPTS=symbols")
                subprocess.run(args, check=True, capture_output=True)
                args = [
                    self.init_script,
                    "&",
                    "nmake",
                    "/f",
                    "makefile.vc ",
                    "install",
                    f"INSTALLDIR={self.install_dir}",
                ]
                if self.mode.name == "DEBUG":
                    args.append("OPTS=symbols")
                subprocess.run(args, check=True, capture_output=True)
                if self.mode.name == "RELEASE":
                    self.force_copy(["bin", "wish86t.exe"], ["bin", "wish.exe"])
                    self.force_copy(["bin", "tk86t.dll"], ["bin", "tk86.dll"])
                    self.force_copy(["lib", "tk86t.lib"], ["lib", "tk86.lib"])
                else:
                    self.force_copy(["bin", "wish86tg.exe"], ["bin", "wish.exe"])
                    self.force_copy(["bin", "tk86tg.dll"], ["bin", "tk86.dll"])
                    self.force_copy(["lib", "tk86tg.lib"], ["lib", "tk86.lib"])
            except subprocess.CalledProcessError as e:
                print("ERROR: Failed to build tk using nmake")
                print(e.output.decode("utf-8"))
                if e.stderr:
                    print(e.stderr.decode("utf-8"))
                exit(1)
        else:
            raise NotImplemented("Non-Windows compilation of tk is not implemented yet")
