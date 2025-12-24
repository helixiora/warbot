# Warbot

CLI bot using OpenAI's `gpt-5-mini` with streaming, thinking display, tool calls, and multi-turn conversations focused on world conflicts, location-based risk assessment, and preparedness guidance.

## Features
- Streaming responses with thinking tokens surfaced in the terminal
- Tool calls with a pluggable registry
- Conversation history across turns

## Tools

Warbot includes three built-in tools for conflict awareness and preparedness:

### `get_world_conflicts`
Fetches current world conflicts from Wikipedia, including:
- **Major wars** (10,000+ combat-related deaths)
- **Minor wars** (1,000-9,999 deaths)
- **Conflicts** (100-999 deaths)
- **Skirmishes** (<100 deaths)

Data is cached locally for 1 hour to reduce API load. Supports optional region filtering (e.g., "Europe", "Middle East", "Asia Pacific"). Returns conflict details including start date, location, continent, and fatality statistics.

### `assess_location_risks`
Assesses risks for a specified location (city, country, or coordinates), evaluating:
- Proximity to active conflicts
- Infrastructure stability
- Digital/internet reliability
- Other relevant risk factors

Currently returns structured risk assessments with categories and severity levels. *Note: This tool uses stubbed data; integrate geocoding and threat intelligence sources for production use.*

### `get_preparation_guidance`
Provides structured preparation guidance for emergency scenarios such as:
- Utilities interruption
- Internet loss
- Armed conflict
- Natural disasters

Returns actionable guidance organized by:
- **Immediate actions**: What to do right away
- **Short-term**: 72-hour preparedness steps
- **Long-term**: Extended preparation strategies
- **Supplies**: Essential items to have on hand
- **Communication**: How to stay connected
- **Evacuation**: Routes and go-bag preparation

Guidance is tailored based on the scenario type and optional location context.

## Installation
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
# or, install via requirements
pip install -r requirements.txt
```

## Configuration
Create a `.env` file (see `.env.example`):
```
OPENAI_API_KEY=your_api_key_here
# Optional
# OPENAI_MODEL=gpt-5-mini
# OPENAI_BASE_URL=
```

## Usage
```bash
# After installation
warbot

# Using python module
python -m warbot

# Override model
warbot --model gpt-5-mini

# Enable debug logging of raw stream chunks
warbot --debug

# Provide a first question automatically
warbot --question "What major conflicts are active right now?"
```

Type `exit` or `quit` to leave the session.

## Development
```bash
pip install -r requirements-dev.txt
pytest
```

## Project Layout
```
src/warbot/
  __main__.py          # CLI entry
  bot.py               # Core bot logic
  stream_handler.py    # Streaming parser
  config.py            # Settings and client builder
  tools/               # Tool framework + tools
tests/                 # Test suite
```

## Notes
- `get_world_conflicts` fetches real data from Wikipedia and caches it locally.
- `assess_location_risks` currently uses stubbed data; integrate geocoding and threat intelligence sources for production.
- Thinking and content are streamed; intermediate thoughts are shown in dim text.


