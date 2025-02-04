# Boss Alert Discord Bot

A Discord bot that helps track and alert for boss spawn times in games. The bot maintains a schedule of boss spawns, sends alerts before they appear, and allows manual tracking of boss deaths.

## Features

- 🕒 Tracks boss spawn cycles automatically
- ⏰ Sends alerts 10 minutes before boss spawns
- 📝 Maintains fixed spawn schedules for each boss
- 🔄 Adjusts schedules when bosses are killed
- 🌎 Timezone-aware scheduling

## Commands

- `!list_bosses` - Shows all bosses with their next spawn times and includes interactive buttons:
  - "Refresh Times" button to update the times
  - "Show Images" button to display all boss images

- `!next <boss_name>` - Shows specific boss information and next spawn time
  Example: `!next Betalanse`

- `!next_boss` - Shows which boss will spawn next, including location and time until spawn

- `!select_boss` - Opens a dropdown menu to select and view boss information


## Documentation

You can find everything you need here: [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html)

### Prerequisites

- Python 3.11 best compatible version with [discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
- A Discord bot token
- A Discord server with a channel for alerts
