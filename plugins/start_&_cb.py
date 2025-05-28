import random
import asyncio
import logging
import uuid
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from helper.database import codeflixbots
from config import *
from config import Config
from collections import defaultdict
from typing import Dict, Any
logger = logging.getLogger(__name__)

# Constants
METADATA_TIMEOUT = 60  # seconds
POINT_RANGE = range(5, 21)  # 5-20 points
SHARE_MESSAGE = """
🚀 *Discover This Amazing Bot!* 🚀

I'm using this awesome file renaming bot with these features:
- Automatic file renaming
- Custom metadata editing
- Thumbnail customization
- Sequential file processing
- And much more!

Join me using this link: {invite_link}
"""
# Global state tracker
metadata_states: Dict[int, Dict[str, Any]] = {}
metadata_waiting = defaultdict(dict)
set_metadata_state = {}  # Global state tracker

METADATA_ON = [
    [InlineKeyboardButton('Metadata Enabled', callback_data='metadata_1'),
     InlineKeyboardButton('✅', callback_data='metadata_1')],
    [InlineKeyboardButton('Set Custom Metadata', callback_data='set_metadata'),
     InlineKeyboardButton('Back', callback_data='help')]
]

METADATA_OFF = [
    [InlineKeyboardButton('Metadata Disabled', callback_data='metadata_0'),
     InlineKeyboardButton('❌', callback_data='metadata_0')],
    [InlineKeyboardButton('Set Custom Metadata', callback_data='set_metadata'),
     InlineKeyboardButton('Back', callback_data='help')]
]

