import random

import discord
from discord import app_commands, ui
from discord.ext import commands

from utils.blackjack import Blackjack
from utils.money import Money


class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.money = Money(bot.database)

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, wager: int = 1):
        """Play some slots!"""

        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        # Get user and guild IDs for database operations
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if not self.money.lose(user_id, guild_id, wager):
            return await interaction.response.send_message(
                "You don't have enough cookies to make this wager!"
            )

        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        def evaluate_slots(wheel1, wheel2, wheel3):
            if wheel1 == wheel2 == wheel3:
                if interaction.guild:
                    payout = wager * 100
                    self.money.earn(user_id, guild_id, payout)
                    return f"You won! Payout: {payout}"
            else:
                return "Tough luck!"

        await interaction.response.send_message(
            f"{wheel1} | {wheel2} | {wheel3}... {evaluate_slots(wheel1, wheel2, wheel3)}"
        )

    class BlackjackView(ui.View):
        def __init__(
            self, game: Blackjack, money, interaction: discord.Interaction, wager: int
        ):
            super().__init__(timeout=30.0)
            self.game = game
            self.money = money
            self.user_id = interaction.user.id
            self.guild_id = interaction.guild.id
            self.user_display_name = interaction.user.display_name
            self.wager = wager
            self.message = None
            self.ended = False

        def disable_buttons(self):
            for item in self.children:
                item.disabled = True

        async def on_timeout(self):
            if not self.ended:
                self.ended = True
                self.disable_buttons()

                result, payout = self.game.stand()

                embed = self.create_game_embed()
                embed.add_field(
                    name="Result",
                    value=f"{result} (You took too long (auto-stand)!)",
                    inline=False,
                )

                if payout > 0:
                    self.money.earn(self.user_id, self.guild_id, payout)
                    embed.add_field(name="Payout", value=f"{payout}", inline=False)

                    if payout == self.wager:
                        embed.color = discord.Color.blue()
                    else:
                        embed.color = discord.Color.green()
                else:
                    embed.color = discord.Color.red()

                try:
                    await self.message.edit(embed=embed, view=self)
                except Exception:
                    pass

        def create_game_embed(self):
            dealer_hand, player_hand = self.game.get_table()

            if self.ended:
                dealer_cards = " | ".join(
                    [f"{card.rank} of {card.suit}" for card in dealer_hand]
                )
                dealer_total = self.game.calculate_hand(dealer_hand)
                dealer_display = f"{dealer_cards} (Total: {dealer_total})"
            else:
                dealer_display = (
                    f"{dealer_hand[0].rank} of {dealer_hand[0].suit} | Hidden card"
                )

            player_cards = " | ".join(
                [f"{card.rank} of {card.suit}" for card in player_hand]
            )
            player_total = self.game.calculate_hand(player_hand)

            embed = discord.Embed(
                title=f"{self.user_display_name}'s blackjack game",
                color=discord.Color.yellow(),
            )
            embed.add_field(name="Dealer's Hand", value=dealer_display, inline=False)
            embed.add_field(
                name="Your Hand",
                value=f"{player_cards} (Total: {player_total})",
                inline=False,
            )
            embed.add_field(name="Wager", value=str(self.wager), inline=False)

            return embed

        @ui.button(label="Hit", style=discord.ButtonStyle.primary)
        async def hit_button(self, interaction: discord.Interaction, button: ui.Button):
            if interaction.user.id != int(self.user_id):
                return await interaction.response.send_message(
                    "This isn't your game!", ephemeral=True
                )

            continue_game = self.game.hit(self.game.player_hand)

            embed = self.create_game_embed()

            if not continue_game:
                self.ended = True
                self.disable_buttons()
                embed.add_field(name="Result", value="Bust! Tough luck!", inline=False)
                embed.color = discord.Color.red()

            await interaction.response.edit_message(embed=embed, view=self)

            if not continue_game:
                self.stop()

        @ui.button(label="Stand", style=discord.ButtonStyle.danger)
        async def stand_button(
            self, interaction: discord.Interaction, button: ui.Button
        ):
            if interaction.user.id != int(self.user_id):
                return await interaction.response.send_message(
                    "This isn't your game!", ephemeral=True
                )

            self.ended = True
            self.disable_buttons()

            result, payout = self.game.stand()

            embed = self.create_game_embed()
            embed.add_field(name="Result", value=result, inline=False)

            if payout > 0:
                self.money.earn(self.user_id, self.guild_id, payout)
                embed.add_field(name="Payout", value=f"{payout}", inline=False)

                if payout == self.wager:
                    embed.color = discord.Color.blue()
                else:
                    embed.color = discord.Color.green()
            else:
                embed.color = discord.Color.red()

            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

    @app_commands.command()
    async def blackjack(self, interaction: discord.Interaction, wager: int = 1):
        """Play some blackjack!"""

        # Ensure command is used in a server context
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server!", ephemeral=True
            )
            return

        # Get user and guild IDs for database operations
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)

        if not self.money.lose(user_id, guild_id, wager):
            return await interaction.response.send_message(
                "You don't have enough cookies to make this wager!"
            )

        game = Blackjack(wager)
        game.initial_deal()

        dealer_hand, player_hand = game.get_table()
        player_total = game.calculate_hand(player_hand)

        if player_total == 21 and len(player_hand) == 2:
            result, payout = game.stand()
            dealer_total = game.calculate_hand(dealer_hand)

            embed = discord.Embed(
                title=f"{interaction.user.display_name}'s blackjack game",
                color=discord.Color.yellow(),
            )

            dealer_cards = " | ".join(
                [f"{card.rank} of {card.suit}" for card in dealer_hand]
            )
            embed.add_field(
                name=f"Dealer's Hand ({dealer_total})", value=dealer_cards, inline=False
            )

            player_cards = " | ".join(
                [f"{card.rank} of {card.suit}" for card in player_hand]
            )
            embed.add_field(
                name=f"Your Hand ({player_total})", value=player_cards, inline=False
            )

            embed.add_field(name="Wager", value=str(wager), inline=False)

            if result == "Blackjack":
                self.money.earn(user_id, guild_id, payout)
                embed.add_field(
                    name="Result",
                    value=f"Natural Blackjack! You won {payout} cookies!",
                    inline=False,
                )
                embed.color = discord.Color.green()
            elif result == "Push":
                self.money.earn(user_id, guild_id, payout)
                embed.add_field(
                    name="Result",
                    value="Push! Both you and dealer have natural blackjack.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Result",
                    value="Dealer has natural blackjack. Tough luck!",
                    inline=False,
                )
                embed.color = discord.Color.red()

            await interaction.response.send_message(embed=embed)
            return

        view = self.BlackjackView(game, self.money, interaction, wager)
        embed = view.create_game_embed()

        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Casino(bot))
