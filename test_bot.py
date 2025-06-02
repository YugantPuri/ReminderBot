from dotenv import load_dotenv
import os
import datetime
import discord
from discord.ext import commands

load_dotenv()

api_key = os.getenv("API_KEY")



intents = discord.Intents.default()
intents.message_content = True  # Needed to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm your bot.")

bot.run(api_key)