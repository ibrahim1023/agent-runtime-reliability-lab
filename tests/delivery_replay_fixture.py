"""Reconstruct synthetic receivers and reuse saved graph output; never run a graph."""

from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3

from reliability_lab.receiver import Ledger


def prepare_replay(source: Path, destination: Path) -> dict:
    """Copy the lab sources and rebuild receivers from already published receipts."""
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))
    saved = json.loads((source / 'results/fresh/final-response-v1/execution.json').read_text())
    graph = saved['graph_execution']
    graph['report_path'] = 'work/replayed-graph/report.json'
    for case in graph['cases']:
        directory = destination / 'work/replayed-graph' / case['case']
        directory.mkdir(parents=True)
        path = directory / 'receiver.sqlite'
        Ledger(path, protected=case['protected'])
        with closing(sqlite3.connect(path)) as conn, conn:
            for receipt in case['entries']:
                conn.execute('INSERT INTO entries(operation_id, message, receipt) VALUES (?, ?, ?)',
                             (receipt['operation_id'], receipt['message'], json.dumps(receipt, sort_keys=True)))
    return graph
