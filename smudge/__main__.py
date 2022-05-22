# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2021-2022 Luiz Renato (ruizlenato@protonmail.com)
import sys
import asyncio
import logging

from pyrogram import idle, __version__ as pyrogram_version

from rich.panel import Panel
from rich import box, print
from rich.logging import RichHandler

from .smudge import Smudge
from smudge.utils import http
from smudge.database import database

# Custom logging format
logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s | %(message)s",
    handlers=[RichHandler(rich_tracebacks=True, log_time_format="%m/%d %H:%M:%S")],
)

# To avoid some annoying log
logging.getLogger("spotipy.client").setLevel(logging.ERROR)
log = logging.getLogger("rich")

logs = "[bold purple]SmudgeLord[/bold purple]"
logs += "\n[cyan]Project maintained by:[/cyan] RuizLenato"
logs += f"\n[yellow]Pyrogram Version:[/yellow] {pyrogram_version}"
print(Panel.fit(logs, border_style="turquoise2", box=box.ASCII))


async def main():
    smudge = Smudge()

    try:
        # start the bot
        await database.connect()
        await smudge.start()

        if "justtest" not in sys.argv:
            await idle()
    except KeyboardInterrupt:
        # exit gracefully
        print("[red]Forced stop... Bye!")
    finally:
        # close https connections and the DB if open
        await smudge.stop()
        await http.aclose()
        if database.is_connected:
            await database.close()


if __name__ == "__main__":
    # open new asyncio event loop
    event_policy = asyncio.get_event_loop_policy()
    event_loop = event_policy.new_event_loop()
    asyncio.set_event_loop(event_loop)

    # start the bot
    event_loop.run_until_complete(main())

    # close asyncio event loop
    event_loop.close()
