import pandas as pd
import numpy as np
from scipy.signal import welch
from pathlib import Path
import matplotlib.pyplot as plt

from data_processing import (
    csv2exps,
    estrai_tempi_marker,
    export_spettrogrammi_completi,
    export_spettrogramma_medio,
    export_welch_per_sezione,
)

# --- config ---
data_dir     = Path('data')
out_dir      = Path('output')
fs           = 125.0
nperseg      = int(fs * 2)
chns         = [f'EXG Channel {i}' for i in range(16)]
bands        = {'δ':(1,4), 'θ':(4,8), 'α':(8,12), 'β':(13,30), 'γ':(30,40)}
valid_dur    = (8, 200)   # sezioni più corte o più lunghe vengono saltate

# (pid, filename, cycle_index) — un partecipante unico per riga
# i file BrainFlow sono split: file_N contiene i partecipanti da N in poi,
# quindi (file_N, cycle_0) = partecipante N+3 univoco
participants = [
    ('P3', 'BrainFlow-RAW_2026-04-24_16-31-12-prove-esperimento_0_prove esperimento 3-4.csv', 0),
    ('P4', 'BrainFlow-RAW_2026-04-24_16-31-12-prove-esperimento_1_prove esperimento 3-4.csv', 0),
    ('P5', 'BrainFlow-RAW_2026-04-24_16-31-12-prove-esperimento_2_prove esperimento 3-4.csv', 0),
    ('P6', 'BrainFlow-RAW_2026-04-24_16-31-12-prove-esperimento_3_prove esperimento 3-4.csv', 0),
    ('P7', 'BrainFlow-RAW_2026-04-24_16-31-12-prove-esperimento_4_prove esperimento 3-4.csv', 0),
    ('P8', 'BrainFlow-RAW_2026-04-24_17-14-03_0_prove esperimento 5-6.csv', 0),
    ('P9', 'BrainFlow-RAW_2026-04-24_17-14-03_1_prove esperimento 5-6.csv', 0),
]

titles = (
    "Sample Index, EXG Channel 0, EXG Channel 1, EXG Channel 2, EXG Channel 3, "
    "EXG Channel 4, EXG Channel 5, EXG Channel 6, EXG Channel 7, EXG Channel 8, "
    "EXG Channel 9, EXG Channel 10, EXG Channel 11, EXG Channel 12, EXG Channel 13, "
    "EXG Channel 14, EXG Channel 15, Accel Channel 0, Accel Channel 1, Accel Channel 2, "
    "Not Used1, Digital Channel 0 (D11), Digital Channel 1 (D12), Digital Channel 2 (D13), "
    "Digital Channel 3 (D17), Not Used2, Digital Channel 4 (D18), Analog Channel 0, "
    "Analog Channel 1, Analog Channel 2, Timestamp, Marker Channel, Timestamp (Formatted)"
).split(', ')


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep='\t', skiprows=4, names=titles, header=None)


def get_cycles(df: pd.DataFrame) -> list[list[tuple]]:
    cycles, current, last = [], [], 0
    for row, val in zip(df.index, df['Marker Channel']):
        val = int(val)
        if val != 0 and val != last:
            if val == 1 and current:
                cycles.append(current)
                current = []
            current.append((row, val))
            last = val
        elif val == 0:
            last = 0
    if current:
        cycles.append(current)
    return cycles


def get_segment(df: pd.DataFrame, cycle: list[tuple], marker_val: int) -> pd.DataFrame | None:
    for i, (row, val) in enumerate(cycle):
        if val != marker_val:
            continue
        end = cycle[i+1][0] if i+1 < len(cycle) else len(df)
        seg = df.iloc[row:end]
        dur = len(seg) / fs
        if valid_dur[0] <= dur <= valid_dur[1]:
            return seg
    return None


def segment_psd(seg: pd.DataFrame) -> tuple:
    psds = [welch(seg[ch].values, fs=fs, nperseg=nperseg) for ch in chns]
    f, psd_mean = psds[0][0], np.mean([p for _, p in psds], axis=0)
    idx = (f >= 1.0) & (f <= 40.0)
    return f[idx], 10 * np.log10(psd_mean[idx] + 1e-10)


