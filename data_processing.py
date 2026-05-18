import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import welch, spectrogram


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


def csv2exps(datadir):
    """get all csvs from a "data" directory, return a dictionary of experiments and a list of all of them"""
    #datadir = Path('data')
    allf = {}
    exps = {}
    sgms = []

    titles = "Sample Index, EXG Channel 0, EXG Channel 1, EXG Channel 2, EXG Channel 3, EXG Channel 4, EXG Channel 5, EXG Channel 6, EXG Channel 7, EXG Channel 8, EXG Channel 9, EXG Channel 10, EXG Channel 11, EXG Channel 12, EXG Channel 13, EXG Channel 14, EXG Channel 15, Accel Channel 0, Accel Channel 1, Accel Channel 2, Not Used1, Digital Channel 0 (D11), Digital Channel 1 (D12), Digital Channel 2 (D13), Digital Channel 3 (D17), Not Used2, Digital Channel 4 (D18), Analog Channel 0, Analog Channel 1, Analog Channel 2, Timestamp, Marker Channel, Timestamp (Formatted)".split(', ')

    for files in datadir.glob('*.csv'):
        df = pd.read_csv(files,sep='\t',skiprows=4,names=titles,header = None)
        allf[files.stem] = df

        all_markers = df.index[df['Marker Channel'] != 0]
        ones = df.index[df['Marker Channel'] == 1]

        file_exps = []

        for i in range(len(ones)):
            start_idx = ones[i]

            if i < len(ones) - 1:
                next_start = ones[i+1]
                valid_ends = all_markers[(all_markers > start_idx) & (all_markers < next_start)]
                end_idx = valid_ends.max() if not valid_ends.empty else start_idx
            else:
                valid_ends = all_markers[all_markers > start_idx]
                end_idx = valid_ends.max() if not valid_ends.empty else start_idx

            file_exps.append(df.loc[start_idx:end_idx].copy())

        sgms.extend(file_exps) #add segments to global list
        exps[files.stem] = file_exps
    return  exps, sgms

    #exps = {'filename': [exp1, exp2, ...], ...} where expi is one experiment segment
    #sgms = [exp1, exp2, ...]


def sampling_frequency(df):
    """get sampling freq. Reminder: timestamps depend on file-writing time, not on the actual device sampling rate"""
    time_diffs = df['Timestamp'].diff().dropna()
    time_diffs = time_diffs[time_diffs > 0]
    if not time_diffs.empty:
        return 1 / time_diffs.mean()
    else:
        return None

def estrai_tempi_marker(exexp, fs_hardware):
    marker_vals = exexp['Marker Channel'].values
    marker_times = []
    last_val = 0

    for row_idx, val in enumerate(marker_vals):
        if val != 0 and val != last_val:
            tempo_sec = row_idx / fs_hardware
            marker_times.append((tempo_sec, int(val)))
            last_val = val
        elif val == 0:
            last_val = 0

    return marker_times
def get_spect(seg: pd.DataFrame, fs_hardware=125.0) -> tuple:
    """get a spectrogram of a segment for every channel, return freqs, times, and psd_db for each channel"""
    samp_w = int(fs_hardware * 2)
    ol = int(samp_w * 0.90)
    chns = [f'EXG Channel {i}' for i in range(16)] #cyton+Daisy standard has 16 channels \




def export_spettrogrammi_completi(sgms, outdir, fs_hardware=125.0):
    samp_w = int(fs_hardware * 2)
    ol = int(samp_w * 0.90)
    chns = [f'EXG Channel {i}' for i in range(16)]

    for i, exexp in enumerate(sgms):
        print(f"Exporting 16 channels - Experiment {i+1}...")
        fig, axes = plt.subplots(16, 1, figsize=(20, 30), sharex=True)

        lunghezza_sec = len(exexp) / fs_hardware
        marker_times = estrai_tempi_marker(exexp, fs_hardware)

        fig.suptitle(f'Experiment {i+1} (16 Channel Detail)\nDuration: {lunghezza_sec:.1f}s', fontsize=22, fontweight='bold', y=0.99)

        for ch_idx, chn in enumerate(chns):
            ax = axes[ch_idx]

            freqs, t, psd = spectrogram(exexp[chn].values, fs=fs_hardware, nperseg=samp_w, noverlap=ol)

            good_is = (freqs >= 1.0) & (freqs <= 40.0)
            fok = freqs[good_is]
            psd = psd[good_is, :]
            psd_db = 10 * np.log10(psd + 1e-10)

            ax.pcolormesh(t, fok, psd_db, shading='gouraud', cmap='viridis')
            ax.set_ylabel(f'Ch {ch_idx}', rotation=0, labelpad=25, va='center', fontweight='bold', fontsize=12)

            if ch_idx == 0:
                ax.set_yticks([10, 20, 30, 40])
            else:
                ax.set_yticks([])
            eeg_bands = {
                r'$\delta$ (1-4 Hz)': (1, 4),
                r'$\theta$ (4-8 Hz)': (4, 8),
                r'$\alpha$ (8-12 Hz)': (8, 12),
                r'$\beta$ (13-30 Hz)': (13, 30),
                r'$\gamma$ (30-40 Hz)': (30, 40)
            }
            for name, (f_min, f_max) in eeg_bands.items():
                ax.axhline(f_min, color='white', linestyle=':', alpha=0.3)
                if ch_idx == 0: # band labels only on top channel
                    ax.text(lunghezza_sec * 0.01, (f_min + f_max)/2, name, color='white', alpha=0.8, va='center', fontsize=10, fontweight='bold')
            for t_m, val in marker_times:
                ax.axvline(x=t_m, color='red', linestyle='--', linewidth=1.5, alpha=0.8)
                if ch_idx == 0:
                    ax.text(t_m, 45, f'M{val}', color='red', fontsize=14, fontweight='bold', ha='center', va='bottom')

        axes[-1].set_xlabel('Time from start (seconds)', fontsize=18, fontweight='bold')
        axes[-1].set_xticks(np.arange(0, lunghezza_sec, step=5.0))
        axes[-1].tick_params(axis='x', labelsize=14)

        plt.tight_layout()
        plt.subplots_adjust(top=0.95, hspace=0.05)

        filepath = outdir / f"Exp_{i+1:02d}_16ch_detail.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)

