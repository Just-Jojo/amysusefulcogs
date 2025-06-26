# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import functools
import logging
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional, Tuple, Type, Union

from redbot.core.bot import Red


__bot: Optional[Red] = None
__original_log: Callable = logging.Logger._log
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
    exc_info: Optional[_ExcInfoType] = ...,  # type:ignore
    extra: Optional[Dict[str, Any]] = ...,  # type:ignore
    stack_info: bool = ...,  # type:ignore
) -> None:
    __original_log(self, level, msg, args, exc_info, extra, stack_info)
    if TYPE_CHECKING:
        assert __bot is not None
    __bot.dispatch("logging", self.name, level, msg, args, exc_info)


def logging_setup(bot: Red) -> None:
    global __bot
    __bot = bot
    setattr(logging.Logger, "_log", _log)


def logging_teardown() -> None:
    if __bot is None:
        return
    setattr(logging.Logger, "_log", __original_log)
