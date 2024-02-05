import sqlite3


class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

    def create_tables(self):
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
        self.conn.commit()

    def get_value(self, user_id, guild_id, column):
        self.cursor.execute(
            f"""
            SELECT {column} FROM users WHERE user_id = ? AND guild_id = ?
            """,
            (user_id, guild_id),
        )
        return self.cursor.fetchone()[0]

    def set_value(self, user_id, guild_id, column, value):
        self.cursor.execute(
            f"""
            UPDATE users SET {column} = ? WHERE user_id = ? AND guild_id = ?
            """,
            (value, user_id, guild_id),
        )
        self.conn.commit()

    def add_column(self, table_name, column_name, data_type, default_value=None):
        if default_value is not None:
            self.cursor.execute(
                f"""
                ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type} DEFAULT {default_value}
                """
            )
        else:
            self.cursor.execute(
                f"""
                ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}
                """
            )
        self.conn.commit()

    def get_leaderboard(self, guild_id):
        self.cursor.execute(
            """
            SELECT user_id, cookies FROM users WHERE guild_id = ?
            ORDER BY cookies DESC
            """,
            (guild_id,),
        )
        return self.cursor.fetchall()

    def create_user(self, member_id, guild_id):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO users (user_id, guild_id)
            VALUES (?, ?)
            """,
            (member_id, guild_id),
        )

    def column_exists(self, table_name, column_name):
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in self.cursor.fetchall()]
        return column_name in columns

    def update_database(self):
        if not self.column_exists("users", "most_valuable_fish"):
            self.add_column("users", "most_valuable_fish", "INTEGER", 0)
        if not self.column_exists("users", "bait"):
            self.add_column("users", "bait", "INTEGER", 0)
        self.conn.commit()


if __name__ == "__main__":
    print("Setting up database...")
    db = Database("data/users.db")
    db.create_tables()
    db.update_database()
    print("Database setup complete.")
