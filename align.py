import pandas as pd
import numpy as np
import json
from pathlib import Path

# --- config ---
eeg_dir      = Path('data')
markers_file = Path('markers.json')
out_dir      = Path('output/segments')
fs           = 125.0

titles = (
    "Sample Index, EXG Channel 0, EXG Channel 1, EXG Channel 2, EXG Channel 3, "
    "EXG Channel 4, EXG Channel 5, EXG Channel 6, EXG Channel 7, EXG Channel 8, "
    "EXG Channel 9, EXG Channel 10, EXG Channel 11, EXG Channel 12, EXG Channel 13, "
    "EXG Channel 14, EXG Channel 15, Accel Channel 0, Accel Channel 1, Accel Channel 2, "
    "Not Used1, Digital Channel 0 (D11), Digital Channel 1 (D12), Digital Channel 2 (D13), "
    "Digital Channel 3 (D17), Not Used2, Digital Channel 4 (D18), Analog Channel 0, "
    "Analog Channel 1, Analog Channel 2, Timestamp, Marker Channel, Timestamp (Formatted)"
).split(', ')


def load_eeg(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep='\t', skiprows=4, names=titles, header=None)


def find_video_start(df: pd.DataFrame) -> int:
    """row index where marker == 0 (video_start signal from sync_server)"""
    hits = df.index[df['Marker Channel'] == 0]
    if hits.empty:
        raise ValueError(f'marker 0 (video_start) non trovato in {df.shape[0]} righe')
    return hits[0]


def cut_segments(df: pd.DataFrame, start_row: int, markers: list) -> list[tuple]:
    """returns [(label, df_segment), ...] one per scene"""
    boundaries = [(m['label'], start_row + int(m['offset_ms'] / 1000 * fs)) for m in markers]
    boundaries.append(('END', len(df)))

    segments = []
    for i in range(len(boundaries) - 1):
        label, row_s = boundaries[i]
        _, row_e     = boundaries[i + 1]
        seg = df.iloc[row_s:row_e].copy()
        seg = seg.reset_index(drop=True)
        segments.append((label, seg))
    return segments


def save_segments(segments: list, stem: str, out_dir: Path):
    for i, (label, seg) in enumerate(segments):
        name = f'{stem}_seg{i+1:02d}_{label}.csv'
        seg.to_csv(out_dir / name, index=False)
        print(f'  → {name} ({len(seg)} samples, {len(seg)/fs:.1f}s)')


if __name__ == '__main__':
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(markers_file) as f:
        markers = json.load(f)
    print(f'{len(markers)} marker caricati da {markers_file}')

    csvs = list(eeg_dir.glob('*.csv'))
    if not csvs:
        raise FileNotFoundError(f'nessun CSV in {eeg_dir}')

    for path in csvs:
        print(f'\n{path.name}')
        df        = load_eeg(path)
        start_row = find_video_start(df)
        print(f'  video_start @ row {start_row} ({start_row/fs:.1f}s dall\'inizio registrazione)')
        segments  = cut_segments(df, start_row, markers)
        save_segments(segments, path.stem, out_dir)

    print(f'\nfatto. segmenti in {out_dir.absolute()}')
