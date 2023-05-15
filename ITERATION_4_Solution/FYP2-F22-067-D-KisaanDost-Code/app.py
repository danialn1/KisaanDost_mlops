from flask import Flask, render_template, request, url_for, redirect, session, jsonify
import pymongo
import bcrypt
import json
import requests
from kisaandost import KisaanDost
from TextToSpeechModule import TextToSpeech
#import whisper
import time
import os
import torchaudio
import base64
import librosa

REMOTE_SERVER_URL = "http://9242-34-72-113-141.ngrok-free.app"
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

# @app.route("/get", methods=['POST'])
# def get_bot_response():
#     userText = request.data
#     userText = json.loads(userText.decode('utf-8'))['msg']
#     response = myKisaanDost.run_chatbot_next_response(userText)
#     return jsonify({"response": response})

import collections
userDialogue = collections.defaultdict(list)

@app.route("/get", methods=['POST'])
def get_bot_response():
    id = session['email']
    userText = request.data
    userText = json.loads(userText.decode('utf-8'))['msg']
    if len(userDialogue[id]) >= 2 and userText == userDialogue[id][-2]['Message']:
        response = userDialogue[id][-1]['Message']
    else:
        userDialogue[id].append({'Agent':'Farmer',
                                 'Message':userText})
        response = myKisaanDost.run_chatbot_next_response(userText, dialog=userDialogue[id])
        userDialogue[id].append({'Agent':'KisaanBot',
                                 'Message':response})
    #audio = tts.predict(response)  # Generate audio from the chatbot response
    tts.predict_and_save(text=response,
                         save_path="",
                         file_name="tts_audio")
    with open("tts_audio.wav", 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')
    #audio_data, sr = librosa.load("tts_audio.wav", sr=48000)
    #audio_data = audio_data.tobytes()
    #audio_data = base64.b64encode(audio_data).decode('utf-8')

    #print(audio.shape)
    #audio = audio.numpy().tolist()
    #buffer = io.BytesIO()
    #torch.save(audio, buffer)
    #buffer.seek(0)
    #audio_data = buffer.getvalue()
    #print(len(audio_data))
    #print(audio.numpy().tolist())
    #audio_data = base64.b64encode(audio_data).decode('utf-8')
    # Save the audio file temporarily
    #audio_path = "chatbot_response.wav"
    #waveform = audio.unsqueeze(0)  # Add a batch dimension if needed
    #torchaudio.save(audio_path, waveform, sample_rate=48000)
    
    return jsonify({"response": response, "audio": audio_data})


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
    
#model = whisper.load_model("small")
#options = dict(task="transcribe", language="ur")

# @app.route('/transcribe', methods=['POST'])
# def transcribe():
#     audio_file = request.files['audio']
#     audio_file.save('audio.wav')  # Save the audio file locally

#     # Open the audio file in binary mode
#     with open('audio.wav', 'rb') as file:
#         audio_data = file.read()

#     # Send the audio data to the Hugging Face Inference API
#     response = requests.post(API_URL, headers=headers, data=audio_data)

#     if response.status_code == 200:
#         transcription = response.json()
#         return jsonify({'transcription': transcription})
#     else:
#         return jsonify({'error': 'Transcription failed'}), response.status_code




#model = whisper.load_model("small")
#options = dict(task="transcribe", language="ur")
from transformers import WhisperProcessor, WhisperForConditionalGeneration

WHISPER_NAME = "ihanif/whisper-medium-urdu"
whisper_processor = WhisperProcessor.from_pretrained(WHISPER_NAME)
whisper_model = WhisperForConditionalGeneration.from_pretrained(WHISPER_NAME)

import librosa
import torch
from pydub import AudioSegment
import io

@app.route("/transcribe", methods=["POST"])
def transcribe():
    # Check if an audio file is included in the request
    if "audio" not in request.files:
        return jsonify({"error": "No audio file found."}), 400
    
    audio_file = request.files["audio"]
    sr = request.form.get('sr')
    file_data = audio_file.read()
    file_data = io.BytesIO(bytes(file_data))
    file_data = AudioSegment.from_file(file_data)
    file_data = file_data.set_sample_width(2).set_frame_rate(16000).set_channels(1)
    file_data.export("input_audio.wav")
    wav, sr = librosa.load("input_audio.wav")
    audio_data = librosa.resample(y=wav, orig_sr=sr, target_sr=16000)
    #print(sr)
    #if sr:
    #    sr = int(sr)
    #    audio_data, _ = librosa.load(file_data, sr=sr)
    #else:
    #    audio_data, _ = librosa.load(file_data, sr=None)
    #print(type(audio_data))
    input_features = whisper_processor(audio_data, sampling_rate=16000, return_tensors="pt").input_features 
    predicted_ids = whisper_model.generate(input_features)
    transcription = whisper_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription
    # Save the audio file temporarily
    #audio_path = "audio.wav"
    #audio_file.save(audio_path)
    
    # Perform transcription
    #result = model.transcribe('audio.wav', **options, fp16=False)
    #transcribed_text = result["text"]

# generate token ids
# decode token ids to text

    # Return the transcription result and processing time
    #return transcribed_text




if __name__ == "__main__":
    app.run()