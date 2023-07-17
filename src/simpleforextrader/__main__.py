"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Simpleforextrader."""


if __name__ == "__main__":
    main(prog_name="simpleforextrader")  # pragma: no cover
