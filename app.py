from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Translation shim so {{ t('...') }} in templates works ---
@app.context_processor
def inject_translator():
    def t(key):
        return key  # simple pass-through; replace with real i18n later
    return dict(t=t)

# DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dogcrm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple Slot model (extend as you like)
class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    booked = db.Column(db.Boolean, default=False)
    customer_name = db.Column(db.String(120))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(50))

# Ensure tables exist also under Gunicorn/Render (Flask 3 safe)
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

# ---------- ONLINE-BOOKING (for your book_* templates) ----------
@app.route("/online-buchung")
def online_booking():
    # Start page for booking (book_index.html)
    return render_template("book_index.html")

@app.route("/online-buchung/slot/<int:slot_id>")
def booking_slot(slot_id):
    slot = Slot.query.get(slot_id)
    return render_template("book_slot.html", slot=slot)

@app.route("/online-buchung/slot/<int:slot_id>/buchen", methods=["POST"])
def booking_submit(slot_id):
    slot = Slot.query.get(slot_id)
    if not slot:
        return "<h2>Slot nicht gefunden.</h2>", 404
    slot.customer_name = request.form.get("name")
    slot.customer_email = request.form.get("email")
    slot.customer_phone = request.form.get("phone")
    slot.booked = True
    db.session.commit()
    return "<h2>Buchung erfolgreich!</h2><p>Danke für Ihre Buchung.</p>"

# ---------- ADMIN ----------
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

if __name__ == "__main__":
    # local dev: keep it here as well
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
