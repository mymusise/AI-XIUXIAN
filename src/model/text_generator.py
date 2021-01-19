from .custom_model import TFGPT2LMHeadModel, TextGenerationPipeline
# from transformers import TextGenerationPipeline
from .custom_model import tokenizer, model_path
from .game import _TextType
import re
from .tokens import TALKING_TOKEN, NONTALKING_TOKEN, HERO_TOKEN


class ExpandToken:
    DO = _TextType('action', TALKING_TOKEN)
    SAY = _TextType('say', NONTALKING_TOKEN)


class TextGenerator(object):
    MAX_LENGTH = 128
    MAX_HISTORY_LENGTH = 128

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

    def text_generator(self, text, repetition_penalty=1, top_k=5, temperature=0.8, eos_token_id=None, **kwargs):
        length_gen = len(text) + self.MAX_LENGTH
        return text_generator(
            text,
            max_length=length_gen,
            do_sample=True,
            repetition_penalty=repetition_penalty,
            top_k=top_k,
            no_repeat_ngram_size=3,
            skip_special_tokens=False,
            eos_token_id=eos_token_id,
            temperature=temperature,
            bad_words_ids=self.bad_words_ids,
            **kwargs
        )[0]['generated_text']

    def clean_result(self, text):
        text = text.replace(' ', '')
        text = text.replace(str(ExpandToken.DO), '')
        text = text.replace(str(ExpandToken.SAY), '')
        # 补全对话结束符: ”
        talk_start_index = list(re.finditer('“', text))[-1].end()
        if '”' not in text[talk_start_index:]:
            text += '”'
        return text

    def add_expand_token(self, text, text_type):
        if text_type == ExpandToken.DO:
            expand_token = ExpandToken.DO
        else:
            expand_token = ExpandToken.SAY

        text = f"{expand_token}{text}\n"
        return text

    def encode_player_name(self, text, player_name):
        return text.replace(player_name, HERO_TOKEN)

    def decode_player_name(self, text, player_name):
        return text.replace(HERO_TOKEN, player_name)

    def gen_next(self, text, text_type, player):
        # text = self.add_expand_token(text, text_type)
        all_text = self.pre_text + text
        all_text = self.encode_player_name(all_text, player.name)
        result = self.text_generator(all_text)
        print(result)
        next = self.clean_result(result[len(all_text):])
        next = self.decode_player_name(next, player.name)
        return next



try:
    model
except NameError:
    print(f'loading model from pretrained {model_path}')
    model = TFGPT2LMHeadModel.from_pretrained(model_path)
    text_generator = TextGenerationPipeline(model, tokenizer)