@Client.on_message(filters.private & filters.text & ~filters.command(['start']))
async def process_metadata_text(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is in metadata state and the message isn't a command
    if user_id in metadata_states and not message.text.startswith('/'):
        try:
            if message.text.lower() == "/cancel":
                await message.reply("🚫 Metadata update cancelled", 
                                reply_markup=InlineKeyboardMarkup(
                                    [[InlineKeyboardButton("Back to Metadata", callback_data="meta")]]
                                ))
            else:
                await hyoshcoder.set_metadata_code(user_id, message.text)
                bool_meta = await hyoshcoder.get_metadata(user_id)
                
                await message.reply(
                    f"✅ <b>Success!</b>\nMetadata set to:\n<code>{message.text}</code>",
                    reply_markup=InlineKeyboardMarkup(METADATA_ON if bool_meta else METADATA_OFF)
                )
                
            metadata_states.pop(user_id, None)
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
            metadata_states.pop(user_id, None)
    else:
        # Let other handlers process the message
        message.continue_propagation()

async def cleanup_metadata_states():
    while True:
        await asyncio.sleep(300)  # Clean every 5 minutes
        current_time = time.time()
        expired = [uid for uid, state in metadata_states.items() 
                    if current_time - state.get('timestamp', 0) > 300]
        for uid in expired:
            metadata_states.pop(uid, None)
class CallbackActions:
    @staticmethod
    async def handle_home(client: Client, query: CallbackQuery):
        """Handle home button callback"""
        buttons = [
            [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
            [
                InlineKeyboardButton("• ᴍʏ sᴛᴀᴛs •", callback_data='mystats'),
                InlineKeyboardButton("• ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ •", callback_data='leaderboard')
            ],
            [
                InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Codeflix_Bots'),
                InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')
            ],
            [
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')
            ]
        ]
        
        return {
            'text': Txt.START_TXT.format(query.from_user.mention),
            'reply_markup': InlineKeyboardMarkup(buttons),
            'disable_web_page_preview': True
        }

    @staticmethod
    async def handle_help(client: Client, query: CallbackQuery, user_id: int):
        """Handle help menu callback"""
        try:
            sequential_status = await codeflixbots.get_sequential_mode(user_id)
            src_info = await codeflixbots.get_src_info(user_id)
            
            btn_sec_text = "Sequential ✅" if sequential_status else "Sequential ❌"
            src_txt = "File name" if src_info == "file_name" else "File caption"

            buttons = [
                [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
                [
                    InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), 
                    InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')
                ],
                [
                    InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), 
                    InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')
                ],
                [
                    InlineKeyboardButton(f'• {btn_sec_text}', callback_data='sequential'),
                    InlineKeyboardButton('ғʀᴇᴇ ᴘᴏɪɴᴛs •', callback_data='freepoints')
                ],
                [
                    InlineKeyboardButton(f'• Extract from: {src_txt}', callback_data='toggle_src'),
                ],
                [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
            ]
            
            return {
                'text': Txt.HELP_TXT.format(client.mention),
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        except Exception as e:
            logger.error(f"Help menu error: {e}")
            return {
                'text': "❌ Error loading help menu",
                'reply_markup': InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="home")]
                ])
            }

    @staticmethod
    async def handle_stats(client: Client, query: CallbackQuery, user_id: int):
        """Handle user stats callback"""
        try:
            stats = await codeflixbots.get_user_file_stats(user_id)
            points = await codeflixbots.get_points(user_id)
            premium_status = await codeflixbots.check_premium_status(user_id)
            user_data = await codeflixbots.read_user(user_id)
            
            # Handle referral stats safely
            referral_stats = user_data.get('referral', {})
            referred_count = referral_stats.get('referred_count', 0)
            referral_earnings = referral_stats.get('referral_earnings', 0)
            
            text = (
                f"📊 <b>Your Statistics</b>\n\n"
                f"✨ <b>Points Balance:</b> {points}\n"
                f"⭐ <b>Premium Status:</b> {'Active ✅' if premium_status.get('is_premium', False) else 'Inactive ❌'}\n"
                f"👥 <b>Referrals:</b> {referred_count} "
                f"(Earned {referral_earnings} ✨)\n\n"
                f"📝 <b>Files Renamed</b>\n"
                f"• Total: {stats.get('total_renamed', 0)}\n"
                f"• Today: {stats.get('today', 0)}\n"
                f"• This Week: {stats.get('this_week', 0)}\n"
                f"• This Month: {stats.get('this_month', 0)}\n"
            )
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
                [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
                [InlineKeyboardButton("🔙 Back", callback_data="help")]
            ])
            
            return {
                'text': text,
                'reply_markup': buttons,
                'parse_mode': enums.ParseMode.HTML
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                'text': "❌ Failed to load statistics",
                'reply_markup': InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="help")]
                ])
            }

    @staticmethod
    def get_leaderboard_keyboard(selected_period: str = "weekly", selected_type: str = "points"):
        """Generate leaderboard navigation keyboard"""
        periods = {
            "daily": "⏳ Daily",
            "weekly": "📆 Weekly", 
            "monthly": "🗓 Monthly",
            "alltime": "🏆 All-Time"
        }
        types = {
            "points": "✨ Points",
            "renames": "📝 Files",
            "referrals": "👥 Referrals"
        }
        
        period_buttons = []
        for period, text in periods.items():
            if period == selected_period:
                period_buttons.append(InlineKeyboardButton(f"• {text} •", callback_data=f"lb_period_{period}"))
            else:
                period_buttons.append(InlineKeyboardButton(text, callback_data=f"lb_period_{period}"))
        
        type_buttons = []
        for lb_type, text in types.items():
            if lb_type == selected_type:
                type_buttons.append(InlineKeyboardButton(f"• {text} •", callback_data=f"lb_type_{lb_type}"))
            else:
                type_buttons.append(InlineKeyboardButton(text, callback_data=f"lb_type_{lb_type}"))
        
        return InlineKeyboardMarkup([
            period_buttons[:2],
            period_buttons[2:],
            type_buttons,
            [InlineKeyboardButton("🔙 Back", callback_data="help")]
        ])

    @staticmethod
    async def handle_leaderboard(client: Client, query: CallbackQuery, period: str = "weekly", type: str = "points"):
        """Handle leaderboard callback - showing top 8"""
        try:
            leaders = await codeflixbots.get_leaderboard(period, type)
            if not leaders:
                return {
                    'text': "📭 No leaderboard data available yet",
                    'reply_markup': InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="help")]
                    ])
                }
            
            type_display = {
                "points": "Points",
                "renames": "Files Renamed",
                "referrals": "Referrals"
            }.get(type, "Points")
            
            period_display = {
                "daily": "Daily",
                "weekly": "Weekly",
                "monthly": "Monthly", 
                "alltime": "All-Time"
            }.get(period, "Weekly")
            
            text = f"🏆 {period_display} {type_display} Leaderboard (Top 8):\n\n"
            for i, user in enumerate(leaders[:8], 1):
                username = user.get('username', f"User {user['_id']}")
                value = user.get('value', 0)
                text += f"{i}. {username} - {value} {type_display} {'⭐' if user.get('is_premium', False) else ''}\n"
            
            return {
                'text': text,
                'reply_markup': CallbackActions.get_leaderboard_keyboard(period, type),
                'parse_mode': enums.ParseMode.HTML
            }
        except Exception as e:
            logger.error(f"Leaderboard error: {e}")
            return {
                'text': "❌ Failed to load leaderboard",
                'reply_markup': InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="help")]
                ])
            }

    @staticmethod
    async def handle_free_points(client: Client, query: CallbackQuery, user_id: int):
        """Improved free points verification and distribution"""
        try:
            me = await client.get_me()
            unique_code = str(uuid.uuid4())[:8]
            invite_link = f"https://t.me/{me.username}?start=refer_{user_id}"
            
            # Generate random points
            points = random.randint(POINT_RANGE.start, POINT_RANGE.stop)
            
            # Check if user is premium for multiplier
            premium_status = await codeflixbots.check_premium_status(user_id)
            if premium_status.get('is_premium', False):
                points = points * 2  # Premium users get double points
            
            # Track the points distribution
            await codeflixbots.add_points(user_id, points)
            
            # Generate shareable links
            share_msg_encoded = f"https://t.me/share/url?url={invite_link}&text={SHARE_MESSAGE.format(invite_link=invite_link)}"
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Bot", url=share_msg_encoded)],
                [InlineKeyboardButton("💰 Watch Ad", callback_data=f"claim_{unique_code}")],
                [InlineKeyboardButton("🔙 Back", callback_data="help")]
            ])
            
            caption = (
                "**✨ Free Points System**\n\n"
                "Earn points by helping grow our community:\n\n"
                "🔹 **Share Bot**: Get 10 points per referral\n"
                "🔹 **Watch Ads**: Earn 5-20 points per ad\n"
                "⭐ **Premium Bonus**: 2x points multiplier\n\n"
                f"🎁 You can earn up to {points} points right now!"
            )
            
            return {
                'text': caption,
                'reply_markup': buttons
            }
        except Exception as e:
            logger.error(f"Free points error: {e}")
            return {
                'text': "❌ Error processing request. Please try again later.",
                'reply_markup': InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="help")]
                ])
            }

