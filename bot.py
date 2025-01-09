# This example requires the 'message_content' intent.

import discord
from discord.ext import commands
from discord import Intents
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

@bot.event
async def on_ready():
    print('Bot is ready')

bot.run(os.getenv('BOT_TOKEN'))
