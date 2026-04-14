import time
import threading
import numpy as np
from datetime import datetime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter

import pyedflib

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Vertical

# -----------------------------
# CONFIG
# -----------------------------
BOARD_ID = BoardIds.CYTON_DAISY_BOARD.value  # 16 channels
SAMPLING_RATE = BoardShim.get_sampling_rate(BOARD_ID)
EEG_CHANNELS = BoardShim.get_eeg_channels(BOARD_ID)

RAIL_THRESHOLD = 4.5e-3  # ~4.5 mV threshold for railing detection

# -----------------------------
# GLOBAL STATE
# -----------------------------
class RecorderState:
    def __init__(self):
        self.board = None
        self.running = False
        self.data_buffer = []
        self.key_log = []
        self.file_name = "session"
        self.labels = {str(i): f"Key{i}" for i in range(1, 10)}

state = RecorderState()

# -----------------------------
# BDF+ WRITER
# -----------------------------
def write_bdf(filename, data):
    n_channels = data.shape[0]

    writer = pyedflib.EdfWriter(
        filename,
        n_channels=n_channels,
        file_type=pyedflib.FILETYPE_BDFPLUS
    )

    channel_info = []
    for i in range(n_channels):
        ch_dict = {
            'label': f'EEG {i}',
            'dimension': 'uV',
            'sample_frequency': SAMPLING_RATE,
            'physical_min': -100000,
            'physical_max': 100000,
            'digital_min': -8388608,
            'digital_max': 8388607,
            'transducer': '',
            'prefilter': ''
        }
        channel_info.append(ch_dict)

    writer.setSignalHeaders(channel_info)
    writer.writeSamples(data)
    writer.close()


def write_keystrokes(filename, key_log):
    with open(filename, "w") as f:
        for ts, key, label in key_log:
            f.write(f"{ts},{key},{label}\n")


# -----------------------------
# DATA THREAD
# -----------------------------
def acquisition_loop():
    global state
    while state.running:
        data = state.board.get_board_data()
        if data.shape[1] > 0:
            state.data_buffer.append(data)
        time.sleep(0.1)


# -----------------------------
# TUI APP
# -----------------------------
class EEGApp(App):

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Input(placeholder="File name...", id="filename"),
            Static("Press START to begin", id="status"),
            Static("", id="channels"),
            Button("START", id="start"),
            Button("STOP", id="stop"),
            Static("Keys: 1-9 mapped", id="keys")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start":
            self.start_recording()
        elif event.button.id == "stop":
            self.stop_recording()

    def on_input_changed(self, event: Input.Changed):
        state.file_name = event.value or "session"

    def start_recording(self):
        if state.running:
            return

        params = BrainFlowInputParams()
        params.serial_port = "/dev/ttyUSB0"
        state.board = BoardShim(BOARD_ID, params)

        state.board.prepare_session()
        state.board.start_stream()

        state.running = True
        state.data_buffer = []
        state.key_log = []

        threading.Thread(target=acquisition_loop, daemon=True).start()
        self.query_one("#status").update("Recording...")

    def stop_recording(self):
        if not state.running:
            return

        state.running = False
        state.board.stop_stream()
        state.board.release_session()

        # concatenate data
        full_data = np.hstack(state.data_buffer)

        eeg_data = full_data[EEG_CHANNELS]

        bdf_name = state.file_name + ".bdf"
        key_name = state.file_name + "_keys.csv"

        write_bdf(bdf_name, eeg_data)
        write_keystrokes(key_name, state.key_log)

        self.query_one("#status").update(f"Saved: {bdf_name}")

    def on_key(self, event):
        if event.key in state.labels:
            ts = time.time()
            label = state.labels[event.key]
            state.key_log.append((ts, event.key, label))

    def on_mount(self):
        self.set_interval(0.5, self.update_display)

    def update_display(self):
        if not state.running or not state.data_buffer:
            return

        latest = state.data_buffer[-1]
        eeg = latest[EEG_CHANNELS]

        lines = []
        for i, ch in enumerate(eeg):
            val = np.mean(ch)
            railing = "⚠️" if abs(val) > RAIL_THRESHOLD else ""
            lines.append(f"Ch{i:02d}: {val: .5f} {railing}")

        self.query_one("#channels").update("\n".join(lines))


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    BoardShim.enable_dev_board_logger()
    app = EEGApp()
    app.run()
