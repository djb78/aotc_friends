# AotC Friends
An automated command-line tool that analyzes Warcraft Logs to track raid attendance, map alts to mains, and recognize every player who contributed to a guild's Ahead of the Curve (AotC) progression.

## Features
Raid logs filtering:
- **Raid Schedule:** leaves out logs that don't coincide with a user provided schedule.
- **AOTC Cutoff:** stops counting pulls after the final boss is killed.

Character stats:
- **Progression Pull Counts:** how many boss pulls each character was present for.
- **Spec & Role Breakdown:** What specs they played, and how often.

Alt mapping (optional):
- **Alt Grouping:** mains and related alts are grouped. tier main determined by highest attendance
- **Player Attendance:** alt pull counts are combined to show player-level attendance.
- **Output Format:** Display nested spec breakdowns for each alt

## Prerequisites
To get data from Warcraft Logs, you need a free client ID and client secret from the [Warcraft Logs Developer Portal](https://www.warcraftlogs.com/api/clients/).

## Setup
### 1. Get the program
clone the repo to the desired location on your local machine
```
git clone https://github.com/djb78/aotc_friends.git
cd aotc-friends
```
### 2. Set up a virtual environment (venv)
create:
```
python -m venv venv
```
activate:
```
windows:     .\venv\Scripts\activate
macos/linux: source venv/bin/activate
```
install dependencies:
```
pip install -r requirements.txt
```

## Configuration
Create a file named `.env` in the root directory of the project and add your warcraftlogs credentials:
```env
WCL_CLIENT_ID=yourid
WCL_CLIENT_SECRET=yoursecret
```
user settings can be controlled from config.json in the root directory

### required fields
- **`zone_id`**: Identifies the raid tier to analyze (see below).
- **`guild_id`**: The guild's numerical ID found in their Warcraft Logs URL. Used to get logs officially attributed to the guild.
- **`region`**: `"US"`, `"EU"`, etc. Used to uniquely identify the guild and characters.
- **`anchor_alt`**: The `"Name-Server"` string of a raider alt with high attendance. Used to fill in any gaps in guild attributed logs.
### optional fields
- **`guild_name`**: Cosmetic flavor for the final report header.
- **`schedule`**: Raid days and times. Logs outside of these windows are automatically ignored. If schedule details are missing or formatted incorrectly, no time-filtering is applied.
- **`has_alts`**: A mapping of player alts to their main characters. If no alts are defined, characters are listed individually

```json
{
	"guild_name": "guild",
	"zone_id": 00,
	"guild_id": 000000,
	"region": "US",
	"anchor_alt": "Name-Server",
	"schedule": {
		"days": ["Tuesday", "Saturday"],
		"start_est": "20:00",
		"end_est": "22:00"
	},
	"has_alts": {
		"Main-Server": ["Alt-Server", "Alt-Server"],
		"Main-Server": ["Alt-Server"]
	}
}
```
## Execution
```
python main.py
```
## Output
friends.md in the root directory

## Testing
this project uses 'pytest' for unit and integration testing. To run the test suite:
```bash
pytest
```

## Background & Motivation
### What is AotC?
Ahead of the Curve (AotC) is a World of Warcraft achievement awarded for defeating the final boss of a raid tier on Heroic difficulty before the next major patch cycle. For casual and semi-hardcore guilds, achieving AotC is the ultimate team goal of the season.

### Why build this?
The idea for this tool was born while reconstructing the five-season AotC history for our casual raiding guild. I realized that, due to scheduling conflicts, many players who spent weeks progressing on wipe nights were missing from the final kill group.

Warcraft Logs doesn't provide an easy way to display this information, particularly for guilds without consistent historical log uploaders. These progression contributors become difficult to represent in a recap. This tool scans a guilds entire raid history to ensure every player who put in the work on progression nights is recognized for their contribution.

## Zone ID reference
#### MIDNIGHT
- 50 - Sporefall
- 46 - VS / DR / MQD
#### TWW
- 44 - Manaforge Omega
- 42 - Liberation of Undermine
- 40 - Blackrock Depths
- 38 - Nerub-ar Palace
#### DF
- 35 - Amirdrassil, the Dream's Hope
- 33 - Aberrus, the Shadowed Crucible
- 31 - Vault of the Incarnates
#### SL
- 29 - Sepulcher of the First Ones
- 28 - Sanctum of Domination
- 26 - Castle Nathria
#### BFA
- 24 - Ny'alotha
- 23 - The Eternal Palace
- 22 - Crucible of Storms
- 21 - Battle of Dazar'alor
- 19 - Uldir
#### LEGION
- 17 - Antorus, The Burning Throne
- 13 - Tomb of Sargeras
- 12 - Trial of Valor
- 11 - The Nighthold
- 10 - Emerald Nightmare
#### WOD
- 8 - Hellfire Citadel
- 7 - Blackrock Foundry
- 6 - Highmaul
#### MOP
- 5 - Siege of Orgrimmar
- 4 - Throne of Thunder