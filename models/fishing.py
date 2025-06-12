from typing import List

from pydantic import BaseModel

from utils.database import Database


class Fish(BaseModel):
    name: str
    weight: int
    rarity: str


class Rod(BaseModel):
    name: str
    price: int
    modifier: float


class Bait(BaseModel):
    name: str
    price: int
    modifier: float


class Rarity(BaseModel):
    name: str
    probability: float
    price: int


class FishingSettings(BaseModel):
    base_catch_chance: float
    level_modifier: float
    experience: int
    fish: List[Fish]
    rod: List[Rod]
    bait: List[Bait]
    rarity: List[Rarity]


class FishingStats:
    def __init__(self, user_id: int, guild_id: int, database: Database):
        self.user_id: int = user_id
        self.guild_id: int = guild_id
        self.database: Database = database

    @property
    def total_fish_caught(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing_stats_core", "total_fish_caught"
        )[0]

    @total_fish_caught.setter
    def total_fish_caught(self, value) -> None:
        self.database.set_value(
            self.user_id,
            self.guild_id,
            "fishing_stats_core",
            "total_fish_caught",
            value,
        )

    @property
    def total_weight(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing_stats_core", "total_weight"
        )[0]

    @total_weight.setter
    def total_weight(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing_stats_core", "total_weight", value
        )

    @property
    def total_value(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing_stats_core", "total_value"
        )[0]

    @total_value.setter
    def total_value(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing_stats_core", "total_value", value
        )

    @property
    def level(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing_stats_core", "level"
        )[0]

    @level.setter
    def level(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing_stats_core", "level", value
        )

    @property
    def experience(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing_stats_core", "experience"
        )[0]

    @experience.setter
    def experience(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing_stats_core", "experience", value
        )


class FishingStatsItems:
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        database: Database,
        item_type: str,
        item_name: str,
        stat_type: str,
    ):
        self.user_id: int = user_id
        self.guild_id: int = guild_id
        self.database: Database = database

        self.item_type: str = item_type
        self.item_name: str = item_name
        self.stat_type: str = stat_type

        with self.database.conn:
            self.database.cursor.execute(
                """
                INSERT OR IGNORE INTO fishing_stats_items (user_id, guild_id, item_type, item_name, stat_type)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    self.user_id,
                    self.guild_id,
                    self.item_type,
                    self.item_name,
                    self.stat_type,
                ),
            )

    @property
    def value(self) -> int:
        with self.database.conn:
            self.database.cursor.execute(
                """
                SELECT value FROM fishing_stats_items WHERE user_id = ? AND guild_id = ? AND item_type = ? AND item_name = ? AND stat_type = ?;
                """,
                (
                    self.user_id,
                    self.guild_id,
                    self.item_type,
                    self.item_name,
                    self.stat_type,
                ),
            )
        return self.database.cursor.fetchone()[0]

    @value.setter
    def value(self, value) -> None:
        with self.database.conn:
            self.database.cursor.execute(
                """
                UPDATE fishing_stats_items SET value = ? WHERE user_id = ? AND guild_id = ? AND item_type = ? AND item_name = ? AND stat_type = ?;
                """,
                (
                    value,
                    self.user_id,
                    self.guild_id,
                    self.item_type,
                    self.item_name,
                    self.stat_type,
                ),
            )
