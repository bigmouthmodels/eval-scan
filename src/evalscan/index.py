import duckdb


def load_data(db_uri: str):
    # inspect-evaldb --log_dir /home/ubuntu/los-alamos/logs/cybench-100 --db_uri cybench-10-t0.db --hide_manual
    con = duckdb.connect(db_uri)
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
