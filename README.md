# Discord Boss Timer Bot

A Discord bot that helps track and alert for boss spawn times in games. The bot maintains a schedule of boss spawns, sends alerts before they appear, and allows manual tracking of boss deaths.

## Features

- 🕒 Tracks boss spawn cycles automatically
- ⏰ Sends alerts 10 minutes before boss spawns
- 📝 Maintains fixed spawn schedules for each boss
- 🔄 Adjusts schedules when bosses are killed
- 🌎 Timezone-aware scheduling

The code in bot.py is designed for a game called PixelHeros. You can further enhance the code if you have access to the API of the game for which you want to create the Boss alerts.

## Commands

- `!next <boss_name>` - Shows when a specific boss will spawn next
- `!dead <boss_name>` - Records a boss death and calculates next spawn
- `!list_bosses` - Shows all bosses and their next spawn times

## Documentation

You can find everything you need here: [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html)

### Prerequisites

- Python 3.11 (best compatible version with [discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
- A Discord bot token
- A Discord server with a channel for alerts
