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
        with self.conn:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, guild_id)
                );
                """
            )
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fishing (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    caught INTEGER DEFAULT 0,
                    revenue INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    current_rod TEXT DEFAULT 'CastLite',
                    bait INTEGER DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id, guild_id) REFERENCES users(user_id, guild_id)
                );
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
                    FOREIGN KEY (user_id, guild_id) REFERENCES users(user_id, guild_id)
                );
                """
            )

    def create_user(self, user_id: str, guild_id: str):
        with self.conn:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO users (user_id, guild_id)
                VALUES (?, ?);
                """,
                (user_id, guild_id)
            )
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO fishing (user_id, guild_id)
                VALUES (?, ?);
                """,
                (user_id, guild_id)
            )
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO cookies (user_id, guild_id)
                VALUES (?, ?);
                """,
                (user_id, guild_id)
            )

    def get_value(self, table: str, column: str, user_id: str, guild_id: str):
        with self.conn:
            self.cursor.execute(
                f"""
                SELECT {column} FROM {table} WHERE user_id = ? AND guild_id = ?;
                """,
                (user_id, guild_id)
            )
        return self.cursor.fetchone()[0]

    def set_value(self, table: str, column: str, user_id: str, guild_id: str, value: str | int):
        with self.conn:
            self.cursor.execute(
                f"""
                UPDATE {table} SET {column} = ? WHERE user_id = ? AND guild_id = ?
                """,
                (value, user_id, guild_id)
            )

# if __name__ == "__main__":
#     db = Database("data/test.db")
#     db.create_user("12345", "54321")
#     value = db.get_value("cookies", "total", "12345", "54321")
#     value = db.set_value("cookies", "total", "12345", "54321", 10)
#     value = db.get_value("cookies", "total", "12345", "54321")
#     print(value)
