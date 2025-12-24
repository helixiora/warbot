# Warbot

CLI bot using OpenAI's `gpt-5-mini` with streaming, thinking display, tool calls, and multi-turn conversations focused on world conflicts, location-based risk assessment, and preparedness guidance.

## Features
- Streaming responses with thinking tokens surfaced in the terminal
- Tool calls with a pluggable registry
- Built-in tools:
  - `get_world_conflicts`: major conflicts and tensions (stubbed; replace with real data sources)
  - `assess_location_risks`: location risk assessment (stubbed)
  - `get_preparation_guidance`: scenario preparation guidance
- Conversation history across turns

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
- Current tool outputs are stubbed; integrate real data sources (news APIs, geocoding, etc.) for production.
- Thinking and content are streamed; intermediate thoughts are shown in dim text.


