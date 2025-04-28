## Funzionalità

+ Impostazioni -> Netcheck 2: 
    + **Consenti relazione tra checklist e modelli** abilita la possibilità di associare ad una checklist un record di un qualsiasi modello.
    + **Vai ai modelli** è un link che porta alla lista dei modelli.
    + Selezionando **Accesso Checklist** dentro al form di un modello abilitiamo quel modello ad essere collegato ad una checklist. Si crea anche un'azione nuova "**Vai alle checklist/Go to Checklist**" visibile nel menu *Azioni* dentro al form del modello con Accesso Checklist a True. Tale azione ti manda alla lista delle checklist associate a questo oggetto.
+ Crea Checklist:
    + Inserire i campi richiesti (se abilitato *Consenti relazione tra checklist e modelli* si vedrà anche il campo Oggetto associato che rappresenta la relazione verso un record specifico).
    + Le righe vengono impostate inline, alcuni tipi di riga (testo / selezione) hanno qualche opzione selezionabile e configurabile in più, scegliendo questi tipi si visualizza un bottone **Modifica opzioni** che apre la riga in un form modale.
    + Tutti i tipi hanno come opzione **Obbligatorio** che implica l'obbligatorietà a compilare quella registrazione.
    + Testo presenta le opzione **Minimo/Massimo numero caratteri**, selezionandola e aprendo il modale si possono scegliere il numero minimo e massimo di carattere per quella riga.
    + Selezione presenta le opzioni:
        + **Selezione su chiave-valore** che indica che si dovranno creare delle opzioni di scelta nel form.
        + **Selezione su modello** che indica che si dovrà scegliere un modello ed un dominio. Il risultato di questo dominio saranno le possibili selezioni che dvrà fare l'utente.
    + **Campi precompilati**: sono righe in cui si può scegliere un qualsiasi record in odoo e il campo di questo oggetto da mostrare. Nella checklist si tramuta in un rigo di sola lettura con questo valore. Scegliere modello e oggetto nel campo *Oggetto precompilato* poi selezionare il campo da cui prendere i dati in *Campo Precompilato*. Si vedrà la preview risultante nel campo *Anteprima Campo Precompilato*.
+ Modelli:
    + Ogni checklist può diventare un modello da riutilizzare semplicemente flaggando il campo **Modello?**.
    + Per creare una checklist da un modello si va nel modello scegliendolo dalla lista raggiungibile tramite menu *Modelli*. Una volta dentro la checklist/modello cliccare sul bottone in alto a destra **Crea**. Verrà creata la checklist dal modello. **ATTENZIONE**: alcuni campi non verranno copiati (e.g. Oggetto associato e se il rigo è un precompilato tutta la parte di oggetto e valore.)
+ Registrazioni:
    + una checklist draft non può avere registrazioni ma può essere cancellata
    + una checklist ready può avere registrazioni non può essere cancellato può essere annullato e le registrazioni vanno in active=False. Può tornare in draft.
    + una checklist done non può essere cancellata, non può avere nuove registrazioni
    + una checklist cancel no registrazioni  