from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import pymongo
import bcrypt
import json
import requests
from kisaandost import KisaanDost
from TextToSpeechModule import TextToSpeech

REMOTE_SERVER_URL = "https://1234.ngrok-free.app"
myKisaanDost = KisaanDost(REMOTE_SERVER_URL)

tts = TextToSpeech()

app = Flask(__name__)
app.secret_key = "testing"

client = pymongo.MongoClient("mongodb+srv://admin:admin@cluster0.zlyczjv.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('total_records')
records = db.register

API_URL = "https://api-inference.huggingface.co/models/ihanif/whisper-medium-urdu"
headers = {"Authorization": "Bearer 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"}

def get_weather(city):
    api_key = 'ea324abd7d9babdbacb0f763e7c59cdb'
    endpoint = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        return f'Temperature: {temperature}°C, Humidity: {humidity}%'
    else:
        return 'Failed to retrieve weather data'

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/get", methods=['POST'])
def get_bot_response():
    userText = request.data
    userText = json.loads(userText.decode('utf-8'))['msg']
    response = "Remote Server Sleeping"#myKisaanDost.run_chatbot_next_response(userText)
    return jsonify({"response": response})

@app.route("/index", methods=['post', 'get'])
def index():
    message = ''
    if "email" in session:
        return redirect(url_for("logged_in"))
    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")
        
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        city = request.form.get("city")
        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})
        if user_found:
            message = 'There already is a user by that name'
            return render_template('index.html', message=message)
        if email_found:
            message = 'This email already exists in database'
            return render_template('index.html', message=message)
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('index.html', message=message)
        else:
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            user_input = {'name': user, 'email': email, 'password': hashed,'city': city}
            records.insert_one(user_input)
            
            user_data = records.find_one({"email": email})
            new_email = user_data['email']
   
            return render_template('logged_in.html', email=new_email)
    return render_template('index.html')
    
@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #check if email exists in database
        email_found = records.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            #encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)

@app.route('/logged_in')
def logged_in():
    if "email" in session:
        # Retrieve the user's email from the session
        email = session["email"]
        # Find the user in the database
        user = db.register.find_one({'email': email})
        # Extract the city from the user document
        city = user['city']
        weather = get_weather(city)
        # Update the login status
        session['is_logged_in'] = True
        return render_template('logged_in.html', email=email, city=city, weather=weather)
    else:
        # Update the login status
        session['is_logged_in'] = False
        return redirect(url_for("login"))

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        # Update the login status
        session['is_logged_in'] = False
        return render_template("home.html")
    else:
        # Update the login status
        session['is_logged_in'] = True
        return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    if "email" in session:
         # Retrieve the user's email from the session
        email = session["email"]
        # Find the user in the database
        user = db.register.find_one({'email': email})
        # Extract the city from the user document
        city = user['city']
        weather = get_weather(city)
        return render_template('chatbot.html', email=email, city=city, weather=weather)
    else:
        return redirect(url_for("login"))

@app.route('/logged_inU')
def logged_inU():
    if "email" in session:
         # Retrieve the user's email from the session
        email = session["email"]
        # Find the user in the database
        user = db.register.find_one({'email': email})
        # Extract the city from the user document
        city = user['city']
        weather = get_weather(city)
        return render_template('logged_inU.html', email=email, city=city, weather=weather)
    else:
        return redirect(url_for("login"))

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    audio_file.save('audio.wav')  # Save the audio file locally

    # Open the audio file in binary mode
    with open('audio.wav', 'rb') as file:
        audio_data = file.read()

    # Send the audio data to the Hugging Face Inference API
    response = requests.post(API_URL, headers=headers, data=audio_data)

    if response.status_code == 200:
        transcription = response.json()[0]['transcription']
        return jsonify({'transcription': transcription})
    else:
        return jsonify({'error': 'Transcription failed'}), response.status_code

if __name__ == "__main__":
    app.run()