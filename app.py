import string
import random
from datetime import datetime, timedelta
from os import path
from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# Crea una nuova applicazione Flask
app = Flask(__name__)

# Imposta il percorso del DB SQLite
db_path = path.join(path.dirname(__file__), 'schedules.db')

# Configura Flask con SQLAlchemy d usare il database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

# Collega SQLAlchemy all'applicazione per l'suo del DB
db = SQLAlchemy(app)

# Classe di definizione della tabella "Schedules" per gli appuntamenti
class Schedules(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule = db.Column(db.DateTime, nullable=False)
    scode = db.Column(db.String(10), nullable=False, unique=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    fiscal_code = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Funzione per strutturare i dati della tabella per essere trasformati in JSON
    def to_dict(self):
        return {
            "schedule": self.schedule.strftime('%d/%m/%Y %H:%M'),
            "scode": self.scode,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "fiscalcode": self.fiscal_code,
            "email": self.email,
            "phone": self.phone,
            "notes": self.notes,
        }

# Classe di definizione della tabella "SchedulesDates" per le date disponibili per gli appuntamenti
class SchedulesDates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule = db.Column(db.DateTime, nullable=False, unique=True)
    used = db.Column(db.Integer, nullable=False, default=0)


# Home page del sito
@app.route('/')
def index():
    # Imposta i parametri per recuperare le date da mostrare (limita il numero di dati)
    today = datetime.now()
    max_range_date = today + timedelta(days=7)  # Con days=7, recupera le date dei prossimi 7 giorni

    # Esegue la query per recuperare le date dei prossimi N giorni
    schedules = db.session.query(
        SchedulesDates.id,
        func.strftime('%d/%m/%Y %H:%M', SchedulesDates.schedule).label('schedule')
    ).filter(
        SchedulesDates.schedule >= today,
        SchedulesDates.schedule <= max_range_date,
        SchedulesDates.used == 0
    ).order_by(SchedulesDates.schedule).all()

    # Mostra pagina dal template index.html
    return render_template('index.html', schedules=schedules)


# Inserimento nuovo appuntamento
@app.route('/insertSchedule', methods=['POST'])
def schedule_insert():
    # Definisce i parametri obbligatori (tutti)
    mandatory_params = ['schedule', 'firstname', 'lastname', 'fiscalcode', 'email', 'phone', 'notes']

    # Controlla che i parametri siano tutti presenti e non vuoti
    for param in mandatory_params:
        if param not in request.form or not request.form[param].strip():    # stringa vuota = false
            # Risponde con la stringa JSON di errore
            return jsonify(
                status = 999,
                error = "Parametro mancante o vuoto: " + param,
                data = ""
            )

    # Recupera dal DB data e ora dell'appuntamento in base all'ID
    schedule_date = SchedulesDates.query.filter_by(id=request.form['schedule'], used=0).first_or_404()

    # Verifica se l'appuntamento risulta ancora presente, altrimenti risponde con errore
    if schedule_date is None:
        return jsonify(
            status = 999,
            error = "Parametro non valido: Data Appuntamento",
            data = ""
        )

    # Recupera tutti i caratteri validi utilizzabili per generare un codice prenotazione
    characters = string.ascii_uppercase + string.digits

    # Genera un codice (stringa) di 10 caratteri casuali
    generated_code = ""
    for _ in range(10):
        generated_code += random.choice(characters)

    # Crea il record con i dati dell'appuntamento
    new_schedule = Schedules(
        schedule=schedule_date.schedule,
        scode=generated_code,
        firstname=request.form['firstname'],
        lastname=request.form['lastname'],
        fiscal_code=request.form['fiscalcode'],
        email=request.form['email'],
        phone=request.form['phone'],
        notes=request.form['notes']
    )

    try:
        # Aggiorna la data come usata (non più disponibile)
        schedule_date.used = 1

        # Inserisce nel DB il nuovo appuntamento
        db.session.add(new_schedule)

        # Committa le modifiche
        db.session.commit()

        # Ritorna la string JSON che ne conferma la modifica
        return jsonify(
            status = 1,
            error = "",
            data = generated_code
        )
    except Exception as e:
        # Annulla le modifiche a causa di un errore
        db.session.rollback()

        # Ritorna la string JSON con l'errore e il dettaglio dell'errore in "data"
        return jsonify(
            status = 999,
            error = "Non è stato possibile registrare la richiesta a causa di un errore!",
            data = e
        )


# Modifica appuntamento
@app.route('/editSchedule', methods=['POST', 'GET'])
def schedule_edit():
    # Controlla il metodo di chiamata. Se "GET", mostro la pagina
    if request.method == 'GET':
        # La pagina viene composta usando il file edit.html
        return render_template('edit.html')

    else:   # Altrimenti (POST) esegue l'aggiornamento

        # Definisce i parametri obbligatori (tutti quelli modificabili)
        mandatory_params = ['firstname', 'lastname', 'email', 'phone', 'notes']

        # Controlla che i parametri siano tutti presenti e non vuoti
        for param in mandatory_params:
            if param not in request.form or not request.form[param].strip():  # Stringa vuota = false
                # Risponde con la stringa JSON di errore
                return jsonify(
                    status = 999,
                    error = "Parametro mancante o vuoto: " + param,
                    data = ""
                )

        # Recupera dal DB l'appuntamento sulla base dei dati minimi necessari (scode e fiscal_code)
        schedule = Schedules.query.filter_by(
            scode=request.form.get('scode'),
            fiscal_code=request.form.get('fiscalcode')
        ).first_or_404()

        # Aggiorna i dati con quelli inviati dalla pagina
        schedule.firstname = request.form.get('firstname')
        schedule.lastname = request.form.get('lastname')
        schedule.email = request.form.get('email')
        schedule.phone = request.form.get('phone')
        schedule.notes = request.form.get('notes')

        try:
            # Committa la modifica
            db.session.commit()

            # Ritorna la string JSON che ne conferma la modifica
            return jsonify(
                status = 1,
                error = "",
                data = True
            )
        except Exception as e:
            # Annulla le modifiche a causa di un errore
            db.session.rollback()

            # Ritorna la string JSON con l'errore e il dettaglio dell'errore in "data"
            return jsonify(
                status = 999,
                error = "È avvenuto un errore durante l'aggiornamento dei dati",
                data = e
            )


# Ricerca appuntamento
@app.route('/searchSchedule/<scode>/<fiscalcode>', methods=['GET'])
def schedule_search(scode, fiscalcode):
    # Recupera i dati della prenotazione dal DB in base a scode e fiscal_code
    schedule = Schedules.query.filter_by(scode=scode, fiscal_code=fiscalcode).first_or_404()

    # Ritorna la string JSON che ne conferma l'eliminazione
    return jsonify(
        status = 1,
        error = "",
        data = schedule.to_dict()
    )


# Eliminazione appuntamento
@app.route('/deleteSchedule/<scode>/<fiscalcode>', methods=['GET'])
def deleteSchedule(scode, fiscalcode):
    # Recupera dal DB il record in base a scode e fiscal_code
    schedule = Schedules.query.filter_by(
        scode=scode,
        fiscal_code=fiscalcode
    ).first_or_404()

    # Recupera dal DB data e ora dell'appuntamento in base a data e ora
    schedule_date = SchedulesDates.query.filter_by(
        schedule=schedule.schedule
    ).first_or_404()

    try:
        # Rimette come disponibile l'appuntamento
        schedule_date.used = 0

        # Elimina l'appuntamento
        db.session.delete(schedule)

        # Committa le modifiche
        db.session.commit()

        # Ritorna la string JSON che ne conferma l'eliminazione
        return jsonify(
            status = 1,
            error = "",
            data = True
        )
    except Exception as e:

        # Ritorna la string JSON con l'errore e il dettaglio dell'errore in "data"
        return jsonify(
            status = 999,
            error = "È avvenuto un errore durante l'eliminazione della prenotazione",
            data = e
        )


# Gestione appuntamenti
@app.route('/management', methods=['GET', 'POST'])
def generate_dates():
    # Controlla il metodo di chiamata. Se "GET", mostra la pagina
    if request.method == 'GET':
        # Recupera la data dell'ultimo slot inserita
        last_date = db.session.query(
            func.strftime('%d/%m/%Y %H:%M', func.max(SchedulesDates.schedule))
        ).scalar()

        # Recupera l'elenco di tutti gli appuntamenti presenti da oggi in poi
        schedules = db.session.query(
            Schedules.lastname,
            Schedules.firstname,
            Schedules.fiscal_code,
            Schedules.scode,
            func.strftime('%d/%m/%Y %H:%M', Schedules.schedule).label('schedule')
        ).filter(
            Schedules.schedule >= datetime.now()
        ).order_by(Schedules.schedule).all()

        # La pagina viene composta usando il file management.html
        return render_template('management.html', last_date=last_date, schedules=schedules)

    else:   # Altrimenti (POST) esegue l'inserimento
        # Controlla che il parametro "days" sia presente e non vuoto
        if "days" not in request.form or not request.form["days"].strip():  # Stringa vuota = false
            # Risponde con la stringa JSON di errore
            return jsonify(
                status = 999,
                error = "Parametro mancante o vuoto: Days",
                data = ""
            )

        # Recupera dal DB l'ultima data presente
        start_date = db.session.query(func.max(SchedulesDates.schedule)).scalar()

        # In caso non vi siano date presenti nel DB, imposta oggi come start_date
        if start_date is None:
            start_date = datetime.now()

        # Definizione degli slot orari (dalle 10:00 alle 16:00 con intervallo di 1 ora)
        start_hour = 10     # Ora di inizio
        end_hour = 16       # Ora di fine (inclusa)
        time_step = timedelta(hours=1)  # Intervallo degli slot (1 ora)

        # Inizializza l'elenco delle schedulazioni
        schedules = []

        # Iterazione per per i successivi 7 giorni
        for i in range(int(request.form["days"])):
            # Aggiunge di volta in volta un giorno (valore di 'i') partendo dal giorno successivo di start_date
            current_day = start_date + timedelta(days=(i+1))

            # Verifica che i giorni sono solo da Lunedì(=0) a Venerdì (=4)
            if current_day.weekday() < 5:
                # Creazione degli slot orari di ogni ora (limitati da start_hour e end_hour)
                time = datetime(current_day.year, current_day.month, current_day.day, start_hour, 0)

                # Iterazione di tutti gli slot orari
                while time.hour <= end_hour:
                    # Aggiungo data e ora all'elenco
                    schedules.append(time)

                    # Incrementa (in base al valore di time_step) per l'iterazione successiva
                    time += time_step

        # Crea l'array degli slot da aggiungere in tabella
        schedule_entries = [SchedulesDates(schedule=sch) for sch in schedules]

        try:
            # Inserisce massivamente gli slot
            db.session.add_all(schedule_entries)

            # Committa le modifiche
            db.session.commit()

            # Ritorna la string JSON che ne conferma l'eliminazione
            return jsonify(
                status = 1,
                error = "",
                data = True
            )
        except Exception as e:
            # Ritorna la string JSON con l'errore e il dettaglio dell'errore in "data"
            return jsonify(
                status = 999,
                error = "È avvenuto un errore durante l'inserimento degli slot di prenotazione",
                data = e
            )


# Avvia l'applicazione con debug attivo
if __name__ == "__main__":
    app.run(debug=True)
