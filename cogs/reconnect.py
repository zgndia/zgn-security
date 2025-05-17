import discord
from discord.ext import commands, tasks
import asyncio
from rich.console import Console
from main import GUILD_ID, VOICE_CHANNEL

# Initialize the console for styled output
console = Console()

# Define a class for managing voice channel reconnection
class ReconnectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Store the bot instance
        self.GUILD_ID = GUILD_ID  # Store the guild ID
        self.TARGET_VOICE_CHANNEL_ID = VOICE_CHANNEL  # Store the target voice channel ID
        self.voice_client = None  # Track the current voice client
        self.voice_channel = None  # Track the target voice channel
        self._reconnecting = False  # Flag to prevent multiple reconnection attempts

    # Clean up when the cog is unloaded
    def cog_unload(self):
        self.voice_reconnect_task.cancel()  # Stop the reconnection task

    # Initialize the bot's voice state on startup
    async def initialize_voice_state(self):
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready
        try:
            guild = await self.bot.fetch_guild(self.GUILD_ID)  # Fetch the guild
            if not guild:
                return

            # Fetch the target voice channel
            self.voice_channel = await guild.fetch_channel(self.TARGET_VOICE_CHANNEL_ID)
            if not self.voice_channel or not isinstance(self.voice_channel, discord.VoiceChannel):
                return

            # Check if the bot is already connected to a voice channel
            if guild.voice_client and guild.voice_client.is_connected():
                self.voice_client = guild.voice_client
                # If connected to the wrong channel, reconnect to the target
                if guild.voice_client.channel.id != self.TARGET_VOICE_CHANNEL_ID:
                    await self.connect_to_channel()
            else:
                await self.connect_to_channel()  # Connect to the target channel
        except Exception as e:
            pass  # Silently handle errors

    # Disconnect the bot from its current voice channel
    async def disconnect_from_channel(self):
        """Disconnect the bot from its current voice channel."""
        try:
            guild = await self.bot.fetch_guild(self.GUILD_ID)  # Fetch the guild
            if not guild:
                print("Guild error")
                return False

            # If the bot is connected, disconnect it
            if guild.voice_client and guild.voice_client.is_connected():
                await guild.voice_client.disconnect(force=True)
                self.voice_client = None  # Clear the voice client
                return True
            return False
        except Exception as e:
            self.voice_client = None
            print(e)  # Log the error
            return False

    # Connect the bot to the target voice channel
    async def connect_to_channel(self):
        """Connect to the target voice channel, disconnecting from any other channel first."""
        try:
            guild = await self.bot.fetch_guild(self.GUILD_ID)  # Fetch the guild
            if not guild:
                return

            # Fetch the target voice channel
            self.voice_channel = await guild.fetch_channel(self.TARGET_VOICE_CHANNEL_ID)
            if not self.voice_channel or not isinstance(self.voice_channel, discord.VoiceChannel):
                return

            # Check if the bot is already in the correct voice channel
            if guild.voice_client and guild.voice_client.is_connected():
                if str(guild.voice_client.channel.id) == str(self.TARGET_VOICE_CHANNEL_ID):
                    self.voice_client = guild.voice_client
                    return
                # Disconnect from the current channel
                await self.disconnect_from_channel()

            # Fetch the bot's member object
            bot_member = guild.me or await guild.fetch_member(self.bot.user.id)
            if not bot_member:
                return

            # Check if the bot has permission to connect and speak
            permissions = self.voice_channel.permissions_for(bot_member)
            if not permissions.connect or not permissions.speak:
                return

            # Connect to the target voice channel
            self.voice_client = await self.voice_channel.connect(timeout=15.0, reconnect=True)
        except discord.errors.Forbidden:
            pass  # Silently handle permission errors
        except discord.errors.ClientException as e:
            self.voice_client = None  # Clear voice client on client error
        except asyncio.TimeoutError:
            self.voice_client = None  # Clear voice client on timeout
        except Exception as e:
            self.voice_client = None  # Clear voice client on other errors

    # Listener for when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        await self.initialize_voice_state()  # Initialize voice state
        # Start the reconnection task if not already running
        if not self.voice_reconnect_task.is_running():
            self.voice_reconnect_task.start()

    # Listener for voice state updates
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id != self.bot.user.id:
            return  # Ignore updates for other members

        # If the bot is disconnected, reconnect to the target channel
        if after.channel is None:
            await self.connect_to_channel()
        
        # If the bot is in the wrong channel, reconnect to the target
        elif str(after.channel.id) != str(self.TARGET_VOICE_CHANNEL_ID):
            print(after.channel)  # Log the current channel
            try:
                await self.disconnect_from_channel()  # Disconnect from current channel
                await self.connect_to_channel()  # Connect to target channel
            except discord.errors.ClientException as e:
                console.print(f"Connection error: {e}", style="bold red")  # Log client errors
            except discord.errors.Forbidden:
                console.print(f"Bot lacks permission to access channel", style="bold red")  # Log permission errors
            except Exception as e:
                console.print(f"Reconnection error: {e}", style="bold red")  # Log other errors
            finally:
                self._reconnecting = False  # Reset debounce flag

    # Periodic task to ensure the bot stays connected to the target channel
    @tasks.loop(seconds=10)
    async def voice_reconnect_task(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready
        try:
            guild = await self.bot.fetch_guild(self.GUILD_ID)  # Fetch the guild
            if not guild:
                return

            # Check if the bot is connected to the correct channel
            if guild.voice_client and guild.voice_client.is_connected():
                if guild.voice_client.channel.id != self.TARGET_VOICE_CHANNEL_ID:
                    await self.connect_to_channel()  # Reconnect if in the wrong channel
            else:
                await self.connect_to_channel()  # Connect if not connected
        except Exception:
            pass  # Silently handle errors

# Setup function to load the ReconnectCog
async def setup(bot):
    console.print("[reconnect.py] loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(ReconnectCog(bot))