import os
import re
import requests
from bs4 import BeautifulSoup
import torch
import torchaudio

class TextToSpeech:
    def __init__(self):
        model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                             model='silero_tts',
                                             language='indic',
                                             speaker='v3_indic')
        self.model = model
        self.urdu_to_roman_urdu_dict = {
                               'ا': 'a',
                               'آ': 'a',
                               'أ': 'a',
                               'ب': 'b',
                               'پ': 'p',
                               'ت': 't',
                               'ٹ': 't',
                               'ث': 's',
                               'ج': 'j',
                               'چ': 'ch',
                               'ح': 'h',
                               'خ': 'kh',
                               'د': 'd',
                               'ڈ': 'd',
                               'ذ': 'dh',
                               'ر': 'r',
                               'ڑ': 'r',
                               'ز': 'z',
                               'ژ': 'zh',
                               'س': 's',
                               'ش': 'sh',
                               'ص': 's',
                               'ض': 'z',
                               'ط': 't',
                               'ظ': 'z',
                               'ع': 'a',
                               'غ': 'gh',
                               'ف': 'f',
                               'ق': 'q',
                               'ک': 'k',
                               'گ': 'g',
                               'ل': 'l',
                               'م': 'm',
                               'ن': 'n',
                               'ں': 'n',
                               'و': 'o',
                               'ﺅ': 'o',
                               'ہ': 'h',
                               'ۂ': 'h',
                               'ۃ': 'h',
                               'ھ': 'h',
                               'ء': 'h',
                               'ی': 'i',
                               'ئ': 'i',
                               'ے': 'e',
                               'ۓ': 'e',
                               '۰': '0',
                               '۱': '1',
                               '۲': '2',
                               '۳': '3',
                               '۴': '4',
                               '۵': '5',
                               '۶': '6',
                               '۷': '7',
                               '۸': '8',
                               '۹': '9',
                               '۔': '.',
                               '؟': '?'
                          }
        self.transliteration_url = 'https://www.ijunoon.com/transliteration/urdu-to-roman/'
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Firefox/80.0'}
        self.DEFAULT_RESPONSE = 'mein abhi kaam nahi kar rahe hon barah karam kuch der baad koshish karen'

    def preprocess_urdu(self,
                        text: str):
        text = text.replace('یٰ', 'ی')
        text = re.sub("[\u200f\u200e]", ' ', text)
        return text
     
    def online_transliterate(self,
                             text: str):
        text = self.preprocess_urdu(text)
        try:
            reply = requests.post(self.transliteration_url,
                                  headers=self.headers,
                                  data={'text': text},
                                  timeout=300)
            soup = BeautifulSoup(reply.text, 'html.parser')
            result_list = soup.find('div', id='ctl00_inpageResult').find_all('p')
            if result_list:
                return result_list[0].text
            else:
                return self.DEFAULT_RESPONSE
        except:
            return self.DEFAULT_RESPONSE
        
    def urdu2roman(self,
                   text: str) -> str:
        text = self.online_transliterate(text)
        return ''.join([self.urdu_to_roman_urdu_dict[char] if char in self.urdu_to_roman_urdu_dict else char for char in text])

    def predict(self,
                text: str):
        if not text.isascii():
            text = self.urdu2roman(text)
        audio = self.model.apply_tts(text,
                                     speaker='hindi_female',
                                     sample_rate=48000)
        return audio
    
    def predict_and_save(self,
                         text: str,
                         save_path: str = "",
                         file_name: str = "tts_audio") -> None:
        if not text.isascii():
            text = self.urdu2roman(text)
        audio = self.model.apply_tts(text,
                                     speaker='hindi_female',
                                     sample_rate=48000)
        file_name = file_name.replace(" ", "_")
        file_name = file_name + '.wav'
        path = os.path.join(save_path, file_name)
        torchaudio.save(path, audio.view(1, -1), 48000)
