# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2021-2022 Luiz Renato (ruizlenato@proton.me)
import os
import shutil
import asyncio
import tempfile

from PIL import Image

from ..bot import Smudge
from ..config import CHAT_LOGS
from ..utils import EMOJI_PATTERN, http
from ..locales import tld

from pyrogram import filters
from pyrogram.helpers import ikb
from pyrogram.errors import PeerIdInvalid, StickersetInvalid
from pyrogram.enums import MessageMediaType, MessageEntityType
from pyrogram.raw.functions.messages import GetStickerSet, SendMedia
from pyrogram.raw.functions.stickers import AddStickerToSet, CreateStickerSet
from pyrogram.types import Message
from pyrogram.raw.types import (
    DocumentAttributeFilename,
    InputDocument,
    InputMediaUploadedDocument,
    InputStickerSetItem,
    InputStickerSetShortName,
)


@Smudge.on_message(filters.command("getsticker"))
async def getsticker(c: Smudge, m: Message):
    try:
        sticker = m.reply_to_message.sticker
    except AttributeError:
        return await m.reply_text(await tld(m, "Stickers.getsticker_no_reply"))

    if sticker.is_video:
        with tempfile.TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, "getsticker")
        sticker_file = await c.download_media(
            message=m.reply_to_message, file_name=f"{path}/{sticker.set_name}.gif"
        )
    elif sticker.is_animated:
        await m.reply_text(await tld(m, "Stickers.animated_unsupported"))
        return

    else:
        with tempfile.TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, "getsticker")
        sticker_file = await c.download_media(
            message=m.reply_to_message, file_name=f"{path}/{sticker.set_name}.png"
        )

    await m.reply_to_message.reply_document(
        document=sticker_file,
        caption=(await tld(m, "Stickers.info_sticker")).format(
            sticker.emoji, sticker.file_id
        ),
    )
    shutil.rmtree(tempdir, ignore_errors=True)


