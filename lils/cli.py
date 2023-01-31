import argparse

from lils.ink import InkScript


def show_output(script):
    # TODO: Add ritch text formatting (maybe md)
    for line in script.output:
        if line.reply:
            print(f"- {line}")
        else:
            line.run_command()
            print(line)


def show_options(script):
    for i, option in enumerate(script.options):
        # TODO: Add ritch text formatting (maybe md)
        print(f"{i+1}. {option.option}")

    # TODO: Add listeners logic
    selected = input("> ")
    try:
        selected = int(selected)
    except ValueError:
        print(f"No valid option '{selected}'. Please write a correct option number")
        show_options(script)
        return

    if selected > len(script.options) or selected < 1:
        print(f"No valid option '{selected}'. Please write a correct option number")
        show_options(script)
        return

    script.choose(selected - 1)


def run(path):
    script = InkScript(path)
    script.run()

    while not script.finished:
        if script.output:
            show_output(script)
        if script.options:
            show_options(script)

    show_output(script)


def main():
    parser = argparse.ArgumentParser(
        prog="lils",
        description="Linux Immersive Learning System",
    )
    parser.add_argument("script")
    args = parser.parse_args()

    run(args.script)
