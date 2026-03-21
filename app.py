from flask import (
    Flask, render_template, request, redirect, url_for,
    make_response, g, abort, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from secrets import token_urlsafe
import smtplib, ssl
from email.message import EmailMessage

app = Flask(__name__)

# ---------------- Security / Config ----------------
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')

# DATABASE_URL (PostgreSQL) + Fallback SQLite
_db_url = os.getenv('DATABASE_URL', 'sqlite:///dogcrm.db')
if _db_url.startswith('postgres://'):  # normalize for SQLAlchemy
    _db_url = _db_url.replace('postgres://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# ---------------- i18n (DE/EN) ----------------
TRANSLATIONS = {
    'de': {
        # General
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online-Buchung',
        'save': 'Speichern',
        'cancel': 'Abbrechen',

        # Navigation
        'german': 'Deutsch',
        'english': 'Englisch',
        'settings': 'Einstellungen',
        'customers': 'Kunden',
        'dogs': 'Hunde',
        'sessions': 'Trainingseinheiten',
        'invoices': 'Rechnungen',
        'search': 'Suche',
        'availability': 'Verfügbarkeiten',
        'availabilities': 'Verfügbarkeiten',
        'online_booking': 'Online-Buchung',

        # Buttons
        'new_customer': 'Neuer Kunde',
        'new_dog': 'Neuer Hund',
        'new_session': 'Neue Einheit',
        'login': 'Anmelden',
        'logout': 'Abmelden',
        'username': 'Benutzername',
        'password': 'Passwort',

        # Settings page
        'settings_title': 'Einstellungen',
        'invoice_prefix': 'Rechnungs-Präfix',
        'next_number': 'Nächste Rechnungsnummer',
        'vat_rate': 'Mehrwertsteuer (%)',

        # Flash / Validation
        'saved': 'Gespeichert.',
        'invalid_csrf': 'Ungültiges Sicherheits‑Token (CSRF). Bitte Seite neu laden.',
        'invalid_prefix': 'Rechnungs‑Präfix ist erforderlich (max. 20 Zeichen).',
        'invalid_next': 'Nächste Rechnungsnummer muss eine Zahl ≥ 1 sein.',
        'invalid_vat': 'Mehrwertsteuer muss zwischen 0 und 100 liegen.',
        'bad_creds': 'Benutzername oder Passwort ist falsch.',

        # Booking emails
        'booking_confirmed_subject': 'Buchung bestätigt',
        'booking_confirmed_body': 'Hallo {name},\nIhre Buchung für {date} um {time} wurde bestätigt.\nViele Grüße'
    },
    'en': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online booking',
        'save': 'Save',
        'cancel': 'Cancel',

        'german': 'German',
        'english': 'English',
        'settings': 'Settings',
        'customers': 'Customers',
        'dogs': 'Dogs',
        'sessions': 'Sessions',
        'invoices': 'Invoices',
        'search': 'Search',
        'availability': 'Availability',
        'availabilities': 'Availabilities',
        'online_booking': 'Online booking',

        'new_customer': 'New customer',
        'new_dog': 'New dog',
        'new_session': 'New session',
        'login': 'Sign in',
        'logout': 'Sign out',
        'username': 'Username',
        'password': 'Password',

        'settings_title': 'Settings',
        'invoice_prefix': 'Invoice prefix',
        'next_number': 'Next invoice number',
        'vat_rate': 'VAT (%)',

        'saved': 'Saved.',
        'invalid_csrf': 'Invalid CSRF token. Please reload the page.',
        'invalid_prefix': 'Invoice prefix is required (max 20 chars).',
        'invalid_next': 'Next invoice number must be a number ≥ 1.',
        'invalid_vat': 'VAT must be between 0 and 100.',
        'bad_creds': 'Invalid username or password.',

        'booking_confirmed_subject': 'Booking confirmed',
        'booking_confirmed_body': 'Hello {name},\nYour booking for {date} at {time} is confirmed.\nBest regards'
    }
}

@app.context_processor
def inject_translator():
    def t(key):
        lang = getattr(g, 'lang', 'de')
        return TRANSLATIONS.get(lang, TRANSLATIONS['de']).get(key, key)
    return dict(t=t)

@app.before_request
def set_lang():
    g.lang = request.cookies.get('lang', 'de')

@app.route('/lang/<code>', endpoint='switch_lang')
def switch_lang(code):
    if code not in TRANSLATIONS:
        code = 'de'
    resp = make_response(redirect(request.referrer or url_for('index')))
    resp.set_cookie('lang', code, max_age=60*60*24*365)
    return resp

# ---------------- Models ----------------
class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    booked = db.Column(db.Boolean, default=False)
    customer_name = db.Column(db.String(120))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(50))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_prefix = db.Column(db.String(50), default="INV-")
    next_number = db.Column(db.Integer, default=1)
    vat_rate = db.Column(db.Float, default=20.0)

class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
