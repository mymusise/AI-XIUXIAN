from django.core.validators import EMPTY_VALUES
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
    CUSTOM_START_ID = -1
    EMPTY_SCRIPT = {0: ""}

    def __init__(self, player_name, step, start_id):
        self.player = Player(player_name)  # 应该初始化更多的用户信息
        self.step = step

        self.init_script(start_id)

    def init_script(self, start_id):
        if type(start_id) == str and start_id.isnumeric():
            start_id = int(start_id)
        elif type(start_id) != int:
            raise TypeError(f"start_id:{start_id} should be int")
        if start_id == self.CUSTOM_START_ID:
            self.scripts = self.EMPTY_SCRIPT
            return

        if start_id not in GAME_SCRIPTS:
            raise ValueError(f"start_id:{start_id} is not in GAME_SCRIPTS")

        scripts = {}
        for k, v in GAME_SCRIPTS[start_id]['content'].items():
            scripts[k] = v.format(player_name=self.player.name)
        self.scripts = scripts

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


GAME_SCRIPTS = {
    1: {
        "name": "乞丐",
        "describe": "",
        "content": {
            0: "漆黑中醒来，{player_name}发现自己在一个完全陌生的树林中，四面一片漆黑。{player_name}此时内心充满了恐惧与不安，他不知道自己如何到这个地方。正在他伸手打算去摸一下自己的口袋，然而发现他的口袋中什么都没有，他决定去找到自己为什么会出现在这里。{player_name}站起身来望了望四周，发现有一条小路。",
        }
    },
    2: {
        "name": "商人",
        "describe": "",
        "content": {
            0: "你叫{player_name}，是一名商人。家族世代为商, 你的祖爷爷曾经是帝国首富, 但是到你这代家族基本已经没落. 为了振兴家族, 从14岁开始{player_name}就辍学跟着家里舅舅干项目, 跟着项目什么脏活累活都干, 干过码头搬运, 清理过下水道. 一天舅舅把{player_name}喊到他的办公室, 给了{player_name}一个任务, 去村庄里征收一片农地, 但是其中一个农民坚决反对这次的征收.",
            2: "这时候, 舅舅的助理告诉{player_name}, 如果村民不肯退步, 他那边有村里几个混混的联系方式, 可以解决一些不好处理的事情. ",
            10: "忙完村里征收农地的事情后, {player_name}回去汇报给他舅舅. ",
        }
    },
    3: {
        "name": "剑修",
        "describe": "",
        "content": {
            0: "你叫{player_name}，是一名剑修，没有门派，没有师傅。小时候在一次巧合下在村子外面捡到一本剑法秘籍，通过十年的琢磨，{player_name}终于把秘籍修炼完了。于是{player_name}离开了村子，想在外面历练一番。离开村子后{player_name}来到一片树林，碰到一位在砍柴的樵夫。",
            2: "{player_name}在树林的边上发现一间客栈，进去发现里面坐满了人，向小二打听了下发现大部分都是来参加比武大赛的。",
            5: "一天忙活下来后，{player_name}感觉有点疲倦，便回到客栈休息去了。第二天大早，{player_name}听到有人在敲门，开门一看，是一位亭亭玉立的小女孩。",
            12: "{player_name}突然感觉背后一凉，后脑勺传来一股力量，眼前一黑，晕了过去。醒来后{player_name}发现自己躺在在一个乌黑的山洞里，山洞的石壁上闪烁着微弱的光，看上去视乎像一些荧光的草。正在{player_name}想站起来时候，发现自己脚被铁链绑住了，铁链的另一头拴在山洞的石壁上。",
            15: "这个时候，一位白发苍苍的老者出现在{player_name}面前。",
            20: "那位老者离开前，扔给了{player_name}一本秘籍，{player_name}打开后发现原来这本秘籍是之前自己修炼的剑法的进阶。{player_name}坐了下来，静静地领悟秘籍中的剑法，不知道过了多长时间，{player_name}站了起来，试了秘籍中的前两式。",
        }
    }
}
