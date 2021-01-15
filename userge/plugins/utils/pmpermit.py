""" setup auto pm message """

# Copyright (C) 2020 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/uaudith/Userge/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from typing import Dict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import BotInlineDisabled

from userge import userge, filters, Message, Config, get_collection
from userge.utils import SafeDict

CHANNEL = userge.getCLogger(__name__)
SAVED_SETTINGS = get_collection("CONFIGS")
ALLOWED_COLLECTION = get_collection("PM_PERMIT")

pmCounter: Dict[int, int] = {}
_IS_INLINE = True
allowAllFilter = filters.create(lambda _, __, ___: Config.ALLOW_ALL_PMS)
noPmMessage = bk_noPmMessage = ("**-ID**\n"
                                "Halo 😁 {flname} ({uname}). ini adalah pesan otomatis \ n "
                                "Harap tunggu sampai Anda disetujui untuk mengirim pesan langsung \ n"
                                "Dan tolong jangan ** SPAM ** sampai saat itu\n"
                               "\n"
                                "**-EN**\n"
                               "Hello 😁 {flname} ({uname}). this is an automated message\n"
                               "Please wait until you get approved to direct message\n "
                               "And please dont **SPAM** until then\n ")
blocked_message = bk_blocked_message = "**-ID**\nAnda diblokir secara otomatis\n**-EN**\nYou were automatically blocked"


async def _init() -> None:
    global noPmMessage, blocked_message, _IS_INLINE  # pylint: disable=global-statement
    async for chat in ALLOWED_COLLECTION.find({"status": 'allowed'}):
        Config.ALLOWED_CHATS.add(chat.get("_id"))
    _pm = await SAVED_SETTINGS.find_one({'_id': 'STATUS PENJAGA PM'})
    if _pm:
        Config.ALLOW_ALL_PMS = bool(_pm.get('data'))
    i_pm = await SAVED_SETTINGS.find_one({'_id': 'INLINE_PM_PERMIT'})
    if i_pm:
        _IS_INLINE = bool(i_pm.get('data'))
    _pmMsg = await SAVED_SETTINGS.find_one({'_id': 'PESAN CUSTOM NOPM'})
    if _pmMsg:
        noPmMessage = _pmMsg.get('data')
    _blockPmMsg = await SAVED_SETTINGS.find_one({'_id': 'PESAN CUSTOM BLOCKPM'})
    if _blockPmMsg:
        blocked_message = _blockPmMsg.get('data')


@userge.on_cmd("allow", about={
    'header': "memungkinkan seseorang untuk menghubungi",
    'description': "Seseorang diizinkan, "
                   "Userge tidak akan mengganggu atau menangani obrolan pribadi semacam itu",
    'usage': "{tr}allow [username | userID]\nreply {tr}allow ke sebuah pesan, "
             "do {tr}allow in the private chat"}, allow_channels=False, allow_via_bot=False)
async def allow(message: Message):
    """ allows to pm """
    userid = await get_id(message)
    if userid:
        if userid in pmCounter:
            del pmCounter[userid]
        Config.ALLOWED_CHATS.add(userid)
        a = await ALLOWED_COLLECTION.update_one(
            {'_id': userid}, {"$set": {'status': 'allowed'}}, upsert=True)
        if a.matched_count:
            await message.edit("`Sudah disetujui untuk mengirim pesan langsung`", del_in=3)
        else:
            await (await userge.get_users(userid)).unblock()
            await message.edit("`Disetujui untuk mengirim pesan langsung`", del_in=3)
    else:
        await message.edit(
            "Saya perlu membalas ke pengguna atau memberikan nama pengguna / id atau berada dalam obrolan pribadi",
            del_in=3)


@userge.on_cmd("nopm", about={
    'header': "Mengaktifkan penjagaan di kotak masuk",
    'description': "Seseorang diizinkan, "
                   "Userge tidak akan mengganggu atau menangani obrolan pribadi semacam itu",
    'usage': "{tr}nopm [username | userID]\nbalasan {tr}nopm ke sebuah pesan, "
             "do {tr}nopm in the private chat"}, allow_channels=False, allow_via_bot=False)
