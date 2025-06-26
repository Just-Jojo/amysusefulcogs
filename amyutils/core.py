# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import asyncio
import enum
import logging
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, TypedDict, TypeVar, Union

import discord
from discord.abc import Messageable
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from .constants import __author__, __version__
from .logging import _ArgsType, _ExcInfoType, logging_setup, logging_teardown
from .typing_fix import context_typing, messageable_typing

__all__ = ("AmyUtils",)


log = logging.getLogger("red.amysusefulcogs.amyutils")
ORIGINAL_MESSAGEABLE_TYPING = Messageable.typing
ORIGINAL_CONTEXT_TYPING = commands.Context.typing
T = TypeVar("T")
Requester = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class LoggingLevel(enum.Enum):
    DEBUG = 10
    INFO = 20
    WARN = WARNING = 30
    ERROR = 40
    CRITICAL = FATAL = 50
    NONE = -1


if TYPE_CHECKING:
    LoggingLevelConverter = LoggingLevel
else:

    class LoggingLevelConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, argument: str) -> LoggingLevel:
            arg = argument.upper()
            try:
                return getattr(LoggingLevel, arg)
            except Exception:
                raise commands.BadArgument from None


class ConfigStructure(TypedDict):
    typing: bool
    logging_enabled: bool
    logging_level: int
    log_channel_id: int


class SendingKwargs(TypedDict):
    """Kwargs so I can send using await ctx.send(**kwargs) and mypy won't complain"""

    content: Optional[str]
    embed: Optional[discord.Embed]


config_structure: ConfigStructure = {
    "typing": False, "logging_enabled": False, "logging_level": -1, "log_channel_id": 0,
}


def _settings_helper(
    data: Dict[str, Union[bool, str]], display: Union[discord.Embed, str]
) -> Union[discord.Embed, str]:
    for key, value in data.items():
        key = " ".join(char.capitalize() for char in key.split(" "))
        if isinstance(display, discord.Embed):
            display.add_field(name=key, value=value)
            continue
        display += f"**{key}:**\t{value}"
    return display


