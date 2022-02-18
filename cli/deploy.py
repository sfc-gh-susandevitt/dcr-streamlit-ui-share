import typer
from rich.console import Console
from dcr_ui.app import deploy_streamlit

app = typer.Typer()
console = Console()


@app.command()
def dashboard() -> None:
    """Deploys the streamlit dashboard."""
    deploy_streamlit()