async def denyToPm(message: Message):
    """ disallows to pm """
    userid = await get_id(message)
    if userid:
        if userid in Config.ALLOWED_CHATS:
            Config.ALLOWED_CHATS.remove(userid)
        a = await ALLOWED_COLLECTION.delete_one({'_id': userid})
        if a.deleted_count:
            await message.edit("`Dilarang mengirim pesan langsung`", del_in=3)
        else:
            await message.edit("`Tidak ada yang berubah`", del_in=3)
    else:
        await message.edit(
            "Saya perlu membalas ke pengguna atau memberikan nama pengguna / id atau berada dalam obrolan pribadi",
            del_in=3)


async def get_id(message: Message):
    userid = None
    if message.chat.type in ['private', 'bot']:
        userid = message.chat.id
    if message.reply_to_message:
        userid = message.reply_to_message.from_user.id
    if message.input_str:
        user = message.input_str.lstrip('@')
        try:
            userid = (await userge.get_users(user)).id
        except Exception as e:
            await message.err(str(e))
    return userid


@userge.on_cmd(
    "pmguard", about={
        'header': "Mengaktifkan modul izin pm",
        'description': "Ini dimatikan secara default. "
                       "Anda dapat mengaktifkan atau menonaktifkan pmguard dengan perintah ini. "
                       "Saat Anda mengaktifkannya lain kali, "
                       "obrolan yang sebelumnya diizinkan akan ada di sana !"},
    allow_channels=False)
async def pmguard(message: Message):
    """ enable or disable auto pm handler """
    global pmCounter  # pylint: disable=global-statement
    if Config.ALLOW_ALL_PMS:
        Config.ALLOW_ALL_PMS = False
        await message.edit("`PM_guard diaktifkan`", del_in=3, log=__name__)
    else:
        Config.ALLOW_ALL_PMS = True
        await message.edit("`PM_guard dinonaktifkan`", del_in=3, log=__name__)
        pmCounter.clear()
    await SAVED_SETTINGS.update_one(
        {'_id': 'PM GUARD STATUS'}, {"$set": {'data': Config.ALLOW_ALL_PMS}}, upsert=True)


@userge.on_cmd(
    "ipmguard", about={
        'header': "Mengaktifkan modul izin pm Inline",
        'description': "Ini dimatikan secara default.",
        'usage': "{tr}ipmguard"},
    allow_channels=False)
async def ipmguard(message: Message):
    """ enable or disable inline pmpermit """
    global _IS_INLINE  # pylint: disable=global-statement
    if _IS_INLINE:
        _IS_INLINE = False
        await message.edit("`Inline PM_guard dinonaktifkan`", del_in=3, log=__name__)
    else:
        _IS_INLINE = True
        await message.edit("`Inline PM_guard diaktifkan`", del_in=3, log=__name__)
    await SAVED_SETTINGS.update_one(
        {'_id': 'INLINE_PM_PERMIT'}, {"$set": {'data': _IS_INLINE}}, upsert=True)


@userge.on_cmd("setpmmsg", about={
    'header': "Mengatur pesan balasan",
    'description': "Anda dapat mengubah pesan default yang diberikan userge pada PM yang tidak diundang",
    'flags': {'-r': "reset ke default"},
    'options': {
        '{fname}': "tambahkan nama depan",
        '{lname}': "tambahkan nama belakang",
        '{flname}': "tambahkan nama lengkap",
        '{uname}': "nama pengguna",
        '{chat}': "nama obrolan",
        '{mention}': "sebutkan pengguna"}}, allow_channels=False)
async def set_custom_nopm_message(message: Message):
    """ setup custom pm message """
    global noPmMessage  # pylint: disable=global-statement
    if '-r' in message.flags:
        await message.edit('`Atur ulang pesan NOpm kustom`', del_in=3, log=True)
        noPmMessage = bk_noPmMessage
        await SAVED_SETTINGS.find_one_and_delete({'_id': 'PESAN CUSTOM NOPM'})
    else:
        string = message.input_or_reply_raw
        if string:
            await message.edit('`Pesan NOpm kustom disimpan`', del_in=3, log=True)
            noPmMessage = string
            await SAVED_SETTINGS.update_one(
                {'_id': 'PESAN CUSTOM NOPM'}, {"$set": {'data': string}}, upsert=True)
        else:
            await message.err("invalid input!")


@userge.on_cmd("ipmmsg", about={
    'header': "Set inline pm msg for Inline pmpermit",
    'usage': "{tr}ipmmsg [text | reply to text msg]"}, allow_channels=False)
async def change_inline_message(message: Message):
    """ set inline pm message """
    string = message.input_or_reply_raw
    if string:
        await message.edit('`Custom inline pm message saved`', del_in=3, log=True)
        await SAVED_SETTINGS.update_one(
            {'_id': 'CUSTOM_INLINE_PM_MESSAGE'}, {"$set": {'data': string}}, upsert=True)
    else:
        await message.err("invalid input!")