def export_spettrogramma_medio(sgms, outdir, fs_hardware=125.0):
    samp_w = int(fs_hardware * 2)
    ol = int(samp_w * 0.90)
    chns = [f'EXG Channel {i}' for i in range(16)]

    for i, exexp in enumerate(sgms):
        print(f"Exporting channel average - Experiment {i+1}...")
        lunghezza_sec = len(exexp) / fs_hardware
        marker_times = estrai_tempi_marker(exexp, fs_hardware)

        psds_accumulati = []
        fok, t = None, None

        for chn in chns:
            freqs, t_temp, psd = spectrogram(exexp[chn].values, fs=fs_hardware, nperseg=samp_w, noverlap=ol)
            good_is = (freqs >= 1.0) & (freqs <= 40.0)
            fok = freqs[good_is]
            psd = psd[good_is, :]
            t = t_temp
            psds_accumulati.append(psd)

        psd_media_lineare = np.mean(psds_accumulati, axis=0)
        psd_media_db = 10 * np.log10(psd_media_lineare + 1e-10)

        fig, ax = plt.subplots(figsize=(16, 8))
        mesh = ax.pcolormesh(t, fok, psd_media_db, shading='gouraud', cmap='viridis')

        ax.set_title(f'Experiment {i+1} (16-Channel Average)\nDuration: {lunghezza_sec:.1f}s', fontsize=18, fontweight='bold')
        ax.set_ylabel('Frequency (Hz)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Time from start (seconds)', fontsize=14, fontweight='bold')

        ax.set_xticks(np.arange(0, lunghezza_sec, step=5.0))

        eeg_bands = {
            r'$\delta$ (1-4 Hz)': (1, 4),
            r'$\theta$ (4-8 Hz)': (4, 8),
            r'$\alpha$ (8-12 Hz)': (8, 12),
            r'$\beta$ (13-30 Hz)': (13, 30),
            r'$\gamma$ (30-40 Hz)': (30, 40)
        }
        for name, (f_min, f_max) in eeg_bands.items():
            ax.axhline(f_min, color='white', linestyle=':', alpha=0.4)
            ax.text(lunghezza_sec * 0.01, (f_min + f_max)/2, name, color='white', alpha=0.8, va='center', fontsize=12, fontweight='bold')

        for t_m, val in marker_times:
            ax.axvline(x=t_m, color='red', linestyle='--', linewidth=2, alpha=0.9)
            ax.text(t_m, 41, f'Marker {val}', color='red', fontsize=12, fontweight='bold', ha='center', va='bottom')

        cbar = plt.colorbar(mesh, ax=ax)
        cbar.set_label('Average Power (dB)', fontsize=12)

        plt.tight_layout()

        filepath = outdir / f"Exp_{i+1:02d}_avg.png"
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        plt.close(fig)

def export_welch_per_sezione(sgms, outdir, fs_hardware=125.0):
    chns = [f'EXG Channel {i}' for i in range(16)]

    for i, exexp in enumerate(sgms):
        print(f"Welch by section - Experiment {i+1}...")

        marker_times = estrai_tempi_marker(exexp, fs_hardware)
        n_rows = len(exexp)

        if not marker_times:
            sections = [('Intero', 0, n_rows)]
        else:
            sections = []
            for j, (t_sec, val) in enumerate(marker_times):
                start_row = int(t_sec * fs_hardware)
                end_row = int(marker_times[j+1][0] * fs_hardware) if j < len(marker_times) - 1 else n_rows
                sections.append((f'M{val}', start_row, end_row))

        fig, ax = plt.subplots(figsize=(12, 6))

        for label, start_row, end_row in sections:
            chunk = exexp.iloc[start_row:end_row]
            if len(chunk) < int(fs_hardware * 2):
                continue

            psds = []
            for chn in chns:
                freqs, psd = welch(chunk[chn].values, fs=fs_hardware, nperseg=int(fs_hardware * 2))
                good_is = (freqs >= 1.0) & (freqs <= 40.0)
                psds.append(psd[good_is])

            freqs_ok = freqs[good_is]
            psd_db = 10 * np.log10(np.mean(psds, axis=0) + 1e-10)
            ax.plot(freqs_ok, psd_db, label=label, linewidth=2)

        bande_eeg = {'δ': (1, 4), 'θ': (4, 8), 'α': (8, 12), 'β': (13, 30), 'γ': (30, 40)}
        for nome, (f_min, f_max) in bande_eeg.items():
            ax.axvline(f_min, color='gray', linestyle=':', alpha=0.4)
            ax.text((f_min + f_max) / 2, 0.02, nome,
                    transform=ax.get_xaxis_transform(), ha='center', fontsize=10, color='gray')

        ax.set_xlabel('Frequency (Hz)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Average Power (dB)', fontsize=13, fontweight='bold')
        ax.set_title(f'Experiment {i+1} — Welch by Section', fontsize=15, fontweight='bold')
        ax.legend(fontsize=11)
        ax.set_xlim(1, 40)

        plt.tight_layout()
        filepath = outdir / f"Exp_{i+1:02d}_welch.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)


# --- overlay tra partecipanti ---

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
