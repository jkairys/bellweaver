"""
CLI commands for managing the Bellweaver API server.
"""

import os
import typer
from typing import Optional

app = typer.Typer(help="Manage the Bellweaver API server")


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        5000,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode with auto-reloader",
    ),
):
    """
    Start the Flask API server.

    Examples:
        # Start server on default host and port (0.0.0.0:5000)
        bellweaver api serve

        # Start server with debug mode enabled
        bellweaver api serve --debug

        # Start server on custom host and port
        bellweaver api serve --host localhost --port 8000
    """
    from bellweaver.api import create_app

    typer.echo(f"Starting Bellweaver API server on {host}:{port}")
    if debug:
        typer.echo("Debug mode: ON (auto-reloader enabled)")
    else:
        typer.echo("Debug mode: OFF")

    app = create_app()
    app.run(debug=debug, host=host, port=port, use_reloader=debug)


if __name__ == "__main__":
    app()
