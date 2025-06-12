# HR Attendance Geolocation Map

## Descrizione

Questo modulo estende `hr_attendance_geolocation` aggiungendo la possibilità di visualizzare su una mappa interattiva i punti geografici di check-in e check-out delle presenze dei dipendenti.

## Caratteristiche

- **Bottone Mappa**: Aggiunge un bottone "Mostra Mappa" nella vista form dei record di presenza
- **Marker Differenziati**: 
  - **Rosso**: Punto di check-in (entrata)
  - **Blu**: Punto di check-out (uscita)
- **Mappa Interattiva**: Utilizza OpenStreetMap tramite Leaflet (gratuito, senza necessità di API key)
- **Popup Informativi**: Cliccando sui marker si visualizzano dettagli come dipendente, orario e coordinate
- **Legenda**: Legenda integrata per distinguere i tipi di marker
- **Responsive**: La mappa si adatta automaticamente per mostrare tutti i punti

## Installazione

1. Assicurarsi che il modulo `hr_attendance_geolocation` sia installato
2. Copiare questo modulo nella cartella addons di Odoo
3. Aggiornare la lista dei moduli
4. Installare il modulo `hr_attendance_geolocation_map`

## Utilizzo

1. Andare in **Risorse Umane > Presenze > Presenze**
2. Aprire un record di presenza che ha dati di geolocalizzazione
3. Cliccare sul bottone **"Mostra Mappa"** nell'header del form
4. La mappa si aprirà mostrando:
   - Marker rosso per il punto di check-in
   - Marker blu per il punto di check-out
   - Popup con informazioni dettagliate cliccando sui marker

## Dipendenze

- `hr_attendance_geolocation`: Per i dati di geolocalizzazione
- Connessione internet: Per caricare le tile di OpenStreetMap e la libreria Leaflet

## Note Tecniche

- Utilizza **Leaflet** per la visualizzazione delle mappe
- Le tile provengono da **OpenStreetMap** (gratuito)
- Il bottone è visibile solo se ci sono dati di geolocalizzazione nel record
- La mappa si centra automaticamente sui punti disponibili

## Supporto

Per segnalazioni di bug o richieste di funzionalità, contattare l'amministratore del sistema.

## Licenza

AGPL-3.0
