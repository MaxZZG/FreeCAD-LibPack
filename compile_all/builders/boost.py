#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Boost build methods."""

import os
import platform
import sys


class BoostBuilder:
    """Mixin for building Boost."""

    def build_boost(self, _=None):
        if self.skip_existing:
            start_crawl_at = os.path.join(self.install_dir, "include")
            contents = [
                f
                for f in os.listdir(start_crawl_at)
                if os.path.isdir(os.path.join(start_crawl_at, f))
            ]
            for item in contents:
                if item.startswith("boost"):
                    print("  Not rebuilding boost, it is already in the LibPack")
                    return
        extra_args = [
            "-D BOOST_INSTALL_LAYOUT=versioned",
            "-D BOOST_ENABLE_CMAKE=ON",
            "-D BOOST_EXCLUDE_LIBRARIES='mpi;graph_parallel;coroutine'",
            "-D BOOST_ENABLE_PYTHON=ON",
            "-D BOOST_LOCALE_ENABLE_ICU=OFF",
        ]
        if platform.machine() == "ARM64" and sys.platform == "win32":
            print(
                "  (NOTE: For Windows-on-ARM, Boost is being configured to use Windows Fibers in boost::context)"
            )
            extra_args.append("-D BOOST_CONTEXT_IMPLEMENTATION=winfib")
        self._build_standard_cmake(extra_args)
        self._configure_boost_version()

    def _configure_boost_version(self):
        """Once Boost has been installed, figure out what version it was and set up the correct include path"""
        start_crawl_at = os.path.join(self.install_dir, "include")
        contents = [
            f for f in os.listdir(start_crawl_at) if os.path.isdir(os.path.join(start_crawl_at, f))
        ]
        for item in contents:
            if item.startswith("boost"):
                self.boost_include_path = os.path.join(start_crawl_at, item)
                break
