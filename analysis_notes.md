# analysis.py — note

Script principale per l'analisi. Importa le funzioni base da `data_processing.py` e aggiunge tutto il necessario per i grafici overlay tra partecipanti. Si lancia con `python3 analysis.py`.

---

## Struttura dei dati

BrainFlow salva le registrazioni in file CSV separati da tab, con 4 righe di header da saltare. Quando una sessione è lunga (più partecipanti registrati di fila), crea più file con un indice `_0`, `_1`, `_2`... Il file `_0` contiene tutto dall'inizio, `_1` riparte dal secondo partecipante, e così via. Questo vuol dire che i dati si sovrappongono tra file.

Per evitare di analizzare lo stesso partecipante più volte, la lista `participants` in cima allo script identifica ogni soggetto come `(file_N, cycle_0)`: il primo ciclo del file N-esimo è sempre un partecipante unico che non appare in nessun file successivo.

Un "ciclo" è una sequenza di marker da M1 a M7 che corrisponde a un singolo partecipante. Il marker M1 segna l'inizio (occhi chiusi), M7 la fine.

---

## Funzioni

### `load_csv(path)`
Carica un CSV BrainFlow assegnando i nomi delle colonne manualmente, perché il file non ha un header utilizzabile. Restituisce un DataFrame pandas.

### `get_cycles(df)`
Scorre il Marker Channel e raggruppa i marker in cicli. Ogni volta che trova un M1 dopo che un ciclo è già iniziato, chiude il precedente e ne apre uno nuovo. Restituisce una lista di cicli, dove ogni ciclo è una lista di tuple `(row_index, marker_value)`.

### `get_segment(df, cycle, marker_val)`
Dato un ciclo e un marker specifico (es. M2), estrae il DataFrame corrispondente alla sezione tra quel marker e il successivo. Se la durata è fuori dal range `valid_dur` (8–200 secondi) restituisce None — questo filtra M7 che nei dati esistenti è corrotto (contiene il tempo di attesa tra un partecipante e l'altro).

### `segment_psd(seg)`
Calcola la PSD con il metodo di Welch su ciascuno dei 16 canali EEG, poi ne fa la media. Restituisce le frequenze (1–40 Hz) e la potenza in dB. `nperseg = fs*2 = 250` campioni = finestre da 2 secondi, buon compromesso tra risoluzione in frequenza e varianza della stima.

### `load_participant_psds()`
Per ogni partecipante in `participants`, carica il file, trova il ciclo corretto, e per ogni marker da M1 a M6 estrae il segmento e calcola la PSD. Restituisce un dizionario `{marker: [(pid, f, psd_db), ...]}` che viene usato da tutte le funzioni di plotting.

### `_draw_bands(ax)` e `_welch_ax(ax, entries, title)`
Funzioni interne di plotting. `_draw_bands` aggiunge le linee verticali tratteggiate con le etichette delle bande EEG (δ θ α β γ). `_welch_ax` disegna le curve di tutti i partecipanti più la media in nero tratteggiato, poi chiama `_draw_bands`. Usate da tutte le funzioni export per non ripetere il codice.

### `export_welch_overlay(data, out_dir)`
Un file PNG per sezione: `Welch_M1.png`, `Welch_M2.png`, ..., `Welch_M6.png`. Ogni grafico mostra la PSD di tutti i partecipanti sovrapposta sulla stessa sezione.

### `export_welch_video(data, out_dir)`
Per ogni partecipante concatena i segmenti M4+M5+M6 in un unico DataFrame e calcola la PSD sull'intera durata del video. Salva `Welch_video.png`. Restituisce la lista di entries per usarla in `export_welch_all`.

### `export_welch_all(data, video_entries, out_dir)`
Una sola figura con tutti i pannelli affiancati: M1, M2, M3, M4, M5, M6 e Video. Utile per confrontare visivamente le sezioni a colpo d'occhio. Salva `Welch_all.png`.

---

## Funzioni importate da data_processing.py

- `csv2exps` — carica tutti i CSV in `data/` e li segmenta per esperimento. Usata per i grafici per-esperimento (non per i grafici overlay).
- `export_spettrogrammi_completi` — spettrogramma per ciascuno dei 16 canali, uno per esperimento.
- `export_spettrogramma_medio` — spettrogramma medio sui 16 canali, uno per esperimento.
- `export_welch_per_sezione` — Welch per sezione su un singolo esperimento, tutte le sezioni sullo stesso grafico.

---

## Output

Tutto va in `output/`. I file per-esperimento seguono la convenzione `Exp_XX_*.png`. I file overlay sono `Welch_M1.png` ... `Welch_M6.png`, `Welch_video.png`, `Welch_all.png`.

`output/` non è tracciato da git (troppo pesante), si rigenera lanciando lo script.
