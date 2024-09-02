import sqlite3


class Database:
    def __init__(self, file: str) -> None:
        self.conn = sqlite3.connect(file)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        self.conn.close()

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fishing (
                user_id INTEGER,
                guild_id INTEGER,
                caught INTEGER DEFAULT 0,
                revenue INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                current_rod TEXT DEFAULT 'CastLite',
                bait INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cookies (
                user_id INTEGER,
                guild_id INTEGER,
                cookies INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                max INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
            """
        )
