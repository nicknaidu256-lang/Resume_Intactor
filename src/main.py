"""Main CLI entry point for Resume Tailoring System."""

from pathlib import Path
import click

from src.config import config
from src.utils import setup_logging
from src.resume_generator import run as run_generator
from src.ui.pages.dashboard import create_dashboard


def _setup_cli_logging(log_level: str, verbose: bool):
    """Configure logging for CLI commands."""
    effective_level = "DEBUG" if verbose else log_level
    logger = setup_logging(config.log_path, effective_level)
    logger.info("Starting ATS Resume Tailoring System")
    logger.info(f"Project root: {Path(__file__).parent.parent}")
    logger.info(f"AI Engine: Cerebras ({config.cerebras_model}) -> Gemini ({config.gemini_model})")
    logger.info(f"Template: {config.template_path}")
    logger.info(f"Output: {config.output_dir}")
    return logger


def _get_scrape_runner():
    """Import scraper runner lazily so `--help` still works if optional scraper deps are missing."""
    try:
        from src.scrapers.scraper_runner import run_full_scrape
    except ModuleNotFoundError as e:
        raise click.ClickException(f"Scraper dependencies are not available: {e}")
    return run_full_scrape


def _get_scorer():
    """Import scorer lazily to keep CLI startup lightweight."""
    try:
        from src.scoring.scorer import score_jobs
    except ModuleNotFoundError as e:
        raise click.ClickException(f"Scoring dependencies are not available: {e}")
    return score_jobs


@click.group()
@click.option(
    "--log-level",
    default=config.log_level,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    show_default=True,
    help="Logging level.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging (overrides --log-level).")
@click.pass_context
def cli(ctx, log_level, verbose):
    """ATS Resume Tailoring System CLI."""
    ctx.ensure_object(dict)
    ctx.obj["logger"] = _setup_cli_logging(log_level, verbose)


@cli.command(name="generate-resume")
@click.pass_context
def generate_resume(ctx):
    """Generate a targeted resume from input/job_description.txt."""
    logger = ctx.obj["logger"]

    try:
        output_path = run_generator()
        click.echo(f"[OK] Resume generated: {output_path}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise click.ClickException(f"File not found: {e}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise click.ClickException(f"Configuration error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise click.ClickException(f"Unexpected error: {e}")


def _extract_jobs(scrape_result):
    """Return a job list from scraper output."""
    if isinstance(scrape_result, list):
        return scrape_result
    if isinstance(scrape_result, dict):
        jobs = scrape_result.get("jobs")
        if isinstance(jobs, list):
            return jobs
    return []


@cli.command()
def scrape():
    """Scrape jobs from SEEK and Jora."""
    click.echo("Starting job scrape...")
    keywords = config.search_keywords if hasattr(config, 'search_keywords') else ["Process Engineer"]
    location = config.search_location if hasattr(config, 'search_location') else "Melbourne VIC"
    
    from src.scrapers.scraper_runner import run_full_scrape
    jobs = run_full_scrape(keywords, location)
    click.echo(f"Found {len(jobs)} jobs")


@cli.command()
def score():
    """Score scraped jobs against profile."""
    click.echo("Scoring jobs...")
    click.echo("Scoring not yet wired to DB")


@cli.command()
def run():
    """Full pipeline: scrape to score."""
    click.echo("Running full pipeline...")
    keywords = config.search_keywords if hasattr(config, 'search_keywords') else ["Process Engineer"]
    location = config.search_location if hasattr(config, 'search_location') else "Melbourne VIC"
    
    from src.scrapers.scraper_runner import run_full_scrape
    from src.scoring.scorer import score_jobs
    
    jobs = run_full_scrape(keywords, location)
    click.echo(f"Scraped {len(jobs)} jobs")

    if not jobs:
        click.echo("No jobs found")
        return
    
    threshold = config.score_threshold if hasattr(config, 'score_threshold') else 0.45
    scored = score_jobs(jobs, threshold=threshold)
    click.echo(f"Qualified: {len(scored)} jobs (score >= {threshold})")
    
    for job in scored[:10]:
        click.echo(f"  - {job.get('title', 'N/A')} @ {job.get('company', 'N/A')} (score: {job.get('score', 0)})")
        return

    scored = score_jobs(jobs, threshold=config.score_threshold)
    click.echo(f"Qualified: {len(scored)} jobs (score >= {config.score_threshold})")

    for job in scored[:config.max_jobs_per_run]:
        click.echo(f"  - {job['title']} @ {job['company']} (score: {job['score']})")


@cli.command()
def dashboard():
    """Launch dashboard UI"""
    click.echo("Opening dashboard at http://localhost:8080")
    create_dashboard().run()


if __name__ == "__main__":
    cli()
