from TextToSpeech import TextToSpeech

tts = TextToSpeech()

text = "دانیال کے پاس ایک بلی ہے۔ دانیال اپنی بلی سے محبت کرتا ہے۔"
audio = tts.predict(text)
tts.predict_and_save(text=text,
                     save_path="",
                     file_name="tts_audio")