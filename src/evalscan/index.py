from pickle import loads
from uuid import uuid4

import duckdb


def load_data(db_uri: str):
    # inspect-evaldb --log_dir /home/ubuntu/los-alamos/logs/cybench-100 --db_uri cybench-10-t0.db --hide_manual
    con = duckdb.connect(db_uri)

    try:
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

    df = con.execute("""
    SELECT *
    FROM tidy_eval_messages tem
    JOIN tidy_eval_sample_headers tesh ON tesh.raw_sample_uuid = tem.raw_sample_uuid
    JOIN tidy_eval_log_headers telh ON telh.raw_eval_log_header_uuid = tem.raw_log_uuid
    """).df()

    df["tool_call"] = df["function"].fillna("Not a tool call").astype(dtype="category")
    df["grade"] = df["scores"].apply(lambda d: d["includes"]["value"])
    df["task_name"] = df["id"]

    return df
