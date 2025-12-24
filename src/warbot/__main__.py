"""CLI entry point for warbot."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from .bot import Warbot
from .config import Settings, load_settings


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Warbot - World conflict awareness CLI bot")
    parser.add_argument(
        "--model",
        help="OpenAI model to use (default: gpt-5-mini)",
    )
    parser.add_argument(
        "--base-url",
        help="Optional custom base URL for OpenAI-compatible endpoints.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging of raw stream chunks.",
    )
    parser.add_argument(
        "--question",
        help="Optional first question to send automatically before the interactive loop.",
    )
    return parser.parse_args(argv)


def build_settings(args: argparse.Namespace) -> Settings:
    settings = load_settings()
    if args.model:
        settings.model = args.model
    if args.base_url:
        settings.base_url = args.base_url
    return settings


def main(argv: Optional[list[str]] = None) -> None:
    console = Console()
    args = parse_args(argv)
    settings = build_settings(args)
    bot = Warbot(settings=settings, console=console, debug=args.debug)

    console.print(Panel("Warbot - type 'exit' or Ctrl+C to quit", style="green"))

    if args.question:
        console.print(f"[bold blue]You:[/bold blue] {args.question}")
        console.print("[bold cyan]Assistant:[/bold cyan] ", end="")
        bot.send_message(args.question)
        console.print()  # newline after response

    try:
        while True:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            if user_input.strip().lower() in {"exit", "quit"}:
                break
            console.print("[bold cyan]Assistant:[/bold cyan] ", end="")
            bot.send_message(user_input)
            console.print()  # newline after response
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted[/red]")
        sys.exit(0)


if __name__ == "__main__":
    main()


