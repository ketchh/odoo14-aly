## DESCRIZIONE
Il pianificatore propone delle date di disponibilità del vettore per una specifica consegna. Una volta scelta la data viene assegnata a quel vettore.
## DOCUMENTAZIONE
Ogni vettore dovrà compilare una lista di capacità con data, provincia di partenza, provincia di arrivo e numero di consegne effettuabili.
Il contact center durante la chiamata al cliente aprirà un wizard in cui metterà una data di inizio (presumibilmente la data di preferenza del cliente) da cui l'algoritmo partirà per trovare disponibilità.
Verrano proposte alcune (2-3-4) date.
Il contact center chiederà al cliente quale di queste date preferisce, la seleziona e il sistema assegnerà al vettore (previo ulteriore controllo di disponibilità) la consegna che assumerà come data confermata quella appena scelta.

Potrebbe accadere che non ci sono disponibilità e bisgona aspettare la compilazione delle capacità da parte del vettore. A tal proposito si può segnare una nota nell'incarico con la data preferita dal cliente e riprovare nei giorni successivi inserendo questa preferenza.

Solo il contact center avrà la possibilità di richiedere la modifica di un appuntamento, tramite un button “rework”. Si potrà quindi vedere un ulteriore tab, non modificabile se non dal contact center ed in alcune fasi, dove poter inserire la causale di rework (censita in una tabella a parte) e delle note. 
Il tab conterrà una lista di rework in quanto la pratica potrebbe essere soggetta a più rework nell’ambito del suo workflow.
In tal caso la consegna viene tolta dall'attuale capacità vettore.
## DOCUMENTAZIONE TECNICA
Il vettore sarà un utente interno con un gruppo aggiuntivo nominato carrier.
Un carrier ha il flag compant_carrier a True.
Un carrier Manager non è necessariamente un carrier (non ha il flag company_carrier a True di default) 
- Carrier Planner: vede,modifica,cancella,crea le proprie capacità
- Carrier Manager Planner: vede,modifica,cancella,crea tutte le capacià.
Tendenzialmente un operatore call center deve essere un carrier manager.

# TODO: 

- usare holidays per fare i 5 giorni lavorativi successivi per suggested_date (quale data iniziale devo prendere per i 5 giorni? now)
- i 5 giorn iosno ocnfigurabili
- mettere un alert nel wizard per avvertire che stai cercando sotto i 5 giorni
