from transformers import TextGenerationPipeline
from transformers import BertTokenizer
from .custom_model import TFGPT2LMHeadModel
from .custom_model import tokenizer, model_path
import re


model = None

if model is None:
    print(f'loading model from pretrained {model_path}')
    model = TFGPT2LMHeadModel.from_pretrained(model_path)
    text_generator = TextGenerationPipeline(model, tokenizer)


class ACTION:
    DO = '执行'
    SAY = '说'


class TextGenerator(object):
    MAX_LENGTH = 256
    MAX_HISTORY_LENGTH = 64
    PRE_NAME = "你"
    PRE_TEXT_ACTION = "> "
    END_ACTION = "。"

    def __init__(self, history):
        self.history = history

    @property
    def pre_text(self):
        return "\n".join(self.history)[-self.MAX_HISTORY_LENGTH:]

    @property
    def bad_words_ids(self):
        bad_words = tokenizer.special_tokens_map.values()
        ids = tokenizer(list(bad_words), add_special_tokens=False)['input_ids']
        return ids

    def clean_warp(self, text):
        return text.replace(self.PRE_TEXT_ACTION, '')

    def wrap_text(self, text, action=ACTION.DO):
        if action == ACTION.DO and text:
            text = self.PRE_NAME + text
        elif action == ACTION.SAY and text:
            text = f"{self.PRE_NAME}{ACTION.SAY}：“{text}。”"
        if not text.endswith(self.END_ACTION):
            text += self.END_ACTION
        text = self.clean_warp(text)
        return text

    def text_generator(self, text, repetition_penalty=1.2, top_k=3, eos_token_id=None, **kwargs):
        length_gen = len(text) + self.MAX_LENGTH
        return text_generator(text, max_length=length_gen, do_sample=True, repetition_penalty=repetition_penalty, top_k=top_k, eos_token_id=eos_token_id, bad_words_ids=self.bad_words_ids, **kwargs)[0]['generated_text']

    def clean_result(self, text):
        return text.replace(' ', '')

    def gen_next(self, text):
        text = self.wrap_text(text)
        all_text = self.pre_text + text
        result = self.text_generator(all_text)
        print(result)
        next = self.clean_result(result[len(all_text):])
        text = self.PRE_TEXT_ACTION + text
        return text, next