def load_participant_psds() -> dict[int, list[tuple]]:
    """returns {marker: [(pid, f, psd_db), ...]} for all valid segments"""
    data = {m: [] for m in [1, 2, 3, 4, 5, 6]}
    for pid, fname, cycle_idx in participants:
        df = load_csv(data_dir / fname)
        cycles = get_cycles(df)
        if cycle_idx >= len(cycles):
            continue
        cycle = cycles[cycle_idx]
        for m in data:
            seg = get_segment(df, cycle, m)
            if seg is not None:
                f, pdb = segment_psd(seg)
                data[m].append((pid, f, pdb))
    return data


def _draw_bands(ax):
    for bname, (flo, fhi) in bands.items():
        ax.axvline(flo, color='gray', linestyle=':', alpha=0.4)
        ax.text((flo+fhi)/2, 0.02, bname, transform=ax.get_xaxis_transform(),
                ha='center', fontsize=10, color='gray')


def _welch_ax(ax, entries: list[tuple], title: str):
    for pid, f, pdb in entries:
        ax.plot(f, pdb, linewidth=2, label=pid)
    ax.plot(f, np.mean([pdb for _, _, pdb in entries], axis=0),
            color='black', linewidth=2.5, linestyle='--', label='mean')
    _draw_bands(ax)
    ax.set_xlabel('Frequenza (Hz)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Potenza Media (dB)', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold')
    ax.legend(fontsize=11)
    ax.set_xlim(1, 40)


def export_welch_overlay(data: dict, out_dir: Path):
    """un grafico per sezione con tutti i partecipanti sovrapposti"""
    for m, entries in data.items():
        if not entries:
            continue
        fig, ax = plt.subplots(figsize=(12, 6))
        _welch_ax(ax, entries, f'M{m} (n={len(entries)})')
        plt.tight_layout()
        plt.savefig(out_dir / f'Welch_M{m}.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'Welch_M{m}.png')


def export_welch_video(data: dict, out_dir: Path):
    """video intero = M4+M5+M6 concatenati per partecipante"""
    entries = []
    for pid, fname, cycle_idx in participants:
        df = load_csv(data_dir / fname)
        cycles = get_cycles(df)
        if cycle_idx >= len(cycles):
            continue
        cycle = cycles[cycle_idx]
        chunks = [get_segment(df, cycle, m) for m in [4, 5, 6]]
        chunks = [c for c in chunks if c is not None]
        if not chunks:
            continue
        combined = pd.concat(chunks, ignore_index=True)
        f, pdb = segment_psd(combined)
        entries.append((pid, f, pdb))

    fig, ax = plt.subplots(figsize=(12, 6))
    _welch_ax(ax, entries, f'Video M4+M5+M6 (n={len(entries)})')
    plt.tight_layout()
    plt.savefig(out_dir / 'Welch_video.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Welch_video.png')
    return entries


def export_welch_all(data: dict, video_entries: list, out_dir: Path):
    """unica figura con tutte le sezioni"""
    panels = [(data[m], f'M{m}') for m in [1,2,3,4,5,6] if data[m]]
    panels.append((video_entries, 'Video'))

    n = len(panels)
    cols = 4
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols*7, rows*6))
    axes = axes.flatten()

    for ax, (entries, title) in zip(axes, panels):
        _welch_ax(ax, entries, f'{title} (n={len(entries)})')
    for ax in axes[len(panels):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.savefig(out_dir / 'Welch_all.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('Welch_all.png')


if __name__ == '__main__':
    out_dir.mkdir(exist_ok=True)

    print('loading data...')
    _, segments = csv2exps(data_dir)

    print('per-experiment plots...')
    export_spettrogrammi_completi(segments, out_dir, fs_hardware=fs)
    export_spettrogramma_medio(segments, out_dir, fs_hardware=fs)
    export_welch_per_sezione(segments, out_dir, fs_hardware=fs)

    print('overlay plots...')
    data = load_participant_psds()
    export_welch_overlay(data, out_dir)
    video_entries = export_welch_video(data, out_dir)
    export_welch_all(data, video_entries, out_dir)

    print(f'done → {out_dir.absolute()}')
