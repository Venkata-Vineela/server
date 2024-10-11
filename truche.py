import base64
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import handledata
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import mysql.connector

from werkzeug.utils import secure_filename

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger()

# # Add a stream handler (console)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger.addHandler(handler)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS to allow cross-origin requests

# Use Flask's built-in secure cookie session management
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

# Define the database initialize function
def initialize_database():
    # conn = sqlite3.connect('../tmp/data/user_data.db')
    conn = mysql.connector.connect(
        user='root',
        password='',
        host=os.environ.get('DB_HOST', '34.16.53.160')
    )

    cursor = conn.cursor()
    
    # Create the database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS truche_db")

    # Connect to the newly created database
    conn.database = 'truche_db'

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            firstname TEXT,
            lastname TEXT,
            username TEXT UNIQUE,
            password TEXT,
            phone TEXT,
            organization TEXT,
            street_address TEXT,
            city TEXT,
            state TEXT,
            zipcode TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            username TEXT,
            friendusername TEXT,
            PRIMARY KEY (username, friendusername),
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (friendusername) REFERENCES users(username)
        )
    ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendrequests (
                username TEXT,
                friendusername TEXT,
                PRIMARY KEY (username, friendusername),
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (friendusername) REFERENCES users(username)
            )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                username TEXT,
                postnumber INT,
                text TEXT,
                file_data TEXT,
                file_name TEXT,
                file_type TEXT,
                visibility TEXT,
                PRIMARY KEY (username,postnumber),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')


    conn.commit()
    conn.close()

# Initialize the database
initialize_database()

# Define the upload folder (if you want to save files locally)
UPLOAD_FOLDER = '/tmp/fileuploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/api/add_post', methods=['POST'])
def add_post():
    if 'user' in session:
        username = session['user']
        text = request.form.get('text')
        visibility = request.form.get('visibility') 
        
        # Handling file upload
        file = request.files.get('file')

        # If there is a file, we need to save it
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            file_data = file_path  # Save file path
            file_name = file.filename
            file_type = file.mimetype
        else:
            file_data = None
            file_name = None
            file_type = None

        # Get the post number for the user
        postnumber = handledata.getpostnumber(username)

        # Call the function to save the post to the database
        success = handledata.addpost(username, postnumber, text, file_data, file_name, file_type, visibility)

        # Call the handledata.addpost function to save the post in the database
        if success:
            return jsonify({"message": "Post added successfully"}), 200
        else:
            return jsonify({"message": "Error Posting"}), 400

@app.route('/api/search_unames', methods=['POST'])
def search_unames():
    if 'user' in session:
        data = request.get_json()
        query = data.get('searchText')
        posts = handledata.getunames(query)

        return jsonify(posts)
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/suggest_unames', methods=['POST'])
def suggest_unames():
    if 'user' in session:
        username = session['user']
        suggestions = handledata.get_uname_suggestions(username)
        return jsonify(suggestions)
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/displayrequests', methods=['POST'])
def displayrequests():
    if 'user' in session:
        username = session['user']
        requests = handledata.get_requests(username)
        req = requests
        return jsonify(req)
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/get_user_data', methods=['POST'])
def get_user_data():
    if 'user' in session:
        data = request.get_json()
        username = data.get('username')
        userdata = handledata.get_user_data(username)

        if userdata:
            return jsonify(userdata), 200
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/api/get_userprofile_data', methods=['POST'])
def get_userprofile_data():
    if 'user' in session:
        username = session['user']
        userdata = handledata.get_userprofile_data(username)

        return jsonify(userdata)
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/get_user_posts', methods=['POST'])
def get_user_posts():
    if 'user' in session:
        username = session['user']
        postdata = handledata.getposts(username)

        return postdata
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/requestfriend', methods=['POST'])
def requestfriend():
    if 'user' in session:
        data = request.get_json()
        friendusername = data.get('username')
        username = session['user']
        value = handledata.add_friend_request(username, friendusername)
        return jsonify(value), 200
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/api/acceptfriend', methods=['POST'])
def acceptfriend():
    if 'user' in session:
        data = request.get_json()
        friendusername = data.get('username')
        username = session['user']
        value = handledata.add_friend_connection(username, friendusername)
        print(value)
        return jsonify(value), 200
    else:
        return jsonify({"message": "Unauthorized"}), 401

