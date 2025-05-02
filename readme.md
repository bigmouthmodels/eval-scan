# EvalScan

EvalScan aims to let you quickly understand agent behaviour and locate task bugs by providing automated scans of Inspect LLM agent evaluation transcripts.

## Features
* Run scans over big collections of evaluation logs - `evalscan`'s currently designed to work with DuckDB databases generate by `evaldb`
* Detect agent behaviours and task bugs such as 
* Automatically generate a report visualising and summarising scan results 

## Installation

```
pip install TODO
```

## Usage

**1. Index**: Index your evaluation logs by running TODO

**2. Scan**: Scan your evaluation results with the default probe library:
```
evalscan scan <db_uri>
```

**3. Report**: Compile a markdown report summarizing and visualizing scan results via
```
evalscan report <db_uri>
```


