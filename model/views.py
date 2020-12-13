from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .text_generator import TextGenerator


class TextGeneratorSerializer(serializers.Serializer):
    history = serializers.ListField()
    input_text = serializers.CharField(max_length=128, required=False, allow_blank=True)


class TextGeneratorView(viewsets.GenericViewSet):

    @action(detail=True, methods=['get'])
    def get_start_text(self, request):
        # TODO: 需要改成根据用户选择类型生成
        return Response({'next':
                         "我是一名剑修，没有门派，没有师傅。小时候在一次巧合下在村子外面捡到一本剑法秘籍，" +
                         "通过十年的琢磨，我终于把秘籍修炼完了。于是我离开了村子，想在外面历练一番。" +
                         "离开村子后我来到一片树林，碰到一位在砍柴的樵夫。"
                         })

    @action(detail=True, methods=['post'])
    def gen_next(self, request):
        serializer = TextGeneratorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        generator = TextGenerator(serializer.data.get('history'))
        current_text, next_text = generator.gen_next(serializer.data.get('input_text'))
        return Response({'next': next_text, 'text': current_text})