@app.route('/api/removefriend', methods=['POST'])
def removefriend():
    if 'user' in session:
        data = request.get_json()
        friendusername = data.get('username')
        username = session['user']
        value = handledata.remove_friend_connection(username, friendusername)
        return  jsonify(value), 200
    else:
        return jsonify({"message": "Unauthorized"}), 401


@app.route('/api/friendstatus', methods=['POST'])
def friendstatus():
    if 'user' in session:
        data = request.get_json()
        friendusername = data.get('username')
        username = session['user']
        status = handledata.friendstatus(username, friendusername)
        return jsonify(status), 200
    else:
        return jsonify({"message": "Unauthorized", "isfriend": "exception"}), 401

# @app.before_request
# def log_request_info():
#     # Log request information for each incoming request
#     logging.info('Request Headers: %s', request.headers)
#     logging.info('Request Method: %s', request.method)
#     logging.info('Request URL: %s', request.url)
#     logging.info('Request Data: %s', request.get_data())


# Sample protected endpoint
@app.route('/api/protected')
def protected():
   #
   # logging.info('Request Headers in protected: %s', request.headers)

    if 'user' in session:
        # Get the username from the session
        session_username = session['user']
        return jsonify({"message": f"Protected resource accessed by {session_username}"})
    return jsonify({"message": "Unauthorized"}), 401
    # data = request.get_json()
    # username = data.get('username')
    # if username in session['user']:
    #     return jsonify({"message": "Protected resource accessed by "})
    # return jsonify({"message": "Unauthorized"}), 401

# Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
   # logging.info('session Data: %s', session)

    if handledata.authenticate(username, password):
        session['user'] = username  # Store the user in the session
        print("success login")
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Login failed"}), 401

# Logout endpoint
@app.route('/api/logout')
def logout():
   # logging.info('loggingout Data: %s', request)

    if 'user' in session:
        session.pop('user', None)
        return jsonify({"message": f"Logout successful"})
    else:
        return jsonify({"message": "Logout Failed. Please try again."})

@app.route('/api/signup', methods=['POST'])
def signup():

    data = request.get_json()
    firstname = data.get("firstName")
    lastname = data.get("lastName")
    username = data.get("username")
    password = data.get("pass")
    phone = data.get("phone")
    organization = data.get("organization")
    street_address = data.get("street_address")
    city = data.get("city")
    state = data.get("state")
    zipcode = data.get("zip")

    if handledata.check_user(username):
        return jsonify({"message": "username already exists"})
    else:
        handledata.add_user(firstname, lastname, username, password, phone, organization, street_address, city, state, zipcode)

    # logging.info('firstname is: %s, lastname: %s, phone: %s, organization: %s', firstname, lastname, phone, organization)
    # logging.info(', street: %s, city: %s, state: %s, zipcode: %s', street_address, city, state, zipcode)
    # logging.info('username in signup : %s', username)
    # logging.info('password fetched from data: %s', password)

    # You can now access the signup data in the 'data' variable
    # Implement your signup logic here
    return jsonify({"message": "Signup successful"})

@app.route('/api/sendhelprequest', methods=['POST'])
def send_help_req():
    if 'user' in session:
        username = session['user']
        helptype = request.json.get('selectedNeed')
        address = request.json.get('address')
        return jsonify(status), 200
    else:
        return jsonify({"message": "Failed"}), 401


@app.route('/api/sendverificationEmail', methods=['POST'])
def send_verification_email():
    email = request.json.get('email')
    otp = request.json.get('otp')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Email configuration
    sender_email = 'trucheapp@gmail.com'  # Replace with your email
    sender_password = 'jdtp hspk rbrh hicr'  # Replace with your email password
    subject = 'Verification Code for Signup'
    message = f'Your verification code is: {otp}'

    # Send the email
    try:
        send_email(sender_email, sender_password, email, subject, message)
        return jsonify({'message': 'Verification email sent successfully'}), 200
    except Exception as e:
        print(f'Error sending email: {e}')
        return jsonify({'error': 'Internal server error'}), 500

def send_email(sender_email, sender_password, to_email, subject, message):
    # Setup the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the message
    msg.attach(MIMEText(message, 'plain'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())

@app.route('/')
def start():
    return 'App Started!'

if __name__ == '__main__':
    print("started app")
    # app.run(host='0.0.0.0', port=6000, threaded=True, debug=False)
