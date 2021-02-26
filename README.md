# AIXX

<p align="center">
<img alt="Build" src="https://github.com/mymusise/AI-XIUXIAN/blob/main/logo.png">
</p>

AIXX是一款免费的开源单人文字冒险游戏，游戏基于AI模型，根据玩家的输入，生成各种各样的游戏内容。

- 在线体验： https://aixx.mymusise.com

- 或者可以在colab上运行：　<a href="https://colab.research.google.com/github/mymusise/AI-XIUXIAN/blob/main/demo.ipynb"><img alt="Build" src="https://colab.research.google.com/assets/colab-badge.svg">
</a>

- 或者你还可以在本地直接运行：
```bash
git clone https://github.com/mymusise/AI-XIUXIAN.git
cd AI-XIUXIAN
pip install -r requirements.txt
cd src/
mkdir logs

python play.py
```

## 自定义

AIXX目前自带了三个默认的故事线， 也支持用户自定义不同的故事，只需要按下面格式定义加入到[game.py]()即可:
```json
GAME_SCRIPTS = {
    ...
    101: {
        "name": "院长",
        "describe": "",
        "content": {
            0: "你叫{player_name}，是一名精神科医生，目前在一所青少年网瘾治疗中心上班。",
            2: "{player_name}为了达到更好的“治疗”效果，开始采用一些非正规的手段对学员进行“治疗”。",
            5: "由于{player_name}“治疗”方法效果拔群，获得了家长和舆论的好评，当地媒体也多次赞扬{player_name}的相关事迹。",
            8: "后来“治疗”的方法被曝光后， 人们才发现{player_name}的“治疗”方法并没有任何医学依据，引起社会很大的争议。政府部门也介入调查并叫停了项目。",
            ...
        },
    ...
}
```

- `101`: 故事的ID
- `name`: 故事名字
- `describe`: 故事描述(暂时没有用到)
- `content`: 具体故事内容
    - `key`: 固定触发的故事回合
    - `value`: 对应的故事内容
    - `{player_name}`: 用来填充玩家名


## 关于模型

- 模型原型： [OPENAI GPT-2](https://openai.com/blog/better-language-models/)
- 数据源： [nlp_chinese_corpus](https://github.com/brightmart/nlp_chinese_corpus) + 部分网络免费公开的小说
- 训练代码： https://github.com/mymusise/gpt2-quickly


### 声明

项目用到的数据均来源网络，本项目未进行任何商业目的。本项目遵从[GPL协议](LICENSE)，引用请注明出处。