#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Builder mixins for compile_all."""

from .boost import BoostBuilder
from .cam import CamBuilder
from .coin import CoinBuilder
from .compression import CompressionBuilder
from .med import MedBuilder
from .misc import MiscBuilder
from .occt import OcctBuilder
from .python import PythonBuilder
from .qt import QtBuilder
from .rendering import RenderingBuilder
from .swig import SwigBuilder
from .tcl import TclBuilder
from .testing import TestingBuilder

__all__ = [
    "BoostBuilder",
    "CamBuilder",
    "CoinBuilder",
    "CompressionBuilder",
    "MedBuilder",
    "MiscBuilder",
    "OcctBuilder",
    "PythonBuilder",
    "QtBuilder",
    "RenderingBuilder",
    "SwigBuilder",
    "TclBuilder",
    "TestingBuilder",
]
