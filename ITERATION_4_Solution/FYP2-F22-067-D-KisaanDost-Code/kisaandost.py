import re
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Set
from transformers import BloomTokenizerFast
import torch

class KisaanDost:
    def __init__(self, text_file_path: str, model_file_path: str):
        self.MODEL_NAME = 'bigscience/bloomz-560m'
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = BloomTokenizerFast.from_pretrained(self.MODEL_NAME)
        self.model = torch.load(model_file_path, map_location=self.device)
        self.model.eval()
        self.eos_token = '</s>'
        self.instruction = '\n'.join(['This is a conversation between Farmer and KisaanDost.',
                                      'Farmer asks queries regarding farming.',
                                      'Farmer is speaking in Urdu.',
                                      'KisaanDost provides information on growing crops using fact-based information.',
                                      'KisaanDost includes all information relevant to the query from the provided Information:',
                                      'Everything KisaanDost says is supported by the provided Information:',
                                      'KisaanDost answers in a single sentence.',
                                      'KisaanDost tries to answer Farmer\'s queries but says KisaanDost does not know if KisaanDost does not know the answer.',
                                      'KisaanDost speaks in Urdu.'
                                     ])
        self.dialog = []

    def get_user_input(self,user_input=None):
        if not user_input:
            user_input = input("Farmer: ")
        if user_input[-1] not in ['۔','؟']:
            user_input += '۔'
        self.dialog.append({'Agent':'Farmer',
                            'Message':user_input})
        
    def generate_response(self):
        try: 
            if self.dialog[-1]['Agent'] != 'Farmer':
                raise Exception("No user input received.") 
            user_input = self.dialog[-1]['Message']
            current_dialog = []
            for message_dict in self.dialog[-5:]:
                current_dialog.append(f"{message_dict['Agent']}: {message_dict['Message']}")
                if message_dict['Agent'] == 'KisaanDost':
                    current_dialog.append(self.eos_token)
            chat_log = '\n'.join(current_dialog)
            prompt = f"Instruction: {self.instruction}\n{chat_log}\nKisaanDost:"
            inp = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            pred = self.model.generate(inp["input_ids"], 
                                       max_new_tokens=80,
                                       do_sample=False,
                                       eos_token_id=self.tokenizer.get_vocab()[self.eos_token])
            generated_text = self.tokenizer.decode(pred[0], skip_special_tokens = True)
            generated_text = generated_text[generated_text.rfind('KisaanDost:')+12:].strip()
            self.dialog.append({'Agent':'KisaanBot',
                                'Message':generated_text})
        except Exception as e:
            self.dialog.append({'Agent':'KisaanBot',
                                'Message':'میں ابھی کام نہیں کر رہا ہوں۔ بعد میں دوبارہ کوشش کریں۔'}) 
    
    def return_last_response_message(self):
        for message_dict in self.dialog[::-1]:
            if message_dict['Agent']=='KisaanBot':
                return message_dict['Message']

    def run_chatbot(self):
        while(1):
            self.get_user_input()
            if self.dialog[-1]['Message'] == 'q۔':
                break    
            self.generate_response()
            print(f"{self.dialog[-1]['Agent']}: {self.dialog[-1]['Message']}")

    def run_chatbot_next_response(self,text):
        self.get_user_input(text)
        self.generate_response()
        return self.dialog[-1]['Message']
