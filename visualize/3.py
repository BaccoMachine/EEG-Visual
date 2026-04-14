import mne
import numpy as np
import matplotlib.pyplot as plt
import cv2

# ---- Load BDF ----
raw = mne.io.read_raw_bdf("your_recording.bdf", preload=True)

raw.filter(1., 45.)

# raw.rename_channels(lambda x: x.replace("EEG ", "").strip())

sfreq = raw.info['sfreq']
data = raw.get_data()
# ch_names = raw.ch_names
data = data[:16]


# ---- Frequency bands ----
bands = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 12),
    "beta": (12, 30),
    "gamma": (30, 45)
}

# ---- OpenBCI Ultracortex (approx positions) ----
# 2D layout (simplified top view)
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

ch_names = [channel_map[i] for i in range(16)]
# ch_names = [channel_map[i] for i in range(16)]
## Keep only channels we have positions for
# valid_idx = [i for i, ch in enumerate(ch_names) if ch in positions]
# data = data[valid_idx]
# ch_names = [ch_names[i] for i in valid_idx]
# ---- Sliding window params ----
win_sec = 2
step_sec = 0.5

win_samples = int(win_sec * sfreq)
step_samples = int(step_sec * sfreq)


frames = []

print("Data shape:", data.shape)
print("Channels:", ch_names)
print(ch_names)
print(list(positions.keys()))
# ---- Helper: compute band power ----
def band_power(signal, sfreq, band):
    freqs, psd = mne.time_frequency.psd_array_welch(
        signal, sfreq=sfreq, fmin=band[0], fmax=band[1], verbose=False
    )
    return np.mean(psd)

# ---- Loop over time ----
for start in range(0, data.shape[1] - win_samples, step_samples):
    segment = data[:, start:start + win_samples]

    dominant_bands = []

    for ch_signal in segment:
        powers = {b: band_power(ch_signal, sfreq, bands[b]) for b in bands}
        dominant = max(powers, key=powers.get)
        dominant_bands.append(dominant)

    # ---- Plot frame ----
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')

    color_map = {
        "delta": "blue",
        "theta": "cyan",
        "alpha": "green",
        "beta": "orange",
        "gamma": "red"
    }

    # for ch, band in zip(ch_names, dominant_bands):
    #     x, y = positions[ch]
    #     ax.scatter(x, y, s=300, color=color_map[band])
    #     ax.text(x, y, ch, ha='center', va='center', fontsize=8, color='white')
    ax.set_facecolor("black")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)

    for ch, band in zip(ch_names, dominant_bands):
        x, y = positions[ch]

        ax.scatter(
            x, y,
            s=1200,
            color=color_map[band],
            edgecolors='white',
            linewidth=1.5
        )

        ax.text(
            x, y, ch,
            ha='center', va='center',
            fontsize=9,
            color='white',
            weight='bold'
        )
    ax.set_title(f"Time: {start/sfreq:.1f}s")

    # Save frame to array
    # fig.canvas.draw()
    # img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    # img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    fig.canvas.draw()

    # Get RGBA buffer
    buf = np.asarray(fig.canvas.buffer_rgba())

    # Convert RGBA → RGB (drop alpha channel)
    img = buf[:, :, :3].copy()

    frames.append(img)

    plt.close(fig)

# ---- Write video ----
height, width, _ = frames[0].shape
out = cv2.VideoWriter("brain_bands.mp4",
                      cv2.VideoWriter_fourcc(*'mp4v'),
                      5, (width, height))

for frame in frames:
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

out.release()
