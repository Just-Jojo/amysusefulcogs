# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import functools
import logging
from types import TracebackType
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Type, Union

from redbot.core.bot import Red

__bot: Optional[Red] = None
__original_log: Callable[Any, Any] = logging.Logger._log
_SysExcInfoType = Union[
    Tuple[Type[BaseException], BaseException, TracebackType, None], Tuple[None, None, None]
]
_ExcInfoType = Union[None, bool, _SysExcInfoType, BaseException]
_ArgsType = Union[Tuple[object, ...], Mapping[str, object]]


@functools.wraps(__original_log)
def _log(
    self,
    level: int,
    msg: Any,
    args: _ArgsType,
    exc_info: Optional[_ExcInfoType] = ...,
    extra: Optional[Dict[str, Any]] = ...,
    stack_info: bool = ...,
) -> None:
    __original_log(self, level, msg, args, exc_info, extra, stack_info)
    __bot.dispatch("logging", self.name, level, msg, args, exc_info)


def logging_setup(bot: Red) -> None:
    global __bot
    __bot = bot
    setattr(logging.Logger, "_log", _log)


def logging_teardown() -> None:
    if __bot is None:
        return
    setattr(logging.Logger, "_log", __original_log)
