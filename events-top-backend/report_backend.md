Ti lascio un report completo della situazione attuale e delle modifiche già introdotte, così puoi partire da lì senza perdere contesto.

SITUAZIONE ATTUALE

Il progetto è tornato stabile lato connessione e autenticazione base:

il database PostgreSQL funziona correttamente;
il backend Flask raggiunge il DB senza errori;
l’app Android riesce a parlare con il backend sia da telefono fisico sia da emulatore, grazie alla configurazione dell’URL backend;
la registrazione e il login funzionano;
la gestione OTP è stata sistemata per gli utenti non verificati;
sono stati aggiunti controlli base contro richieste duplicate, spam OTP e tentativi ripetuti.

MODIFICHE GIÀ APPORTATE

Database e configurazione backend
È stato mantenuto un solo file .env.
La configurazione corretta del backend è:

DB_HOST=localhost
DB_PORT=5432
DB_NAME=events_top_db
DB_USER=postgres
DB_PASSWORD=postgres
SECRET_KEY=project-work-secret-key-2024
FLASK_ENV=development

config.py legge questi valori con load_dotenv().
Il problema iniziale era una password PostgreSQL salvata male: riscrivendola manualmente e salvando il file, il backend ha ripreso a leggere gli eventi correttamente.
Verifica backend
Il backend Flask parte su 0.0.0.0.
La route corretta per testare gli eventi è /api/events/search.
Dal browser, la chiamata restituisce 200.
Quindi il backend è operativo e il problema non era più nel server, ma nella rete/configurazione Android.
Connessione Android
In AndroidManifest.xml è già presente:
android.permission.INTERNET
android:usesCleartextTraffic="true"
È stato creato UrlConfigFragment per cambiare l’URL backend direttamente dall’app.
Questo serve perché:
su telefono fisico si usa l’IP del PC in rete locale;
su emulatore si usa http://10.0.2.2:5000/.
In ApiClient la URL viene letta da SharedPreferences, e il client Retrofit viene ricreato quando si cambia URL.
Il problema di connessione sul telefono si è risolto anche dopo aver autorizzato Python / VSCode su rete privata nel firewall Windows e dopo il toggle Wi-Fi del telefono.
Auth / OTP
La registrazione ora gestisce correttamente:
email nuove;
email già registrate ma non verificate;
email già verificate;
username già esistenti.
Gli utenti non verificati possono ricevere un nuovo OTP invece di restare bloccati.
È stato aggiunto un cleanup degli utenti non verificati scaduti/vecchi.
Sono stati aggiunti controlli base su:
tentativi OTP;
resend OTP con cooldown;
tentativi login;
anti doppio click/duplicazione richiesta in registrazione.

FILE / AREE PRINCIPALI TOCCATE

.env
config.py
app.py
AndroidManifest.xml
network/ApiClient.java
fragments/main/UrlConfigFragment.java
repositories/auth_repository.py
services/auth_service.py

STATO LOGICO ATTUALE DI AUTH

Il file auth_service.py attualmente gestisce:

registrazione;
verifica OTP;
reinvio OTP;
login;
profilo utente;
ricerca utenti.

La registrazione ora:

crea un utente nuovo se l’email non esiste;
aggiorna e reinvia OTP se l’email esiste ma l’account non è verificato;
blocca se l’email è già verificata;
blocca se lo username è già in uso.

IDEA DEL PROSSIMO STEP

Il prossimo lavoro da fare può essere diviso in quattro blocchi.

OTP system più robusto
hash dell’OTP nel database;
scadenza gestita in modo più solido lato DB;
limitazione server-side del resend OTP;
eventuale pulizia automatica più elegante per account non verificati vecchi.
Android più robusto
debounce lato UI per evitare doppio click;
client API retry-safe;
protezione contro richieste duplicate;
idempotency key per le richieste più sensibili.
Funzionalità social, solo per utenti loggati
Serve implementare:
preferiti;
recensioni eventi;
visualizzazione delle proprie recensioni;
visualizzazione dei propri eventi preferiti.

Questa parte deve rispettare il requisito:

gli utenti autenticati possono lasciare recensioni sugli eventi;
le recensioni devono avere un punteggio da 0 a 5, con stelle o icone equivalenti;
i commenti devono essere persistenti e associati all’utente che li inserisce;
il sistema deve essere supportato da backend e autenticazione.
Notifiche evento
Serve implementare una funzione che permetta all’utente loggato di impostare un promemoria per un evento di interesse, valido in un intervallo tra il giorno corrente e il giorno dell’evento.

Questa parte deve rispettare il requisito:

interfaccia dedicata per impostare notifiche temporali sugli eventi;
la notifica deve aprire direttamente la scheda dell’evento quando selezionata.
Amicizie
Al momento le richieste di amicizia non funzionano:
non vengono inviate;
non vengono ricevute.

Questa funzionalità va sistemata a livello backend + frontend, probabilmente con:

tabella o relazione dedicata;
endpoint per invio/rifiuto/accettazione;
lista richieste ricevute;
lista amicizie confermate.

RICHIESTA OPERATIVA PER IL PROSSIMO STEP

Puoi prendere questo punto di partenza e implementare, nell’ordine:

social/favorites/reviews per utenti loggati;
notifiche evento;
amicizie;
rifinitura sicurezza OTP e anti-duplicati.

Obiettivo finale:

mantenere il progetto stabile;
non rompere il flusso già funzionante;
aggiungere funzionalità in modo incrementale e coerente con l’architettura attuale.