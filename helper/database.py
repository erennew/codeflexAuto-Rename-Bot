import motor.motor_asyncio
import datetime
import pytz
import logging
import secrets
from typing import Optional, Dict, List, Union, AsyncGenerator, Any
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError, ConnectionFailure
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, database_name: str):
        """Initialize database connection with enhanced settings."""
        self._uri = uri
        self._database_name = database_name
        self._client = None
        self.db = None
        self.users = None
        
    async def connect(self):
        """Establish database connection with enhanced settings and error handling."""
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                self._uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                maxPoolSize=100,
                minPoolSize=10,
                retryWrites=True,
                retryReads=True
            )
            
            # Test connection
            await self._client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
            
            # Initialize database and collections
            self.db = self._client[self._database_name]
            self.users = self.db.users
            
            # Create indexes
            await self._create_indexes()
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Database connection failed: {e}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create necessary indexes with enhanced error handling."""
        indexes = [
            ("users", [("referral.referrer_id", False)]),
            ("users", [("ban_status.is_banned", False)]),
            ("users", [("premium.is_premium", False)]),
            ("users", [("activity.last_active", -1)]),
        ]
        
        for collection, fields in indexes:
            try:
                for field, unique in fields:
                    await self.db[collection].create_index(field, unique=unique)
                logger.info(f"Created indexes for {collection}")
            except PyMongoError as e:
                logger.error(f"Failed to create indexes for {collection}: {e}")
                continue

    def new_user(self, id: int) -> Dict[str, Any]:
        """Create a new user document with comprehensive default values."""
        now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        return {
            "_id": int(id),
            "username": None,
            "join_date": now.isoformat(),
            "file_id": None,
            "caption": None,
            "metadata": True,
            "metadata_code": "Telegram : @Codeflix_Bots",
            "format_template": None,
            "ban_status": {
                "is_banned": False,
                "ban_duration": 0,
                "banned_on": None,
                "ban_reason": '',
            },
            "points": {
                "balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "last_earned": None
            },
            "premium": {
                "is_premium": False,
                "since": None,
                "until": None,
                "plan": None
            },
            "referral": {
                "referrer_id": None,
                "referred_count": 0,
                "referral_earnings": 0,
                "referred_users": []
            },
            "settings": {
                "sequential_mode": False,
                "src_info": "file_name",
                "leaderboard_period": "weekly",
                "leaderboard_type": "points"
            },
            "activity": {
                "last_active": now.isoformat(),
                "total_files_renamed": 0,
                "today_count": 0,
                "today_date": now.date().isoformat()
            }
        }

    async def add_user(self, client, message):
        """Add a new user with comprehensive initialization."""
        u = message.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            try:
                await self.users.insert_one(user)
                logger.info(f"Added new user: {u.id}")
            except Exception as e:
                logger.error(f"Error adding user {u.id}: {e}")

    async def is_user_exist(self, id: int) -> bool:
        """Check if user exists in database."""
        try:
            user = await self.users.find_one({"_id": int(id)})
            return bool(user)
        except Exception as e:
            logger.error(f"Error checking if user {id} exists: {e}")
            return False

    async def total_users_count(self) -> int:
        """Get total number of users."""
        try:
            return await self.users.count_documents({})
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0

    async def read_user(self, id: int) -> Optional[Dict]:
        """Get user document by ID."""
        try:
            return await self.users.find_one({"_id": int(id)})
        except Exception as e:
            logger.error(f"Error reading user {id}: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user data."""
        try:
            await self.users.delete_many({"_id": int(user_id)})
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    async def set_thumbnail(self, id: int, file_id: str) -> bool:
        """Set user's thumbnail."""
        try:
            await self.users.update_one(
                {"_id": int(id)},
                {"$set": {"file_id": file_id}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting thumbnail for user {id}: {e}")
            return False

    async def get_thumbnail(self, id: int) -> Optional[str]:
        """Get user's thumbnail."""
        try:
            user = await self.users.find_one({"_id": int(id)})
            return user.get("file_id") if user else None
        except Exception as e:
            logger.error(f"Error getting thumbnail for user {id}: {e}")
            return None

    async def set_caption(self, id: int, caption: str) -> bool:
        """Set user's default caption."""
        try:
            await self.users.update_one(
                {"_id": int(id)},
                {"$set": {"caption": caption}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting caption for user {id}: {e}")
            return False

    async def get_caption(self, id: int) -> Optional[str]:
        """Get user's default caption."""
        try:
            user = await self.users.find_one({"_id": int(id)})
            return user.get("caption") if user else None
        except Exception as e:
            logger.error(f"Error getting caption for user {id}: {e}")
            return None

    async def set_format_template(self, id: int, format_template: str) -> bool:
        """Set user's auto-rename format template."""
        try:
            await self.users.update_one(
                {"_id": int(id)},
                {"$set": {"format_template": format_template}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting format template for user {id}: {e}")
            return False

    async def get_format_template(self, id: int) -> Optional[str]:
        """Get user's auto-rename format template."""
        try:
            user = await self.users.find_one({"_id": int(id)})
            return user.get("format_template") if user else None
        except Exception as e:
            logger.error(f"Error getting format template for user {id}: {e}")
            return None

    async def get_metadata(self, user_id: int) -> bool:
        """Get user's metadata setting."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            return user.get("metadata", True) if user else True
        except Exception as e:
            logger.error(f"Error getting metadata for user {user_id}: {e}")
            return True

    async def set_metadata(self, user_id: int, bool_meta: bool) -> bool:
        """Set user's metadata setting."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"metadata": bool_meta}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting metadata for user {user_id}: {e}")
            return False

    async def get_metadata_code(self, user_id: int) -> Optional[str]:
        """Get user's metadata code."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            return user.get("metadata_code") if user else None
        except Exception as e:
            logger.error(f"Error getting metadata code for user {user_id}: {e}")
            return None

    async def set_metadata_code(self, user_id: int, metadata_code: str) -> bool:
        """Set user's metadata code."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"metadata_code": metadata_code}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting metadata code for user {user_id}: {e}")
            return False

    # Points System
    async def add_points(self, user_id: int, points: int) -> bool:
        """Add points to user's balance."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {
                    "$inc": {
                        "points.balance": points,
                        "points.total_earned": points
                    },
                    "$set": {"points.last_earned": datetime.datetime.now().isoformat()}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error adding points to user {user_id}: {e}")
            return False

    async def get_points(self, user_id: int) -> int:
        """Get user's current points balance."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            return user.get("points", {}).get("balance", 0) if user else 0
        except Exception as e:
            logger.error(f"Error getting points for user {user_id}: {e}")
            return 0

    # Premium System
    async def check_premium_status(self, user_id: int) -> Dict:
        """Check user's premium status with auto-expiration."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            if not user:
                return {"is_premium": False, "reason": "User not found"}
                
            if user["premium"]["is_premium"]:
                if user["premium"]["until"] and \
                   datetime.datetime.fromisoformat(user["premium"]["until"]) < datetime.datetime.now():
                    await self.deactivate_premium(user_id)
                    return {"is_premium": False, "reason": "Subscription expired"}
                return {"is_premium": True, "until": user["premium"]["until"], "plan": user["premium"]["plan"]}
            return {"is_premium": False, "reason": "No active subscription"}
        except Exception as e:
            logger.error(f"Error checking premium status for user {user_id}: {e}")
            return {"is_premium": False, "reason": "Error checking status"}

    async def activate_premium(self, user_id: int, plan: str, duration_days: int) -> bool:
        """Activate premium subscription for a user."""
        try:
            now = datetime.datetime.now()
            until = now + datetime.timedelta(days=duration_days)
            
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {
                    "premium.is_premium": True,
                    "premium.since": now.isoformat(),
                    "premium.until": until.isoformat(),
                    "premium.plan": plan
                }}
            )
            return True
        except Exception as e:
            logger.error(f"Error activating premium for user {user_id}: {e}")
            return False

    async def deactivate_premium(self, user_id: int) -> bool:
        """Deactivate premium subscription for a user."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {
                    "premium.is_premium": False,
                    "premium.until": None,
                    "premium.plan": None
                }}
            )
            return True
        except Exception as e:
            logger.error(f"Error deactivating premium for user {user_id}: {e}")
            return False

    # File Stats
    async def track_file_rename(self, user_id: int) -> bool:
        """Track a file rename operation."""
        try:
            today = datetime.date.today().isoformat()
            update = {
                "$inc": {
                    "activity.total_files_renamed": 1,
                    "activity.today_count": 1
                },
                "$set": {
                    "activity.last_active": datetime.datetime.now().isoformat(),
                    "activity.today_date": today
                }
            }
            
            # Reset today's count if date changed
            user = await self.users.find_one({"_id": int(user_id)})
            if user and user.get("activity", {}).get("today_date") != today:
                update["$set"]["activity.today_count"] = 1
                
            await self.users.update_one(
                {"_id": int(user_id)},
                update
            )
            return True
        except Exception as e:
            logger.error(f"Error tracking file rename for user {user_id}: {e}")
            return False

    async def get_user_file_stats(self, user_id: int) -> Dict:
        """Get user's file rename statistics."""
        stats = {
            "total_renamed": 0,
            "today": 0,
            "this_week": 0,
            "this_month": 0
        }
        
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            if not user:
                return stats
                
            stats["total_renamed"] = user.get("activity", {}).get("total_files_renamed", 0)
            stats["today"] = user.get("activity", {}).get("today_count", 0)
            
            # For weekly and monthly stats, we'd need a separate collection in a production system
            # Here we'll just return the same as today for simplicity
            stats["this_week"] = stats["today"]
            stats["this_month"] = stats["today"]
            
            return stats
        except Exception as e:
            logger.error(f"Error getting file stats for user {user_id}: {e}")
            return stats

    # Leaderboard System
    async def get_leaderboard(self, period: str = "weekly", type: str = "points") -> List[Dict]:
        """
        Get leaderboard data.
        
        Args:
            period: "daily", "weekly", "monthly", or "alltime"
            type: "points" or "renames"
            
        Returns:
            list: Leaderboard entries with user details
        """
        try:
            if period not in ["daily", "weekly", "monthly", "alltime"]:
                period = "weekly"
                
            if type == "points":
                sort_field = "points.balance"
            elif type == "renames":
                sort_field = "activity.total_files_renamed"
            else:
                sort_field = "points.balance"
                
            cursor = self.users.find({"ban_status.is_banned": False}).sort(sort_field, -1).limit(10)
            leaders = await cursor.to_list(length=10)
            
            return [{
                "_id": user["_id"],
                "username": user.get("username", f"user_{user['_id']}"),
                "value": user["points"]["balance"] if type == "points" else user["activity"]["total_files_renamed"],
                "is_premium": user["premium"]["is_premium"]
            } for user in leaders]
            
        except Exception as e:
            logger.error(f"Error getting {period} leaderboard: {e}")
            return []

    async def set_leaderboard_period(self, user_id: int, period: str) -> bool:
        """Set user's preferred leaderboard period."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"settings.leaderboard_period": period}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting leaderboard period for user {user_id}: {e}")
            return False

    async def set_leaderboard_type(self, user_id: int, lb_type: str) -> bool:
        """Set user's preferred leaderboard type."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"settings.leaderboard_type": lb_type}}
            )
            return True
        except Exception as e:
            logger.error(f"Error setting leaderboard type for user {user_id}: {e}")
            return False

    # Sequential Mode
    async def get_sequential_mode(self, user_id: int) -> bool:
        """Get user's sequential mode setting."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            return user.get("settings", {}).get("sequential_mode", False) if user else False
        except Exception as e:
            logger.error(f"Error getting sequential mode for user {user_id}: {e}")
            return False

    async def toggle_sequential_mode(self, user_id: int) -> bool:
        """Toggle user's sequential mode setting."""
        try:
            current = await self.get_sequential_mode(user_id)
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"settings.sequential_mode": not current}}
            )
            return not current
        except Exception as e:
            logger.error(f"Error toggling sequential mode for user {user_id}: {e}")
            return False

    # Source Info (file_name vs caption)
    async def get_src_info(self, user_id: int) -> str:
        """Get user's source info preference."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            return user.get("settings", {}).get("src_info", "file_name") if user else "file_name"
        except Exception as e:
            logger.error(f"Error getting src_info for user {user_id}: {e}")
            return "file_name"

    async def toggle_src_info(self, user_id: int) -> str:
        """Toggle user's source info preference."""
        try:
            current = await self.get_src_info(user_id)
            new_setting = "file_name" if current == "caption" else "caption"
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"settings.src_info": new_setting}}
            )
            return new_setting
        except Exception as e:
            logger.error(f"Error toggling src_info for user {user_id}: {e}")
            return "file_name"

    # Referral System
    async def set_referrer(self, user_id: int, referrer_id: int) -> bool:
        """Set referrer for a user."""
        try:
            await self.users.update_one(
                {"_id": int(user_id)},
                {"$set": {"referral.referrer_id": referrer_id}}
            )
            
            # Update referrer's stats
            await self.users.update_one(
                {"_id": int(referrer_id)},
                {
                    "$inc": {"referral.referred_count": 1},
                    "$push": {"referral.referred_users": user_id}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error setting referrer for user {user_id}: {e}")
            return False

    async def get_referral_stats(self, user_id: int) -> Dict:
        """Get user's referral statistics."""
        try:
            user = await self.users.find_one({"_id": int(user_id)})
            if not user:
                return {}
                
            return {
                "referred_count": user.get("referral", {}).get("referred_count", 0),
                "referral_earnings": user.get("referral", {}).get("referral_earnings", 0),
                "referred_users": user.get("referral", {}).get("referred_users", [])
            }
        except Exception as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            return {}

    # Admin Stats
    async def total_banned_users_count(self) -> int:
        """Get total number of banned users."""
        try:
            return await self.users.count_documents({"ban_status.is_banned": True})
        except Exception as e:
            logger.error(f"Error counting banned users: {e}")
            return 0

    async def total_premium_users_count(self) -> int:
        """Get total number of premium users."""
        try:
            return await self.users.count_documents({"premium.is_premium": True})
        except Exception as e:
            logger.error(f"Error counting premium users: {e}")
            return 0

    async def get_daily_active_users(self) -> int:
        """Get count of daily active users."""
        try:
            today = datetime.datetime.now().date()
            return await self.users.count_documents({
                "activity.last_active": {
                    "$gte": today.isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error counting daily active users: {e}")
            return 0

# Initialize database instance
codeflixbots = Database(Config.DB_URL, Config.DB_NAME)
