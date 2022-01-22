import asyncio
import logging
import aiocron
import datetime

from pyrogram import Client, idle

from rich.panel import Panel
from rich import box, print as rprint

from tortoise import run_async, Tortoise

from smudge.config import *
from smudge.database import connect_database

# Date
date = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(message)s", level="INFO")
logging.getLogger("pyrogram.client").setLevel(logging.WARNING)

log = logging.getLogger("rich")
logs = "[bold purple]SmudgeLord Running[/bold purple]"
logs += f"\n[SmudgeLord] Project maintained by: Renatoh"
rprint(Panel.fit(logs, border_style="turquoise2", box=box.ASCII))

# Pyrogram Client
plugins = dict(root="smudge.plugins")
client = Client(
    "smudge",
    workers=20,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode="html",
    plugins=plugins,
)


async def main():
    await client.start()
    print(f"[SmudgeLord] Starting...\nDate: {date}")
    await connect_database()
    await client.send_message(
        chat_id=CHAT_LOGS,
        text="<b>SmudgeLord started!</b>\n<b>Date:</b> {}".format(date),
    )

    @aiocron.crontab("*/60 * * * *")
    async def backup() -> None:
        await client.send_document(
            CHAT_LOGS,
            "smudge/database/database.db",
            caption="<b>Database backuped!</b>\n<b>- Date:</b> {}".format(date),
        )
        logging.warning("[SmudgeLord] Database backuped!")

    await idle()
    await client.stop()


if __name__ == "__main__":
    asyncio.create_task(run_async(main()))
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        asyncio.create_task(Tortoise.close_connections())
        loop.close()
