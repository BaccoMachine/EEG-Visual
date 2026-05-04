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

Processes raw BrainFlow CSVs from Cyton+Daisy (16ch, 125 Hz).

Splits recordings into experiments using the Marker Channel, then generates three plots per experiment:

- **16ch detail** — spectrogram for each channel (1–40 Hz), with band labels and marker lines
- **avg** — same but averaged across all 16 channels
- **welch** — Welch PSD split by marker section, all on one plot

Output goes to `output/`. Put BrainFlow CSVs in `data/` and run:

```bash
python3 data_processing.py
```
