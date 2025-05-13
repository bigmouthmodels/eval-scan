import click

from evalscan.index import index as _index
from evalscan.scan import scan as _scan
from evalscan.report import report as _report


@click.group()
def evalscan(): ...


@evalscan.command()
@click.option("--logs-dir")
@click.option("--db-uri")
def index(logs_dir, db_uri):
    _index(logs_dir, db_uri)


@evalscan.command()
@click.option("--db-uri")
def scan(db_uri):
    _scan(db_uri)


@evalscan.command()
@click.option("--db-uri", prompt="Enter eval results database URI")
def report(db_uri):
    _report(db_uri)
