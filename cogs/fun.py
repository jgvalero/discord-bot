from discord.ext import commands

import random
import json
import os


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if os.path.exists("data/trivia_questions.json"):
            with open("data/trivia_questions.json", "r") as f:
                self.trivia_questions = json.load(f)
        else:
            self.trivia_questions = []

    @commands.command()
    async def trivia(self, ctx):
        """Starts a trivia game"""
        if not self.trivia_questions:
            await ctx.send(
                "There are no trivia questions! You can add some in data/trivia_questions.json. Check out the README for more info."
            )
            return

        question = random.choice(self.trivia_questions)
        choices = "\n".join(
            f"{i+1}. {choice}" for i, choice in enumerate(question["choices"])
        )
        await ctx.send(
            f"{question['question']}\nChoices:\n{choices}\nYou can answer with the number or the text!"
        )

        def check(m):
            return m.channel == ctx.channel and (
                m.content.lower() == str(question["answer"][0])
                or m.content.lower() == question["answer"][1].lower()
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
        except TimeoutError:
            await ctx.send(
                f"Ya'll ran out of time, the correct answer is {question['answer'][0]}. {question['answer'][1]}!"
            )
        else:
            await ctx.send(
                f"You are cool, {msg.author}! You got it right ({question['answer'][0]}. {question['answer'][1]})!"
            )


async def setup(bot):
    await bot.add_cog(Fun(bot))
