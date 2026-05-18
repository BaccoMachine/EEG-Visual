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

- `data_processing.py` — library: CSV loading, marker handling, per-experiment plots (16ch detail, avg, Welch by section) and cross-participant overlays. Config + participants list on top.
- `analysis.py` — runner. Imports from `data_processing.py` and generates everything. Notes in `analysis_notes.md`.
- `record/`, `visualize/` — older scripts, kept for reference.
- `rename_openbci_files_.py` — renames raw files to something usable.
- `archive/web/` — old browser-based experiment pipeline (marker definer + sync server). Not in use right now.

## Run

Put BrainFlow CSVs in `data/`, then:

```bash
python3 analysis.py
```

Output goes in `output/`.
