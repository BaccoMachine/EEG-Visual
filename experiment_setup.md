# Experiment setup — note di sessione (2026-05-15)

Documentazione del workflow attuale per esperimenti EEG con Cyton+Daisy, sync server e marker injection nella GUI OpenBCI.

---

## Architettura

```
[browser experiment.html]  ──HTTP POST──▶  [sync_server.py Flask :9000]
                                                   │
                                                   ▼ UDP byte
                                       [OpenBCI GUI :5100 Marker Mode]
                                                   │
                                                   ▼
                                       [BrainFlow Streamer → CSV]
```

Tre processi sulla stessa macchina (o due con server e GUI su PC che acquisisce, browser su PC stimolatore — devono stare nella stessa rete locale).

---

## Componenti

### `sync_server.py`
Server Flask che traduce HTTP POST in pacchetti UDP verso la GUI OpenBCI.

- Riceve `POST /marker` con `{"value": N}`
- Invia un **singolo byte** (`chr(N)`) via UDP a `127.0.0.1:5100`
- `GET /ping` per test connessione (ritorna `{"ok": true}`)
- Endpoint CORS-aperti per uso da browser

**Importante:** la porta 5100 e il formato a singolo byte sono **vincolati dal listener interno della GUI OpenBCI** in Marker Mode. Non sono configurabili lato GUI in versioni standard.

### `web/experiment.html`
Pagina autonoma per gestire la presentazione degli stimoli e l'invio dei marker. Tutto modulare via interfaccia, nessun file di config esterno richiesto.

**Sezioni configurabili:**
- **Fase**: occhi chiusi / occhi aperti / croce fissazione / pausa nera / personalizzata (testo + colori liberi). Durata in secondi. Marker opzionale (label vuoto = no marker).
- **Video**: file locale via `<input type=file>`. Player con scrub. Bottone "+ marker @ tempo corrente" piazza marker al timestamp del player. Marker editabili in `mm:ss.mmm` o `ms`, ordinati automaticamente in ordine cronologico. Start/end value configurabili.

**Funzionalità:**
- Aggiungi/rimuovi/riordina sezioni a piacere (su / giù / elimina)
- Configurazione persiste in `localStorage` (eccetto il blob video, da ricaricare)
- Overlay fullscreen durante l'esecuzione con countdown
- ESC per annullare l'esperimento in corso
- Download log sessione (CSV con `label, value, unix_ms`) per backup/analisi indipendente

### `align.py`
Lo script di segmentazione esistente, non modificato in questa sessione. Cerca il marker `0` (video_start) nel `Marker Channel` del CSV BrainFlow come ancora di sincronizzazione e taglia segmenti basandosi su `markers.json`. Da rivedere per usare il nuovo flusso (vedi note finali).

---

## Setup operativo

### Lato OpenBCI GUI
1. Connetti Cyton+Daisy, avvia sessione
2. **Settings → Marker Mode**: abilita, imposta Receive Port = `5100`, IP = `127.0.0.1`
3. Aggiungi widget **BrainFlow Streamer** → modalità **File** → punta a `data/`
4. **Start Data Stream** + **Start Recording**

### Lato server (terminale)
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
python sync_server.py
```
Output atteso:
```
sync_server → OpenBCI GUI 127.0.0.1:5100
in ascolto su 0.0.0.0:9000
```

### Lato browser
1. Apri `web/experiment.html` (puoi caricarlo anche da `file://`)
2. Campo IP server: `http://127.0.0.1:9000` (stesso PC) o `http://<IP_LAN>:9000` (PC separato)
3. Configura sezioni e marker, START

---

## Diagnostica

**Test 1 — server raggiungibile:**
```bash
curl http://127.0.0.1:9000/ping
# → {"ok": true}
```

**Test 2 — UDP arriva alla GUI:**
```bash
curl -X POST http://127.0.0.1:9000/marker \
     -H "Content-Type: application/json" \
     -d '{"value":42}'
```
Verifica che nel Time Series widget appaia il marker. Poi in LibreOffice / pandas controlla colonna **AF (32)** = `Marker Channel`:
```bash
awk -F'\t' 'NR>4 && $32!=0 {print NR, $32}' file.csv
```

**Test 3 — UDP isolato (se OpenBCI non riceve):**
```bash
python3 -c "import socket;s=socket.socket(2,2);s.bind(('',5100));print(s.recvfrom(1024))"
```
(da lanciare con OpenBCI **chiuso**, libera la porta). Conferma se il problema è il sync_server o la GUI.

---

## Storia delle decisioni (da questa sessione)

1. **Versione iniziale**: sync_server inviava UDP su porta `12345` con payload stringa (`str(value).encode()`). La GUI non riceveva nulla nel Marker Channel.

2. **Investigazione**: con `python3 -c "...socket.recvfrom..."` confermato che il sync_server invia UDP correttamente. Il problema era lato GUI: il widget Networking standard **invia dati in uscita**, non riceve marker.

3. **Fix applicato**:
   - Porta cambiata a `5100` (listener interno hardcoded della GUI Marker Mode, da [docs ufficiali](https://docs.openbci.com/Software/OpenBCISoftware/GUIWidgets/))
   - Payload cambiato da stringa a **singolo byte** (`bytes([int(value) & 0xFF])`) come richiesto dal Marker Mode

4. **Refactoring experiment.html**: passato da formato statico (markers.json esterno + sequenza fissa baseline→video→baseline) a interfaccia completamente modulare con sezioni componibili a piacere.

---

## TODO futuri

- **Verificare end-to-end** con una registrazione di test che il marker arrivi davvero al CSV BrainFlow dopo il fix sulla porta 5100
- **Aggiornare `align.py`** per supportare il nuovo schema marker (1, 2, 3 = baseline pre; 0 = video_start; 7, 8 = baseline post; 99 = video_end) anziché lo schema M1-M7 dei dataset precedenti
- Valutare un fallback **timestamp-based alignment** usando `unix_ms` del log sessione + colonna `Timestamp` del CSV, utile se in futuro la GUI cambia comportamento sul Marker Mode
- Documentare in `README.md` il nuovo flusso (al momento la quick start non menziona sync_server / experiment.html)
