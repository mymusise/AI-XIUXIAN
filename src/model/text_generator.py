from transformers import TextGenerationPipeline
from transformers import BertTokenizer
from .custom_model import TFGPT2LMHeadModel
from .custom_model import tokenizer, model_path
from .game import _TextType
import re


model = None

if model is None:
    print(f'loading model from pretrained {model_path}')
    model = TFGPT2LMHeadModel.from_pretrained(model_path)
    text_generator = TextGenerationPipeline(model, tokenizer)


class ExpandToken:
    DO = _TextType('action', '【场景】')
    SAY = _TextType('say', '【对话】')


class TextGenerator(object):
    MAX_LENGTH = 256
    MAX_HISTORY_LENGTH = 64

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

    def text_generator(self, text, repetition_penalty=1.2, top_k=0, temperature=0.7, eos_token_id=None, **kwargs):
        length_gen = len(text) + self.MAX_LENGTH
        return text_generator(
            text,
            max_length=length_gen,
            do_sample=True,
            repetition_penalty=repetition_penalty,
            top_k=top_k,
            eos_token_id=eos_token_id,
            temperature=temperature,
            bad_words_ids=self.bad_words_ids,
            **kwargs
        )[0]['generated_text']

    def clean_result(self, text):
        text = text.replace(' ', '')
        text = text.replace(str(ExpandToken.DO), '')
        text = text.replace(str(ExpandToken.SAY), '')
        return text

    def add_expand_token(self, text, text_type):
        if text_type == ExpandToken.DO:
            expand_token = ExpandToken.DO
        else:
            expand_token = ExpandToken.SAY

        text = f"{expand_token}{text}\n"
        return text

    def gen_next(self, text, text_type):
        text = self.add_expand_token(text, text_type)
        all_text = self.pre_text + text
        result = self.text_generator(all_text)
        print(result)
        next = self.clean_result(result[len(all_text):])
        return next
