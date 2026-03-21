from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Datenbank (lokal oder Render Postgres – später konfigurierbar)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dogcrm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Beispielmodell für Termine (du kannst anpassen)
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/online-buchung")
def booking_form():
    return render_template("booking.html")

@app.route("/online-buchung/senden", methods=["POST"])
def booking_submit():
    new_entry = Booking(
        name=request.form.get("name"),
        email=request.form.get("email"),
        phone=request.form.get("phone"),
        date=request.form.get("date"),
        time=request.form.get("time")
    )
    db.session.add(new_entry)
    db.session.commit()
    return render_template("thankyou.html")

@app.route("/admin/bookings")
def admin_list():
    bookings = Booking.query.all()
    return render_template("admin_bookings.html", bookings=bookings)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=False)