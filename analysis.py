from data_processing import (
    data_dir,
    out_dir,
    fs,
    csv2exps,
    export_spettrogrammi_completi,
    export_spettrogramma_medio,
    export_welch_per_sezione,
    load_participant_psds,
    export_welch_overlay,
    export_welch_video,
    export_welch_all,
)


if __name__ == '__main__':
    out_dir.mkdir(exist_ok=True)

    print('loading data...')
    _, segments = csv2exps(data_dir)

    print('per-experiment plots...')
    export_spettrogrammi_completi(segments, out_dir, fs_hardware=fs)
    export_spettrogramma_medio(segments, out_dir, fs_hardware=fs)
    export_welch_per_sezione(segments, out_dir, fs_hardware=fs)

    print('overlay plots...')
    data = load_participant_psds()
    export_welch_overlay(data, out_dir)
    video_entries = export_welch_video(data, out_dir)
    export_welch_all(data, video_entries, out_dir)

    print(f'done → {out_dir.absolute()}')
