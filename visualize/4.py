import mne
import numpy as np
import matplotlib.pyplot as plt
import cv2
from mne.time_frequency import psd_array_welch

# =========================
# CONFIG
# =========================
FILE = "your_recording.bdf"

sfreq_target = None  # keep original sampling rate

bands = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 12),
    "beta": (12, 30),
    "gamma": (30, 45)
}

color_map = {
    "delta": "blue",
    "theta": "cyan",
    "alpha": "green",
    "beta": "orange",
    "gamma": "red"
}

band_greek = {
    "delta": "δ",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
    "gamma": "γ"
}

# =========================
# OPENBCI CYTON + DAISY MAP
# =========================
channel_map = {
    0: "Fp1", 1: "Fp2",
    2: "F7",  3: "F3",
    4: "Fz",  5: "F4",
    6: "F8",  7: "T7",
    8: "C3",  9: "Cz",
    10: "C4", 11: "T8",
    12: "P7", 13: "P3",
    14: "P4", 15: "P8",
}

positions = {
    "Fp1": (-0.5, 1.0), "Fp2": (0.5, 1.0),

    "F7": (-1.0, 0.6), "F3": (-0.5, 0.6),
    "Fz": (0.0, 0.7),  "F4": (0.5, 0.6),
    "F8": (1.0, 0.6),

    "T7": (-1.1, 0.0), "C3": (-0.5, 0.0),
    "Cz": (0.0, 0.0),  "C4": (0.5, 0.0),
    "T8": (1.1, 0.0),

    "P7": (-0.9, -0.6), "P3": (-0.4, -0.5),
    "P4": (0.4, -0.5),  "P8": (0.9, -0.6),
}

# =========================
# LOAD DATA
# =========================
raw = mne.io.read_raw_bdf(FILE, preload=True)

# Clean channel names (optional safety)
raw.rename_channels(lambda x: x.replace("EEG ", "").strip())

data = raw.get_data()[:16]  # Cyton + Daisy only
sfreq = raw.info["sfreq"]

ch_names = [channel_map[i] for i in range(16)]

print("Data shape:", data.shape)
print("Channels:", ch_names)

# =========================
# PARAMETERS
# =========================
win_sec = 2
step_sec = 0.5

win_samples = int(win_sec * sfreq)
step_samples = int(step_sec * sfreq)

# =========================
# BAND POWER FUNCTION
# =========================
# def band_power(signal, sfreq, band):
#     freqs, psd = psd_array_welch(
#         signal,
#         sfreq=sfreq,
#         fmin=band[0],
#         fmax=band[1],
#         verbose=False
#     )
#     val = np.mean(psd)
#     return 0 if np.isnan(val) else val

# def band_power(signal, sfreq, band):
#     n_times = len(signal)

#     freqs, psd = psd_array_welch(
#         signal,
#         sfreq=sfreq,
#         fmin=band[0],
#         fmax=band[1],
#         n_fft=min(128, n_times),   # ✅ FIX HERE
#         n_per_seg=min(128, n_times),
#         verbose=False
#     )

#     val = np.mean(psd)
#     return 0 if np.isnan(val) else val

def band_power(signal, sfreq, band):
    n_times = len(signal)

    n_fft = min(64, n_times)

    freqs, psd = psd_array_welch(
        signal,
        sfreq=sfreq,
        fmin=band[0],
        fmax=band[1],
        n_fft=n_fft,
        n_per_seg=n_fft,
        verbose=False
    )

    return np.trapezoid(psd, freqs)  # more stable than mean
# =========================
# VIDEO SETUP
# =========================
frames = []

# =========================
# PROCESS WINDOW BY WINDOW
# =========================
for start in range(0, data.shape[1] - win_samples, step_samples):

    segment = data[:, start:start + win_samples]

    dominant_bands = []

    for ch_signal in segment:

        powers = {
            b: band_power(ch_signal, sfreq, bands[b])
            for b in bands
        }

        dominant = max(powers, key=powers.get)
        dominant_bands.append(dominant)

    # =========================
    # DRAW FRAME
    # =========================
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
    ax.set_facecolor("black")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis("off")

    # head outline
    circle = plt.Circle((0, 0), 1.1, color="white", fill=False, linewidth=2)
    ax.add_patch(circle)

    # plot electrodes
    for ch, band in zip(ch_names, dominant_bands):

        if ch not in positions:
            continue

        x, y = positions[ch]

        ax.scatter(
            x, y,
            s=1200,
            color=color_map[band],
            edgecolors="white",
            linewidth=1.5
        )
        # Greek letter INSIDE circle
        ax.text(
            x, y,
            band_greek[band],
            ha="center",
            va="center",
            fontsize=16,
            color="white",
            weight="bold"
        )
        # ax.text(
        #     x, y,
        #     ch,
        #     color="white",
        #     ha="center",
        #     va="center",
        #     fontsize=8,
        #     weight="bold"
        # )
        # optional small electrode label (outside)
        ax.text(
            x, y - 0.18,
            ch,
            ha="center",
            va="center",
            fontsize=7,
            color="black"
        )

    ax.set_title(f"EEG Band Activity | t={start/sfreq:.1f}s", color="white")

    # =========================
    # CONVERT FIG TO IMAGE
    # =========================
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]

    frames.append(img)
    plt.close(fig)

# =========================
# WRITE VIDEO
# =========================
h, w, _ = frames[0].shape

out = cv2.VideoWriter(
    "brain_bands.mp4",
    cv2.VideoWriter_fourcc(*"mp4v"),
    5,
    (w, h)
)

for f in frames:
    out.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))

out.release()

print("Saved: brain_bands.mp4")
