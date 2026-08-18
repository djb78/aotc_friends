# AotC Friends
An automated command-line tool that analyzes Warcraft Logs to track raid attendance, identify core raiders, and map character alts back to their mains for a unified guild roster during Ahead of the Curve (AotC) progression.

## What It Does
### Core Functionality
This tool scans your raid history to identify every character who participated in scheduled guild runs, tracking:
- **Progression Pull Counts:** Exactly how many boss pulls each character was present for.
- **Spec & Role Breakdown:** What specs and roles they played, and how often.
- **AOTC Cutoff:** Automatically stops counting pulls after the final boss is killed, ensuring stats reflect true progression effort.
### Alt Mapping (Optional)
To account for people playing alts, you can provide a manual mapping in `config.json`. 
The tool will then:
- Group alts together with their main, raid tier main determined by alt attendance
- Combine their pull counts to show true, player-level attendance.
- Display nested spec breakdowns for each character they played

## Prerequisites
To get data from Warcraft Logs, you need a free client ID and client secret from the [Warcraft Logs Developer Portal](https://www.warcraftlogs.com/api/clients/).

## Setup
### 1. Get the program
clone the repo to the desired location on your local machine
```
git clone 
cd aotc-friends
```
### 2. Set up a virtual environment (venv)
```
python -m venv venv
```
activate:
	windows:        `.\venv\Scripts\activate`
	macOS/Linux: `source venv/bin/activate`
install dependencies
```
pip install -r requirements.txt
```
### 3. Create a local file for API credentials
Create a file named `.env` in the root directory of the project and add your warcraftlogs credentials:
```env
WCL_CLIENT_ID=yourid
WCL_CLIENT_SECRET=yoursecret
```

## Configuration
user settings can be controlled from config.json in the root directory

config.json structure
```json
{
	"guild_name": "guild",
	"zone_id": 00,
	"guild_id": 000000,
	"region": "US",
	"regular": "Name-Server",
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

### required fields
- **`zone_id`**: Identifies the raid tier to analyze (see the reference list below).
- **`guild_id`**: The guild's numerical ID found in their Warcraft Logs URL. Used to get logs officially attributed to the guild.
- **`region`**: `"US"`, `"EU"`, etc. Used to uniquely identify the guild and characters.
- **`regular`**: The `"Name-Server"` string of a raider with high attendance. Used to fill in any gaps in guild attributed logs.
### optional fields
- **`guild_name`**: Cosmetic flavor for the final report header.
- **`schedule`**: Raid days and times. Logs outside of these windows are automatically ignored. If schedule details are missing or formatted incorrectly, no time-filtering is applied.
- **`has_alts`**: A mapping of player alts to their main characters. If no alts are defined, characters are listed individually

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

# Zone ID reference
### MIDNIGHT
50 - Sporefall
46 - VS / DR / MQD
### TWW
44 - Manaforge Omega
42 - Liberation of Undermine
40 - Blackrock Depths
38 - Nerub-ar Palace
### DF
35 - Amirdrassil, the Dream's Hope
33 - Aberrus, the Shadowed Crucible
31 - Vault of the Incarnates
### SL
29 - Sepulcher of the First Ones
28 - Sanctum of Domination
26 - Castle Nathria
### BFA
24 - Ny'alotha
23 - The Eternal Palace
22 - Crucible of Storms
21 - Battle of Dazar'alor
19 - Uldir
### LEGION
17 - Antorus, The Burning Throne
13 - Tomb of Sargeras
12 - Trial of Valor
11 - The Nighthold
10 - Emerald Nightmare
### WOD
8 - Hellfire Citadel
7 - Blackrock Foundry
6 - Highmaul
### MOP
5 - Siege of Orgrimmar
4 - Throne of Thunder