@userge.on_cmd("setbpmmsg", about={
    'header': "Mengatur pesan blok",
    'description': "Anda dapat mengubah pesan default blockPm"
                    "yang diberikan pengguna pada PM yang tidak diundang",
    'flags': {'-r': "reset ke default"},
    'options': {
        '{fname}': "tambahkan nama depan",
        '{lname}': "tambahkan nama belakang",
        '{flname}': "tambahkan nama lengkap",
        '{uname}': "nama pengguna",
        '{chat}': "nama obrolan",
        '{mention}': "sebutkan pengguna"}}, allow_channels=False)
async def set_custom_blockpm_message(message: Message):
    """ setup custom blockpm message """
    global blocked_message  # pylint: disable=global-statement
    if '-r' in message.flags:
        await message.edit('`Custom BLOCKpm message reset`', del_in=3, log=True)
        blocked_message = bk_blocked_message
        await SAVED_SETTINGS.find_one_and_delete({'_id': 'PESAN CUSTOM BLOCKPM'})
    else:
        string = message.input_or_reply_raw
        if string:
            await message.edit('`Pesan BLOCKpm kustom disimpan`', del_in=3, log=True)
            blocked_message = string
            await SAVED_SETTINGS.update_one(
                {'_id': 'PESAN CUSTOM BLOCKPM'}, {"$set": {'data': string}}, upsert=True)
        else:
            await message.err("invalid input!")


@userge.on_cmd(
    "vpmmsg", about={
        'header': "Displays the reply message for uninvited PMs"},
    allow_channels=False)
async def view_current_noPM_msg(message: Message):
    """ view current pm message """
    await message.edit(f"--current PM message--\n\n{noPmMessage}")


@userge.on_cmd(
    "vbpmmsg", about={
        'header': "Displays the reply message for blocked PMs"},
    allow_channels=False)
async def view_current_blockPM_msg(message: Message):
    """ view current block pm message """
    await message.edit(f"--current blockPM message--\n\n{blocked_message}")


@userge.on_filters(~allowAllFilter & filters.incoming & filters.private & ~filters.bot
                   & ~filters.me & ~filters.service & ~Config.ALLOWED_CHATS, allow_via_bot=False)
async def uninvitedPmHandler(message: Message):
    """ pm message handler """
    user_dict = await userge.get_user_dict(message.from_user.id)
    user_dict.update({'chat': message.chat.title if message.chat.title else "this group"})
    if message.from_user.is_verified:
        return
    if message.from_user.id in pmCounter:
        if pmCounter[message.from_user.id] > 3:
            del pmCounter[message.from_user.id]
            await message.reply(
                blocked_message.format_map(SafeDict(**user_dict))
            )
            await message.from_user.block()
            await asyncio.sleep(1)
            await CHANNEL.log(
                f"#BLOCKED\n{user_dict['mention']} has been blocked due to spamming in pm !! ")
        else:
            pmCounter[message.from_user.id] += 1
            await message.reply(
                f"Kamu punya {pmCounter[message.from_user.id]} dari 4 ** Peringatan**\n"
                "Harap tunggu sampai Anda mendapatkan persetujuan untuk pm !", del_in=5)
    else:
        pmCounter.update({message.from_user.id: 1})
        if userge.has_bot and _IS_INLINE:
            try:
                bot_username = (await userge.bot.get_me()).username
                k = await userge.get_inline_bot_results(bot_username, "pmpermit")
                await userge.send_inline_bot_result(
                    message.chat.id, query_id=k.query_id,
                    result_id=k.results[2].id, hide_via=True
                )
            except BotInlineDisabled:
                await message.reply(
                    noPmMessage.format_map(SafeDict(**user_dict)) + '\n`- Protected by WillyamWillys`')
        else:
            await message.reply(
                noPmMessage.format_map(SafeDict(**user_dict)) + '\n`- Protected by WillyamWillys`')
        await asyncio.sleep(1)
        await CHANNEL.log(f"#NEW_MESSAGE\n{user_dict['mention']} has messaged you")


@userge.on_filters(~allowAllFilter & filters.outgoing & ~filters.edited
                   & filters.private & ~Config.ALLOWED_CHATS, allow_via_bot=False)
