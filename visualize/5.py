import mne
import numpy as np
import matplotlib.pyplot as plt
import cv2
from mne.time_frequency import psd_array_welch

# =========================
# LOAD DATA
# =========================
raw = mne.io.read_raw_bdf("your_recording.bdf", preload=True)

raw.rename_channels(lambda x: x.replace("EEG ", "").strip())
raw.filter(1., 40.)
raw.notch_filter(50)

data = raw.get_data()[:16]
sfreq = raw.info["sfreq"]

# =========================
# BAND DEFINITIONS
# =========================
bands = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 12),
    "beta": (12, 30),
    "gamma": (30, 45)
}

band_colors = {
    "delta": "Blues",
    "theta": "PuBu",
    "alpha": "Greens",
    "beta": "Oranges",
    "gamma": "Reds"
}

band_greek = {
    "delta": "δ",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ"
}

# =========================
# 10–20 MONTAGE (CRITICAL)
# =========================
montage = mne.channels.make_standard_montage("standard_1020")
raw.set_montage(montage, match_case=False)

# =========================
# TIME WINDOWS
# =========================
win_sec = 2
step_sec = 0.5

win = int(win_sec * sfreq)
step = int(step_sec * sfreq)

frames = []

# =========================
# BAND POWER FUNCTION
# =========================
def band_power(sig, sfreq, band):
    n_fft = min(128, len(sig))

    freqs, psd = psd_array_welch(
        sig,
        sfreq=sfreq,
        fmin=band[0],
        fmax=band[1],
        n_fft=n_fft,
        n_per_seg=n_fft,
        verbose=False
    )

    return np.log(np.trapezoid(psd, freqs) + 1e-12)

# =========================
# MAIN LOOP
# =========================
for start in range(0, data.shape[1] - win, step):

    segment = data[:, start:start + win]

    band_maps = {}

    for b in bands:
        vals = []

        for ch in segment:
            vals.append(band_power(ch, sfreq, bands[b]))

        band_maps[b] = np.array(vals)

    # dominant band per channel
    dominant = np.array(list(band_maps.keys()))[
        np.argmax(np.vstack(list(band_maps.values())), axis=0)
    ]

    # =========================
    # PLOT TOPOGRAPHIC MAPS
    # =========================
    fig, axes = plt.subplots(1, 5, figsize=(15, 3))

    for i, (b, ax) in enumerate(zip(bands.keys(), axes)):

        mne.viz.plot_topomap(
            band_maps[b],
            raw.info,
            axes=ax,
            show=False,
            cmap=band_colors[b],
            contours=6
        )

        ax.set_title(band_greek[b], fontsize=14)

    fig.suptitle(f"EEG Band Topography | t={start/sfreq:.1f}s")

    # =========================
    # CONVERT FRAME
    # =========================
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    frames.append(img)

    plt.close(fig)

# =========================
# SAVE VIDEO
# =========================
h, w, _ = frames[0].shape

out = cv2.VideoWriter(
    "eeg_research.mp4",
    cv2.VideoWriter_fourcc(*"mp4v"),
    5,
    (w, h)
)

for f in frames:
    out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))

out.release()

print("Saved: eeg_research.mp4")
