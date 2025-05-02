# ❀ EvalScan

EvalScan aims to let you quickly understand agent behaviour and locate task bugs through automated scans of your Inspect LLM agent evaluation transcripts.

## Features
* Run scans over big collections of evaluation logs - `evalscan`'s currently designed to work with DuckDB databases generate by `evaldb`
* Visualize agent behaviours and task bugs such as
    * Tool call sequences
    * Length of reasoning messages
    * Refusals and requests for user input
* Automatically generate a report visualising and summarising scan results 

## Installation

```
pip install TODO
```

## Usage

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


