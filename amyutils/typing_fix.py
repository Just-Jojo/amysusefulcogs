# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.abc import Messageable
from discord.context_managers import Typing as DPYTyping
from discord.ext.commands.context import DeferTyping as DPYDeferTyping
from redbot.core import commands

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional, Type, TypeVar, Union

    from discord.ext.commands._types import BotT

    BE = TypeVar("BE", bound="BaseException")

    wraps = lambda t: t  # noqa

else:
    from functools import wraps


__all__ = ("Typing",)

log = logging.getLogger("red.amyscogs.amyutils.typing")


class Typing(DPYTyping):
    @wraps(DPYTyping.wrapped_typer)
    async def wrapped_typer(self) -> None:  # type:ignore
        try:
            await super().wrapped_typer()
        except discord.HTTPException as exc:
            log.debug("Ignoring error in `typing.wrapped_typer`", exc_info=exc)

    @wraps(DPYTyping.__aenter__)
    async def __aenter__(self) -> None:
        try:
            await super().__aenter__()
        except discord.HTTPException as exc:
            log.debug("Ignoring error in `typing.__aenter__`", exc_info=exc)

    @wraps(DPYTyping.__aexit__)
    async def __aexit__(
        self, exc_type: Optional[Type[BE]], exc: Optional[BE], traceback: Optional[TracebackType]
    ) -> None:
        try:
            self.task.cancel()
        except Exception as try_exc:
            log.debug("Ignoring error in `typing.__aexit__`", exc_info=try_exc)


class DeferTyping(DPYDeferTyping[BotT]):
    async def do_defer(self) -> None:
        try:
            await super().do_defer()
        except discord.HTTPException as exc:
            log.debug("Ignoring exception in `do_defer`", exc_info=exc)


@wraps(commands.Context.typing)
def context_typing(
    self: commands.Context, *, ephemeral: bool = False
) -> Union[Typing, DeferTyping[BotT]]:
    if self.interaction is None:
        return Typing(self)
    return DeferTyping(self, ephemeral=ephemeral)


@wraps(Messageable.typing)
def messageable_typing(self: Messageable) -> Typing:
    return Typing(self)
