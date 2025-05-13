from datetime import datetime, timedelta
import os
from pathlib import Path
import shutil
import tempfile
from time import time

import duckdb
from faker import Faker
import humanize
import pytz
import pandas as pd

from evalscan.plots import lasagne_stacked_plotly

fake = Faker()

# Field names
fn_sample = "tidy_sample_uuid"
fn_log = "raw_log_uuid"
fn_model = "model"
fn_index = "index"
fn_task_name = "id"
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
    # cont_score_cols = ["n_reasoning_chars"]
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


def report(db_uri):
    start_time = time()
    con = duckdb.connect(db_uri)
    evals_df = (
        con.execute("SELECT * FROM evals").df().sort_values(by="created").reset_index()
    )
    samples_df = (
        con.execute("SELECT * FROM samples")
        .df()
        .sort_values(by=["eval_id", "id", "epoch"])
        .reset_index()
    )
    # messages_df = con.execute("SELECT * FROM messages").df()

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
            ]
        )

        report_metadata_df = pd.Series(
            {
                "Report generated": raw_timestamp.strftime("%Y-%m-%d %H:%m:%S %Z"),
                "Source database": db_uri,
            },
            name="Report metadata",
        )
        md_lines.append(report_metadata_df.to_markdown())

        md_lines.extend(
            [
                "<details><summary>Logs</summary>\n",
                evals_df.drop(["dataset_sample_ids"], axis=1).to_markdown(),
                "</details>",
            ]
        )
        md_lines.extend(
            [
                "<details><summary>Samples</summary>\n",
                samples_df.drop(["input", "target"], axis=1).to_markdown(),
                "</details>",
            ]
        )
        # md_lines.extend(get_plots(data, temp_dir))

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
