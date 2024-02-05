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
                cookies INTEGER,
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
