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
import os
from secrets import token_urlsafe

app = Flask(__name__)

# ---------------- Security / Config ----------------
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dogcrm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'  # wohin redirecten, wenn nicht eingeloggt

# ---------------- i18n (vollständig) ----------------
TRANSLATIONS = {
    'de': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online-Buchung',
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
        'new_customer': 'Neuer Kunde',
        'new_dog': 'Neuer Hund',
        'new_session': 'Neue Einheit',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
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
        'login_title': 'Admin‑Login',
        'username': 'Benutzername',
        'password': 'Passwort',
        'login': 'Anmelden',
        'bad_creds': 'Benutzername oder Passwort ist falsch.'
    },
    'en': {
        'app_title': 'Dog Training CRM',
        'public_booking': 'Online booking',
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
        'save': 'Save',
        'cancel': 'Cancel',
        'settings_title': 'Settings',
        'invoice_prefix': 'Invoice prefix',
        'next_number': 'Next invoice number',
        'vat_rate': 'VAT (%)',
        # Flash / Validation
        'saved': 'Saved.',
        'invalid_csrf': 'Invalid CSRF token. Please reload the page.',
        'invalid_prefix': 'Invoice prefix is required (max 20 chars).',
        'invalid_next': 'Next invoice number must be a number ≥ 1.',
        'invalid_vat': 'VAT must be between 0 and 100.',
        'login_title': 'Admin Login',
        'username': 'Username',
        'password': 'Password',
        'login': 'Sign in',
        'bad_creds': 'Invalid username or password.'
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
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# -------- Admin bootstrap route (one‑time initializer) --------
# Erstellt einen Admin mit ENV‑Variablen ADMIN_USERNAME / ADMIN_PASSWORD.
# Danach die Route wieder entfernen oder INIT_TOKEN setzen.
@app.route('/admin/init-admin')
def init_admin():
    token = os.getenv('INIT_TOKEN')  # optionaler Schutz
    if token and request.args.get('token') != token:
        return "Forbidden", 403
    u = os.getenv('ADMIN_USERNAME', 'admin')
    p = os.getenv('ADMIN_PASSWORD', 'admin123!')
    if AdminUser.query.filter_by(username=u).first():
        return "admin exists", 200
    user = AdminUser(username=u)
    user.set_password(p)
    db.session.add(user)
    db.session.commit()
    return f"admin created: {u}", 201

# ---------------- Helper: CSRF ----------------
def ensure_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = token_urlsafe(32)
    return session['csrf_token']

def verify_csrf(form_token: str) -> bool:
    return form_token and session.get('csrf_token') and form_token == session['csrf_token']

# ---------------- Pages (public) ----------------
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
    slot.customer_name = request.form.get("name", "").strip()
    slot.customer_email = request.form.get("email", "").strip()
    slot.customer_phone = request.form.get("phone", "").strip()
    slot.booked = True
    db.session.commit()
    return "<h2>Buchung erfolgreich!</h2><p>Danke für Ihre Buchung.</p>"

# ---------------- Admin: Auth ----------------
@app.route('/admin/login', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login():
    ensure_csrf_token()
    if request.method == 'POST':
        if not verify_csrf(request.form.get('csrf_token')):
            flash(TRANSLATIONS[g.lang]['invalid_csrf'], 'error')
            return redirect(url_for('admin_login'))

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        flash(TRANSLATIONS[g.lang]['bad_creds'], 'error')
        return redirect(url_for('admin_login'))

    return render_template('login.html', csrf_token=session.get('csrf_token'))

@app.route('/admin/logout', endpoint='admin_logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

# ---------------- Admin: Views (geschützt) ----------------
# Availability
@app.route("/admin/availability", endpoint="availability")
@login_required
def availability_index():
    return render_template("availability_index.html")
app.add_url_rule("/admin/availability",
                 endpoint="availability_index",
                 view_func=availability_index)

@app.route("/admin/availability/new", endpoint="new_availability")
@login_required
def availability_new():
    return render_template("availability_new.html")
app.add_url_rule("/admin/availability/new",
                 endpoint="availability_new",
                 view_func=availability_new)

# Customers
@app.route("/admin/customers/new", endpoint="new_customer")
@login_required
def customers_new():
    return render_template("customers_new.html")
app.add_url_rule("/admin/customers/new",
                 endpoint="customers_new",
                 view_func=customers_new)

@app.route("/admin/customers/edit", endpoint="edit_customer")
@login_required
def customers_edit():
    return render_template("customers_edit.html")
app.add_url_rule("/admin/customers/edit",
                 endpoint="customers_edit",
                 view_func=customers_edit)

@app.route("/admin/customers/detail", endpoint="customer_detail")
@login_required
def customers_detail():
    return render_template("customers_detail.html")
app.add_url_rule("/admin/customers/detail",
                 endpoint="customers_detail",
                 view_func=customers_detail)

# Dogs
@app.route("/admin/dogs/new", endpoint="new_dog")
@login_required
def dogs_new():
    return render_template("dogs_new.html")
app.add_url_rule("/admin/dogs/new",
                 endpoint="dogs_new",
                 view_func=dogs_new)

# Invoice
@app.route("/admin/invoice/detail", endpoint="invoice")
@login_required
def invoice_detail():
    return render_template("invoice_detail.html")
app.add_url_rule("/admin/invoice/detail",
                 endpoint="invoice_detail",
                 view_func=invoice_detail)

# Search
@app.route("/admin/search", endpoint="admin_search")
@login_required
def search_page():
    return render_template("search.html")
app.add_url_rule("/admin/search",
                 endpoint="search",
                 view_func=search_page)

# Sessions
@app.route("/admin/sessions/new", endpoint="new_session")
@login_required
def sessions_new():
    return render_template("sessions_new.html")
app.add_url_rule("/admin/sessions/new",
                 endpoint="sessions_new",
                 view_func=sessions_new)

# Settings (GET + POST + CSRF + Validation + Flash)
@app.route("/admin/settings", methods=['GET', 'POST'], endpoint="admin_settings")
@login_required
def settings_page():
    csrf = ensure_csrf_token()
    s = Settings.query.first()
    if not s:
        s = Settings()
        db.session.add(s)
        db.session.commit()

    if request.method == 'POST':
        if not verify_csrf(request.form.get('csrf_token')):
            flash(TRANSLATIONS[g.lang]['invalid_csrf'], 'error')
            return redirect(url_for('admin_settings'))

        # --- Validation ---
        prefix = (request.form.get('invoice_prefix') or '').strip()
        next_no_raw = (request.form.get('next_number') or '').strip()
        vat_raw = (request.form.get('vat_rate') or '').strip()

        ok = True
        if not prefix or len(prefix) > 20:
            flash(TRANSLATIONS[g.lang]['invalid_prefix'], 'error')
            ok = False

        try:
            next_no = int(next_no_raw)
            if next_no < 1:
                raise ValueError()
        except Exception:
            flash(TRANSLATIONS[g.lang]['invalid_next'], 'error')
            ok = False
            next_no = s.next_number  # fallback

        try:
            vat = float(vat_raw.replace(',', '.'))
            if vat < 0 or vat > 100:
                raise ValueError()
        except Exception:
            flash(TRANSLATIONS[g.lang]['invalid_vat'], 'error')
            ok = False
            vat = s.vat_rate  # fallback

        if ok:
            s.invoice_prefix = prefix
            s.next_number = next_no
            s.vat_rate = vat
            db.session.commit()
            flash(TRANSLATIONS[g.lang]['saved'], 'success')
            return redirect(url_for('admin_settings'))

    return render_template("settings.html", s=s, csrf_token=csrf)

# Alias für Templates, die 'settings' als Endpoint nutzen
app.add_url_rule("/admin/settings",
                 endpoint="settings",
                 view_func=settings_page)

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
    # Lokaler Start
    app.run(host="0.0.0.0", port=5000)
