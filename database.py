import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "followers.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                twitch_id TEXT,
                twitch_login TEXT,
                youtube_channel_id TEXT,
                kick_username TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_twitch_link(discord_id: str, twitch_id: str, twitch_login: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (discord_id, twitch_id, twitch_login, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(discord_id) DO UPDATE SET
                twitch_id = excluded.twitch_id,
                twitch_login = excluded.twitch_login,
                updated_at = CURRENT_TIMESTAMP
        """, (str(discord_id), str(twitch_id), twitch_login))
        conn.commit()

def save_youtube_link(discord_id: str, youtube_channel_id: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (discord_id, youtube_channel_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(discord_id) DO UPDATE SET
                youtube_channel_id = excluded.youtube_channel_id,
                updated_at = CURRENT_TIMESTAMP
        """, (str(discord_id), str(youtube_channel_id)))
        conn.commit()

def save_kick_link(discord_id: str, kick_username: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (discord_id, kick_username, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(discord_id) DO UPDATE SET
                kick_username = excluded.kick_username,
                updated_at = CURRENT_TIMESTAMP
        """, (str(discord_id), kick_username.lower()))
        conn.commit()

def get_user_by_discord_id(discord_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE discord_id = ?", (str(discord_id),))
        return cursor.fetchone()

def get_user_by_twitch_id(twitch_id: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE twitch_id = ?", (str(twitch_id),))
        return cursor.fetchone()
