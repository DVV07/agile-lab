from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# * 1. Database Configuration *
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'  # Use SQLite; file-based
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress a warning
db = SQLAlchemy(app)

# * 2. Database Model *
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    amount_due = db.Column(db.Float, nullable=False)

    def __repr__(self):  # Helps with debugging; represents the object
        return f"Student(first_name='{self.first_name}', last_name='{self.last_name}')"

    def to_dict(self):  # Helper method to convert to dictionary
        return {
            'student_id': self.student_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'dob': self.dob.isoformat(),  # Convert date to string
            'amount_due': self.amount_due
        }

# Create the database tables within the app context
with app.app_context():
    db.create_all()

# * 3. Create (POST /students) *
@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()  # Get data from the request body

    # Validate the data (basic validation)
    if not data or 'first_name' not in data or 'last_name' not in data or 'dob' not in data or 'amount_due' not in data:
        return jsonify({'message': 'Invalid input. Please provide all required fields.'}), 400  # Bad Request

    try:
        # Convert date string to date object
        dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()  # Assuming YYYY-MM-DD format
        new_student = Student (
            first_name=data['first_name'],
            last_name=data['last_name'],
            dob=dob,
            amount_due=data['amount_due'] )

        db.session.add(new_student)
        db.session.commit()

        return jsonify({'message': 'Student created!', 'student': new_student.to_dict()}), 201  # Created
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    except Exception as e:
        return jsonify({'message': f'Error creating student: {str(e)}'}), 500  # Internal Server Error

# * 4. Read (GET /students and GET /students/<int:student_id>) *
@app.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()  # Get all students from the database
    return jsonify({'students': [student.to_dict() for student in students]})

@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.query.get(student_id)  # Get student by ID
    if student:
        return jsonify({'student': student.to_dict()})
    return jsonify({'message': 'Student not found'}), 404  # Not Found

# * 5. Update (PUT /students/<int:student_id>) *
@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update'}), 400

    try:
        if 'first_name' in data:
            student.first_name = data['first_name']
        if 'last_name' in data:
            student.last_name = data['last_name']
        if 'dob' in data:
            student.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
        if 'amount_due' in data:
            student.amount_due = data['amount_due']

        db.session.commit()
        return jsonify({'message': 'Student updated!', 'student': student.to_dict()})
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    except Exception as e:
        return jsonify({'message': f'Error updating student: {str(e)}'}), 500

# * 6. Delete (DELETE /students/<int:student_id>) *
@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted!'}), 200  # Or 204 No Content

# * 7. File Upload (POST /upload) *
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the request contains a file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # Securely save the file (you might want to generate unique filenames)
        filename = os.path.join('uploads', file.filename)  # Specify upload directory
        file.save(filename)
        return jsonify({'message': 'File uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)  
