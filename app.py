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
        'english': 'Englisch'
    },
    'en': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online booking',
        'german': 'German',
        'english': 'English'
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

@app.route('/lang/<code>')
def switch_lang(code):
    # nur 'de' und 'en' erlauben
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

# Flask 3 kompatibel: Tabellen einmalig beim Import anlegen
with app.app_context():
    db.create_all()

# ---------------- Routes: Pages ----------------
@app.route("/")
def index():
    return render_template("index.html")

# Online-Buchung – Endpoint-Name so, wie base.html ihn verlinkt
@app.route("/online-buchung", endpoint="book_index")
def online_booking():
    slots = Slot.query.filter_by(booked=False).all()
    return render_template("book_index.html", slots=slots)

@app.route("/online-buchung/slot/<int:slot_id>")
def booking_slot(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot:
        abort(404)
    return render_template("book_slot.html", slot=slot)

@app.route("/online-buchung/slot/<int:slot_id>/buchen", methods=["POST"])
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

# Admin-Ansichten (Templates existieren in deinem Repo)
@app.route("/admin/availability")
def availability_index():
    return render_template("availability_index.html")

@app.route("/admin/availability/new")
def availability_new():
    return render_template("availability_new.html")

@app.route("/admin/customers/new")
def customers_new():
    return render_template("customers_new.html")

@app.route("/admin/customers/edit")
def customers_edit():
    return render_template("customers_edit.html")

@app.route("/admin/customers/detail")
def customers_detail():
    return render_template("customers_detail.html")

@app.route("/admin/dogs/new")
def dogs_new():
    return render_template("dogs_new.html")

@app.route("/admin/invoice/detail")
def invoice_detail():
    return render_template("invoice_detail.html")

@app.route("/admin/search")
def search():
    return render_template("search.html")

@app.route("/admin/sessions/new")
def sessions_new():
    return render_template("sessions_new.html")

@app.route("/admin/settings")
def settings():
    return render_template("settings.html")

# -------- Optional: Health + Seed (für Tests) --------
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
