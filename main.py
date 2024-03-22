from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbs import Doctor, Patient, Appointment, Base,User
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for flash messages

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bkiiru45@gmail.com'
app.config['MAIL_PASSWORD'] = 'jblq hvfx bawg ygcp'



mail = Mail(app)

# Database connection
engine = create_engine(
    'postgresql://postgres:Kevin254!@localhost:5432/doctors_booking')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Flask-Login initialization
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    # Fetch list of doctors from the database
    doctors = session.query(Doctor).all()
    return render_template('index.html', doctors=doctors)


@app.route('/doctors')
def doctor():
    # Fetch list of doctors from the database
    doctors = session.query(Doctor).all()
    return render_template('doctors.html', doctors=doctors)


@app.route('/book_appointment', methods=['POST', 'GET'])
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form['doctor']
        patient_name = request.form['name']
        patient_email = request.form['email']
        appointment_date = request.form['date']
        appointment_time = request.form['time']

        appointment_datetime = datetime.strptime(
            appointment_date + ' ' + appointment_time, '%Y-%m-%d %H:%M')

        doctor = session.query(Doctor).filter_by(id=doctor_id).first()
        if doctor:
            if len(doctor.appointments) < 5:
                # Find or create the patient
                patient = session.query(Patient).filter_by(
                    name=patient_name).first()
                if not patient:
                    patient = Patient(name=patient_name, email=patient_email)
                    session.add(patient)
                    session.commit()

                # Create new appointment with the patient object
                appointment = Appointment(
                    doctor_id=doctor_id, patient=patient, date=appointment_datetime)
                session.add(appointment)
                session.commit()

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
        doctors = session.query(Doctor).all()
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
    return render_template('confirmation.html')


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        specialty = request.form['specialty']
        phone = request.form['phone']

        # Create new doctor
        doctor = Doctor(name=name, email=email,
                        specialty=specialty, phone=phone)
        session.add(doctor)
        session.commit()

        return redirect(url_for('add_doctor'))
    else:
        return render_template('doctors.html')
    

# # Route for user registration
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']

#         # Check if the username or email already exists
#         if User.query.filter_by(username=username).first() is not None:
#             flash('Username already exists. Please choose a different one.', 'error')
#             return redirect(url_for('register'))
#         elif User.query.filter_by(email=email).first() is not None:
#             flash('Email already exists. Please choose a different one.', 'error')
#             return redirect(url_for('register'))

#         # Create a new user
#         new_user = User(username=username, email=email)
#         new_user.set_password(password)

#         # Add the user to the database
#         db.session.add(new_user)
#         db.session.commit()

#         flash('Registration successful. You can now log in.', 'success')
#         return redirect(url_for('login'))

#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         user = User.query.filter_by(username=username).first()

#         if user and user.check_password(password):
#             login_user(user)
#             flash('Login successful!', 'success')
#             return redirect(url_for('index'))
#         else:
#             flash('Invalid username or password. Please try again.', 'error')

#     return render_template('login.html')


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('You have been logged out.', 'success')
#     return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
