import random

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import Database


class Casino(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("data/users.db")

    @app_commands.command()
    async def slots(self, interaction: discord.Interaction, wager: int = 1):
        """Play some slots!"""

        user_cookies = 0
        if interaction.guild:
            user_cookies = self.db.get_value(
                interaction.user.id, interaction.guild.id, "cookies"
            )
            if user_cookies < wager:
                return await interaction.response.send_message(
                    "You don't have enough cookies to make this wager!"
                )
            else:
                self.db.set_value(
                    interaction.user.id,
                    interaction.guild.id,
                    "cookies",
                    user_cookies - wager,
                )

        SYMBOLS = ["🍉", "🍊", "🍋", "🍌", "🍒"]
        wheel1 = random.choice(SYMBOLS)
        wheel2 = random.choice(SYMBOLS)
        wheel3 = random.choice(SYMBOLS)

        def evaluate_slots(wheel1, wheel2, wheel3):
            if wheel1 == wheel2 == wheel3:
                if interaction.guild:
                    payout = wager * 10
                    self.db.set_value(
                        interaction.user.id,
                        interaction.guild.id,
                        "cookies",
                        payout * 10,
                    )
                    return f"You won! Payout: {payout}"
            else:
                return "Tough luck!"

        await interaction.response.send_message(
            f"{wheel1} | {wheel2} | {wheel3}... {evaluate_slots(wheel1, wheel2, wheel3)}"
        )

    @app_commands.command()
    async def blackjack(self, interaction: discord.Interaction, wager: int = 1):
        """Starts a game of blackjack with a wager!"""

        user_cookies = self.db.get_value(
            interaction.user.id, interaction.guild.id, "cookies"
        )
        if user_cookies < wager:
            return await interaction.response.send_message(
                "You don't have enough cookies to make this wager!"
            )

        DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
        DEALER_HIT_THRESHOLD = 17

        random.shuffle(DECK)

        player_hand = [DECK.pop(), DECK.pop()]
        dealer_hand = [DECK.pop(), DECK.pop()]

        # await ctx.send(f"Your hand: {player_hand} ({sum(player_hand)})")
        # await ctx.send(f"Dealer's hand: {dealer_hand[0]} _")

        # while sum(player_hand) < 21:
        #     await ctx.send("Would you like to hit or stand? [hit/stand]")

        #     def check(m):
        #         return m.author == ctx.author and m.content.lower() in ["hit", "stand"]

        #     try:
        #         message = await self.bot.wait_for("message", check=check, timeout=60.0)
        #     except asyncio.TimeoutError:
        #         await ctx.send(
        #             "Sorry, you took too long to respond! Because of that, you lose your cookies!"
        #         )
        #         self.db.set_value(
        #             ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
        #         )
        #         return

        #     if message.content.lower() == "hit":
        #         player_hand.append(DECK.pop())
        #         await ctx.send(f"Your hand: {player_hand} ({sum(player_hand)})")
        #     else:
        #         break

        # if sum(player_hand) > 21:
        #     await ctx.send("Bust! You lose!")
        #     self.db.set_value(
        #         ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
        #     )
        # elif sum(player_hand) == 21:
        #     await ctx.send("Blackjack! You win!")
        #     self.db.set_value(
        #         ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
        #     )
        # else:
        #     while sum(dealer_hand) < DEALER_HIT_THRESHOLD:
        #         dealer_hand.append(DECK.pop())
        #     await ctx.send(f"Dealer's hand: {dealer_hand} ({sum(dealer_hand)})")

        #     if sum(dealer_hand) > 21:
        #         await ctx.send("Dealer busts! You win!")
        #         self.db.set_value(
        #             ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
        #         )
        #     elif sum(dealer_hand) < sum(player_hand):
        #         await ctx.send("You win!")
        #         self.db.set_value(
        #             ctx.author.id, ctx.guild.id, "cookies", user_cookies + wager
        #         )
        #     elif sum(dealer_hand) > sum(player_hand):
        #         await ctx.send("You lose!")
        #         self.db.set_value(
        #             ctx.author.id, ctx.guild.id, "cookies", user_cookies - wager
        #         )
        #     else:
        #         await ctx.send("It's a tie! Zoo wee mama!")

        return await interaction.response.send_message("Bazinga!")

    @app_commands.command()
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "What would you like to do?", view=Blackjack()
        )


class Blackjack(discord.ui.View):
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.red)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Do stuff

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Do stuff

        await interaction.response.edit_message(view=self)


async def setup(bot):
    await bot.add_cog(Casino(bot))