class AmyUtils(commands.Cog):
    """Some somewhat-helpful utilities for Red"""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**config_structure)

        self._cached_typing: bool = False
        self._logging_enabled: bool = False
        self._cached_level: LoggingLevel = LoggingLevel.NONE
        self._log_channel: Optional[discord.abc.Messageable] = None
        self._task: asyncio.Task[None] = self.bot.loop.create_task(self.start_up())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author:**\t{__author__}\n"
            f"**Version:**\t{__version__}"
        )

    async def red_delete_data_for_user(
        self, *, requester: Requester, user_id: int
    ) -> None:
        return
        super().red_delete_data_for_user

    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # I don't think this is ever gonna get implimented ;-;
        return {}

    async def cog_unload(self) -> None:
        self._task.cancel()
        # Not going to do an inverse, just in case I wanna do more stuff
        if self._cached_typing:
            setattr(Messageable, "typing", ORIGINAL_MESSAGEABLE_TYPING)
            setattr(commands.Context, "typing", ORIGINAL_CONTEXT_TYPING)
        if self._logging_enabled:
            logging_teardown()

    async def start_up(self) -> None:
        await self.bot.wait_until_red_ready()
        self._cached_typing = await self.config.typing()
        await self._patch_typing()
        self._logging_enabled = _l = await self.config.logging_enabled()
        if _l:
            logging_setup(self.bot)
        log_channel_id = await self.config.log_channel_id()
        if log_channel_id:
            try:
                self._log_channel = await self.bot.fetch_channel(log_channel_id)  # type:ignore
            except discord.DiscordException:
                pass
        self._cached_level = LoggingLevel(await self.config.logging_level())

    async def cog_check(self, ctx: commands.Context) -> bool:  # type:ignore
        return await ctx.bot.is_owner(ctx.author)

    @commands.group(name="amyutils", invoke_without_command=True)
    async def amy_utils(self, ctx: commands.Context) -> None:
        """Base command for Amy's utility cog"""
        data = await self.config.all()
        sender: Union[discord.Embed, str]
        if await ctx.embed_requested():
            sender = discord.Embed(
                title="Settings for Amy's Utils",
                colour=await ctx.embed_colour(),
            )
            sender.set_footer(text=f"Amy's Utils - Version {__version__}")
        else:
            sender = "# Settings for Amy's Utils\n"
        sender = _settings_helper(data, sender)
        kwargs: SendingKwargs
        if isinstance(sender, str):
            sender += f"\n\n-# Amy's Utils - Version {__version__}"
            kwargs = {"content": sender, "embed": None}
        else:
            kwargs = {"content": None, "embed": sender}
        await ctx.send(**kwargs)
        await ctx.send_help()

    @amy_utils.command(name="logging")
    async def amy_utils_logging(self, ctx: commands.Context) -> None:
        """Sets logging to be sent to a discord channel (on specific levels)

        At some point this will also allow you to customize the
        cogs and the levels of different loggers.
        I only recommend to have this on info as debug may be a bit too much
        """
        self._logging_enabled ^= True
        await self.config.logging_enabled.set(self._logging_enabled)
        await ctx.tick()

    @amy_utils.command(name="logginglevel")
    async def logging_level(self, ctx: commands.Context, level: LoggingLevel) -> None:
        """Set level to watch for to send to the log channel"""
        await self.config.logging_level.set(level.value)
        self._cached_level = level
        await ctx.send(f"Logging level is now set to {level.name.capitalize()}")

    @amy_utils.command(name="patchtyping")
    async def patch_typing(self, ctx: commands.Context) -> None:
        """Patch typing to not error if discord fucks up

        This will log if/when it breaks and why
        """
        self._cached_typing ^= True
        await self.config.typing.set(self._cached_typing)
        enabled = "enabled" if self._cached_typing else "disabled"
        await ctx.send(f"The typing patch is now {enabled}")
        await self._patch_typing()

    async def _patch_typing(self) -> None:
        if self._cached_typing:
            m_coro = messageable_typing
            c_coro = context_typing
            log.debug("Patching typing")
        else:
            m_coro = ORIGINAL_MESSAGEABLE_TYPING  # type:ignore
            c_coro = ORIGINAL_CONTEXT_TYPING  # type:ignore
            log.debug("Removing patching from typing")
        setattr(Messageable, "typing", m_coro)
        setattr(commands.Context, "typing", c_coro)

    @commands.Cog.listener()
    async def on_logging(
        self, name: str, level: int, msg: Any, args: _ArgsType, exc_info: Optional[_ExcInfoType]
    ) -> None:
        if not self._logging_enabled:
            return
        if not self._log_channel:
            return
        if not name.startswith("red"):
            # TODO Maybe add some stuff for discord and other things
            return
        if self._cached_level is LoggingLevel.NONE or level != self._cached_level:
            return
        display_name = " ".join(_.capitalize() for _ in list(name.split("."))[1:])
        kwargs: SendingKwargs
        if await self.bot.embed_requested(self._log_channel):  # type:ignore
            embed = discord.Embed(title=display_name, description=msg)
            if exc_info:
                embed.add_field(
                    name="Exception, see your logs for more", value=exc_info.__class__.__name__
                )
            embed.set_footer(text="Amy's Utils")
            kwargs = {"content": None, "embed": embed}
        else:
            content = (
                f"**{display_name}**\n\n"
                f"{box(msg)}\n\n"
            )
            if exc_info:
                content += (
                    f"**Exception, see your logs for more**  {exc_info.__class__.__name__}\n\n"
                )
            content += "-# Amy's Utils"
            kwargs = {"content": content, "embed": None}
        await self._log_channel.send(**kwargs)  # type:ignore
