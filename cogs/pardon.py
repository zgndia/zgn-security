import discord
from discord.ext import commands
from rich.console import Console
from datetime import datetime
from discord.utils import utcnow
import json
from main import CLIENT_PROFILE_URL, GUILD_URL, GUILD_NAME

# Initialize the console for styled output
console = Console()

# Define a class for handling pardon commands
class Pardon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Command to remove a member's timeout, requires moderate_members permission
    @commands.command(name="pardon", help="`[STAFF]` Removes a member's timeout.")
    @commands.has_permissions(moderate_members=True)
    async def pardon(self, ctx, member_input, *, reason="None"):
        try:
            member = None

            # Handle member input (either a Member object or ID/mention)
            if isinstance(member_input, discord.Member):
                member = member_input
            else:
                # Extract member ID from mention or raw input
                member_id_str = str(member_input).strip('<@!>')
                member_id = int(member_id_str)

                # Try to get member from cache, else fetch from API
                member = ctx.guild.get_member(member_id)
                if member is None:
                    member = await ctx.guild.fetch_member(member_id)

            # Check if the member is currently timed out
            if member.timed_out_until is None or member.timed_out_until < utcnow():
                await ctx.send(f"{member.display_name} is not timed out.")
                return
            
            try:
                # Load punishment data from JSON file
                with open("data/punishment_data.json", 'r') as file:
                    try:
                        data = json.load(file)  # Load existing JSON data
                    except json.JSONDecodeError:  # Handle empty or invalid JSON
                        data = {}  # Initialize empty dictionary

                    # Update punishment count for the member
                    user_id = str(member.id)
                    if user_id in data:
                        punish_count = int(data[user_id]) - 1  # Decrease punishment count
                        if punish_count < 0:
                            punish_count = 0
                        data[user_id] = str(punish_count)  # Update count

                    # Write updated data back to JSON file
                    with open("data/punishment_data.json", 'w') as file:
                        json.dump(data, file, indent=4)  # Pretty print JSON

            except Exception as e:
                console.print(f"An error occurred: {e}", style="bold rgb(204,0,0)")  # Log errors in red

            # Remove the member's timeout
            await member.edit(timed_out_until=None)
            # Send confirmation embed with reason
            await ctx.send(embed=get_embed(
                f"{member.display_name}'s timeout has been removed.",  # Translated
                f"Reason for timeout removal:\n```\n{reason}```"
            ))

        except discord.NotFound:
            await ctx.send("The specified user was not found in the server.")  # Translated
        except discord.Forbidden:
            await ctx.send("I don't have permission to remove the member's timeout.")  # Translated
        except Exception as e:
            await ctx.send(f"An error occurred while removing the timeout: {e}")  # Translated

# Function to create a formatted embed for notifications
def get_embed(title, description):
    embed = discord.Embed(title=title, description=description,
                         colour=0x00b0f4,
                         timestamp=datetime.now())
    
    # Set embed author with bot's name and profile picture
    embed.set_author(name="Zgn Security",
                    icon_url=CLIENT_PROFILE_URL)

    # Set embed footer with guild name and icon
    embed.set_footer(text=GUILD_NAME,  # Replaced "Unity Roleplay" with GUILD_NAME
                    icon_url=GUILD_URL)

    return embed

# Setup function to load the Pardon cog
async def setup(bot):
    console.print("[pardon.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(Pardon(bot))