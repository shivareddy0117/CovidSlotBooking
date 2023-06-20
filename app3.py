from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime, timedelta

# Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vaccination.db'  # SQLite DB path
db = SQLAlchemy(app)

# Models
class Beneficiary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssn = db.Column(db.String(9), unique=True)
    name = db.Column(db.String(50))
    dob = db.Column(db.Date)
    phone = db.Column(db.String(10))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiary.id'))
    date = db.Column(db.Date)
    time_slot = db.Column(db.String(20))
    dose = db.Column(db.Integer)  # 1 for first dose, 2 for second dose
    center = db.Column(db.String(50))

# Schemas
class BeneficiarySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Beneficiary

class AppointmentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Appointment

# Schema instances
beneficiary_schema = BeneficiarySchema()
appointment_schema = AppointmentSchema()

# Routes

@app.route('/register', methods=['GET', 'POST'])
def register_beneficiary():
 if request.method == 'POST':
    try:
        data = request.json
        name = data['name']
        dob = datetime.strptime(data['dob'], '%d-%m-%Y').date()
        ssn = data['ssn']
        phone = data['phone']

        # Input validation
        if len(ssn) != 9 or not ssn.isdigit() or len(phone) != 10 or not phone.isdigit():
            return jsonify({'message': 'Invalid input'}), 400

        if datetime.now().year - dob.year < 45:
            return jsonify({'message': 'Beneficiary should be 45 or older'}), 400

        new_beneficiary = Beneficiary(name=name, dob=dob, ssn=ssn, phone=phone)
        db.session.add(new_beneficiary)
        db.session.commit()

        return json.dumps(beneficiary_schema.dump(new_beneficiary)), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500
 return render_template('register.html')



@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'POST':
        try:
            data = request.json
            beneficiary_id = data['beneficiary_id']
            date = datetime.strptime(data['date'], '%d-%m-%Y').date()
            time_slot = data['time_slot']
            dose = data['dose']
            center = data['center']

            # Input validation
            if dose not in [1, 2] or center not in ['CenterA', 'CenterB', 'CenterC', 'CenterD']:
                return jsonify({'message': 'Invalid input'}), 400

            # A slot cannot be booked before 90 days.
            if date < datetime.now().date() or date > datetime.now().date() + timedelta(days=90):
                return jsonify({'message': 'Invalid date'}), 400

            # Each time slot should allow only 10 users to register.
            if Appointment.query.filter_by(date=date, time_slot=time_slot, center=center).count() >= 10:
                return jsonify({'message': 'Time slot is full'}), 400

            # There are a total of 30 vaccinations available per day in each vaccine center.
            if Appointment.query.filter_by(date=date, center=center).count() >= 30:
                return jsonify({'message': 'No more vaccinations available at this center on this date'}), 400

            # One beneficiary can at any time have at most two appointments (one for the first dose and one for the second dose)
            if Appointment.query.filter_by(beneficiary_id=beneficiary_id).count() >= 2:
                return jsonify({'message': 'Beneficiary already has two appointments'}), 400

            # Time between first and second dose is a minimum of 15 days.
            if dose == 2:
                first_dose_appointment = Appointment.query.filter_by(beneficiary_id=beneficiary_id, dose=1).first()
                if not first_dose_appointment or (date - first_dose_appointment.date).days < 15:
                    return jsonify({'message': 'At least 15 days must pass between the first and second doses'}), 400

            # 15 are available for first dose, 15 are available for second dose.
            if Appointment.query.filter_by(date=date, center=center, dose=dose).count() >= 15:
                return jsonify({'message': 'No more doses available at this center on this date'}), 400

            new_appointment = Appointment(beneficiary_id=beneficiary_id, date=date, time_slot=time_slot, dose=dose, center=center)
            db.session.add(new_appointment)
            db.session.commit()

            return jsonify(appointment_schema.dump(new_appointment)), 201

        except Exception as e:
            return jsonify({'message': str(e)}), 500

    return render_template('book.html')  # Render the booking form if it's a GET request

@app.route('/appointments')
def appointments():
    appointments = Appointment.query.all()  # Get all appointments
    result = appointment_schema.dump(appointments, many=True)  # serialize the data
    return jsonify(result)

@app.route('/beneficiaries')
def beneficiaries():
    beneficiaries = Beneficiary.query.all() # Get all beneficiaries
    return render_template('beneficiaries.html', beneficiaries=beneficiaries) # Render a template and pass the beneficiaries

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == "__main__":
    with app.app_context():  # Setting up an application context
        db.create_all()  # Create tables
    app.run(debug=True)
