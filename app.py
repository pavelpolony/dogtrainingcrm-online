from flask import Flask, render_template, request, redirect, url_for, flash, make_response, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ---------------- DB: Render-tauglich (Postgres via DATABASE_URL) ----------------
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "dog_training_crm_pro.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

db = SQLAlchemy(app)

# ---------------- Dummy current_user für alte Templates ----------------
class GuestUser:
    is_authenticated = False

@app.context_processor
def inject_guest_user():
    return {'current_user': GuestUser()}

# ---------------- i18n ----------------
TRANSLATIONS = {
    'de': {
        'app_title': 'Dog Training CRM',
        'customers': 'Kunden',
        'new_customer': '+ Neuer Kunde',
        'name': 'Name',
        'contact': 'Kontakt',
        'dogs': 'Hunde',
        'details': 'Details',
        'search': 'Suche',
        'search_ph': 'Suchen…',
        'first_name': 'Vorname',
        'last_name': 'Nachname',
        'email': 'E-Mail',
        'phone': 'Telefon',
        'address': 'Adresse',
        'notes': 'Notizen',
        'save': 'Speichern',
        'edit': 'Bearbeiten',
        'delete': 'Löschen',
        'confirm_delete': 'Wirklich löschen?',
        'add_dog': '+ Hund hinzufügen',
        'breed': 'Rasse',
        'age_years': 'Alter (Jahre)',
        'sessions': 'Trainingstermine',
        'add_session': '+ Termin',
        'date_time': 'Datum & Zeit',
        'location': 'Ort',
        'topic': 'Thema',
        'duration': 'Dauer (Minuten)',
        'price': 'Preis (€)',
        'status': 'Status',
        'planned': 'geplant',
        'done': 'erledigt',
        'cancelled': 'storniert',
        'mark_done': 'Erledigt',
        'invoice': 'Rechnung',
        'create_invoice': 'Rechnung erstellen',
        'invoices': 'Rechnungen',
        'public_booking': 'Online-Buchung',
        'availabilities': 'Verfügbare Slots',
        'add_availability': '+ Slot anlegen',
        'book': 'Buchen',
        'book_this_slot': 'Diesen Termin buchen',
        'customer_name': 'Kund:innen-Name',
        'dog_name': 'Hunde-Name',
        'confirm': 'Bestätigen',
        'language': 'Sprache',
        'german': 'Deutsch',
        'english': 'Englisch',
        'settings': 'Einstellungen',
        'vat_rate': 'Umsatzsteuer (%)',
        'invoice_prefix': 'Rechnungs-Präfix',
        'next_number': 'Nächste Nummer',
        'download_pdf': 'PDF herunterladen',
        'login': 'Login',
        'logout': 'Logout',
    },
    'en': {
        'app_title': 'Dog Training CRM',
        'customers': 'Customers',
        'new_customer': '+ New customer',
        'name': 'Name',
        'contact': 'Contact',
        'dogs': 'Dogs',
        'details': 'Details',
        'search': 'Search',
        'search_ph': 'Search…',
        'first_name': 'First name',
        'last_name': 'Last name',
        'email': 'Email',
        'phone': 'Phone',
        'address': 'Address',
        'notes': 'Notes',
        'save': 'Save',
        'edit': 'Edit',
        'delete': 'Delete',
        'confirm_delete': 'Really delete?',
        'add_dog': '+ Add dog',
        'breed': 'Breed',
        'age_years': 'Age (years)',
        'sessions': 'Training sessions',
        'add_session': '+ Session',
        'date_time': 'Date & Time',
        'location': 'Location',
        'topic': 'Topic',
        'duration': 'Duration (minutes)',
        'price': 'Price (€)',
        'status': 'Status',
        'planned': 'planned',
        'done': 'done',
        'cancelled': 'cancelled',
        'mark_done': 'Mark done',
        'invoice': 'Invoice',
        'create_invoice': 'Create invoice',
        'invoices': 'Invoices',
        'public_booking': 'Online booking',
        'availabilities': 'Available slots',
        'add_availability': '+ Add slot',
        'book': 'Book',
        'book_this_slot': 'Book this slot',
        'customer_name': 'Customer name',
        'dog_name': 'Dog name',
        'confirm': 'Confirm',
        'language': 'Language',
        'german': 'German',
        'english': 'English',
        'settings': 'Settings',
        'vat_rate': 'VAT rate (%)',
        'invoice_prefix': 'Invoice prefix',
        'next_number': 'Next number',
        'download_pdf': 'Download PDF',
        'login': 'Login',
        'logout': 'Logout',
    }
}

def t(key):
    lang = getattr(g, 'lang', 'de')
    return TRANSLATIONS.get(lang, TRANSLATIONS['de']).get(key, key)

@app.context_processor
def inject_t():
    return {'t': t}

@app.before_request
def set_lang():
    g.lang = request.cookies.get('lang', 'de')

@app.route('/lang/<code>')
def switch_lang(code):
    if code not in TRANSLATIONS:
        code = 'de'
    resp = make_response(redirect(request.referrer or url_for('index')))
    resp.set_cookie('lang', code, max_age=60*60*24*365)
    return resp

# ---------------- Dummy Admin-Routen für altes base.html ----------------
@app.route('/admin/login', endpoint='admin_login')
def admin_login():
    flash('Diese vereinfachte Version hat keinen Admin-Login.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/logout', endpoint='admin_logout')
def admin_logout():
    return redirect(url_for('index'))

# ---------------- Models ----------------
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_prefix = db.Column(db.String(50), default='2026-')
    next_number = db.Column(db.Integer, default=1)
    default_vat = db.Column(db.Float, default=19.0)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    notes = db.Column(db.Text)
    dogs = db.relationship('Dog', backref='owner', cascade='all, delete-orphan')

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    breed = db.Column(db.String(120))
    age_years = db.Column(db.Integer)
    notes = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    sessions = db.relationship('TrainingSession', backref='dog', cascade='all, delete-orphan')

class TrainingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(255))
    topic = db.Column(db.String(255))
    duration_minutes = db.Column(db.Integer)
    price_eur = db.Column(db.Float)
    status = db.Column(db.String(50), default='geplant')
    notes = db.Column(db.Text)
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'), nullable=False)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    location = db.Column(db.String(255))
    status = db.Column(db.String(30), default='free')  # free, booked

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer')
    vat_rate = db.Column(db.Float, default=19.0)
    status = db.Column(db.String(30), default='draft')
    total_net = db.Column(db.Float, default=0.0)
    total_vat = db.Column(db.Float, default=0.0)
    total_gross = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
