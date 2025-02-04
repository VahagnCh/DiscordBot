import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta
import asyncio
import pytz
import json
from discord.ui import Button, View, Select
from discord import ButtonStyle

# Set up Discord bot with message content intent
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Set timezone for all time calculations
timezone = pytz.timezone('America/Mexico_City')

# Cache system to store spawn calculations and reduce computation
spawn_cache = {}  # Stores next spawn times for each boss
CACHE_DURATION = timedelta(minutes=1)  # How long to keep cached values
last_cache_update = None  # Tracks when cache was last updated

def calculate_next_spawn(base_time, cycle_hours, current_time):
    """
    Calculate the next spawn time for a boss
    base_time: Initial spawn time
    cycle_hours: Hours between spawns
    current_time: Current time to calculate from
    Returns: Next spawn time after current_time
    """
    while base_time < current_time:
        base_time += timedelta(hours=cycle_hours)
    return base_time

def update_spawn_cache():
    """
    Update the cache with latest spawn calculations for all bosses
    Stores both next spawn time and time until spawn for each boss
    """
    global last_cache_update
    current_time = timezone.localize(datetime.now())
    
    for boss_name, info in bosses.items():
        next_spawn = calculate_next_spawn(
            info['base_time'],
            info['cycle'],
            current_time
        )
        spawn_cache[boss_name] = {
            'next_spawn': next_spawn,
            'time_until': next_spawn - current_time
        }
    
    last_cache_update = current_time

def get_next_spawn(boss_info, current_time=None):
    """
    Get next spawn time for a specific boss
    boss_info: Dictionary containing boss information
    current_time: Time to calculate from (defaults to now)
    """
    if current_time is None:
        current_time = timezone.localize(datetime.now())
    
    return calculate_next_spawn(
        boss_info['base_time'],
        boss_info['cycle'],
        current_time
    )

def get_boss_image(boss_info):
    """
    Get the image file for a boss if it exists
    boss_info: Dictionary containing boss information including image path
    Returns: discord.File object or None if image doesn't exist
    """
    if 'image' in boss_info:
        image_path = boss_info['image']
        if os.path.exists(image_path):
            return discord.File(image_path)
    return None

def load_bosses():
    """
    Load boss data from JSON file and initialize spawn times
    Returns: Dictionary of boss information with initialized base times
    """
    with open('bosses.json', 'r') as f:
        boss_data = json.load(f)
    
    # Get current date for base times
    current_time = datetime.now()
    
    # Convert JSON time format to timezone-aware datetime
    for boss in boss_data.values():
        base = boss['base_time']
        # Create naive datetime first, then localize it
        naive_time = current_time.replace(
            hour=base['hour'],
            minute=base['minute'],
            second=base['second'],
            microsecond=0
        )
        # Localize the naive datetime to our timezone
        boss['base_time'] = timezone.localize(naive_time)
    
    return boss_data

# Load boss data at startup
bosses = load_bosses()

async def check_spawns():
    """
    Background task that checks for upcoming boss spawns
    Sends alerts 10 minutes before each boss spawn
    """
    await bot.wait_until_ready()
    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    
    while not bot.is_closed():
        current_time = timezone.localize(datetime.now())
        
        # Update cache if it's expired
        if last_cache_update is None or current_time - last_cache_update > CACHE_DURATION:
            update_spawn_cache()
        
        # Check each boss for upcoming spawns
        for boss_name, info in bosses.items():
            next_spawn = spawn_cache[boss_name]['next_spawn']
            time_until_spawn = next_spawn - current_time
            
            # Send alert if boss spawns in 10 minutes and hasn't been alerted yet
            if timedelta(minutes=9) < time_until_spawn <= timedelta(minutes=10) and not info['alerted']:
                image = get_boss_image(info)
                await channel.send(
                    f'⚠️ **Alert**: {boss_name} will spawn in 10 minutes in {info["location"]}! '
                    f'(at {next_spawn.strftime("%H:%M:%S")})',
                    file=image if image else None
                )
                info['alerted'] = True
            
            # Reset alert flag after spawn time
            if time_until_spawn <= timedelta(0):
                info['alerted'] = False
        
        await asyncio.sleep(60)  # Check every minute

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    print('Bot is ready and running')
    channel = bot.get_channel(int(os.getenv('CHANNEL_ID')))
    await channel.send('BOSS ALERT BOT is ready!')
    bot.loop.create_task(check_spawns())