# Start Command Handler
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    await codeflixbots.add_user(client, message)

    # Initial interactive text and sticker sequence
    m = await message.reply_text("ʜᴇʜᴇ..ɪ'ᴍ ᴀɴʏᴀ!\nᴡᴀɪᴛ ᴀ ᴍᴏᴍᴇɴᴛ. . .")
    await asyncio.sleep(0.4)
    await m.edit_text("🎊")
    await asyncio.sleep(0.5)
    await m.edit_text("⚡")
    await asyncio.sleep(0.5)
    await m.edit_text("ᴡᴀᴋᴜ ᴡᴀᴋᴜ!...")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker after the text sequence
    await message.reply_sticker("CAACAgUAAxkBAAECroBmQKMAAQ-Gw4nibWoj_pJou2vP1a4AAlQIAAIzDxlVkNBkTEb1Lc4eBA")

    # Get start message content
    response = await CallbackActions.handle_home(client, message)
    
    # Send start message with or without picture
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=response['text'],
            reply_markup=response['reply_markup'],
            disable_web_page_preview=response.get('disable_web_page_preview', True)
        )
    else:
        await message.reply_text(
            text=response['text'],
            reply_markup=response['reply_markup'],
            disable_web_page_preview=response.get('disable_web_page_preview', True)
        )

