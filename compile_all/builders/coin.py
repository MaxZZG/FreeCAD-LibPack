#!/bin/python3

# SPDX-License-Identifier: LGPL-2.1-or-later

"""Coin and Quarter build methods."""

import os


class CoinBuilder:
    """Mixin for building Coin and Quarter."""

    def build_coin(self, _=None):
        """Builds and installs Coin using standard CMake settings"""
        if self.skip_existing:
            self._configure_coin_cmake_path()
            if self.coin_cmake_path is not None:
                print("  Not rebuilding Coin, it is already in the LibPack")
                return
        extra_args = ["-D COIN_BUILD_TESTS=Off"]
        self._build_standard_cmake(extra_args)
        self._configure_coin_cmake_path()

    def _configure_coin_cmake_path(self):
        """Coin installs its cMake file into a directory named with the full version, so figure out what that is"""
        start_crawl_at = os.path.join(self.install_dir, "lib", "cmake")
        contents = [
            f for f in os.listdir(start_crawl_at) if os.path.isdir(os.path.join(start_crawl_at, f))
        ]
        for item in contents:
            if item.startswith("Coin"):
                self.coin_cmake_path = os.path.join(start_crawl_at, item)
                break

    def build_quarter(self, _=None):
        """Builds and installs Quarter using standard CMake settings"""
        if self.skip_existing:
            if os.path.exists(os.path.join(self.install_dir, "include", "Quarter")):
                print("  Not rebuilding Quarter, it is already in the LibPack")
                return
        extra_args = [
            "-D QUARTER_BUILD_EXAMPLES=Off",
            "-D QUARTER_USE_QT5=Off",
            "-D QUARTER_USE_QT6=On",
        ]
        self._build_standard_cmake(extra_args=extra_args)
