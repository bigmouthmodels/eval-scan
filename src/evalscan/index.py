from uuid import uuid4
from pickle import loads

import duckdb
from inspect_ai.log import list_eval_logs

from evaldb import insert_inspect_transcripts_to_database


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
            df = (  # noqa: F841
                con.execute("""
                SELECT * FROM raw_eval_log_headers
            """)
                .df()
                .assign(
                    eval_log=lambda df: df["pickled_evallog"].apply(
                        lambda pel: loads(pel)
                    )
                )
                .assign(
                    status=lambda df: df["eval_log"].apply(lambda el: el.status),
                    eval_run_id=lambda df: df["eval_log"].apply(
                        lambda el: el.eval.run_id
                    ),
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
        raise ValueError(f"No evaluation logs found in {logs_dir}.")


def load_data(db_uri: str):
    # inspect-evaldb --log_dir /home/ubuntu/los-alamos/logs/cybench-100 --db_uri cybench-10-t0.db --hide_manual
    con = duckdb.connect(db_uri)
    df = con.execute("""
    SELECT *
    FROM tidy_eval_messages tem
    JOIN tidy_eval_sample_headers tesh ON tesh.raw_sample_uuid = tem.raw_sample_uuid
    JOIN tidy_eval_log_headers telh ON telh.raw_eval_log_header_uuid = tem.raw_log_uuid
    JOIN message_scores ms ON tem.uuid = ms.message_uuid
    """).df()

    df["tool_call"] = df["function"].fillna("Not a tool call").astype(dtype="category")
    df["grade"] = df["scores"].apply(lambda d: d["includes"]["value"])
    df["task_name"] = df["id"]

    return df