# Callback Query Handler
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    """Main callback query handler with improved error handling"""
    data = query.data
    user_id = query.from_user.id
    
    try:
        # Always answer the callback first to prevent client-side issues
        await query.answer()
        
        response = None
        
        if data == "home":
            response = await CallbackActions.handle_home(client, query)
        
        elif data == "help":
            response = await CallbackActions.handle_help(client, query, user_id)
        
        elif data == "mystats":
            response = await CallbackActions.handle_stats(client, query, user_id)
        
        elif data == "leaderboard":
            response = await CallbackActions.handle_leaderboard(client, query)
        
        elif data.startswith("lb_"):
            parts = data.split("_")
            if len(parts) == 3:
                period = parts[2] if parts[1] == "period" else "weekly"
                type = parts[2] if parts[1] == "type" else "points"
                
                await codeflixbots.set_leaderboard_period(user_id, period)
                await codeflixbots.set_leaderboard_type(user_id, type)
                
                response = await CallbackActions.handle_leaderboard(client, query, period, type)
        
        elif data == "freepoints":
            response = await CallbackActions.handle_free_points(client, query, user_id)
        
        elif data.startswith("claim_"):
            code = data.split("_")[1]
            points = await codeflixbots.claim_points(user_id, code)
            if points:
                await query.answer(f"🎉 You earned {points} points!", show_alert=True)
                response = await CallbackActions.handle_help(client, query, user_id)
            else:
                await query.answer("❌ Invalid or already claimed", show_alert=True)
                return
        
        elif data == "caption":
            buttons = [
                [InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/CodeflixSupport'), 
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ]
            response = {
                'text': Txt.CAPTION_TXT,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        
        # Metadata toggle handler
        elif data in ["meta", "metadata_0", "metadata_1"]:
            if data.startswith("metadata_"):
                enable = data.endswith("_1")
                await hyoshcoder.set_metadata(user_id, enable)
            
            bool_meta = await hyoshcoder.get_metadata(user_id)
            meta_code = await hyoshcoder.get_metadata_code(user_id) or "Not set"
            
            await query.message.edit_text(
                f"<b>Current Metadata:</b>\n\n➜ {meta_code}",
                reply_markup=InlineKeyboardMarkup(METADATA_ON if bool_meta else METADATA_OFF)
            )
            await query.answer(f"Metadata {'enabled' if bool_meta else 'disabled'}")
        elif data == "set_metadata":
            try:
                metadata_states[user_id] = {
                    "waiting": True,
                    "timestamp": time.time(),
                    "original_msg": query.message.id
                }
                
                prompt = await query.message.edit_text(
                    "📝 <b>Send new metadata text</b>\n\n"
                    "Example: <code>Telegram : @REQUETE_ANIME_30sbot</code>\n"
                    f"Current: {await hyoshcoder.get_metadata_code(user_id) or 'None'}\n\n"
                    "Reply with text or /cancel",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("❌ Cancel", callback_data="meta")]]
                    )
                )
                
                metadata_states[user_id]["prompt_id"] = prompt.id
                
            except Exception as e:
                metadata_states.pop(user_id, None)
                await query.answer(f"Error: {str(e)}", show_alert=True)
        elif data == "file_names":
            format_template = await codeflixbots.get_format_template(user_id) or "Not set"
            buttons = [
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), 
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ]
            response = {
                'text': Txt.FILE_NAME_TXT.format(format_template=format_template),
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        
        elif data == "thumbnail":
            thumb = await codeflixbots.get_thumbnail(user_id)
            buttons = [
                [InlineKeyboardButton("• View Thumbnail", callback_data="showThumb")],
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), 
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ]
            response = {
                'text': Txt.THUMBNAIL_TXT,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'photo': thumb
            }
        
        elif data == "showThumb":
            thumb = await codeflixbots.get_thumbnail(user_id)
            caption = "Here is your current thumbnail" if thumb else "No thumbnail set"
            buttons = [
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), 
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="help")]
            ]
            response = {
                'text': caption,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'photo': thumb
            }
        
        elif data == "source":
            buttons = [
                [InlineKeyboardButton("• ᴄʟᴏsᴇ", callback_data="close"), 
                 InlineKeyboardButton("ʙᴀᴄᴋ •", callback_data="home")]
            ]
            response = {
                'text': Txt.SOURCE_TXT,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        
        elif data == "donate":
            buttons = [
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="help"), 
                 InlineKeyboardButton("ᴏᴡɴᴇʀ •", url='https://t.me/sewxiy')]
            ]
            response = {
                'text': Txt.DONATE_TXT,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        
        elif data == "about":
            buttons = [
                [
                    InlineKeyboardButton("• sᴜᴘᴘᴏʀᴛ", url='https://t.me/CodeflixSupport'), 
                    InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs •", callback_data="help")
                ],
                [
                    InlineKeyboardButton("• ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/cosmic_freak'), 
                    InlineKeyboardButton("ɴᴇᴛᴡᴏʀᴋ •", url='https://t.me/otakuflix_network')
                ],
                [InlineKeyboardButton("• ʙᴀᴄᴋ •", callback_data="home")]
            ]
            response = {
                'text': Txt.ABOUT_TXT,
                'reply_markup': InlineKeyboardMarkup(buttons),
                'disable_web_page_preview': True
            }
        
        elif data == "sequential":
            await codeflixbots.toggle_sequential_mode(user_id)
            response = await CallbackActions.handle_help(client, query, user_id)
        
        elif data == "toggle_src":
            await codeflixbots.toggle_src_info(user_id)
            response = await CallbackActions.handle_help(client, query, user_id)
        
        elif data == "close":
            try:
                await query.message.delete()
                if query.message.reply_to_message:
                    await query.message.reply_to_message.delete()
            except Exception as e:
                logger.warning(f"Error deleting message: {e}")
            return
        
        else:
            await query.answer("Unknown callback", show_alert=True)
            return

        # Send response
        if response:
            try:
                if 'photo' in response:
                    # Handle media messages
                    if query.message.photo:
                        # Editing existing photo message
                        await query.message.edit_media(
                            media=InputMediaPhoto(
                                media=response['photo'] or Config.START_PIC,
                                caption=response.get('text', '')
                            ),
                            reply_markup=response['reply_markup']
                        )
                    else:
                        # Converting text message to photo
                        await query.message.delete()
                        await client.send_photo(
                            chat_id=query.message.chat.id,
                            photo=response['photo'] or Config.START_PIC,
                            caption=response.get('text', ''),
                            reply_markup=response['reply_markup'],
                            disable_web_page_preview=response.get('disable_web_page_preview', True)
                        )
                else:
                    # Handle text messages
                    await query.message.edit_text(
                        text=response.get('text', ''),
                        reply_markup=response['reply_markup'],
                        disable_web_page_preview=response.get('disable_web_page_preview', True),
                        parse_mode=enums.ParseMode.HTML if response.get('parse_mode') == 'html' else None
                    )
            except Exception as e:
                logger.error(f"Failed to update message: {e}")
                await query.answer("Failed to update - please try again", show_alert=True)
            
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        try:
            await query.answer("❌ An error occurred", show_alert=True)
        except:
            pass

# Donation Command Handler
@Client.on_message(filters.command("donate"))
async def donation(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton(text="ᴏᴡɴᴇʀ", url='https://t.me/sewxiy')]
    ])
    yt = await message.reply_photo(photo='https://graph.org/file/1919fe077848bd0783d4c.jpg', caption=Txt.DONATE_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Premium Command Handler
@Client.on_message(filters.command("premium"))
async def getpremium(bot, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/sewxiy"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ])
    yt = await message.reply_photo(photo='https://graph.org/file/feebef43bbdf76e796b1b.jpg', caption=Txt.PREMIUM_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Plan Command Handler
@Client.on_message(filters.command("plan"))
async def premium(bot, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("sᴇɴᴅ ss", url="https://t.me/sewxiy"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ])
    yt = await message.reply_photo(photo='https://graph.org/file/8b50e21db819f296661b7.jpg', caption=Txt.PREPLANS_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Bought Command Handler
@Client.on_message(filters.command("bought") & filters.private)
async def bought(client, message):
    msg = await message.reply('Wait im checking...')
    replied = message.reply_to_message

    if not replied:
        await msg.edit("<b>Please reply with the screenshot of your payment for the premium purchase to proceed.\n\nFor example, first upload your screenshot, then reply to it using the '/bought' command</b>")
    elif replied.photo:
        await client.send_photo(
            chat_id=LOG_CHANNEL,
            photo=replied.photo.file_id,
            caption=f'<b>User - {message.from_user.mention}\nUser id - <code>{message.from_user.id}</code>\nUsername - <code>{message.from_user.username}</code>\nName - <code>{message.from_user.first_name}</code></b>',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close_data")]
            ])
        )
        await msg.edit_text('<b>Your screenshot has been sent to Admins</b>')

@Client.on_message(filters.private & filters.command("help"))
async def help_command(client, message):
    # Await get_me to get the bot's user object
    bot = await client.get_me()
    mention = bot.mention

    # Send the help message with inline buttons
    await message.reply_text(
        text=Txt.HELP_TXT.format(mention=mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ •", callback_data='file_names')],
            [InlineKeyboardButton('• ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ •', callback_data='caption')],
            [InlineKeyboardButton('• ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ •', callback_data='donate')],
            [InlineKeyboardButton('• ʜᴏᴍᴇ', callback_data='home')]
        ])
    )
