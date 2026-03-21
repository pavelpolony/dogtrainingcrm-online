from flask import Flask, render_template, request, redirect, url_for, make_response, g, abort
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# ---------------- i18n (minimal) ----------------
TRANSLATIONS = {
    'de': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online-Buchung',
        'german': 'Deutsch',
        'english': 'Englisch',
        'new_customer': 'Neuer Kunde'
    },
    'en': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online booking',
        'german': 'German',
        'english': 'English',
        'new_customer': 'New customer'
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
    # 1 Jahr gültig
    resp.set_cookie('lang', code, max_age=60 * 60 * 24 * 365)
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

# Tabellen einmalig beim Import anlegen (Flask 3 + Gunicorn kompatibel)
with app.app_context():
    db.create_all()

# ---------------- Pages ----------------
@app.route("/", endpoint="index")
def home_index():
    return render_template("index.html")

# ---------- ONLINE-BOOKING ----------
# Endpoint-Name so, wie in base.html verlinkt (book_index)
@app.route("/online-buchung", endpoint="book_index")
def online_booking():
    slots = Slot.query.filter_by(booked=False).all()
    return render_template("book_index.html", slots=slots)

# Slot-Ansicht – Endpoint 'book_slot'
@app.route("/online-buchung/slot/<int:slot_id>", endpoint="book_slot")
def booking_slot(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot:
        abort(404)
    return render_template("book_slot.html", slot=slot)

# Slot buchen – Endpoint 'book_submit'
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

# ---------- ADMIN (Templates existieren in deinem Repo) ----------
# Availability
@app.route("/admin/availability", endpoint="availability")
def availability_index():
    return render_template("availability_index.html")
# Alias für evtl. Template-Link 'availability_index'
app.add_url_rule("/admin/availability", endpoint="availability_index", view_func=availability_index)

@app.route("/admin/availability/new", endpoint="new_availability")
def availability_new():
    return render_template("availability_new.html")
# Alias für evtl. Template-Link 'availability_new'
app.add_url_rule("/admin/availability/new", endpoint="availability_new", view_func=availability_new)

# Customers
@app.route("/admin/customers/new", endpoint="new_customer")
def customers_new():
    return render_template("customers_new.html")
# Alias für evtl. Template-Link 'customers_new'
app.add_url_rule("/admin/customers/new", endpoint="customers_new", view_func=customers_new)

@app.route("/admin/customers/edit", endpoint="edit_customer")
def customers_edit():
    return render_template("customers_edit.html")
# Alias
app.add_url_rule("/admin/customers/edit", endpoint="customers_edit", view_func=customers_edit)

@app.route("/admin/customers/detail", endpoint="customer_detail")
def customers_detail():
    return render_template("customers_detail.html")
# Alias
app.add_url_rule("/admin/customers/detail", endpoint="customers_detail", view_func=customers_detail)

# Dogs
@app.route("/admin/dogs/new", endpoint="new_dog")
def dogs_new():
    return render_template("dogs_new.html")
# Alias
app.add_url_rule("/admin/dogs/new", endpoint="dogs_new", view_func=dogs_new)

# Invoice
@app.route("/admin/invoice/detail", endpoint="invoice")
def invoice_detail():
    return render_template("invoice_detail.html")
# Alias
app.add_url_rule("/admin/invoice/detail", endpoint="invoice_detail", view_func=invoice_detail)

# Search
@app.route("/admin/search", endpoint="admin_search")
def search():
    return render_template("search.html")
# Alias
app.add_url_rule("/admin/search", endpoint="search", view_func=search)

# Sessions
@app.route("/admin/sessions/new", endpoint="new_session")
def sessions_new():
    return render_template("sessions_new.html")
# Alias
app.add_url_rule("/admin/sessions/new", endpoint="sessions_new", view_func=sessions_new)

# Settings
@app.route("/admin/settings", endpoint="admin_settings")
def settings():
    return render_template("settings.html")
# Alias
app.add_url_rule("/admin/settings", endpoint="settings", view_func=settings)

# ---------- Optional: Health + Seed (für Tests) ----------
@app.route("/health")
def health():
    return "ok", 200

@app.route("/admin/seed")
def admin_seed():
    if Slot.query.count() == 0:
        db.session.add_all([
            Slot(date="2026-03-22", time="10:00"),
            Slot(date="2026-03-22", time="11:00"),
            Slot(date="2026-03-23", time="15:30"),
        ])
        db.session.commit()
        return "seeded 3 slots", 200
    return "already seeded", 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
