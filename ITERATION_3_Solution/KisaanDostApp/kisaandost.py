import re
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Set
import rank_bm25
from transformers import BloomTokenizerFast
import torch

class AgriRetriever:
    def __init__(self,text_file_path: str):
        self.text_file_path = text_file_path
        self.corpus = self.read_text_file(self.text_file_path)        
        self.corpus = self.clean_text_corpus(self.corpus)
        self.corpus_sentences = self.extract_sentences_from_corpus(self.corpus)
        self.corpus_sentences = self.remove_duplicate_sentences(self.corpus_sentences)
        self.preprocessed_corpus_sentences = self.get_preprocessed_sentences(self.corpus_sentences)
        tokenized_preprocessed_corpus_sentences = [sent.split() for sent in self.preprocessed_corpus_sentences]
        self.ranker = rank_bm25.BM25Okapi(tokenized_preprocessed_corpus_sentences)

    def read_text_file(self,file_path: str) -> str:
        """
        Reads a text file in utf-8 format. 
        If unable to read file, empty string is returned.
        
        Input:
            file_path: Path of file to be read
            
        Return: Text in file.
        """
        try:
            with open(file_path, "rb") as f:
                file_data =  f.read().decode('utf-8') 
            return file_data
        except:
            print("Failed to read text file!!!")
            return ""

    def clean_text_corpus(self,corpus: str) -> str:
        """
        Performs Data Cleaning on corpus
        
        Input:
            corpus: Corpus to clean
            
        Return: Cleaned corpus
        """
        corpus = corpus.strip() #Remove spaces from beginning and end of string
        corpus = re.sub(r'\r', '', corpus) #Remove Carriage Return character
        corpus = re.sub(r'[\n]+', '\n', corpus) #Remove multiple newline characters with single newline
        corpus = re.sub(r'---', '', corpus) #Remove ---
        return corpus

    def extract_sentences_from_corpus(self,corpus: str) -> List[str]:
        """
        Returns list of sentences from corpus
        
        Input:
            corpus: Corpus to extract sentences from
                
        Return: List of sentences
        """
        corpus_sentences = []
        for segment in corpus.split('\n'):
            corpus_sentences.append(segment)
        return corpus_sentences
    
    def clean_sentence(self,sentence: str,) -> str:
        """
        Performs Data Cleaning on sentence
        
        Input:
            sentence: Sentence to clean
        
        Return: Cleaned sentence
        """
        sentence = sentence.lower() #Convert to lower case
        sentence = sentence.strip() #Remove spaces from beginning and end of string
        sentence = re.sub(r'[^\w\d\s]', ' ', sentence) #Remove punctuation
        sentence = re.sub(r'(\b\w\b)', '', sentence) #Remove dangling characters
        sentence = re.sub(r'[ ]{2,}', ' ', sentence) #Replace multiple contiguous spaces with single space
        return sentence

    def remove_duplicate_sentences(self,corpus_sentences: List[str]) -> List[str]:
        """
        Removes duplicate sentences from list.
        Sentences are cleaned and stemming is performed before comparison
        Only alphanumeric portion of strings are used for comparison
        
        Input:
            corpus_sentences: List of sentences from corpus
                
        Return: List of sentences from corpus with duplicates removed.
        """
        unique_corpus_sentences = []
        unique_values = set()
        for sent in corpus_sentences:
            sent_clean = self.clean_sentence(sent)
            sent_alphanum = re.sub(r'[^\w\d]','',sent_clean)
            sent_alphanum_lower = sent_alphanum.lower()
            if sent_alphanum_lower in unique_values:
                continue
            else:
                unique_corpus_sentences.append(sent)
                unique_values.add(sent_alphanum_lower)
        
        return unique_corpus_sentences

    def get_preprocessed_sentences(self,sentences: List[str]) -> List[str]:
        """
        Perform cleaning and stemming on dataset
        
        Input:
            sentences: Dataset that will be preprocessed
            
        Return: List of preprocessed sentences
        """
        preprocessed_sentences=[]
        for s in sentences:
            clean_s = self.clean_sentence(s)
            preprocessed_sentences.append(clean_s)
        return preprocessed_sentences

    def get_top_k_similar_sentences(self,question: str, top_k: int = 3) -> List[str]:
        """
        Compares question with sentences from corpus using cosine similarity
        Returns top k similar sentences from corpus
        
        Input:
            question: Question to compare corpus with
            top_k: Number of most similar sentences to return
            
        Return: List of top k most similar sentences
        """
        preprocessed_question = self.get_preprocessed_sentences([question])[0]
        similarity_scores = self.ranker.get_scores(preprocessed_question.split())
        sorted_indexes = similarity_scores.argsort() #Argsort array in ascending order
        return [self.corpus_sentences[sorted_indexes[-(1+i)]] for i in range(top_k)] #Return top k similar sentences

class KisaanDost:
    def __init__(self, text_file_path: str, model_file_path: str):
        self.text_file_path = text_file_path
        self.retriever = AgriRetriever(self.text_file_path)
        MODEL_NAME = 'bigscience/bloomz-560m'
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
        self.prior_dialog = [ u'Farmer: آپ کس قسم کی فصلوں کے بارے میں جانتے ہیں؟',
                              u'KisaanDost: میں گندم، کپاس، چاول، کھجور، کیلا، مکئی، تیل کے بیج، امرود، گنا اور آلو اگانے کا طریقہ جانتا ہوں۔',
                              self.eos_token,
                              u'Farmer: صوبہ پنجاب میں چاول اگانے کے لیے کتنی آبپاشی کی ضرورت ہے؟',
                              u'KisaanDost: ایک کلو چاول پیدا کرنے کے لیے اوسطاً 3000 لیٹر پانی درکار ہوتا ہے۔', 
                              self.eos_token
                            ]
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
            knowledge = self.retriever.get_top_k_similar_sentences(user_input,3)
            knowledge = '\n'.join(knowledge)
            current_dialog = []
            for message_dict in self.dialog[-5:]:
                current_dialog.append(f"{message_dict['Agent']}: {message_dict['Message']}")
                if message_dict['Agent'] == 'KisaanDost':
                    current_dialog.append(self.eos_token)
            chat_log = '\n'.join(self.prior_dialog + current_dialog)
            prompt = f"Instruction: {self.instruction}\nInformation: {knowledge}\n{chat_log}\nKisaanDost:"
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
