from tensorflow.core.framework.node_def_pb2 import _NODEDEF_EXPERIMENTALDEBUGINFO
import re
from .tokens import TALKING_TOKEN, NONTALKING_TOKEN


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
    DO = _TextType('action', TALKING_TOKEN)
    SAY = _TextType('say', NONTALKING_TOKEN)


class Player(object):

    def __init__(self, name):
        self.name = name


class GameController(object):
    PRE_TEXT_ACTION = "> "
    END_ACTION_ADD = "。"

    def __init__(self, player_name, step):
        self.player = Player(player_name)  # 应该初始化更多的用户信息
        self.step = step
        # self.scripts = {
        #     0: f"你叫{self.player.name}，是一名剑修，没有门派，没有师傅。小时候在一次巧合下在村子外面捡到一本剑法秘籍，通过十年的琢磨，{self.player.name}终于把秘籍修炼完了。于是{self.player.name}离开了村子，想在外面历练一番。离开村子后{self.player.name}来到一片树林，碰到一位在砍柴的樵夫。",
        #     1: f"{self.player.name}在树林的边上发现一间客栈，进去发现里面坐满了人，向小二打听了下发现大部分都是来参加比武大赛的。",
        #     10: f"一天忙活下来后，{self.player.name}感觉有点疲倦，便回到客栈休息去了。第二天大早，{self.player.name}听到有人在敲门，开门一看，是一位亭亭玉立的小女孩。",
        #     15: f"{self.player.name}突然感觉背后一凉，后脑勺传来一股力量，眼前一黑，晕了过去。醒来后{self.player.name}发现自己躺在在一个乌黑的山洞里，山洞的石壁上闪烁着微弱的光，看上去视乎像一些荧光的草。正在{self.player.name}想站起来时候，发现自己脚被铁链绑住了，铁链的另一头拴在山洞的石壁上。",
        #     16: f"这个时候，一位白发苍苍的老者出现在{self.player.name}面前。",
        #     20: f"那位老者离开前，扔给了{self.player.name}一本秘籍，{self.player.name}打开后发现原来这本秘籍是之前自己修炼的剑法的进阶。{self.player.name}坐了下来，静静地领悟秘籍中的剑法，不知道过了多长时间，{self.player.name}站了起来，试了秘籍中的前两式。",
        # }
        self.scripts = {
            0: f"漆黑中醒来，{self.player.name}发现自己在一个完全陌生的树林中，四面一片漆黑。{self.player.name}此时内心充满了恐惧与不安，他不知道自己如何到这个地方。正在他伸手打算去摸一下自己的口袋，然而发现他的口袋中什么都没有，他决定去找到自己为什么会出现在这里。{self.player.name}站起身来望了望四周，发现有一条小路。"
        }

    @property
    def scene(self):
        script = ''
        for k, v in self.scripts.items():
            if self.step > k:
                script = v
        return script

    def clean_warp(self, text):
        return text.replace(self.PRE_TEXT_ACTION, '')

    def wrap_text(self, text, text_type=TextType.DO):
        if text == '':
            return text

        # 给输入添加人名
        if text_type == TextType.DO:
            text = self.player.name + text
        elif text_type == TextType.SAY:
            text = f"{self.player.name}{TextType.SAY}：“{text}。”"

        # 添加结束标点符号在后面。
        if not re.match(r".*(！|”|？|。)$", text):
            text += self.END_ACTION_ADD

        text = self.PRE_TEXT_ACTION + text
        return text

    def get_given_steps(self, steps) -> str:
        if steps in self.scripts:
            return self.scripts.get(steps, None)
        return ''
