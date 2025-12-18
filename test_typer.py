"""Test typer options."""
import typer

app = typer.Typer()

@app.command()
def test(
    value: str = typer.Option(..., "--value", "-v"),
):
    print(f"Got value: {value}")

if __name__ == "__main__":
    app()
