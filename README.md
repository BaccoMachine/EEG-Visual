# OpenBCI Scripts

Using Cyton + Daisy on a Ultracortex

This software is horribly vibe coded with minimal corrections, further development will improve it.

## Quick Start

not all packages are needed by all scripts 

```
python3 -m venv env
source env/bin/activate
```

```
pip install mne numpy matplotlib opencv-python 
pip install brainflow textual pyedflib numpy 
pip install fastapi uvicorn pypdf python-multipart
```

## EEG Analysis (`data_processing.py`)

Pipeline for processing raw BrainFlow CSV recordings from the Cyton+Daisy (16 channels, 125 Hz).

**What it does:**

1. **Segmentation** — reads all CSVs in `data/`, splits each recording into experiments using the Marker Channel (marker `1` = start, any other marker = end of section)
2. **Spectrogram per channel** — for each experiment, generates a 16-panel spectrogram (1–40 Hz, Viridis colormap) with EEG band labels (δ θ α β γ) and marker timestamps overlaid
3. **Average spectrogram** — mean power across all 16 channels in a single plot, same band/marker annotations
4. **Welch PSD per section** — splits each experiment at marker boundaries and plots the average Welch PSD (1–40 Hz) for each section on the same axes

**Output:** PNG files saved to `output_grafici/`

```
Exp_01_Dettaglio_16_canali.png   # per-channel spectrogram
Exp_01_Media_Globale.png         # cross-channel mean spectrogram
Exp_01_Welch_Sezioni.png         # Welch PSD by marker section
```

**Run:**

```bash
python3 data_processing.py
```

Place BrainFlow CSV files in `data/` before running.
