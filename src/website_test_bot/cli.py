"""Command-line interface for the Website Test Bot."""

import os
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import datetime
import typer
from website_test_bot import __version__
from website_test_bot.config import load_config, merge_cli_args
from website_test_bot.crawler import crawl_website_sync
from website_test_bot.generator import generate_tests
from website_test_bot.reporter import generate_report
from website_test_bot.runner import run_tests

# Create Typer app
app = typer.Typer(
    name="Website Test Bot",
    help="Automated website testing bot using Playwright and Pytest.",
    add_completion=False,
)
# Create Rich console
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Website Test Bot version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit.",
    )
) -> None:
    """Website Test Bot - Automated website testing using Playwright and Pytest."""
    pass


@app.command("run")
def run(
    url: str = typer.Argument(..., help="URL of the website to test."),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
    depth: int | None = typer.Option(
        None, "--depth", "-d", help="Maximum depth to crawl."
    ),
    headful: bool = typer.Option(False, "--headful", "-H", help="Run in headful mode."),
    browsers: str | None = typer.Option(
        None,
        "--browsers",
        "-b",
        help="Comma-separated list of browsers to test (chromium,firefox,webkit).",
    ),
    concurrency: int | None = typer.Option(
        None, "--concurrency", "-C", help="Number of concurrent tasks."
    ),
    output_dir: str | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory for reports."
    ),
) -> None:
    """Run the Website Test Bot on a target URL."""
    # Start time
    start_time = datetime.datetime.now()
    # Create timestamp for reports
    timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    if output_dir is None:
        output_dir = f"./reports/{timestamp}"
    # Welcome message
    console.print(
        Panel.fit(
            "🤖 [bold green]Website Test Bot[/bold green] 🤖",
            subtitle=f"v{__version__}",
        )
    )
    console.print(f"Target URL: [blue]{url}[/blue]")
    # Load configuration
    console.print("Loading configuration...")
    config = load_config(config_path)
    # Merge CLI args
    cli_args = {
        "depth": depth,
        "headful": headful,
        "browsers": browsers,
        "concurrency": concurrency,
        "output_dir": output_dir,
    }
    config = merge_cli_args(config, cli_args)
    # Print configuration summary
    console.print(f"Crawl depth: [cyan]{config.crawler.depth}[/cyan]")
    console.print(
        f"Browsers: [cyan]{', '.join(config.test.browsers)}[/cyan] "
        f"({'headless' if config.test.headless else 'headful'})"
    )
    console.print(f"Output directory: [cyan]{config.report.output_dir}[/cyan]")
    # Create output directory
    os.makedirs(config.report.output_dir, exist_ok=True)
    # Step 1: Crawl website
    console.print("\n[bold]Step 1: Crawling website...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Crawling...", total=None)
        crawl_data = crawl_website_sync(url, config)
        progress.update(task, completed=True)
    console.print(f"Discovered [green]{len(crawl_data.pages)}[/green] pages")
    # Step 2: Generate tests
    console.print("\n[bold]Step 2: Generating tests...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating...", total=None)
        test_files = generate_tests(crawl_data, config)
        progress.update(task, completed=True)
    console.print(f"Generated [green]{len(test_files)}[/green] test files")
    # Step 3: Run tests
    console.print("\n[bold]Step 3: Running tests...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running...", total=None)
        test_results = run_tests(test_files, config)
        progress.update(task, completed=True)
    console.print(
        f"Tests: [green]{test_results.passed}[/green] passed, "
        f"[red]{test_results.failed}[/red] failed, "
        f"[yellow]{test_results.skipped}[/yellow] skipped"
    )
    # Step 4: Generate report
    console.print("\n[bold]Step 4: Generating report...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating...", total=None)
        report_path = generate_report(test_results, config)
        progress.update(task, completed=True)
    # Calculate duration
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    # Print summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"Duration: [cyan]{duration}[/cyan]")
    console.print(f"Report: [blue]{report_path}[/blue]")
    # Exit with error if any tests failed
    if test_results.failed > 0:
        console.print("\n[bold red]Tests failed![/bold red]")
        raise typer.Exit(code=1)
    else:
        console.print("\n[bold green]All tests passed![/bold green]")


if __name__ == "__main__":
    app()
