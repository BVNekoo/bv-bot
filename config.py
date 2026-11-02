import os
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))

# Liste des salons de bienvenue
raw_channel_ids = os.getenv("WELCOME_CHANNEL_IDS", os.getenv("WELCOME_CHANNEL_ID", ""))
WELCOME_CHANNEL_IDS = [int(x.strip()) for x in raw_channel_ids.split(",") if x.strip().isdigit()]
WELCOME_CHANNEL_ID = WELCOME_CHANNEL_IDS[0] if WELCOME_CHANNEL_IDS else 0

# Rôles Discord à donner
AUTO_JOIN_ROLE_ID = int(os.getenv("AUTO_JOIN_ROLE_ID", 0))
TWITCH_FOLLOWER_ROLE_ID = int(os.getenv("TWITCH_FOLLOWER_ROLE_ID", 0))
YOUTUBE_SUBSCRIBER_ROLE_ID = int(os.getenv("YOUTUBE_SUBSCRIBER_ROLE_ID", 0))
KICK_FOLLOWER_ROLE_ID = int(os.getenv("KICK_FOLLOWER_ROLE_ID", 0))

# Twitch
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID", "")

# YouTube
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")

# Kick
KICK_CHANNEL_SLUG = os.getenv("KICK_CHANNEL_SLUG", "")

# Serveur Web
PORT = int(os.getenv("PORT", 8000))
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
