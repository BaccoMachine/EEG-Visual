# OpenBCI Scripts

Cyton + Daisy on a Ultracortex, 16ch @ 125 Hz.

Vibe coded, work in progress.

## Setup

```
python3 -m venv env
source env/bin/activate
pip install mne numpy matplotlib opencv-python brainflow scipy pandas
```

Not every script needs everything.

## What's here

- `data_processing.py` — splits BrainFlow CSVs by Marker Channel and makes per-experiment plots (16ch detail, average, Welch by section). Put the CSVs in `data/`, run it, output goes in `output/`.
- `analysis.py` — overlay plots across participants. Reads the same data through `data_processing.py` functions. Notes in `analysis_notes.md`.
- `record/`, `visualize/` — older scripts, kept for reference.
- `rename_openbci_files_.py` — renames raw files to something usable.
- `archive/web/` — old browser-based experiment pipeline (marker definer + sync server). Not in use right now.

## Run

```bash
python3 data_processing.py
python3 analysis.py
```
