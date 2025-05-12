import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from pickle import loads
from uuid import uuid4
from time import time

import click
import duckdb
from inspect_ai.log import list_eval_logs
import humanize
import pandas as pd
import pytz
from faker import Faker

from evaldb import insert_inspect_transcripts_to_database

fake = Faker()

from evalscan.index import load_data
from evalscan.plots import lasagne_stacked_plotly
from evalscan.probes import dummy_probe

# uv run evalscan index --logs-dir /home/ubuntu/eval-scan/tests/assets/cybench-100 --db-uri cybench-100.db
# uv run evalscan scan --db-uri /home/ubuntu/eval-scan/cybench-100.db
# uvx harlequin cybench-100.db

# Probes
PROBES = [
    dummy_probe
]

# Field names
fn_sample = "tidy_sample_uuid"
fn_log = "raw_log_uuid"
fn_model = "model"
fn_index = "index"
fn_task_name = "task_name"
fn_grade = "grade"


def get_n_samples(data: pd.DataFrame) -> int:
    return len(data[fn_sample].unique())


def get_n_models(data: pd.DataFrame) -> int:
    return len(data[fn_model].unique())


def get_n_logs(data: pd.DataFrame) -> int:
    return len(data[fn_log].unique())


def get_n_tasks(data: pd.DataFrame) -> int:
    return len(data[fn_task_name].unique())


def get_plots(data: pd.DataFrame, temp_dir: str) -> list[str]:
    # Writes plots, returns a list of markdown strings for including them
    models = data[fn_model].unique()
    cat_score_cols = ["tool_call"]
    cont_score_cols = ["n_reasoning_chars"]
    md_lines = []
    for model in models:
        for fn_score in cat_score_cols:
            fp = lasagne_stacked_plotly(
                data,
                model,
                dst_dir=temp_dir,
                index_col=fn_index,
                score_col=fn_score,
                grade_col=fn_grade,
                model_col=fn_model,
                task_col=fn_task_name,
                yticklabels=True,
                legend=True,
            )
            md_lines.append(f"![](./{fp.name})")
        # for fn_score in cont_score_cols:
        #     fp = lasagne_stacked_continuous_plotly(
        #         data,
        #         model,
        #         dst_dir = temp_dir,
        #         index_col = fn_index,
        #         score_col = fn_score,
        #         grade_col = fn_grade,
        #         model_col = fn_model,
        #         task_col = fn_task_name,
        #         yticklabels = True,
        #         legend = True
        #     )
        #     md_lines.append(f"![](./{fp.name})")

    return md_lines


@click.group()
def evalscan():
    ...
    

@evalscan.command()
@click.option("--logs-dir")
@click.option("--db-uri")
def index(logs_dir, db_uri):
    eval_log_infos = list_eval_logs(logs_dir, formats=["eval", "json"], recursive=True)
    if len(eval_log_infos) > 0:
        eval_log_filepaths = [str(eli.name) for eli in eval_log_infos]
        insert_inspect_transcripts_to_database(
            eval_log_filepaths,
            db_uri,
            show_manual=False,
            max_logs_loaded_into_memory=10,
        ) 
        try:
            con = duckdb.connect(db_uri)
            df = (
                con.execute("""
                SELECT * FROM raw_eval_log_headers
            """)
                .df()
                .assign(
                    eval_log=lambda df: df["pickled_evallog"].apply(lambda pel: loads(pel))
                )
                .assign(
                    status=lambda df: df["eval_log"].apply(lambda el: el.status),
                    eval_run_id=lambda df: df["eval_log"].apply(lambda el: el.eval.run_id),
                    eval_task_id=lambda df: df["eval_log"].apply(
                        lambda el: el.eval.task_id
                    ),
                    eval_task=lambda df: df["eval_log"].apply(lambda el: el.eval.task),
                    model=lambda df: df["eval_log"].apply(lambda el: el.eval.model),
                )
                .drop(columns=["pickled_evallog", "eval_log"])
                .assign(raw_eval_log_header_uuid=lambda df: df["uuid"])
                .assign(uuid=lambda df: df["uuid"].apply(lambda _: uuid4()))
                .drop(["inserted"], axis=1)
            )
            con.execute("CREATE TABLE tidy_eval_log_headers AS SELECT * FROM df")
        except duckdb.duckdb.CatalogException:
            pass
    else:
        raise ValueError(f"No evaluation logs found in {log_dir}.")


