from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for flash messages

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bkiiru45@gmail.com'
app.config['MAIL_PASSWORD'] = 'jblq hvfx bawg ygcp'

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Kevin254!@localhost:5432/my_hospital'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

mail = Mail(app)

# Define User model


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Define Doctor, Patient, and Appointment models


class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    specialty = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)

    appointments = db.relationship('Appointment', back_populates='doctor')


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    appointments = db.relationship('Appointment', back_populates='patient')


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    date = db.Column(db.DateTime)
    time = db.Column(db.String)

    doctor = db.relationship('Doctor', back_populates='appointments')
    patient = db.relationship('Patient', back_populates='appointments')

# Routes...


@app.route('/')
def index():
    # Fetch list of doctors from the database
    doctors = Doctor.query.all()
    return render_template('index.html', doctors=doctors)


@app.route('/doctors')
def doctor():
    if "email"not in session:
        flash("login to book appointment", "error")
        return redirect(url_for('login'))
    # Fetch list of doctors from the database
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)


@app.route('/book_appointment', methods=['POST', 'GET'])
def book_appointment():
    if "email"not in session:
        flash("login to book appointment", "error")
        return redirect(url_for('login'))
    if request.method == 'POST':
        doctor_id = request.form['doctor']
        patient_name = request.form['name']
        patient_email = request.form['email']
        appointment_date = request.form['date']
        appointment_time = request.form['time']

        appointment_datetime = datetime.strptime(
            appointment_date + ' ' + appointment_time, '%Y-%m-%d %H:%M')

        doctor = Doctor.query.filter_by(id=doctor_id).first()
        if doctor:
            if len(doctor.appointments) < 5:
                # Find or create the patient
                patient = Patient.query.filter_by(
                    name=patient_name).first()
                if not patient:
                    patient = Patient(name=patient_name, email=patient_email)
                    db.session.add(patient)
                    db.session.commit()

                # Create new appointment with the patient object
                appointment = Appointment(
                    doctor_id=doctor_id, patient=patient, date=appointment_datetime)
                db.session.add(appointment)
                db.session.commit()

                # Send email notifications to the patient and doctor
                if send_email_to_patient(patient_name, patient_email, doctor.name, appointment_datetime) and send_email_to_doctor(patient_name, doctor.email, appointment_datetime, doctor.name):
                    flash('Appointment successfully booked!', 'success')
                    return redirect(url_for('confirmation'))
                else:
                    flash(
                        'Failed to send confirmation email. Please try again later.', 'error')
                    return redirect(url_for('index'))
            else:
                flash(
                    'Sorry, this doctor is fully booked at the selected time. Please choose another time slot.', 'error')
                return redirect(url_for('index'))
        else:
            flash('Doctor not found.', 'error')
            return redirect(url_for('index'))
    else:
        # Fetch list of doctors from the database if the request method is GET
        doctors = Doctor.query.all()
        return render_template('appointment.html', doctors=doctors)


def send_email_to_patient(patient_name, patient_email, doctor_name, appointment_datetime):
    try:
        msg = Message('Appointment Confirmation',
                      sender='kevinropy@gmail.com',
                      recipients=[patient_email])
        msg.body = f'Hello {patient_name}, your appointment with Dr. {doctor_name} is confirmed for {appointment_datetime}.'
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email to patient: {e}")
        return False


def send_email_to_doctor(patient_name, doctor_email, appointment_datetime, doctor_name):
    try:
        msg = Message('New Appointment Scheduled',
                      sender='kevinropy@gmail.com',
                      recipients=[doctor_email])
        msg.body = f'Hello Dr. {doctor_name}, {patient_name} has scheduled an appointment with you for {appointment_datetime}.'
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email to doctor: {e}")
        return False


@app.route('/confirmation')
def confirmation():
    if "email"not in session:
        flash("login to book appointment", "error")
        return redirect(url_for('login'))
    return render_template('confirmation.html')


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if "email"not in session:
        flash("login to book appointment", "error")
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        specialty = request.form['specialty']
        phone = request.form['phone']

        # Create new doctor
        doctor = Doctor(name=name, email=email,
                        specialty=specialty, phone=phone)
        db.session.add(doctor)
        db.session.commit()

        return redirect(url_for('doctor'))
    else:
        return render_template('doctors.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if not name:
            flash('Name is required.', 'error')
        elif not email:
            flash('Email is required.', 'error')
        elif not password:
            flash('Password is required.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different one.', 'error')
        else:
            # Create a new user
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the user by email
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Store user's email in session to track login status
            session['email'] = user.email
            flash('Login successful!', 'success')
            # Redirect to homepage or any other page after successful login
            return redirect(url_for('book_appointment'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
