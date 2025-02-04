import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta
import asyncio
import pytz
import json

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Get your timezone
timezone = pytz.timezone('America/Mexico_City')  # Change this to your timezone

def get_boss_image(boss_info):
    """Get boss image if it exists"""
    if 'image' in boss_info and os.path.exists(boss_info['image']):
        return discord.File(boss_info['image'])
    return None

# Load bosses from JSON file
def load_bosses():
    with open('bosses.json', 'r') as f:
        boss_data = json.load(f)
        
    # Convert the base_time from JSON format to timezone-aware datetime
    for boss in boss_data.values():
        base = boss['base_time']
        boss['base_time'] = timezone.localize(
            datetime.now().replace(
                hour=base['hour'],
                minute=base['minute'],
                second=base['second'],
                microsecond=0
            )
        )
    return boss_data

# Load bosses at startup
bosses = load_bosses()

async def check_spawns():
    await bot.wait_until_ready()
    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    
    while not bot.is_closed():
        current_time = timezone.localize(datetime.now())
        
        for boss_name, info in bosses.items():
            # If no death recorded, use base_time to calculate next spawn
            if info['last_death'] is None:
                base = info['base_time']
                while base < current_time:
                    base += timedelta(hours=info['cycle'])
                next_spawn = base
            else:
                next_spawn = info['last_death'] + timedelta(hours=info['cycle'])
            
            time_until_spawn = next_spawn - current_time
            
            # If 10 minutes before spawn and haven't alerted yet
            if timedelta(minutes=9) < time_until_spawn <= timedelta(minutes=10) and not info['alerted']:
                image = get_boss_image(info)
                if image:
                    await channel.send(
                        f'⚠️ **Alert**: {boss_name} will spawn in 10 minutes in {info["location"]}! (at {next_spawn.strftime("%H:%M:%S")})',
                        file=image
                    )
                else:
                    await channel.send(f'⚠️ **Alert**: {boss_name} will spawn in 10 minutes in {info["location"]}! (at {next_spawn.strftime("%H:%M:%S")})')
                info['alerted'] = True
            
            # Reset alert flag after spawn time
            if time_until_spawn <= timedelta(0):
                info['alerted'] = False
                if info['last_death'] is None:  # Only for base_time spawns
                    info['base_time'] = next_spawn + timedelta(hours=info['cycle'])
        
        await asyncio.sleep(60)  # Check every minute

@bot.event
async def on_ready():
    print('Bot is ready and running')
    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    await channel.send('BOSS ALERT BOT is ready!')
    bot.loop.create_task(check_spawns())

@bot.command()
async def dead(ctx, *, boss_name: str):
    """Record boss death time. Usage: !dead bossName"""
    if boss_name in bosses:
        bosses[boss_name]['last_death'] = timezone.localize(datetime.now())
        bosses[boss_name]['alerted'] = False
        next_spawn = datetime.now() + timedelta(hours=bosses[boss_name]['cycle'])
        
        image = get_boss_image(bosses[boss_name])
        if image:
            await ctx.send(
                f'{boss_name} died. Next spawn at {next_spawn.strftime("%H:%M:%S")}',
                file=image
            )
        else:
            await ctx.send(f'{boss_name} died. Next spawn at {next_spawn.strftime("%H:%M:%S")}')
    else:
        await ctx.send(f'Unknown boss: {boss_name}')

@bot.command()
async def next(ctx, *, boss_name: str):
    """Check next spawn time. Usage: !next bossName"""
    if boss_name in bosses:
        info = bosses[boss_name]  # This 'info' is the boss_info dictionary
        # Now info contains all the boss data from JSON
        current_time = timezone.localize(datetime.now())
        
        if info['last_death']:
            next_spawn = info['last_death'] + timedelta(hours=info['cycle'])
        else:
            base = info['base_time']
            while base < current_time:
                base += timedelta(hours=info['cycle'])
            next_spawn = base
        
        time_until = next_spawn - current_time
        image = get_boss_image(info)
        if image:
            await ctx.send(
                f'{boss_name} ({info["location"]}) next spawn: {next_spawn.strftime("%H:%M:%S")} (in {str(time_until).split(".")[0]})',
                file=image
            )
        else:
            await ctx.send(f'{boss_name} ({info["location"]}) next spawn: {next_spawn.strftime("%H:%M:%S")} (in {str(time_until).split(".")[0]})')
    else:
        await ctx.send(f'Unknown boss: {boss_name}')

@bot.command()
async def list_bosses(ctx):
    """List all bosses and their spawn cycles"""
    message = "Boss List:\n```"
    current_time = timezone.localize(datetime.now())
    
    for boss, info in bosses.items():
        if info['last_death']:
            next_spawn = info['last_death'] + timedelta(hours=info['cycle'])
        else:
            base = info['base_time']
            while base < current_time:
                base += timedelta(hours=info['cycle'])
            next_spawn = base
        
        time_until = next_spawn - current_time
        message += f"{boss} ({info['location']}): {info['cycle']}h cycle - Next: {next_spawn.strftime('%H:%M:%S')} (in {str(time_until).split('.')[0]})\n"
    message += "```"
    await ctx.send(message)

bot.run(os.getenv('BOT_TOKEN'))
