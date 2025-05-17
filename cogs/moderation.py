from discord.ext import commands
import discord
import json
from main import GUILD, PREFIX, OWNERID, BAD_WORDS_CHANNEL, TIMEOUT_CHANNEL, BAD_WORDS, GUILD_URL, CLIENT_PROFILE_URL, GUILD_NAME
from datetime import datetime, timedelta
from rich.console import Console

# Initialize the console for styled output
console = Console()

# Define staff and owner role IDs for permission checks
role_ids = GUILD["staff_id"]
role_ids.append(OWNERID)

# Define a class for handling message content moderation
class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Listener for processing incoming messages
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore messages from bots
        if message.content.startswith(PREFIX):  # Check if the message is a command
            return  # Stop processing for commands

        try:
            # Initialize variables for punishment tracking
            punish_time = 0
            timed_out = False
            admin = False  # Track if the user has admin/staff permissions

            # Check if any banned keyword is in the message
            for word in BAD_WORDS:
                if word in message.content.lower():
                    # Check if the user is an admin or has a staff role
                    if message.author.guild_permissions.administrator or any(role.id in [int(role_id) for role_id in role_ids] for role in message.author.roles):
                        admin = True

                    # Fetch channels for logging bad words and timeouts
                    channel = self.bot.get_channel(int(BAD_WORDS_CHANNEL))
                    t_channel = self.bot.get_channel(int(TIMEOUT_CHANNEL))
                    
                    if not admin:
                        await message.delete()  # Delete the message containing the bad word

                        try:
                            # Load punishment data from JSON file
                            with open("data/punishment_data.json", 'r') as file:
                                try:
                                    data = json.load(file)  # Load existing JSON data
                                except json.JSONDecodeError:  # Handle empty or invalid JSON
                                    data = {}  # Initialize empty dictionary

                            # Update punishment count for the user
                            user_id = str(message.author.id)
                            if user_id in data:
                                punish_count = int(data[user_id]) + 1  # Increment count
                                data[user_id] = str(punish_count)
                            else:
                                data[user_id] = "1"  # Initialize count
                                punish_count = 1

                            # Write updated data back to JSON file
                            with open("data/punishment_data.json", 'w') as file:
                                json.dump(data, file, indent=4)  # Pretty print JSON

                        except Exception as e:
                            console.print(f"An error occurred: {e}", style="bold rgb(204,0,0)")  # Log errors in red
                    
                        # Determine timeout duration based on punishment count
                        punish_time = get_punish_time(punish_count)
                        timeout_duration = timedelta(seconds=punish_time)

                        try:
                            # Apply timeout to the user
                            await message.author.timeout(timeout_duration, reason=f"Use of banned word: {word}")
                            timed_out = True
                        except discord.Forbidden:
                            timed_out = False  # Bot lacks permission
                        except Exception as e:
                            timed_out = False
                            console.print(e, style="bold rgb(204,0,0)")  # Log errors

                    # Format duration for display
                    if punish_time / 3600 < 1:
                        dur = "30 minutes"
                    else:
                        dur = str(punish_time / 3600) + " Hours"  # Translated "Saat" to "Hours"

                    # Create embeds for logging
                    t_embed = timeout_embed(message.author, f'Zgn Security: Use of banned word "{word}".', dur)
                    embed = get_embed(message.author, f"<#{message.channel.id}>", word, str(message.content))
                    
                    try:
                        # Send embeds to respective channels
                        await channel.send(embed=embed)
                        if timed_out:
                            await t_channel.send(embed=t_embed)
                    except Exception as e:
                        console.print(f"❌ Error sending embed: {e}", style="bold rgb(204,0,0)")  # Log errors
                    
                    return  # Stop checking after the first bad word
        except Exception as e:
            console.print("[moderation.py]", e, style="bold rgb(204,0,0)")  # Log general errors

        # Allow command processing to continue
        await self.bot.process_commands(message)

# Function to determine timeout duration based on punishment count
def get_punish_time(punish_count):
    if punish_count >= 1 and punish_count < 3:
        punish_time = 30 * 60  # 30 minutes
    elif punish_count >= 3 and punish_count < 5:
        punish_time = 1 * 3600  # 1 hour
    elif punish_count >= 5 and punish_count < 8:
        punish_time = 3 * 3600  # 3 hours
    elif punish_count >= 8 and punish_count < 10:
        punish_time = 6 * 3600  # 6 hours
    elif punish_count >= 10:
        punish_time = 12 * 3600  # 12 hours

    return punish_time

# Function to create an embed for timeout notifications
def timeout_embed(user, reason, duration):
    embed = discord.Embed(
        title="Timeout Detected",  # Translated from "Timeout Tespit Edildi"
        description=f"{str(user.display_name)} has been timed out, reason:\n```\n{reason}```\nTimeout duration: {duration}\nUser ID: {str(user.id)}",
        colour=0x00b0f4,
        timestamp=datetime.now()
    )

    # Set embed author with bot's name and profile picture
    embed.set_author(name="Zgn Security",
                    icon_url=CLIENT_PROFILE_URL)

    # Set embed footer with guild name and icon
    embed.set_footer(text=GUILD_NAME, icon_url=GUILD_URL)  # Replaced "Unity Roleplay"

    return embed

# Function to create an embed for bad word detection
def get_embed(user, channel, bad_word, full_message):
    embed = discord.Embed(
        title="Banned Word Detected",  # Translated from "Küfür Tespit Edildi"
        description=f"{str(user.display_name)} used a banned word in {str(channel)}.\nDetected word:\n```\n{str(bad_word)}\n```\nFull message:\n```\n{str(full_message)}\n```\nUser ID: {str(user.id)}",
        colour=0x00b0f4,
        timestamp=datetime.now()
    )
    
    # Set embed author with bot's name and profile picture
    embed.set_author(name="Zgn Security",
                    icon_url=CLIENT_PROFILE_URL)

    # Set embed footer with guild name and icon
    embed.set_footer(text=GUILD_NAME, icon_url=GUILD_URL)  # Replaced "Unity Roleplay"

    return embed

# Setup function to load the MessageHandler cog
async def setup(bot):
    console.print("[moderation.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(MessageHandler(bot))