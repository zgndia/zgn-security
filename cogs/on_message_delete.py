from discord.ext import commands
import discord
from datetime import datetime
from discord.utils import utcnow
from rich.console import Console

# Initialize the console for styled output
console = Console()

from main import DELETED_MESSAGE_CHANNEL, CLIENT_PROFILE_URL, GUILD_URL, GUILD_NAME

# Define a class for logging deleted messages
class DeleteLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance

    # Listener for when a message is deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        try:
            # Ignore messages from bots or the bot itself
            if message.author.bot:
                return
            if message.author.id == self.bot.user.id:
                return

            # Fetch the channel for logging deleted messages
            channel = self.bot.get_channel(int(DELETED_MESSAGE_CHANNEL))
            if channel is None:
                console.print(f"Delete log channel not found: {DELETED_MESSAGE_CHANNEL}", style="bold red")
                return

            deleter = None
            guild = message.guild

            # Get message content or indicate if it's empty/non-text
            content = message.content or "[Empty Message or Non-Text Content]"

            # Check audit logs for the message deleter if permissions allow
            if guild is not None and guild.me.guild_permissions.view_audit_log:
                async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                    if entry.target.id == message.author.id:
                        time_diff = (utcnow() - entry.created_at).total_seconds()
                        if time_diff < 5 and hasattr(entry.extra, "channel") and entry.extra.channel.id == message.channel.id:
                            deleter = entry.user  # Store the user who deleted the message
                            break

            # Create embed with or without deleter information
            if deleter:
                embed = get_embed(
                    message.author,
                    f'<#{message.channel.id}>',
                    content,
                    msg_deleter=deleter
                )
            else:
                embed = get_embed(
                    message.author,
                    f'<#{message.channel.id}>',
                    content
                )

            # Send the embed to the log channel
            await channel.send(embed=embed)

        except Exception as e:
            console.print("[message_delete.py]", e, style="bold rgb(204,0,0)", markup=False)  # Log errors in red

# Function to create a formatted embed for deleted message logs
def get_embed(user, channel, full_message, msg_deleter=None):
    description = (
        f"A message sent by {str(user.display_name)} in {str(channel)} was detected as deleted.\n\n"
        f"Deleted message:\n```\n{str(full_message)}\n```\n"
        f"User ID: {str(user.id)}"
    )

    if msg_deleter:
        description += f"\n\nDeleted by: {str(msg_deleter.display_name)}"

    embed = discord.Embed(
        title="Message Deleted",  # Translated from "Mesaj Silindi"
        description=description,
        colour=0x00b0f4,
        timestamp=datetime.now()
    )

    # Set embed author with bot's name and profile picture
    embed.set_author(name="Zgn Security",
                    icon_url=CLIENT_PROFILE_URL)
    # Set embed footer with guild name and icon
    embed.set_footer(text=GUILD_NAME, icon_url=GUILD_URL)  # Replaced "Unity Roleplay" with GUILD_NAME

    return embed

# Setup function to load the DeleteLog cog
async def setup(bot):
    console.print("[on_message_delete.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(DeleteLog(bot))