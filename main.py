import json
import re
import asyncio
import os
import nacl
import discord
from rich.console import Console
from discord.ext import commands

def remove_comments(jsonc_string):
    # Remove comments only if they are not inside string literals
    def replacer(match):
        group = match.group(0)
        if group.startswith('//'):
            return ''
        return group
    pattern = r'(\".*?\"|\'.*?\'|//.*?$)'
    return re.sub(pattern, replacer, jsonc_string, flags=re.MULTILINE)

# Read the JSONC file
with open('config/config.jsonc', 'r', encoding='utf-8') as file:
    jsonc_data = file.read()

# Remove comments from the JSONC data
json_data = remove_comments(jsonc_data)

# Parse the JSON data
CONFIG = json.loads(json_data)
DATA_CL = CONFIG["Client_Data"]
GUILD = CONFIG["Guild_Data"]
MODERATION = CONFIG["Moderation"]

### Datas here
TOKEN = DATA_CL["token"]
PREFIX = DATA_CL["prefix"]
OWNERID = DATA_CL["ownerID"]
RICH_PRESENCE = DATA_CL["discordRichPresence"]
EXCLAMATION_MARK = DATA_CL["excalamationImage"]
CLIENT_PROFILE_URL = DATA_CL["clientProfilePicture"]

BAD_WORDS = MODERATION["badWords"]

GUILD_NAME = GUILD["guildName"]
GUILD_URL = GUILD["guildImage"]
DELETED_MESSAGE_CHANNEL = GUILD["deletedMsgLogChannel"]
GUILD_ID = GUILD["guildID"]
TIMEOUT_CHANNEL = GUILD["timeoutLogChannel"]
BAD_WORDS_CHANNEL = GUILD["badWordLogChannel"]
VOICE_CHANNEL = GUILD["voiceChannelID"]
SERVER_STATUS = GUILD["serverStatus"]
ROLE_ADD_LOG = GUILD["roleAddLog"]
ROLE_REMOVE_LOG = GUILD["roleRemoveLog"]

console = Console()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True


Client = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

def line():
    console.print('------------------------------------------------------------------------------------------', style="bold rgb(255,240,255)")

# Bot is ready
@Client.event
async def on_ready():
    line()
    console.print(f'Logged in as {Client.user}', style="bold rgb(235,185,255)")
    line()
    console.print("Registered Commands:", style="bold rgb(235,185,255)")
    for command in Client.commands:
        console.print(str(command.name) + " --> " + str(command.help).replace("`",""), style="bold rgb(235,185,255)")
    line()
    await Client.change_presence(
        status=discord.Status.online,
        activity=discord.Game(RICH_PRESENCE)
    )
    try:
        vc = await Client.fetch_channel(VOICE_CHANNEL)
        await vc.connect()
    except Exception as e:
        console.print(e, style="bold rgb(204,0,0)")


# Automatically load all cogs in /cogs folder
async def load_cogs():
    line()
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await Client.load_extension(f'cogs.{filename[:-3]}')  # Strip .py


async def main():
    await load_cogs()
    await Client.start(TOKEN)

if __name__ == "__main__":
    line()
    console.print("""
 ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄    ▄    ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄   ▄▄▄ ▄▄▄▄▄▄▄ ▄▄   ▄▄ 
█       █       █  █  █ █  █       █       █       █  █ █  █   ▄  █ █   █       █  █ █  █
█▄▄▄▄   █   ▄▄▄▄█   █▄█ █  █  ▄▄▄▄▄█    ▄▄▄█       █  █ █  █  █ █ █ █   █▄     ▄█  █▄█  █
 ▄▄▄▄█  █  █  ▄▄█       █  █ █▄▄▄▄▄█   █▄▄▄█     ▄▄█  █▄█  █   █▄▄█▄█   █ █   █ █       █
█ ▄▄▄▄▄▄█  █ █  █  ▄    █  █▄▄▄▄▄  █    ▄▄▄█    █  █       █    ▄▄  █   █ █   █ █▄     ▄█
█ █▄▄▄▄▄█  █▄▄█ █ █ █   █   ▄▄▄▄▄█ █   █▄▄▄█    █▄▄█       █   █  █ █   █ █   █   █   █  
█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄█  █▄▄█  █▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄█  █▄█▄▄▄█ █▄▄▄█   █▄▄▄█  

""", style="bold rgb(179,0,255)")
    asyncio.run(main())

# Title color (179,0,255)
# Print color (235,185,255)
# Warn color (255,165,10)
# Error color (204,0,0)