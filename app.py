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
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    session_id = db.Column(db.Integer, db.ForeignKey('training_session.id'))

# ---------------- DB initialisieren ----------------
with app.app_context():
    db.create_all()
    if not Setting.query.first():
        db.session.add(Setting())
        db.session.commit()

# ------------- Helper -------------
def get_settings():
    s = Setting.query.first()
    if not s:
        s = Setting()
        db.session.add(s)
        db.session.commit()
    return s

def next_invoice_number():
    s = get_settings()
    num = f"{s.invoice_prefix}{s.next_number:04d}"
    s.next_number += 1
    db.session.commit()
    return num

# ------------- Routes -------------
@app.route('/')
def index():
    customers = Customer.query.order_by(Customer.last_name).all()
    return render_template('index.html', customers=customers)

@app.route('/search')
def search():
    q = request.args.get('q', '')
    customers = []
    if q:
        like = f"%{q}%"
        customers = Customer.query.filter(
            (Customer.first_name.ilike(like)) |
            (Customer.last_name.ilike(like)) |
            (Customer.email.ilike(like)) |
            (Customer.phone.ilike(like))
        ).all()
    return render_template('search.html', q=q, customers=customers)

@app.route('/customers/new', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        c = Customer(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            notes=request.form.get('notes')
        )
        db.session.add(c)
        db.session.commit()
        flash('Kunde angelegt', 'success')
        return redirect(url_for('index'))
    return render_template('customers_new.html')

@app.route('/customers/<int:customer_id>')
def customer_detail(customer_id):
    c = Customer.query.get_or_404(customer_id)
    invoices = Invoice.query.filter_by(customer_id=c.id).order_by(Invoice.date.desc()).all()
    return render_template('customers_detail.html', c=c, invoices=invoices)

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def customer_edit(customer_id):
    c = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        for f in ['first_name', 'last_name', 'email', 'phone', 'address', 'notes']:
            setattr(c, f, request.form.get(f))
        db.session.commit()
        flash('Kunde aktualisiert', 'success')
        return redirect(url_for('customer_detail', customer_id=c.id))
    return render_template('customers_edit.html', c=c)

@app.route('/customers/<int:customer_id>/delete', methods=['POST'])
def customer_delete(customer_id):
    c = Customer.query.get_or_404(customer_id)
    db.session.delete(c)
    db.session.commit()
    flash('Kunde gelöscht', 'info')
    return redirect(url_for('index'))

@app.route('/customers/<int:customer_id>/dogs/new', methods=['GET', 'POST'])
def dog_new(customer_id):
    c = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        d = Dog(
            name=request.form['name'],
            breed=request.form.get('breed'),
            age_years=int(request.form.get('age_years') or 0) or None,
            notes=request.form.get('notes'),
            owner=c
        )
        db.session.add(d)
        db.session.commit()
        flash('Hund angelegt', 'success')
        return redirect(url_for('customer_detail', customer_id=c.id))
    return render_template('dogs_new.html', c=c)

@app.route('/dogs/<int:dog_id>/delete', methods=['POST'])
def dog_delete(dog_id):
    d = Dog.query.get_or_404(dog_id)
    cid = d.customer_id
    db.session.delete(d)
    db.session.commit()
    flash('Hund gelöscht', 'info')
    return redirect(url_for('customer_detail', customer_id=cid))

@app.route('/dogs/<int:dog_id>/sessions/new', methods=['GET', 'POST'])
def session_new(dog_id):
    d = Dog.query.get_or_404(dog_id)
    if request.method == 'POST':
        s = TrainingSession(
            date=datetime.fromisoformat(request.form['date']),
            location=request.form.get('location'),
            topic=request.form.get('topic'),
            duration_minutes=int(request.form.get('duration_minutes') or 0) or None,
            price_eur=float(request.form.get('price_eur') or 0) or None,
            status=request.form.get('status') or 'geplant',
            notes=request.form.get('notes'),
            dog=d
        )
        db.session.add(s)
        db.session.commit()
        flash('Trainingstermin angelegt', 'success')
        return redirect(url_for('customer_detail', customer_id=d.customer_id))
    return render_template('sessions_new.html', d=d)

@app.route('/sessions/<int:session_id>/done', methods=['POST'])
def session_done(session_id):
    s = TrainingSession.query.get_or_404(session_id)
    s.status = 'erledigt'
    db.session.commit()
    flash('Trainingstermin als erledigt markiert', 'success')
    return redirect(url_for('customer_detail', customer_id=s.dog.customer_id))

@app.route('/sessions/<int:session_id>/invoice', methods=['POST'])
def session_invoice(session_id):
    s = TrainingSession.query.get_or_404(session_id)
    cust = s.dog.owner
    inv = Invoice(
        number=next_invoice_number(),
        customer=cust,
        vat_rate=get_settings().default_vat,
        status='draft',
    )
    item = InvoiceItem(
        invoice=inv,
        description=f"Training: {s.topic or 'Hundetraining'} ({s.dog.name}) am {s.date.strftime('%d.%m.%Y %H:%M')}",
        quantity=1,
        unit_price=float(s.price_eur or 0.0),
        session_id=s.id
    )
    db.session.add(inv)
    db.session.add(item)

    total_net = item.quantity * item.unit_price
    total_vat = total_net * (inv.vat_rate / 100.0)
    inv.total_net = total_net
    inv.total_vat = total_vat
    inv.total_gross = total_net + total_vat

    db.session.commit()
    flash('Rechnung erstellt', 'success')
    return redirect(url_for('invoice_detail', invoice_id=inv.id))

@app.route('/availability')
def availability_index():
    slots = Availability.query.order_by(Availability.start.asc()).all()
    return render_template('availability_index.html', slots=slots)

@app.route('/availability/new', methods=['GET', 'POST'])
def availability_new():
    if request.method == 'POST':
        slot = Availability(
            start=datetime.fromisoformat(request.form['start']),
            duration_minutes=int(request.form.get('duration_minutes') or 60),
            location=request.form.get('location'),
            status='free'
        )
        db.session.add(slot)
        db.session.commit()
        flash('Slot angelegt', 'success')
        return redirect(url_for('availability_index'))
    return render_template('availability_new.html')

@app.route('/book')
def book_index():
    now = datetime.utcnow()
    slots = Availability.query.filter(
        Availability.status == 'free',
        Availability.start >= now
    ).order_by(Availability.start.asc()).all()
    return render_template('book_index.html', slots=slots)

@app.route('/book/<int:slot_id>', methods=['GET', 'POST'])
def book_slot(slot_id):
    slot = Availability.query.get_or_404(slot_id)
    if slot.status != 'free':
        flash('Slot nicht verfügbar', 'info')
        return redirect(url_for('book_index'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        phone = request.form.get('phone')
        dog_name = request.form['dog_name']
        topic = request.form.get('topic')

        c = Customer.query.filter_by(email=email).first() if email else None
        if not c:
            c = Customer(first_name=first_name, last_name=last_name, email=email, phone=phone)
            db.session.add(c)
            db.session.flush()

        d = Dog.query.filter_by(customer_id=c.id, name=dog_name).first()
        if not d:
            d = Dog(name=dog_name, owner=c)
            db.session.add(d)
            db.session.flush()

        s = TrainingSession(
            date=slot.start,
            location=slot.location,
            topic=topic or 'Einzeltraining',
            duration_minutes=slot.duration_minutes,
            price_eur=0.0,
            status='geplant',
            dog=d
        )
        slot.status = 'booked'
        db.session.add(s)
        db.session.commit()
        flash('Buchung bestätigt', 'success')
        return redirect(url_for('index'))

    return render_template('book_slot.html', slot=slot)

@app.route('/invoices/<int:invoice_id>')
def invoice_detail(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    return render_template('invoice_detail.html', inv=inv)

@app.route('/invoices/<int:invoice_id>/pdf')
def invoice_pdf(invoice_id):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except Exception as e:
        return f"ReportLab nicht verfügbar: {e}", 500

    inv = Invoice.query.get_or_404(invoice_id)
    tmp_pdf = "/tmp/invoice.pdf"
    c = canvas.Canvas(tmp_pdf, pagesize=A4)
    width, height = A4
    y = height - 30 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, f"Rechnung / Invoice {inv.number}")
    y -= 10 * mm

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Datum / Date: {inv.date.strftime('%d.%m.%Y')}")
    y -= 8 * mm

    c.drawString(20 * mm, y, f"Kunde / Customer: {inv.customer.first_name} {inv.customer.last_name}")
    y -= 6 * mm

    if inv.customer.address:
        c.drawString(20 * mm, y, inv.customer.address)
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Position")
    c.drawString(120 * mm, y, "Netto (€)")
    y -= 6 * mm

    c.setFont("Helvetica", 10)
    for item in inv.items:
        c.drawString(20 * mm, y, f"{item.description}")
        c.drawRightString(190 * mm, y, f"{item.quantity * item.unit_price:.2f}")
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(190 * mm, y, f"Zwischensumme: {inv.total_net:.2f} €")
    y -= 5 * mm
    c.drawRightString(190 * mm, y, f"USt ({inv.vat_rate:.2f}%): {inv.total_vat:.2f} €")
    y -= 5 * mm
    c.drawRightString(190 * mm, y, f"Gesamt: {inv.total_gross:.2f} €")

    c.showPage()
    c.save()

    with open(tmp_pdf, "rb") as f:
        pdf = f.read()

    resp = make_response(pdf)
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f'inline; filename="invoice_{inv.number}.pdf"'
    return resp

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    s = get_settings()
    if request.method == 'POST':
        s.invoice_prefix = request.form.get('invoice_prefix') or s.invoice_prefix
        s.next_number = int(request.form.get('next_number') or s.next_number)
        s.default_vat = float(request.form.get('default_vat') or s.default_vat)
        db.session.commit()
        flash('Einstellungen gespeichert', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', s=s)

@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        if not Setting.query.first():
            db.session.add(Setting())
            db.session.commit()
    print('DB initialisiert')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
``
