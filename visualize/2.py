import mne
import matplotlib.pyplot as plt

# Path to your BDF+ file
bdf_file = "asd.bdf"

# Load data
raw = mne.io.read_raw_bdf(bdf_file, preload=True)

# Get data and time vector
data, times = raw.get_data(return_times=True)

# Create figure
plt.figure(figsize=(15, 10))

# Offset between channels (so they don't overlap)
offset = 0
spacing = max(data.flatten()) - min(data.flatten())

# Plot each channel
for i, channel in enumerate(data):
    plt.plot(times, channel + i * spacing, linewidth=0.5)

# Label channels on y-axis
plt.yticks(
    [i * spacing for i in range(len(raw.ch_names))],
    raw.ch_names
)

plt.xlabel("Time (seconds)")
plt.ylabel("Channels")
plt.title("EEG Channels Timeline")

# Improve layout
plt.tight_layout()

# Save image
plt.savefig("eeg_timeline.png", dpi=300)

# Optional: show plot
plt.show()
