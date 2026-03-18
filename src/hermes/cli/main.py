"""CLI entrypoint for Hermes."""

import typer


app = typer.Typer(help="Hermes local orchestrator CLI.")


@app.command()
def version() -> None:
    """Show the current Hermes version."""
    typer.echo("Hermes 0.1.0")


if __name__ == "__main__":
    app()
