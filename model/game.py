from tensorflow.core.framework.node_def_pb2 import _NODEDEF_EXPERIMENTALDEBUGINFO
import re


class _TextType(object):

    def __init__(self, key, text):
        self.key = key
        self.text = text
    
    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, _TextType):
            return other.key == self.key and other.text == self.text
        elif isinstance(other, str):
            return other == self.key


class TextType:
    DO = _TextType('action', '')
    SAY = _TextType('say', '说')


class ExpandToken:
    DO = _TextType('action', '【对话】')
    SAY = _TextType('say', '【场景】')


class GameController(object):
    scripts = {
        0: "你是一名剑修，没有门派，没有师傅。小时候在一次巧合下在村子外面捡到一本剑法秘籍，通过十年的琢磨，你终于把秘籍修炼完了。于是你离开了村子，想在外面历练一番。离开村子后你来到一片树林，碰到一位在砍柴的樵夫。",
        5: "你在树林的边上发现一间客栈，进去发现里面坐满了人，向小二打听了下发现大部分都是来参加比武大赛的。"
    }
    PRE_TEXT_ACTION = "> "
    END_ACTION_ADD = "。"
    PRE_NAME = "你"

    def clean_warp(self, text):
        return text.replace(self.PRE_TEXT_ACTION, '')

    def wrap_text(self, text, text_type=TextType.DO):
        if text == '':
            return text

        if text_type == TextType.DO:
            text = self.PRE_NAME + text
        elif text_type == TextType.SAY:
            text = f"{self.PRE_NAME}{TextType.SAY}：“{text}。”"
        if not re.match(r".*(！|”|？|。)$", text):
            text += self.END_ACTION_ADD

        text = self.PRE_TEXT_ACTION + text
        return text

    def get_given_steps(self, steps):
        if steps in self.scripts:
            return self.scripts.get(steps, None)
        return None
