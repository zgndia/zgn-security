import discord
from discord.ext import commands
import asyncio
from rich.console import Console
from datetime import datetime
from main import SERVER_STATUS

# Initialize the console for styled output
console = Console()

# Define a class for security-related commands
class SecurityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antiraid_enabled = None  # Tracks if anti-raid is enabled
        self.locked_channels = set()  # Stores IDs of locked channels
        self.ar_on = "Anti-Raid Status: ON"  # Message for anti-raid enabled
        self.ar_off = "Anti-Raid Status: OFF"  # Message for anti-raid disabled

    # Command to lock or unlock a channel, requires manage_channels permission
    @commands.has_permissions(manage_channels=True)
    @commands.command(name="lockdown", help='[STAFF] Prevents messages from being sent in the selected channel.')
    async def lockdown(self, ctx, duration: int = None):
        """Locks or unlocks a channel. Optional duration (in seconds) can be provided."""

        try:
            channel = ctx.channel  # Get the current channel
            overwrite = channel.overwrites_for(ctx.guild.default_role)  # Get permissions for @everyone

            # If channel is already locked, unlock it
            if channel.id in self.locked_channels:
                overwrite.send_messages = None  # Reset send_messages permission
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                self.locked_channels.remove(channel.id)  # Remove from locked channels
                await ctx.send(f"🔓 {channel.mention} has been unlocked.")
                return

            # Lock the channel by denying send_messages permission
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            self.locked_channels.add(channel.id)  # Add to locked channels
            if duration:
                await ctx.send(f"🔒 {channel.mention} has been locked for {duration} seconds.")
                await asyncio.sleep(duration)  # Wait for the specified duration

                # Unlock the channel after duration if still locked
                if channel.id in self.locked_channels:
                    overwrite.send_messages = None
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    self.locked_channels.remove(channel.id)
                    await ctx.send(f"🔓 {channel.mention} has been unlocked after {duration} seconds.")
            else:
                await ctx.send(f"🔒 {channel.mention} has been temporarily locked.")
        except Exception as e:
            console.print("[security.py]", e, style="bold rgb(204,0,0)", markup=False)  # Log errors in red

    # Listener for when a new member joins the server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Initialize anti-raid status if not set
        if self.antiraid_enabled is None:
            self.antiraid_enabled = await SecurityCommands.antiraid.get_ar_data(self)
        if self.antiraid_enabled:
            # Check if the account is less than 14 days old
            account_age = (datetime.utcnow() - member.created_at).days
            if account_age <= 14:
                try:
                    # Kick the member if their account is too new
                    await member.kick(reason="Anti-raid: Account was kicked because it is less than 2 weeks old")
                    print(f"{member} was kicked due to anti-raid.")
                except Exception as e:
                    console.print(f"{member} could not be kicked: {e}", style="bold rgb(204,0,0)", markup=False)

    # Command to toggle anti-raid feature, requires administrator permission
    @commands.has_permissions(administrator=True)
    @commands.command(help="[STAFF] Toggles the server's anti-raid feature.")
    async def antiraid(self, ctx, toggle=""):
        try:
            # Fetch the status channel
            channel = await self.bot.fetch_channel(SERVER_STATUS)

            # Initialize anti-raid status if not set
            if self.antiraid_enabled is None:
                self.antiraid_enabled = await get_ar_data(self, channel)

            # Toggle anti-raid if no valid input or empty
            if toggle.lower() not in ["on", "off"] or toggle == "":
                self.antiraid_enabled = not self.antiraid_enabled
            
            # Set anti-raid based on explicit toggle
            if toggle.lower() == "on":
                self.antiraid_enabled = True
            elif toggle.lower() == "off":
                self.antiraid_enabled = False
            
            await ctx.message.delete()  # Delete the command message
            # Send temporary status message
            if self.antiraid_enabled:
                await ctx.send("Anti-Raid enabled.", mention_author=False, delete_after=3)
            else:
                await ctx.send("Anti-Raid disabled.", mention_author=False, delete_after=3)

            # Update the status message in the status channel
            messages = await get_messages(channel)
            for message in messages:
                if message.author == self.bot.user:
                    if message.content == self.ar_on and not self.antiraid_enabled:
                        await message.edit(content=self.ar_off)
                        return
                    elif message.content == self.ar_off and self.antiraid_enabled:
                        await message.edit(content=self.ar_on)
                        return
            
            # Send new status message if none exists
            if self.antiraid_enabled:
                await channel.send(self.ar_on)
            else:
                await channel.send(self.ar_off)
        except Exception as e:
            console.print(e, style="bold rgb(204,0,0)", markup=False)  # Log errors in red

    # Command to restrict or allow a role's permissions, requires administrator permission
    @commands.has_permissions(administrator=True)
    @commands.command(name="rolelock", help='[STAFF] Restricts the permissions of the selected role.')
    async def rolelock(self, ctx, role: discord.Role, toggle: str):
        """Prevents or allows a role from sending messages in all text channels."""
        if toggle.lower() not in ["on", "off"]:
            return await ctx.send("Usage: !rolelock @Role on/off")

        # Update permissions for the role in all text channels
        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(role)
                if toggle.lower() == "on":
                    overwrite.send_messages = False  # Deny send_messages
                else:
                    overwrite.send_messages = None  # Reset send_messages
                await channel.set_permissions(role, overwrite=overwrite)
            except Exception as e:
                console.print(f"Error in channel {channel.name}: {e}", style="bold rgb(204,0,0)", markup=False)

        await ctx.send(f"🔐 {role.name} role has been set to {toggle} in all channels.")

# Function to fetch recent messages from a channel
async def get_messages(channel):
    messages = []
    async for msg in channel.history(limit=20):
        messages.append(msg)
            
    return messages
        
# Function to retrieve anti-raid status from channel messages
async def get_ar_data(self, channel):
    try:
        for message in await get_messages(channel):
            if message.author == self.bot.user:
                if message.content == self.ar_on:
                    return True
                elif message.content == self.ar_off:
                    return False
        return False  # Default to disabled if no status found
    except Exception as e:
        console.print(e, style="bold rgb(204,0,0)", markup=False)
        return False

# Setup function to load the SecurityCommands cog
async def setup(bot):
    console.print("[security.py] is loading...", style="bold rgb(235,185,255)", markup=False)
    await bot.add_cog(SecurityCommands(bot))