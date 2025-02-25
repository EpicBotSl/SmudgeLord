# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2021-2022 Luiz Renato (ruizlenato@proton.me)
import random

from ..bot import Smudge
from ..locales import tld

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden


@Smudge.on_message(filters.command("slap"))
async def slap(c: Smudge, m: Message):
    if m.reply_to_message:
        try:
            user1 = (
                f"<a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>"
            )
        except AttributeError:
            user1 = m.chat.title
        try:
            user2 = f"<a href='tg://user?id={m.reply_to_message.from_user.id}'>{m.reply_to_message.from_user.first_name}</a>"
        except AttributeError:
            user2 = m.chat.title

        temp = random.choice(await tld(m, "Memes.slaps_templates_list"))
        item = random.choice(await tld(m, "Memes.items_list"))
        hit = random.choice(await tld(m, "Memes.hit_list"))
        throw = random.choice(await tld(m, "Memes.throw_list"))

        reply = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

        await m.reply_text(reply)
    else:
        await m.reply_text("Bruuuh")


@Smudge.on_message(filters.regex(r"^framengo"))
async def framengo(c: Smudge, m: Message):
    try:
        await m.reply_video(video="https://telegra.ph/file/edead6d5de1df2eb2ab84.mp4")
    except ChatWriteForbidden:
        return


@Smudge.on_message(filters.regex(r"paysandu"))
async def paysandu(c: Smudge, m: Message):
    answer = random.choice(["yes", "no"])
    if answer != "yes":
        return
    try:
        await m.reply_audio(
            audio="CQACAgEAAx0CUYV5ZQACJEBi1xxZbiuqd3r96dG5RbePA6-hBgACOgIAAqa2uUatB5Ukvjck9R4E"
        )
    except ChatWriteForbidden:
        return