@bot.command()
async def next(ctx, *, boss_name: str):
    """Check next spawn time. Usage: !next bossName"""
    if boss_name in bosses:
        current_time = timezone.localize(datetime.now())
        info = bosses[boss_name]
        
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
async def next_boss(ctx):
    """Command to show the next boss to spawn"""
    current_time = timezone.localize(datetime.now())
    
    # Update cache if needed
    if last_cache_update is None or current_time - last_cache_update > CACHE_DURATION:
        update_spawn_cache()
    
    # Find boss with earliest spawn time
    next_boss = min(spawn_cache.items(), key=lambda x: x[1]['next_spawn'])
    boss_name, spawn_data = next_boss
    info = bosses[boss_name]
    
    image = get_boss_image(info)
    await ctx.send(
        f'⏰ Next boss: **{boss_name}**\n'
        f'Location: {info["location"]}\n'
        f'Spawns at: {spawn_data["next_spawn"].strftime("%H:%M:%S")} '
        f'(in {str(spawn_data["time_until"]).split(".")[0]})',
        file=image if image else None
    )

# UI Components
class BossView(View):
    """Interactive view for boss list with refresh and image buttons"""
    def __init__(self):
        super().__init__(timeout=180)  # View expires after 3 minutes

    @discord.ui.button(label="Refresh Times", style=ButtonStyle.green)
    async def refresh_button(self, interaction: discord.Interaction, button: Button):
        """Button to refresh the boss list with current times"""
        current_time = timezone.localize(datetime.now())
        update_spawn_cache()
        
        message = "Boss List:\n```"
        for boss_name, spawn_data in spawn_cache.items():
            message += (
                f"{boss_name} ({bosses[boss_name]['location']}): "
                f"{bosses[boss_name]['cycle']}h cycle - Next: "
                f"{spawn_data['next_spawn'].strftime('%H:%M:%S')} "
                f"(in {str(spawn_data['time_until']).split('.')[0]})\n"
            )
        message += "```"
        await interaction.response.edit_message(content=message)

    @discord.ui.button(label="Show Images", style=ButtonStyle.blurple)
    async def images_button(self, interaction: discord.Interaction, button: Button):
        """Button to display all boss images with their information"""
        await interaction.response.defer()
        current_time = timezone.localize(datetime.now())
        
        # Send each boss image with its information
        for boss_name, info in bosses.items():
            image = get_boss_image(info)
            if image:
                next_spawn = spawn_cache[boss_name]['next_spawn']
                time_until = spawn_cache[boss_name]['time_until']
                await interaction.followup.send(
                    f'**{boss_name}** - {info["location"]}\n'
                    f'Next spawn: {next_spawn.strftime("%H:%M:%S")} '
                    f'(in {str(time_until).split(".")[0]})',
                    file=image
                )

@bot.command()
async def list_bosses(ctx):
    """List all bosses and their spawn cycles"""
    current_time = timezone.localize(datetime.now())
    
    message = "Boss List:\n```"
    for boss, info in bosses.items():
        base = info['base_time']
        while base < current_time:
            base += timedelta(hours=info['cycle'])
        next_spawn = base
        time_until = next_spawn - current_time
        message += f"{boss} ({info['location']}): {info['cycle']}h cycle - Next: {next_spawn.strftime('%H:%M:%S')} (in {str(time_until).split('.')[0]})\n"
    message += "```"
    
    view = BossView()
    await ctx.send(message, view=view)

class BossSelect(Select):
    """Dropdown menu for selecting individual bosses"""
    def __init__(self):
        # Create options for each boss with their basic info
        options = [
            discord.SelectOption(
                label=boss_name,
                description=f"{info['location']} - {info['cycle']}h cycle"
            )
            for boss_name, info in bosses.items()
        ]
        super().__init__(
            placeholder="Select a boss to see details",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle boss selection from dropdown"""
        boss_name = self.values[0]
        info = bosses[boss_name]
        
        # Get spawn information from cache
        if last_cache_update is None or timezone.localize(datetime.now()) - last_cache_update > CACHE_DURATION:
            update_spawn_cache()
        
        spawn_data = spawn_cache[boss_name]
        image = get_boss_image(info)
        
        # Send boss information with image if available
        await interaction.response.send_message(
            f'**{boss_name}** ({info["location"]})\n'
            f'Cycle: {info["cycle"]} hours\n'
            f'Next spawn: {spawn_data["next_spawn"].strftime("%H:%M:%S")} '
            f'(in {str(spawn_data["time_until"]).split(".")[0]})',
            file=image if image else None
        )

@bot.command()
async def select_boss(ctx):
    """Command to show boss selection dropdown menu"""
    view = View(timeout=180)  # View expires after 3 minutes
    view.add_item(BossSelect())
    await ctx.send("Select a boss to see details:", view=view)

# Start the bot
bot.run(os.getenv('BOT_TOKEN'))
