#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""
compile_all - Build system for FreeCAD LibPack.

This package provides the Compiler class for building all dependencies
in the FreeCAD LibPack.
"""

from .base import CompilerBase
from .builders import (
    BoostBuilder,
    CamBuilder,
    CoinBuilder,
    CompressionBuilder,
    MedBuilder,
    MiscBuilder,
    OcctBuilder,
    PythonBuilder,
    QtBuilder,
    RenderingBuilder,
    SwigBuilder,
    TclBuilder,
    TestingBuilder,
)
from .core import (
    BuildMode,
    apply_patch,
    libpack_dir,
    patch_files,
    remove_readonly,
    to_dynamic,
    to_exe,
    to_static,
)


class Compiler(
    PythonBuilder,
    QtBuilder,
    CoinBuilder,
    BoostBuilder,
    CompressionBuilder,
    SwigBuilder,
    RenderingBuilder,
    TclBuilder,
    OcctBuilder,
    MedBuilder,
    MiscBuilder,
    CamBuilder,
    TestingBuilder,
    CompilerBase,
):
    """
    Main compiler class that combines all package builders.

    Inherits from all builder mixins and CompilerBase to provide
    a complete build system for FreeCAD LibPack dependencies.
    """

    pass


__all__ = [
    "BuildMode",
    "Compiler",
    "apply_patch",
    "libpack_dir",
    "patch_files",
    "remove_readonly",
    "to_dynamic",
    "to_exe",
    "to_static",
]
