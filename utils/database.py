import sqlite3
import logging

TABLE_USERS = "users"
COLUMN_USER_ID = "user_id"
COLUMN_GUILD_ID = "guild_id"
COLUMN_COOKIES = "cookies"
COLUMN_MOST_VALUABLE_FISH = "most_valuable_fish"
COLUMN_BAIT = "bait"


def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            raise

    return wrapper


class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

    @handle_errors
    def create_tables(self):
        with self.conn:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    cookies INTEGER DEFAULT 0,
                    most_valuable_fish INTEGER DEFAULT 0,
                    bait INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
                """
            )

    @handle_errors
    def get_value(self, user_id, guild_id, column):
        with self.conn:
            self.cursor.execute(
                f"""
                SELECT {column} FROM users WHERE user_id = ? AND guild_id = ?
                """,
                (user_id, guild_id),
            )
            return self.cursor.fetchone()[0]

    @handle_errors
    def set_value(self, user_id, guild_id, column, value):
        with self.conn:
            self.cursor.execute(
                f"""
                UPDATE users SET {column} = ? WHERE user_id = ? AND guild_id = ?
                """,
                (value, user_id, guild_id),
            )

    @handle_errors
    def add_column(self, table_name, column_name, data_type, default_value=None):
        if not (self.is_valid_name(table_name) and self.is_valid_name(column_name)):
            raise ValueError("Invalid table name or column name")

        with self.conn:
            if default_value is not None:
                self.cursor.execute(
                    """
                    ALTER TABLE ? ADD COLUMN ? ? DEFAULT ?
                    """,
                    (table_name, column_name, data_type, default_value),
                )
            else:
                self.cursor.execute(
                    """
                    ALTER TABLE ? ADD COLUMN ? ?
                    """,
                    (table_name, column_name, data_type),
                )

    def is_valid_name(self, name):
        """Checks if a name is valid (for use as a table name or column name)."""
        return name.isidentifier()

    @handle_errors
    def get_leaderboard(self, guild_id):
        with self.conn:
            self.cursor.execute(
                """
                SELECT user_id, cookies FROM users WHERE guild_id = ?
                ORDER BY cookies DESC
                """,
                (guild_id,),
            )
            return self.cursor.fetchall()

    @handle_errors
    def create_user(self, member_id, guild_id):
        with self.conn:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO users (user_id, guild_id)
                VALUES (?, ?)
                """,
                (member_id, guild_id),
            )

    @handle_errors
    def column_exists(self, table_name, column_name):
        with self.conn:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in self.cursor.fetchall()]
            return column_name in columns

    @handle_errors
    def update_database(self):
        self.add_column(TABLE_USERS, COLUMN_MOST_VALUABLE_FISH, "INTEGER", 0)
        self.add_column(TABLE_USERS, COLUMN_BAIT, "INTEGER", 0)

    def __del__(self):
        self.conn.close()


if __name__ == "__main__":
    print("Setting up database...")
    db = Database("data/users.db")
    db.create_tables()
    db.update_database()
    print("Database setup complete.")
