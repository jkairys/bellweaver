"""
CLI commands for managing mock data.
"""

import typer
from pathlib import Path
from typing import Optional

from bellweaver.adapters.mock_data import collect_compass_events

app = typer.Typer(help="Manage mock data for development and testing")


@app.command("update")
def update_mock_data(
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days ahead to fetch events for",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-l",
        help="Maximum number of events to fetch",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to save mock data (default: backend/data/mock)",
    ),
):
    """
    Collect real Compass data for use as mock data in development.

    This command:
    1. Authenticates with Compass using credentials from .env
    2. Fetches calendar events for the specified date range
    3. Saves the raw response to data/mock/compass_events.json

    Requires COMPASS_BASE_URL, COMPASS_USERNAME, and COMPASS_PASSWORD
    to be set in your .env file.
    """
    typer.echo("Updating mock data from Compass...")

    try:
        # Resolve output directory if provided
        if output_dir:
            output_dir = output_dir.resolve()

        # Collect events
        events = collect_compass_events(
            days=days,
            limit=limit,
            output_dir=output_dir,
        )

        # Calculate date range for display
        from datetime import datetime, timedelta

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        # Get output file path
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "mock"

        events_file = output_dir / "compass_events.json"

        # Display success message
        typer.secho("\n✓ Success! Mock data collected.", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"  Total events: {len(events)}")
        typer.echo(f"  Date range: {start_date} to {end_date}")
        typer.echo(f"  Output: {events_file}")

    except ValueError as e:
        typer.secho(f"\n✗ Configuration Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"\n✗ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
