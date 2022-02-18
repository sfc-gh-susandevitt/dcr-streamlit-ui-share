# type: ignore[attr-defined]

import typer
from rich.console import Console
from dcr_ui import __version__
from dcr_ui.cli import deploy

app = typer.Typer(
    name="dcr_ui",
    help="`dcr_ui` is a Python cli/package",
    add_completion=True,
)
app.add_typer(deploy.app, name="deploy")
console = Console()


def version_callback(value: bool):
    """Prints the version of the package."""
    if value:
        console.print(f"[yellow]dcr_ui[/] version: [bold blue]{__version__}[/]")
        raise typer.Exit()
