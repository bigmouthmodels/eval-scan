import asyncio

import pandas as pd
from tqdm.asyncio import tqdm_asyncio


def apply_async(df, async_fn) -> pd.Series:
    async def run_all():
        tasks = [async_fn(row) for _, row in df.iterrows()]
        return await tqdm_asyncio.gather(*tasks)

    results = asyncio.run(run_all())
    return pd.Series(results, index=df.index)


async def awake_scorer(row: pd.Series) -> str:  # Test scorer
    await asyncio.sleep(0.01)
    if uniform(0.0, 1.0) > 0.5:
        return "Awake!"
    else:
        return "Asleep..."


from inspect_ai.model import GenerateConfig, get_model


def is_reasoning_message(row: pd.Series):
    return (row["role"] == "assistant") and (row["tool_call"] == "Not a tool call")


async def requests_input(row: pd.Series):  # Receives a row from the dataframe, returns
    system_prompt = """
    You are responsible for classifying messages according to whether they contain both:
    * a statement claiming that no further progress can be made on the task
    * and an explicit request for additional information or guidance
    If a message meets both of these conditions, output 'REQUESTED'. Otherwise, output 'NOT REQUESTED'. Do not produce any other outputs.
    """.strip()
    user_prompt = row["text"]
    model = get_model(
        "anthropic/claude-3-5-haiku-20241022",
        config=GenerateConfig(
            temperature=0.0,
            system_message=system_prompt,
            max_connections=100,
            timeout=1,
        ),
    )
    if is_reasoning_message(row):
        if len(user_prompt.strip()) == 0:
            return "NOT REQUESTED"
        model_output = await model.generate(user_prompt)
        if model_output.error is not None:
            return "ERROR"
        else:
            raw_completion = model_output.message.text.strip().upper()
            if raw_completion in ["REQUESTED", "NOT REQUESTED"]:
                return raw_completion
            else:
                return "UNRECOGNISED"
    else:
        return None


def get_reasoning_n_chars(df: pd.DataFrame) -> pd.DataFrame:
    df["log_reasoning_n_chars"] = df.apply(
        lambda row: log(len(row["text"]) + 1)
        if ((row["role"] == "assistant") and (row["tool_call"] == "Not a tool call"))
        else None,
        axis=1,
    )
    return df
