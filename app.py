from flask import Flask, render_template, request, redirect, url_for, make_response, g, abort
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ---------------- i18n (vollständig) ----------------
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
        'online_booking': 'Online-Buchung',

        # Buttons
        'new_customer': 'Neuer Kunde',
        'new_dog': 'Neuer Hund',
        'new_session': 'Neue Einheit',

        # Settings page
        'settings_title': 'Einstellungen',
        'invoice_prefix': 'Rechnungs-Präfix',
        'next_number': 'Nächste Rechnungsnummer',
        'vat_rate': 'Mehrwertsteuer (%)'
    },

    'en': {
        # General
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online booking',
        'save': 'Save',
        'cancel': 'Cancel',

        # Navigation
        'german': 'German',
        'english': 'English',
        'settings': 'Settings',
        'customers': 'Customers',
        'dogs': 'Dogs',
        'sessions': 'Sessions',
        'invoices': 'Invoices',
        'search': 'Search',
        'availability': 'Availability',
        'online_booking': 'Online booking',

        # Buttons
        'new_customer': 'New customer',
        'new_dog': 'New dog',
        'new_session': 'New session',

        # Settings page
        'settings_title': 'Settings',
        'invoice_prefix': 'Invoice prefix',
        'next_number': 'Next invoice number',
        'vat_rate': 'VAT (%)'
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

# ---------------- DB ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dogcrm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

with app.app_context():
    db.create_all()

# ---------------- Pages ----------------
@app.route("/", endpoint="index")
def home_index():
    return render_template("index.html")

# ---------- ONLINE BOOKING ----------
@app.route("/online-buchung", endpoint="book_index")
def online_booking():
    slots = Slot.query.filter_by(booked=False).all()
    return render_template("book_index.html", slots=slots)

@app.route("/online-buchung/slot/<int:slot_id>", endpoint="book_slot")
def booking_slot(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot:
        abort(404)
    return render_template("book_slot.html", slot=slot)

@app.route("/online-buchung/slot/<int:slot_id>/buchen", methods=["POST"], endpoint="book_submit")
def booking_submit(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot:
        abort(404)
    slot.customer_name = request.form.get("name")
    slot.customer_email = request.form.get("email")
    slot.customer_phone = request.form.get("phone")
    slot.booked = True
    db.session.commit()
    return "<h2>Buchung erfolgreich!</h2><p>Danke für Ihre Buchung.</p>"

# ---------- ADMIN ----------
@app.route("/admin/availability", endpoint="availability")
def availability_index():
    return render_template("availability_index.html")

@app.route("/admin/availability/new", endpoint="new_availability")
def availability_new():
    return render_template("availability_new.html")

@app.route("/admin/customers/new", endpoint="new_customer")
def customers_new():
    return render_template("customers_new.html")

@app.route("/admin/customers/edit", endpoint="edit_customer")
def customers_edit():
    return render_template("customers_edit.html")

@app.route("/admin/customers/detail", endpoint="customer_detail")
def customers_detail():
    return render_template("customers_detail.html")

@app.route("/admin/dogs/new", endpoint="new_dog")
def dogs_new():
    return render_template("dogs_new.html")

@app.route("/admin/invoice/detail", endpoint="invoice")
def invoice_detail():
    return render_template("invoice_detail.html")

@app.route("/admin/search", endpoint="admin_search")
def search():
    return render_template("search.html")

@app.route("/admin/sessions/new", endpoint="new_session")
def sessions_new():
    return render_template("sessions_new.html")

# ---------- SETTINGS PAGE ----------
@app.route("/admin/settings", endpoint="admin_settings")
def settings_page():
    s = Settings.query.first()
    if not s:
        s = Settings()
        db.session.add(s)
        db.session.commit()
    return render_template("settings.html", s=s)

# ---------- Health + Seed ----------
@app.route("/health")
def health():
    return "ok", 200

@app.route("/admin/seed")
def admin_seed():
    if Slot.query.count() == 0:
        db.session.add_all([
            Slot(date="2026-03-22", time="10:00"),
            Slot(date="2026-03-22", time="11:00"),
            Slot(date="2026-03-23", time="15:30")
        ])
        db.session.commit()
        return "seeded"
    return "already seeded"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
