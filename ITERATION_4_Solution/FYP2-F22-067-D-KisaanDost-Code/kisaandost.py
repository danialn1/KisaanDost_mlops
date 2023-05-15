import requests

class KisaanDost:
    def __init__(self, remote_server_url: str):
        if remote_server_url[-1] != '/':
            remote_server_url += '/'
        self.remote_server_url = remote_server_url
        self.headers = {'Content-Type': 'application/json'}
        self.dialog = []
        self.DEFAULT_RESPONSE = u'میں ابھی کام نہیں کر رہا ہوں بارہ کرم کچھ دیر بعد کوشیش کریں'

    def get_user_input(self, user_input=None):
        if not user_input:
            user_input = input("Farmer: ")
        if user_input[-1] not in ['۔','؟']:
            user_input += '۔'
        self.dialog.append({'Agent':'Farmer',
                            'Message':user_input})

    def get_remote_server_response(self, dialog):
        response = requests.post(self.remote_server_url,
                                 json={'dialog': dialog},
                                 headers=self.headers,
                                 timeout=300)
        text = response.json()['kisaanDostReply']
        return text
        
    def generate_response(self, dialog=[]):
        try: 
            if len(dialog) == 0 or dialog[-1]['Agent'] != 'Farmer':
                raise Exception("No user input received.") 
            text = self.get_remote_server_response(dialog[-5:])
            if u'اسلام علیکم' not in dialog[-1]['Message'] and u'وا الاکوم سلام' in text:
                text = text.replace(u'وا الاکوم سلام۔', '')
                text = text.replace(u'وا الاکوم سلام', '')
                text = text.strip()
            return text
        except Exception as e:
            return self.DEFAULT_RESPONSE

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

    def run_chatbot_next_response(self,text, dialog = []):
        response = self.generate_response(dialog)
        return response