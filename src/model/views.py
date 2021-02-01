from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .text_generator import TextGenerator, text_generator, tokenizer
from .game import GameController, GAME_SCRIPTS
from apis.settings import logger
from utils.base import BaseView
import os


class StartInfoView(BaseView, viewsets.GenericViewSet):

    @action(detail=True)
    def get_start_info(self, request):
        result = [{"id": k, "name": v['name'], "describe": v['describe']}
                  for k, v in GAME_SCRIPTS.items()]
        return Response(result)


class TextGeneratorSerializer(serializers.Serializer):
    history = serializers.ListField()
    input_text = serializers.CharField(
        max_length=128, required=False, allow_blank=True)
    steps = serializers.IntegerField()
    text_type = serializers.ChoiceField(choices=['action', 'say'])
    start_id = serializers.IntegerField(default=1)


class TextGeneratorView(BaseView, viewsets.GenericViewSet):
    default_player_name = "王多多"

    @action(detail=True, methods=['post'])
    def gen_next(self, request):
        serializer = TextGeneratorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        input_text = serializer.data.get('input_text')
        text_type = serializer.data.get('text_type')
        step = serializer.data.get('steps')
        start_id = serializer.data.get('start_id', 1)

        game = GameController(self.default_player_name, step, start_id)

        current_text = game.wrap_text(input_text, text_type=text_type)

        given_text = game.get_given_steps(step)
        if given_text:
            add_scene = False
        else:
            add_scene = True

        next_text = ''
        if step > 0:
            generator = TextGenerator(
                serializer.data.get('history'), game.scene)
            next_text = generator.gen_next(game.clean_warp(
                current_text), text_type, game.player, add_scene)

        if given_text is not None:
            next_text += given_text

        self.logger.info(f"[next_text={next_text}]")
        return Response({'next': next_text, 'text': current_text})


class SuggestionView(BaseView):

    @property
    def max_length_limit(self):
        return int(os.environ.get('MAX_LENGTH_LIMIT', 0))

    @property
    def num_suggest_limit(self):
        return int(os.environ.get('NUM_SUGGEST_LIMIT', 0))

    def get(self, request):
        current = request.GET.get('current', '')
        len_gen = int(request.GET.get('max_length', 6))
        num_suggest = int(request.GET.get('num_suggest', 3))

        len_current = len(tokenizer(current, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=None)['input_ids'])

        if not current or len_current == 0:
            return Response([], content_type="application/json")

        if self.max_length_limit and len_gen > self.max_length_limit:
            len_gen = self.max_length_limit
        if len_gen > 128:  # n_position = 256 = max_len_current + max_len_gen
            len_gen = 128

        if self.num_suggest_limit and num_suggest > self.num_suggest_limit:
            num_suggest = self.num_suggest_limit

        if len_current > 128:
            current = current[-128 + 1:]
            len_current = len(tokenizer(current, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=None)['input_ids'])

        self.logger.info(f"[Suggestion generating len_current={len_current} len_gen={len_gen}]")
        result = text_generator(current, max_length=len_current + len_gen, repetition_penalty=1.5, top_k=num_suggest, num_beams=num_suggest, num_return_sequences=num_suggest)
        result = [item['generated_text'][len(current):] for item in result]
        self.logger.info(f"[Suggestion result={result}]")
        return Response(result, content_type="application/json")
