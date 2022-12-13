from flask import Flask
from flask import render_template, request, jsonify, redirect, url_for, send_file
import csv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
import qrcode
import zipfile

zip_file = 'data/qr.zip'
csv_file = 'data/people.csv'

# create the extension
db = SQLAlchemy()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db.init_app(app)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    surname = db.Column(db.String)
    telephone_number = db.Column(db.String)
    checked = db.Column(db.Boolean)

    @hybrid_property
    def code(self):
        return f"{str(self.id)}_{self.name.lower()}_{self.surname.lower()}"

    @hybrid_property
    def qr_code_file(self):
        return f"static/qr/{self.code}.png"


with app.app_context():
    db.create_all()

# render qr code scanner page
@app.route('/')
def index():
    return render_template('index.html')

# render the people page
@app.route('/csv', methods=['GET'])
def read_csv():
    people = Person.query.all()
    return render_template('csv.html', people=people)

# render the upload page
@app.route('/upload', methods=['GET'])
def upload_form():
    return render_template('upload.html')

# upload a csv file
@app.route('/upload', methods=['POST'])
def upload():
    # manage the file upload
    file = request.files['file']
    file.save('data/temp.csv')

    # create data list
    with open('data/temp.csv', 'r') as f:
        reader = csv.reader(f)
        if reader is None:
            os.remove('data/temp.csv')
            return redirect(url_for('upload_form'))
        data = list(reader)

    # check if the file is valid
    for data_row in data:
        if len(data_row) != 5:
            os.remove('data/temp.csv')
            return redirect(url_for('upload_form'))

    # delete all person table
    Person.query.delete()

    # insert all the data in the db
    for data_row in data:
        person = Person(
            id = data_row[0],
            name = data_row[1],
            surname = data_row[2],
            telephone_number = data_row[3],
            checked = True if data_row[4] == 'OK' else False
        )
        db.session.add(person)

    db.session.commit()

    # delete the temp file
    os.remove('data/temp.csv')

    # generate qr codes
    generate_qr()
    
    return redirect(url_for('read_csv'))

def generate_qr():
    # remove all elements from qr folder
    for filename in os.listdir('static/qr'):
        os.remove(f'static/qr/{filename}')

    people = Person.query.all()
    for person in people:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(person.code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(person.qr_code_file)

@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    if not 'text' in data:
        return jsonify({
                'status': 'KO',
                'response': f'QR code non valido'
            })

    values = [v.lower() for v in data['text'].split('_')]

    if (len(values) != 3):
        return jsonify({
            'status': 'KO',
            'response': 'Invalid input'
        })

    person = Person.query.filter(Person.id.ilike(values[0]), Person.name.ilike(values[1]), Person.surname.ilike(values[2])).first()
    
    if person is None:
        return jsonify({
            'status': 'KO',
            'response': f'{values[1]} {values[2]} Non presente'
        })

    elif not person.checked:
        person.checked = True
        db.session.commit()
        return jsonify({
            'status': 'OK',
            'response': f'{values[1]} {values[2]} is now OK'
        })

    else:
        return jsonify({
            'status': 'OK?',
            'response': f'{values[1]} {values[2]} Already checked'
        })
    
# toggle ok/ko for person given the id
@app.route('/toggle/<int:id>', methods=['GET'])
def toggle(id):
    person = Person.query.filter_by(id=id).first()
    if person is not None:
        person.checked = not person.checked
        db.session.commit()

    return redirect(url_for('read_csv'))

# download the csv file
@app.route('/download', methods=['GET'])
def download():
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        people = Person.query.all()
        for person in people:
            writer.writerow([person.id, person.name, person.surname, person.telephone_number, 'OK' if person.checked else 'KO'])
    
    return send_file(csv_file, as_attachment=True)

# downlaod the zip file of qr codes
@app.route('/download/qr', methods=['GET'])
def download_qr():
    zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('static/qr'):
        for file in files:
            zipf.write(os.path.join (root, file))
    zipf.close()
    
    return send_file(zip_file, as_attachment=True)