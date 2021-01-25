from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .text_generator import TextGenerator
from .game import GameController
from apis.settings import logger
from utils.base import BaseView


class TextGeneratorSerializer(serializers.Serializer):
    history = serializers.ListField()
    input_text = serializers.CharField(max_length=128, required=False, allow_blank=True)
    steps = serializers.IntegerField()
    text_type = serializers.ChoiceField(choices=['action', 'say'])


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

        game = GameController(self.default_player_name)

        current_text = game.wrap_text(input_text, text_type=text_type)
        
        next_text = ''
        if step > 0:
            generator = TextGenerator(serializer.data.get('history'))
            next_text = generator.gen_next(game.clean_warp(current_text), text_type, game.player)

        given_text = game.get_given_steps(step)
        if given_text is not None:
            next_text += given_text

        self.logger.info(f"[next_text={next_text}]")
        return Response({'next': next_text, 'text': current_text})
