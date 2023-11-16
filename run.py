import click
import src.utils
from src.cache import EvaluationCache
from src.evaluator import ResumeEvaluator
from src.fetcher import ResumeFetcher
from src.mailer import Mailer

@click.group()
def cli():
    pass

@click.command(name="clear-cache")
@click.option('--path', required=True, help="Provide the path of the resume-folder.")
def clear_cache(path):
    """Clear the evaluation cache of resumes, given a folder."""
    cache = EvaluationCache()
    click.echo(f'clearing all evaluations for resumes in {path}')
    cache.clear_all_evaluations(path)
    click.echo('Done!')

@click.command(name="sample")
@click.option('--source', required=True, help="source of the folder from where files are to be sampled")
@click.option('--destination', required=True, help="destination where sampled files while be moved")
@click.option('--rate', required=True, help="sampling rate in decimal. E.g. 0.1 is 10%", type=float)
def sample(source, destination, rate):
    """Sample files from one folder to another, copying a percentage"""
    src.utils.sample_and_copy_files(source, destination, rate)
    click.echo(f"{rate*100}% of files from {source} copied to {destination}")

@click.command(name="evaluate")
def evaluate():
    """Evaluate resumes. Ensure that config.yaml is correctly populated before running evaluations."""
    evaluator = ResumeEvaluator()
    evaluator.evaluate()

@click.command(name="fetch")
def fetch():
    """Fetches resumes. Ensure that config.yaml is correctly populated before triggering a fetch."""
    fetcher = ResumeFetcher()
    fetcher.fetch()

@click.command(name="reach-out")
@click.option('--candidates', required=True, help="path of Greenhouse export CSV to get candidates from")
def reach_out(candidates):
    """Reach out to shortlisted candidates with a request to meet."""
    mailer = Mailer()
    mailer.trigger(candidates)    

cli.add_command(clear_cache)
cli.add_command(sample)
cli.add_command(evaluate)
cli.add_command(reach_out)

if __name__ == '__main__':
    cli()