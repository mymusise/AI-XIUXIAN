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
    MAX_HISTORY_LENGTH = 256
    SHORT_LENGTH = 16

    def __init__(self, history, sence):
        self.history = history
        self._scene = sence

    @property
    def pre_text(self):
        return "\n".join(self.history)[-self.MAX_HISTORY_LENGTH:]

    @property
    def short_text(self):
        return self.pre_text[-self.SHORT_LENGTH:]

    @property
    def bad_words_ids(self):
        bad_words = tokenizer.special_tokens_map.values()
        ids = tokenizer(list(bad_words), add_special_tokens=False)['input_ids']
        return ids

    @property
    def scene(self):
        print("self._scene", self._scene)
        print("self.pre_text", self.pre_text)
        if self._scene[:-10] in self.pre_text:
            return ''
        return self._scene

    def text_generator(self, text, repetition_penalty=1.5, top_k=1, temperature=0.8, eos_token_id=None, sentences_nums=2, **kwargs):
        model.set_sentence_num(sentences_nums)
        length_gen = len(tokenizer(text, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=None)['input_ids'])
        length_gen += self.MAX_LENGTH
        return text_generator(
            text,
            max_length=length_gen,
            do_sample=True,
            repetition_penalty=repetition_penalty,
            top_k=top_k,
            # no_repeat_ngram_size=2,
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
        talk_start_index = list(re.finditer('“', text))
        if talk_start_index:
            talk_start_index = talk_start_index[-1].end()
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

    def gen_next(self, text, text_type, player, add_scene=True):
        # text = self.add_expand_token(text, text_type)
        # text = self.encode_player_name(text, player.name)
        # result = self.text_generator(text, sentences_nums=1)
        # print(result)
        # result = result[self.SHORT_LENGTH:]
        all_text = self.pre_text + text
        if add_scene:
            all_text = self.scene + all_text

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
    model = TFGPT2LMHeadModel.from_pretrained(model_path, use_cache=True)
    text_generator = TextGenerationPipeline(model, tokenizer)
