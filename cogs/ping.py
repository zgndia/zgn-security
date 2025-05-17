import discord
from discord.ext import commands
from rich.console import Console

# Initialize the console for styled output
console = Console()

# Define a class for general commands
class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Command to respond with "Pong!" when invoked
    @commands.command(help='Responds to the user with a "Pong!" message.')
    async def ping(self, ctx):
        await ctx.reply("Pong!", mention_author=False)  # Reply to the user without mentioning them

# Setup function to load the General cog
async def setup(bot):
    console.print("[ping.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(General(bot))