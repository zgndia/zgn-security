import discord
from discord.ext import commands
from rich.console import Console
from datetime import datetime, timedelta
from main import GUILD_URL, CLIENT_PROFILE_URL, PREFIX, GUILD_NAME

# Initialize the console for styled output
console = Console()

# Define a class for handling the help command
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Command to display information about available commands
    @commands.command(help='Provides information about commands.')
    async def help(self, ctx):
        try:
            embed = self.get_embed()  # Generate the help embed
            await ctx.send(embed=embed)  # Send the embed to the channel
        except Exception as e:
            console.print(e, style="bold rgb(204,0,0)")  # Log errors in red

    # Function to create a formatted embed listing all commands
    def get_embed(self):
        embed = discord.Embed(
            title="Commands",  # Translated from "Komutlar"
            description=f"Information about the current commands available in Zgn Security.",  # Translated
            colour=0x00b0f4,
            timestamp=datetime.now()
        )

        # Set embed author with bot's name and profile picture
        embed.set_author(name="Zgn Security",
                        icon_url=CLIENT_PROFILE_URL)

        # Set embed footer with guild name and icon
        embed.set_footer(text=GUILD_NAME, icon_url=GUILD_URL)  # Replaced "Unity Roleplay"
        
        # Add a field for each command with its name and help text
        for command in self.bot.commands:
            embed.add_field(
                name=str(PREFIX + command.name),
                value=command.help,
                inline=True
            )

        return embed

# Setup function to load the Help cog
async def setup(bot):
    console.print("[help.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(Help(bot))