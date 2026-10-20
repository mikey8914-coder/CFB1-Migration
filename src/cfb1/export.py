"""Serialize one canonical weekly board to CSV, JSON and copy/paste text."""
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cfb1.handoff import HANDOFF_COLUMNS, HandoffTables


@dataclass(frozen=True)
class SerializedHandoff:
    title: str
    stem: str
    csv: str
    json: str
    text: str


def serialize_handoff(handoff, slate_date):
    """No I/O: machine files retain probabilities as fractions, missing as null/blank.

    Accept a date or ISO YYYY-MM-DD string. Text uses the same rows/values as
    machine files, not a separately rounded or ROI-filtered display board.
    """
    day = date.fromisoformat(slate_date) if isinstance(slate_date, str) else slate_date
    if type(day) is not date:
        raise ValueError('Supply an explicit slate date')
    board = handoff.weekly if isinstance(handoff, HandoffTables) else handoff
    if list(board.columns) != HANDOFF_COLUMNS:
        raise ValueError('Weekly handoff schema/order differs from the contract')
    numeric = board.select_dtypes(include='number')
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError('Infinite output values cannot be exported')
    if board.Game.isna().any() or board.Game.astype(str).str.strip().eq('').any():
        raise ValueError('Output requires nonblank Game')
    title = day.strftime('%m-%d') + ' CFB — CFB1'
    stem = day.strftime('%m-%d') + '_CFB_CFB1'
    csv = board.to_csv(index=False)
    records = json.loads(board.to_json(orient='records', double_precision=15))
    payload = {'schema_version':'CFB1_STANDARD_HANDOFF_V1', 'slate_date':day.isoformat(),
        'title':title, 'columns':HANDOFF_COLUMNS, 'rows':records}
    json_text = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
    text = title + '\n\n----- BEGIN CFB1 FINAL BOARD CSV -----\n' + csv + '----- END CFB1 FINAL BOARD CSV -----\n'
    return SerializedHandoff(title, stem, csv, json_text, text)


def export_handoff(handoff, slate_date, directory):
    """Explicit opt-in filesystem writes, no Colab downloads or archive restore."""
    bundle = serialize_handoff(handoff, slate_date)
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    paths = {}
    for extension, content in [('csv',bundle.csv), ('json',bundle.json), ('txt',bundle.text)]:
        path = destination / (bundle.stem + '.' + extension)
        path.write_text(content, encoding='utf-8')
        paths[extension] = path
    return paths
