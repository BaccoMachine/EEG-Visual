import mne
import matplotlib.pyplot as plt

# Replace this with the path to your BDF+ file
bdf_file = "asd.bdf"

# Load the BDF+ file
raw = mne.io.read_raw_bdf(bdf_file, preload=True)

# Print info about channels
print(raw.info)

# Plot all channels as a timeline
raw.plot(n_channels=len(raw.ch_names), scalings='auto', title='EEG Timeline')
