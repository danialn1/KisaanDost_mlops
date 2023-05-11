import requests

class KisaanDost:
    def __init__(self, remote_server_url: str):
        if remote_server_url[-1] != '/':
            remote_server_url += '/'
        self.remote_server_url = remote_server_url
        self.headers = {'Content-Type': 'application/json'}
        self.dialog = []

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
        
    def generate_response(self):
        try: 
            if self.dialog[-1]['Agent'] != 'Farmer':
                raise Exception("No user input received.") 
            text = self.get_remote_server_response(self.dialog[-5:])
            if u'اسلام علیکم' not in self.dialog[-1]['Message'] and u'وا الاکوم سلام' in text:
                text = text.replace(u'وا الاکوم سلام۔', '')
                text = text.replace(u'وا الاکوم سلام', '')
                text = text.strip()
            self.dialog.append({'Agent':'KisaanBot',
                                'Message':text})
        except Exception as e:
            print("ERROR:",e)
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