import sys
TTS_PATH = "TTS/"
sys.path.append(TTS_PATH)

import os
import string
import time
import argparse
import json

import numpy as np
import torch

from TTS.tts.utils.synthesis import synthesis
from TTS.tts.utils.text.symbols import make_symbols, phonemes, symbols
try:
    from TTS.utils.audio import AudioProcessor
except:
    from TTS.utils.audio import AudioProcessor

from TTS.tts.models import setup_model
from TTS.config import load_config
from TTS.tts.models.vits import *

from TTS.tts.utils.speakers import SpeakerManager
from pydub import AudioSegment
import librosa

class NoPrint(object):
    def __init__(self):
        self.devnull = open(os.devnull,'w')

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.devnull, self.devnull

    def __exit__(self, *args):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self.devnull.close()

class TextToSpeech:
    def __init__(self,
                 model_files_dir="./ModelFiles"):
        self.paths = {'MODEL_PATH':'best_model_latest.pth.tar',
                      'CONFIG_PATH':'config.json',
                      'TTS_LANGUAGES':'language_ids.json',
                      'TTS_SPEAKERS':'speakers.json',
                      'CONFIG_SE_PATH':'config_se.json',
                      'CHECKPOINT_SE_PATH':'SE_checkpoint.pth.tar',
                      'REFERENCE_AUDIO':'reference_audio'}
        for k in self.paths.keys():
            self.paths[k] = os.path.join(model_files_dir ,self.paths[k])
        self.USE_CUDA = torch.cuda.is_available()        
        self.config = load_config(self.paths['CONFIG_PATH'])
        with NoPrint():
            self.ap = AudioProcessor(**self.config.audio, verbose = False)
        speaker_embedding = None
        self.config.model_args['d_vector_file'] = self.paths['TTS_SPEAKERS']
        self.config.model_args['use_speaker_encoder_as_loss'] = False
        with NoPrint():
            self.model = setup_model(self.config)
        self.model.language_manager.set_language_ids_from_file(self.paths['TTS_LANGUAGES'])
        self.model.length_scale = 1
        self.model.inference_noise_scale = 0.3 
        self.model.inference_noise_scale_dp = 0.3 
        cp = torch.load(self.paths['MODEL_PATH'], map_location=torch.device('cpu'))
        model_weights = cp['model'].copy()
        for key in list(model_weights.keys()):
            if "speaker_encoder" in key:
                del model_weights[key]
        self.model.load_state_dict(model_weights)
        self.model.eval()
        if self.USE_CUDA:
            self.model = self.model.cuda()
        use_griffin_lim = False
        with NoPrint():
            SE_speaker_manager = SpeakerManager(encoder_model_path=self.paths['CHECKPOINT_SE_PATH'],
                                                encoder_config_path=self.paths['CONFIG_SE_PATH'],
                                                use_cuda=self.USE_CUDA)
        reference_files = [os.path.join(self.paths['REFERENCE_AUDIO'], val) for val in os.listdir(self.paths['REFERENCE_AUDIO'])]
        for sample in reference_files:
            os.system(f"ffmpeg-normalize {sample} -nt rms -t=-27 -o {sample} -ar 16000 -f")
        self.reference_emb = SE_speaker_manager.compute_d_vector_from_clip(reference_files)
        self.language_id = 0
    
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
        
    def urdu2roman(self,
                   text: str) -> str:
        return ''.join([self.urdu_to_roman_urdu_dict[char] if char in self.urdu_to_roman_urdu_dict else char for char in text])

    def predict(self,
                text: str):
        if not text.isascii():
            text = self.urdu2roman(text)
        wav, _, _, _ = synthesis(model=self.model,
                                 text=text,
                                 CONFIG=self.config,
                                 use_cuda=self.USE_CUDA,
                                 ap=self.ap,
                                 speaker_id=None,
                                 d_vector=self.reference_emb,
                                 style_wav=None,
                                 language_id=self.language_id,
                                 enable_eos_bos_chars=self.config.enable_eos_bos_chars,
                                 use_griffin_lim=True,
                                 do_trim_silence=False).values()

        return wav
    
    def predict_and_save(self,
                         text: str,
                         save_path: str = "",
                         file_name: str = "tts_audio") -> None:
        if not text.isascii():
            text = self.urdu2roman(text)
        wav, _, _, _ = synthesis(model=self.model,
                                 text=text,
                                 CONFIG=self.config,
                                 use_cuda=self.USE_CUDA,
                                 ap=self.ap,
                                 speaker_id=None,
                                 d_vector=self.reference_emb,
                                 style_wav=None,
                                 language_id=self.language_id,
                                 enable_eos_bos_chars=self.config.enable_eos_bos_chars,
                                 use_griffin_lim=True,
                                 do_trim_silence=False).values()
        file_name = file_name.replace(" ", "_")
        file_name = file_name + '.wav'
        path = os.path.join(save_path, file_name)
        self.ap.save_wav(wav, path)

