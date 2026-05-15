import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.signal import welch, spectrogram
import numpy as np


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


if __name__ == "__main__":
    datadir = Path('data')
    outdir = Path('output')
    outdir.mkdir(exist_ok=True)
    
    print("Reading CSVs and segmenting experiments...")
    experiments, segments = csv2exps(datadir)

    if segments:
        print(f"Found {len(segments)} segments. Generating plots...")
        #export_spettrogramma_medio(segments, outdir, fs_hardware=125.0)
        #export_spettrogrammi_completi(segments, outdir, fs_hardware=125.0)
        export_welch_per_sezione(segments, outdir, fs_hardware=125.0)
        print(f"Done. Output saved to: {outdir.absolute()}")
    else:
        print("No valid segments found. Check the files in /data.")