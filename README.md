# Progetto di tesi
Questo repository contiene il codice sorgente del progetto di tesi.


## Installazione

Il progetto è stato sviluppato in ambiente Linux (Rocky Linux 9.4) con Python versione 3.9.18

Per installare il progetto, in una cartella dedicata, copiare tutti i file del repository ed eseguire i seguenti comandi da un terminale, posizionato nella cartella:

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0 'app:app'
```

Spiegazione comandi:
* Creazione di un ambiente virtuale dedicato al progetto nella cartella, chiamato venv
* Attivazione dell'ambiente
* Installazione dei requisiti del progetto (Flask, Flask-SQLAlchemy e Gunicorn)
* Avvio del server web Gunicorn



### Ricreazione database

Per ricreare il database procedere nel seguente modo:
* Eliminare/rinominare il database corrente, se presente
* Accedere tramite linea di comando alla cartella dove è presente l'ambiente/applicazione
* Attivare l'ambiente con ``` source venv/bin/activate ```
* Eseguire i seguenti comandi:
  
  ```bash
  flask shell
  db.create_all()
  ```


## Ambiente di prova

È stato predisposto un ambiente già pronto all'uso all'indirizzo: https://l31-pw.onrender.com/

NB: La pagina potrebbe impiegare fino a 1 minuto, prima di aprirsi per la prima volta. Questo è dovuto ai limiti della piattaforma utilizzata per ospitare l'applicazione (Render).