@Smudge.on_message(filters.command("kang"))
async def kang_sticker(c: Smudge, m: Message):
    prog_msg = await m.reply_text(await tld(m, "Stickers.kanging"))
    sticker_emoji = "🤔"
    packnum = 0
    packname_found = False
    resize = False
    animated = False
    videos = False
    convert = False
    reply = m.reply_to_message
    user = await c.resolve_peer(m.from_user.username or m.from_user.id)

    if reply and reply.media:
        if reply.photo:
            resize = True

        elif reply.video or reply.animation:
            convert = True
            videos = True

        elif reply.document:
            if "image" in reply.document.mime_type:
                # mime_type: image/webp
                resize = True

            elif reply.document.mime_type in (
                MessageMediaType.VIDEO,
                MessageMediaType.ANIMATION,
            ):
                # mime_type: application/video
                videos = True
                convert = True
            elif "tgsticker" in reply.document.mime_type:
                # mime_type: application/x-tgsticker
                animated = True
        elif reply.sticker:
            if not reply.sticker.file_name:
                return await prog_msg.edit_text(
                    await tld(m, "Stickers.err_no_file_name")
                )
            if reply.sticker.emoji:
                sticker_emoji = reply.sticker.emoji
            animated = reply.sticker.is_animated
            videos = reply.sticker.is_video
            if videos:
                convert = False
            elif not reply.sticker.file_name.endswith(".tgs"):
                resize = True
        else:
            return await prog_msg.edit_text(
                await tld(m, "Stickers.invalid_media_string")
            )

        pack_prefix = "anim" if animated else "vid" if videos else "a"
        packname = f"{pack_prefix}_{m.from_user.id}_by_{c.me.username}"

        if len(m.command) > 1 and m.command[1].isdigit() and int(m.command[1]) > 0:
            # provide pack number to kang in desired pack
            packnum = m.command.pop(1)
            packname = f"{pack_prefix}{packnum}_{m.from_user.id}_by_{c.me.username}"
        if len(m.command) > 1:
            # matches all valid emojis in input
            sticker_emoji = (
                "".join(set(EMOJI_PATTERN.findall("".join(m.command[1:]))))
                or sticker_emoji
            )
        filename = await c.download_media(m.reply_to_message)
        if not filename:
            # Failed to download
            await prog_msg.delete()
            return
    else:
        return await prog_msg.edit_text(await tld(m, "Stickers.kang_noreply"))

    try:
        if resize:
            filename = resize_image(filename)
        elif convert:
            filename = await convert_video(filename)
            if filename is False:
                return await prog_msg.edit_text("Error")
        max_stickers = 50 if animated else 120
        while not packname_found:
            try:
                stickerset = await c.invoke(
                    GetStickerSet(
                        stickerset=InputStickerSetShortName(short_name=packname),
                        hash=0,
                    )
                )
                if stickerset.set.count >= max_stickers:
                    packnum += 1
                    packname = (
                        f"{pack_prefix}_{packnum}_{m.from_user.id}_by_{c.me.username}"
                    )
                else:
                    packname_found = True
            except StickersetInvalid:
                break
        file = await c.save_file(filename)
        media = await c.invoke(
            SendMedia(
                peer=(await c.resolve_peer(CHAT_LOGS)),
                media=InputMediaUploadedDocument(
                    file=file,
                    mime_type=c.guess_mime_type(filename),
                    attributes=[DocumentAttributeFilename(file_name=filename)],
                ),
                message=f"#Sticker kang by UserID -> {m.from_user.id}",
                random_id=c.rnd_id(),
            ),
        )
        msg_ = media.updates[-1].message
        stkr_file = msg_.media.document
        if packname_found:
            await prog_msg.edit_text(await tld(m, "Stickers.use_existing_pack"))
            await c.invoke(
                AddStickerToSet(
                    stickerset=InputStickerSetShortName(short_name=packname),
                    sticker=InputStickerSetItem(
                        document=InputDocument(
                            id=stkr_file.id,
                            access_hash=stkr_file.access_hash,
                            file_reference=stkr_file.file_reference,
                        ),
                        emoji=sticker_emoji,
                    ),
                )
            )
        else:
            await prog_msg.edit_text(await tld(m, "Stickers.create_new_pack_string"))
            try:
                stkr_title = f"@{m.from_user.username[:32]}'s SmudgePack"
            except TypeError:
                stkr_title = f"@{m.from_user.first_name[:32]}'s SmudgePack"
            if animated:
                stkr_title += " Anim"
            elif videos:
                stkr_title += " Vid"
            if packnum != 0:
                stkr_title += f" v{packnum}"
            try:
                await c.invoke(
                    CreateStickerSet(
                        user_id=user,
                        title=stkr_title,
                        short_name=packname,
                        stickers=[
                            InputStickerSetItem(
                                document=InputDocument(
                                    id=stkr_file.id,
                                    access_hash=stkr_file.access_hash,
                                    file_reference=stkr_file.file_reference,
                                ),
                                emoji=sticker_emoji,
                            )
                        ],
                        animated=animated,
                        videos=videos,
                    )
                )
            except PeerIdInvalid:
                return await prog_msg.edit_text(
                    await tld(m, "Stickers.pack_contact_pm"),
                    reply_markup=ikb(
                        [
                            [
                                (
                                    await tld(m, "Main.start"),
                                    f"https://t.me/{c.me.username}?start",
                                    "url",
                                )
                            ]
                        ]
                    ),
                )

    except Exception as all_e:
        await prog_msg.edit_text(f"{all_e.__class__.__name__} : {all_e}")
    else:
        await prog_msg.edit_text(
            (await tld(m, "Stickers.kanged_string")).format(packname, sticker_emoji)
        )
        # Cleanup
        await c.delete_messages(chat_id=CHAT_LOGS, message_ids=msg_.id, revoke=True)
        try:
            os.remove(filename)
        except OSError:
            pass


def resize_image(filename: str) -> str:
    im = Image.open(filename)
    maxsize = 512
    scale = maxsize / max(im.width, im.height)
    sizenew = (int(im.width * scale), int(im.height * scale))
    im = im.resize(sizenew, Image.NEAREST)
    downpath, f_name = os.path.split(filename)
    # not hardcoding png_image as "sticker.png"
    png_image = os.path.join(downpath, f"{f_name.split('.', 1)[0]}.png")
    im.save(png_image, "PNG")
    if png_image != filename:
        os.remove(filename)
    return png_image


async def convert_video(filename: str) -> str:
    downpath, f_name = os.path.split(filename)
    webm_video = os.path.join(downpath, f"{f_name.split('.', 1)[0]}.webm")
    cmd = [
        "ffmpeg",
        "-loglevel",
        "quiet",
        "-i",
        filename,
        "-t",
        "00:00:03",
        "-vf",
        "fps=30",
        "-c:v",
        "vp9",
        "-b:v:",
        "500k",
        "-preset",
        "ultrafast",
        "-s",
        "512x512",
        "-y",
        "-an",
        webm_video,
    ]

    proc = await asyncio.create_subprocess_exec(*cmd)
    # Wait for the subprocess to finish
    await proc.communicate()

    if webm_video != filename:
        os.remove(filename)
    return webm_video


__help__ = "Stickers"
plugin_name = "Stickers.name"
plugin_help = "Stickers.help"
