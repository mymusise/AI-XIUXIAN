import os
from model.game import GameController, GAME_SCRIPTS
from model.text_generator import text_generator, TextGenerator, ExpandToken


def play():
    scripts = [{"id": k, "name": v['name'], "describe": v['describe']}
                  for k, v in GAME_SCRIPTS.items()]
    script_id = None
    while not script_id:
        print("选择一个故事开端：")
        for script in scripts:
            print(f"{script['id']}: {script['name']}")
        script_id = input(f"[{scripts[0]['id']}-{scripts[-1]['id']}]: ")
        if not script_id.isnumeric() or int(script_id) not in GAME_SCRIPTS:
            print("请选择正确的数字")

    history = []
    step = 1
    name = input(f"请输入你的名字：")
    game = GameController(name, step, script_id)
    init_text = game.get_given_steps(0)
    print(init_text)
    history.append(init_text)
    current_text = input("输入要执行的内容： >")
    while 1:
        current_text = game.wrap_text(current_text, text_type=ExpandToken.DO)
        history.append(current_text)
        given_text = game.get_given_steps(step)
        if given_text:
            add_scene = False
        else:
            add_scene = True
        generator = TextGenerator(history, game.scene)
        next_text = generator.gen_next(game.clean_warp(
                current_text), ExpandToken.DO, game.player, add_scene)
        print(f"| {next_text}")
        history.append(next_text)
        current_text = input("输入要执行的内容：")
        step += 1
        game.step = step


if __name__ == "__main__":
    play()
