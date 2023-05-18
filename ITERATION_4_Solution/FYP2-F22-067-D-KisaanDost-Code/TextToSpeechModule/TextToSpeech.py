import os
import re
import requests
from bs4 import BeautifulSoup
import torch
import torchaudio

class TextToSpeech:
    def __init__(self):
        self.CHUNK_SIZE = 15
        dir = os.path.dirname(__file__)
        self.local_file = 'tts_model.pt'
        self.local_file = os.path.join(dir, self.local_file)
        if not os.path.isfile(self.local_file):
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/indic/v3_indic.pt',
                                           self.local_file)  
        self.model = torch.package.PackageImporter(self.local_file).load_pickle("tts_models", "model")
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
        text_words = text.split()
        audio = None
        for i in range(0, len(text_words), self.CHUNK_SIZE):
            curr_words = text_words[i:i + self.CHUNK_SIZE]
            curr_text = ' '.join(curr_words)
            if audio == None:
                audio = self.model.apply_tts(curr_text,
                                             speaker='hindi_female',
                                             sample_rate=48000)
            else:
                new_audio = self.model.apply_tts(curr_text,
                                                 speaker='hindi_female',
                                                 sample_rate=48000)
                audio = torch.cat((audio, new_audio), 0)
        return audio
    
    def predict_and_save(self,
                         text: str,
                         save_path: str = "",
                         file_name: str = "tts_audio") -> None:
        if not text.isascii():
            text = self.urdu2roman(text)
        text_words = text.split()
        audio = None
        for i in range(0, len(text_words), self.CHUNK_SIZE):
            curr_words = text_words[i:i + self.CHUNK_SIZE]
            curr_text = ' '.join(curr_words)
            if audio == None:
                audio = self.model.apply_tts(curr_text,
                                             speaker='hindi_female',
                                             sample_rate=48000)
            else:
                new_audio = self.model.apply_tts(curr_text,
                                                 speaker='hindi_female',
                                                 sample_rate=48000)
                audio = torch.cat((audio, new_audio), 0)
        file_name = file_name.replace(" ", "_")
        file_name = file_name + '.wav'
        path = os.path.join(save_path, file_name)
        torchaudio.save(path, audio.view(1, -1), 48000)
