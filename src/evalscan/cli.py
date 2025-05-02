import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from time import time

import click
import humanize
import pandas as pd
import pytz

from evalscan.index import load_data
from evalscan.plots import lasagne_stacked_plotly, lasagne_stacked_continuous_plotly

# Scope: reporting on closed automated agent evals

# Input:
# - a results database
# - a specification of the plots to generate
# Output: a markdown file and supporting plot files
# - list of entries to write to markdown file

# Start with the lasagne plots

# Assumptions about the interface to the data?

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
                dst_dir = temp_dir,
                index_col = fn_index,
                score_col = fn_score,
                grade_col = fn_grade,
                model_col = fn_model,
                task_col = fn_task_name,
                yticklabels = True,
                legend = True,
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


@click.command()
@click.option("--db-uri", prompt="Enter eval results database URI")
def main(db_uri):
    start_time = time()
    data = load_data(db_uri)

    with tempfile.TemporaryDirectory() as temp_dir:  # Use a temp dir to handle cleanup
        raw_timestamp = datetime.now(pytz.UTC)
        timestamp = raw_timestamp.strftime("%Y%m%dT%H%M%SZ")

        md_lines = []
        md_lines.extend(
            [
                "# EvalScan Report",
                "---",
                "> [!WARNING]\n> EvalScan is a new tool that is being actively developed. It hasn't been comprehensively tested, so you should interpret results cautiously."
                f"Report generated: {raw_timestamp.strftime('%Y-%m-%d %H:%m:%S %Z')}",
                f"Source database: {db_uri}",
                f"No. samples: {get_n_samples(data)}",
                f"No. models: {get_n_models(data)}",
                f"No. tasks: {get_n_tasks(data)}",
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

        shutil.make_archive(f"evalscan-report-{timestamp}", "zip", temp_dir, Path(temp_dir).parent)
