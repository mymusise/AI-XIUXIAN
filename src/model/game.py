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
        5: "你在树林的边上发现一间客栈，进去发现里面坐满了人，向小二打听了下发现大部分都是来参加比武大赛的。",
        10: "一天忙活下来后，你感觉有点疲倦，便回到客栈休息去了。第二天大早，你听到有人在敲你的门，你开门一看，是一位亭亭玉立的小女孩。",
        15: "突然你感觉背后一凉，后脑勺传来一股力量，眼前一黑，晕了过去。醒来后你发现自己躺在在一个乌黑的山洞里，山洞的石壁上闪烁着微弱的光，看上去视乎像一些荧光的草。正在你想站起来时候，发现自己脚被铁链绑住了，铁链的另一头拴在山洞的石壁上。",
        16: "这个时候，一位白发苍苍的老者出现在你面前。",
        20: "那位老者离开前，扔给了你一本秘籍，你打开后发现原来这本秘籍是之前自己修炼的剑法的进阶。你坐了下来，静静地领悟秘籍中的剑法，不知道过了多长时间，你站了起来，试了秘籍中的前两式。",

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