async def outgoing_auto_approve(message: Message):
    """ outgoing handler """
    userID = message.chat.id
    if userID in pmCounter:
        del pmCounter[userID]
    Config.ALLOWED_CHATS.add(userID)
    await ALLOWED_COLLECTION.update_one(
        {'_id': userID}, {"$set": {'status': 'allowed'}}, upsert=True)
    user_dict = await userge.get_user_dict(userID)
    await CHANNEL.log(f"**#AUTO_APPROVED**\n{user_dict['mention']}")

if userge.has_bot:
    @userge.bot.on_callback_query(filters.regex(pattern=r"pm_allow\((.+?)\)"))
    async def pm_callback_allow(_, c_q: CallbackQuery):
        owner = await userge.get_me()
        if c_q.from_user.id == owner.id:
            userID = int(c_q.matches[0].group(1))
            await userge.unblock_user(userID)
            user = await userge.get_users(userID)
            if userID in Config.ALLOWED_CHATS:
                await c_q.edit_message_text(
                    f"{user.mention} sudah diizinkan untuk Direct Message.")
            else:
                await c_q.edit_message_text(
                    f"{user.mention} allowed to Direct Messages.")
                await userge.send_message(
                    userID, f"{owner.mention} `menyetujui Anda untuk Direct Message.`")
                if userID in pmCounter:
                    del pmCounter[userID]
                Config.ALLOWED_CHATS.add(userID)
                await ALLOWED_COLLECTION.update_one(
                    {'_id': userID}, {"$set": {'status': 'allowed'}}, upsert=True)
        else:
            await c_q.answer(f"Hanya {owner.first_name} memiliki akses ke Izinkan.")

    @userge.bot.on_callback_query(filters.regex(pattern=r"pm_block\((.+?)\)"))
    async def pm_callback_block(_, c_q: CallbackQuery):
        owner = await userge.get_me()
        if c_q.from_user.id == owner.id:
            userID = int(c_q.matches[0].group(1))
            user_dict = await userge.get_user_dict(userID)
            await userge.send_message(
                userID, blocked_message.format_map(SafeDict(**user_dict)))
            await userge.block_user(userID)
            if userID in pmCounter:
                del pmCounter[userID]
            if userID in Config.ALLOWED_CHATS:
                Config.ALLOWED_CHATS.remove(userID)
            k = await ALLOWED_COLLECTION.delete_one({'_id': userID})
            user = await userge.get_users(userID)
            if k.deleted_count:
                await c_q.edit_message_text(
                    f"{user.mention} `Dilarang mengirim pesan langsung`")
            else:
                await c_q.edit_message_text(
                    f"{user.mention} `sudah Dilarang mengirim pesan langsung.`")
        else:
            await c_q.answer(f"Hanya {owner.first_name} memiliki akses ke Blokir.")

    @userge.bot.on_callback_query(filters.regex(pattern=r"^pm_spam$"))
    async def pm_spam_callback(_, c_q: CallbackQuery):
        owner = await userge.get_me()
        if c_q.from_user.id == owner.id:
            await c_q.answer("Maaf, Anda tidak dapat mengklik sendiri")
        else:
            del pmCounter[c_q.from_user.id]
            user_dict = await userge.get_user_dict(c_q.from_user.id)
            await c_q.edit_message_text(
                blocked_message.format_map(SafeDict(**user_dict)))
            await userge.block_user(c_q.from_user.id)
            await asyncio.sleep(1)
            await CHANNEL.log(
                f"#BLOCKED\n{c_q.from_user.mention} telah diblokir karena spamming di pm !! ")

    @userge.bot.on_callback_query(filters.regex(pattern=r"^pm_contact$"))
    async def pm_contact_callback(_, c_q: CallbackQuery):
        owner = await userge.get_me()
        if c_q.from_user.id == owner.id:
            await c_q.answer("Maaf, Anda tidak dapat mengklik sendiri")
        else:
            user_dict = await userge.get_user_dict(c_q.from_user.id)
            await c_q.edit_message_text(
                noPmMessage.format_map(SafeDict(**user_dict)) + '\n`- Protected by WillyamWillys`')
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Mengizinkan", callback_data=f"pm_allow({c_q.from_user.id})"),
                        InlineKeyboardButton(
                            text="Memblokir", callback_data=f"pm_block({c_q.from_user.id})")
                    ]
                ]
            )
            await userge.bot.send_message(
                owner.id,
                f"{c_q.from_user.mention} PESAN CUSTOM NOPM.",
                reply_markup=buttons
            )
