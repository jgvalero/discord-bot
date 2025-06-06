from typing import List

from pydantic import BaseModel

from utils.database import Database


class Fish(BaseModel):
    name: str
    weight: int
    price: int
    chance: float


class Rod(BaseModel):
    name: str
    price: int
    modifier: float


class Bait(BaseModel):
    name: str
    price: int
    modifier: float


class FishingSettings(BaseModel):
    base_catch_chance: float
    level_modifier: float
    experience: int
    fish: List[Fish]
    rod: List[Rod]
    bait: List[Bait]


class FishingStats:
    def __init__(self, user_id: int, guild_id: int, database: Database):
        self.user_id: int = user_id
        self.guild_id: int = guild_id
        self.database: Database = database

    @property
    def total_fish_caught(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing", "total_fish_caught"
        )[0]

    @total_fish_caught.setter
    def total_fish_caught(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing", "total_fish_caught", value
        )

    @property
    def total_weight(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing", "total_weight"
        )[0]

    @total_weight.setter
    def total_weight(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing", "total_weight", value
        )

    @property
    def total_value(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing", "total_value"
        )[0]

    @total_value.setter
    def total_value(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing", "total_value", value
        )

    @property
    def level(self) -> int:
        return self.database.get_value(self.user_id, self.guild_id, "fishing", "level")[
            0
        ]

    @level.setter
    def level(self, value) -> None:
        self.database.set_value(self.user_id, self.guild_id, "fishing", "level", value)

    @property
    def experience(self) -> int:
        return self.database.get_value(
            self.user_id, self.guild_id, "fishing", "experience"
        )[0]

    @experience.setter
    def experience(self, value) -> None:
        self.database.set_value(
            self.user_id, self.guild_id, "fishing", "experience", value
        )
