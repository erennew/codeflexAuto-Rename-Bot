from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import codeflixbots
from config import Config
import asyncio
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Auto-delete delay in seconds
AUTO_DELETE_DELAY = 30

# Emoji constants
EMOJI = {
    'success': "✅",
    'error': "❌",
    'file': "📁",
    'points': "✨",
    'premium': "⭐"
}

async def auto_delete_message(message: Message, delay: int = AUTO_DELETE_DELAY):
    """Auto-delete message after delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Couldn't delete message: {e}")

async def send_response(
    client: Client,
    chat_id: int,
    text: str,
    reply_markup=None,
    photo=None,
    delete_after: int = AUTO_DELETE_DELAY,
    parse_mode: enums.ParseMode = enums.ParseMode.HTML
):
    """Enhanced response handler with auto-delete"""
    try:
        if photo:
            msg = await client.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            msg = await client.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        
        if delete_after:
            asyncio.create_task(auto_delete_message(msg, delete_after))
        return msg
    except Exception as e:
        logger.error(f"Response error: {e}")
        return None

@Client.on_message(filters.private & filters.command('set_caption'))
async def add_caption(client: Client, message: Message):
    """Set custom caption with validation"""
    if len(message.command) == 1:
        return await send_response(
            client,
            message.chat.id,
            "**Give me a caption**\n\nExample:\n`/set_caption 📕Name ➠ : {filename}\n\n🔗 Size ➠ : {filesize}\n\n⏰ Duration ➠ : {duration}`",
            delete_after=30
        )
    
    try:
        caption = message.text.split(" ", 1)[1]
        if len(caption) > 500:
            raise ValueError("Caption too long (max 500 characters)")
            
        await codeflixbots.set_caption(message.from_user.id, caption=caption)
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['success']} **Caption saved successfully!**",
            photo=Config.START_PIC,
            delete_after=30
        )
    except ValueError as e:
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} {str(e)}",
            delete_after=15
        )
    except Exception as e:
        logger.error(f"Set caption error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Failed to save caption",
            delete_after=15
        )

@Client.on_message(filters.private & filters.command('del_caption'))
async def delete_caption(client: Client, message: Message):
    """Delete user's caption"""
    try:
        old_caption = await codeflixbots.get_caption(message.from_user.id)
        if not old_caption:
            return await send_response(
                client,
                message.chat.id,
                f"{EMOJI['error']} **You don't have a caption set**",
                photo=Config.START_PIC,
                delete_after=15
            )
            
        await codeflixbots.set_caption(message.from_user.id, caption=None)
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['success']} **Caption deleted successfully!**",
            photo=Config.START_PIC,
            delete_after=30
        )
    except Exception as e:
        logger.error(f"Delete caption error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Failed to delete caption",
            delete_after=15
        )

@Client.on_message(filters.private & filters.command(['see_caption', 'view_caption']))
async def see_caption(client: Client, message: Message):
    """View user's current caption"""
    try:
        caption = await codeflixbots.get_caption(message.from_user.id)
        if caption:
            await send_response(
                client,
                message.chat.id,
                f"**Your current caption:**\n\n`{caption}`",
                photo=Config.START_PIC,
                delete_after=30
            )
        else:
            await send_response(
                client,
                message.chat.id,
                f"{EMOJI['error']} **You don't have a caption set**",
                photo=Config.START_PIC,
                delete_after=15
            )
    except Exception as e:
        logger.error(f"View caption error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Couldn't retrieve caption",
            delete_after=15
        )

@Client.on_message(filters.private & filters.command(['view_thumb', 'viewthumb']))
async def view_thumbnail(client: Client, message: Message):
    """View user's current thumbnail"""
    try:
        thumb = await codeflixbots.get_thumbnail(message.from_user.id)
        if thumb:
            msg = await client.send_photo(
                chat_id=message.chat.id,
                photo=thumb,
                caption="**Your current thumbnail**"
            )
            asyncio.create_task(auto_delete_message(msg, 30))
        else:
            await send_response(
                client,
                message.chat.id,
                f"{EMOJI['error']} **You don't have a thumbnail set**",
                photo=Config.START_PIC,
                delete_after=15
            )
    except Exception as e:
        logger.error(f"View thumbnail error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Couldn't retrieve thumbnail",
            delete_after=15
        )

@Client.on_message(filters.private & filters.command(['del_thumb', 'delthumb']))
async def remove_thumbnail(client: Client, message: Message):
    """Remove user's thumbnail"""
    try:
        old_thumb = await codeflixbots.get_thumbnail(message.from_user.id)
        if not old_thumb:
            return await send_response(
                client,
                message.chat.id,
                f"{EMOJI['error']} **No thumbnail to delete**",
                photo=Config.START_PIC,
                delete_after=15
            )
            
        await codeflixbots.set_thumbnail(message.from_user.id, file_id=None)
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['success']} **Thumbnail deleted successfully!**",
            photo=Config.START_PIC,
            delete_after=30
        )
    except Exception as e:
        logger.error(f"Delete thumbnail error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Failed to delete thumbnail",
            delete_after=15
        )

@Client.on_message(filters.private & filters.photo)
async def add_thumbnail(client: Client, message: Message):
    """Set new thumbnail from photo"""
    try:
        m = await send_response(
            client,
            message.chat.id,
            "**Processing your thumbnail...**",
            delete_after=5
        )
        
        await codeflixbots.set_thumbnail(message.from_user.id, file_id=message.photo.file_id)
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['success']} **Thumbnail saved successfully!**",
            photo=Config.START_PIC,
            delete_after=30
        )
    except Exception as e:
        logger.error(f"Add thumbnail error: {e}")
        await send_response(
            client,
            message.chat.id,
            f"{EMOJI['error']} Failed to save thumbnail",
            delete_after=15
        )
