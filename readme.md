Receives a list of eval logs in a .txt file as input, outputs a markdown report providing an analysis of those logs.

```
uvx run evalscan --log-dir ./path/to/log/dir --output-name cybench-100
```

Target use-cases:
* Understanding agent behaviour
* Detecting agent failures
* Finding task bugs

What's the use-case?
* Lots of evaluation logs from multiple models and tasks
* Want to understand all the samples 