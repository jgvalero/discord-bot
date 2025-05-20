from utils.database import Database


class Money:
    def __init__(self, db: Database):
        self.db = db

    def lose(self, user_id, guild_id, amount) -> bool:
        balance = self.get_money(user_id, guild_id)

        # Check if enough money
        if balance < amount:
            return False

        # Update values
        balance = balance - amount
        total_lost = self.get_total_lost(user_id, guild_id) + amount

        # Update database
        # Balance
        self.db.set_value(
            user_id,
            guild_id,
            "cookies",
            "cookies",
            balance,
        )

        # Total lost
        self.db.set_value(
            user_id,
            guild_id,
            "cookies",
            "total_lost",
            total_lost,
        )

        return True

    def earn(self, user_id, guild_id, amount) -> bool:
        balance = self.get_money(user_id, guild_id)

        # Update values
        balance = balance + amount
        total_earned = self.get_total_earned(user_id, guild_id) + amount

        # Update database
        # Balance
        self.db.set_value(
            user_id,
            guild_id,
            "cookies",
            "cookies",
            balance,
        )

        # Total Earned
        self.db.set_value(
            user_id,
            guild_id,
            "cookies",
            "total_earned",
            total_earned,
        )

        # Max
        max = self.get_max(user_id, guild_id)
        if balance > max:
            self.db.set_value(
                user_id,
                guild_id,
                "cookies",
                "max",
                balance,
            )

        return True

    def get_money(self, user_id, guild_id) -> int:
        return self.db.get_value(user_id, guild_id, "cookies", "cookies")[0]

    def get_total_earned(self, user_id, guild_id) -> int:
        return self.db.get_value(user_id, guild_id, "cookies", "total_earned")[0]

    def get_total_lost(self, user_id, guild_id) -> int:
        return self.db.get_value(user_id, guild_id, "cookies", "total_lost")[0]

    def get_max(self, user_id, guild_id) -> int:
        return self.db.get_value(user_id, guild_id, "cookies", "max")[0]