@evalscan.command()
@click.option("--db-uri")
def scan(db_uri):
    # List of scanners, list of messages to scan
    # Check if the message has already been scanned
    # If not, run the scanner
    # Need a dummy scanner to be able to do this
    con = duckdb.connect(db_uri)
    
    # Get the messages as a dataframe
    df = con.execute("""
    SELECT *
    FROM tidy_eval_messages tem
    JOIN tidy_eval_sample_headers tesh ON tesh.raw_sample_uuid = tem.raw_sample_uuid
    JOIN tidy_eval_log_headers telh ON telh.raw_eval_log_header_uuid = tem.raw_log_uuid
    """).df()
    
    # Get the scores as a dataframe
    # uuid, message id, score id, score, metadata
    con.execute("""
    CREATE TABLE IF NOT EXISTS message_scores (
        uuid UUID PRIMARY KEY NOT NULL,
        message_uuid UUID NOT NULL,
        FOREIGN KEY (message_uuid) REFERENCES tidy_eval_messages(uuid),
        inserted TIMESTAMPTZ NOT NULL,
        score_name VARCHAR NOT NULL,
        score VARCHAR NOT NULL,
        input_tokens INT NOT NULL,
        output_tokens INT NOT NULL,
        metadata VARCHAR
    )
    """)

    for probe in PROBES:
        probe(df, con) # Probe handles writing the score to the database too


@evalscan.command()
@click.option("--db-uri", prompt="Enter eval results database URI")
def report(db_uri):
    start_time = time()
    data = load_data(db_uri)

    with tempfile.TemporaryDirectory() as temp_dir:  # Use a temp dir to handle cleanup
        raw_timestamp = datetime.now(pytz.UTC)
        timestamp = raw_timestamp.strftime("%Y%m%dT%H%M%SZ")

        md_lines = []
        md_lines.extend(
            [
                f"# EvalScan Report (`{'-'.join(fake.words())}`)",
                "---",
                "> [!WARNING]\n> EvalScan is a new tool that is being actively developed. It hasn't been comprehensively tested, so you should interpret results cautiously."
                "",
                f"Report generated: `{raw_timestamp.strftime('%Y-%m-%d %H:%m:%S %Z')}`",
                f"Source database: `{db_uri}`",
                f"No. samples: `{get_n_samples(data)}`",
                f"No. models: `{get_n_models(data)}`",
                f"No. tasks: `{get_n_tasks(data)}`",
            ]
        )
        md_lines.extend(get_plots(data, temp_dir))

        compile_time = timedelta(seconds=time() - start_time)
        md_lines.append("---")
        md_lines.append(f"_Compiled in {humanize.naturaldelta(compile_time)}_")

        with open(f"{temp_dir}/evalscan-report-{timestamp}.md", "w") as md_file:
            for line in md_lines:
                print(line, file=md_file)
                print("", file=md_file)

        # Move the entire contents into a directory so the report unzips neatly for users
        os.makedirs(f"{temp_dir}/evalscan-report-{timestamp}")
        for filepath in list(Path(temp_dir).rglob("*")):
            if filepath.is_file():
                shutil.move(
                    filepath,
                    filepath.parent / f"evalscan-report-{timestamp}" / filepath.name,
                )

        shutil.make_archive(f"evalscan-report-{timestamp}", "zip", f"{temp_dir}")
