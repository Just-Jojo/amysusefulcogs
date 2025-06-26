# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from redbot import VersionInfo

__all__ = ("__author__", "__version__")


__author__: Final[str] = "Amy (jojo7791)"
__version__: VersionInfo = VersionInfo.from_json(
    {"major": 1, "minor": 0, "micro": 0, "releaselevel": "final", "serial": 0},
)

if not TYPE_CHECKING:
    del Final, VersionInfo
