# ❀ EvalScan

EvalScan aims to let you quickly understand agent behaviour and locate task bugs through automated scans of your Inspect LLM agent evaluation transcripts.

## Features
* Scan big collections of Inspect logs - `evalscan`'s currently designed to work with DuckDB databases generate by `evaldb`
* Visualize and tabulate agent behaviours and task bugs such as
    * Tool call sequences
    * Length of reasoning messages
    * Refusals and requests for user input
* Generate reports of scan results 

## Install

```
pip install TODO
```

## Use

**1. Index**: Index your evaluation logs with `evaldb`.

**2. Scan**: Scan your evaluation results with the default probe library:
```
evalscan scan <db_uri>
```
This creates a separate scores table in your database.

**3. Report**: Compile a markdown report summarizing and visualizing scan results via
```
evalscan report <db_uri>
```


