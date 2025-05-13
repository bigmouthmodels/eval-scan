import duckdb


from inspect_ai.analysis.beta import evals_df, samples_df, messages_df


def index(logs_dir, db_uri):
    con = duckdb.connect(db_uri)
    eval_df = evals_df(logs_dir)  # noqa: F841
    con.execute("CREATE TABLE evals AS SELECT * FROM eval_df")
    sample_df = samples_df(logs_dir)  # noqa: F841
    con.execute("CREATE TABLE samples AS SELECT * FROM sample_df")
    message_df = messages_df(logs_dir)  # noqa: F841
    con.execute("CREATE TABLE messages AS SELECT * FROM message_df")
