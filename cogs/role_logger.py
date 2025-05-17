import discord
from discord.ext import commands
from rich.console import Console
from main import ROLE_ADD_LOG, ROLE_REMOVE_LOG, GUILD_URL, CLIENT_PROFILE_URL, GUILD_NAME
from datetime import datetime

# Initialize the console for styled output
console = Console()

# Define a class for logging role changes
class RoleLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Listener for member updates, specifically role changes
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        try:
            # Check if roles have changed; if not, exit
            if before.roles == after.roles:
                return  # No role change

            # Identify added and removed roles by comparing before and after
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            # Fetch the log channels for role additions and removals
            remove_log = await self.bot.fetch_channel(ROLE_REMOVE_LOG)
            add_log = await self.bot.fetch_channel(ROLE_ADD_LOG)

            # Log added roles
            if added_roles:
                for role in added_roles:
                    await add_log.send(embed=get_embed(
                        "Role Added",  # Translated from "Rol Eklendi"
                        f"<@{after.id}> has been assigned the role: <@&{role.id}>"
                    ))
            # Log removed roles
            if removed_roles:
                for role in removed_roles:
                    await remove_log.send(embed=get_embed(
                        "Role Removed",  # Translated from "Rol Alındı"
                        f"<@{after.id}> has lost the role: <@&{role.id}>"
                    ))
        except Exception as e:
            console.print(e, style="bold red")  # Log errors in bold red

# Function to create a formatted embed for logging
def get_embed(title, description):
    # Create an embed with the specified title and description
    embed = discord.Embed(title=title, description=description,
                         colour=0x00b0f4,
                         timestamp=datetime.now())
    
    # Set the author field with the bot's name and profile picture
    embed.set_author(name="Zgn Security",
                    icon_url=CLIENT_PROFILE_URL)

    # Set the footer with the server name and icon
    embed.set_footer(text=GUILD_NAME,
                    icon_url=GUILD_URL)

    return embed

# Setup function to load the RoleLogger cog
async def setup(bot):
    console.print("[role_logger.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(RoleLogger(bot))