"""Explore the results of the agent"""

import json
import os

from evaluation import Answer, print_scores


def load_answers(filepath: str) -> list[Answer]:
    with open(os.path.join("data", "answers", filepath)) as f:
        answers_dict = json.load(f)
        return [Answer(**answer) for answer in answers_dict]


def print_wrong_answers(answers: list[Answer]) -> None:
    print("*" * 30 + "Wrong Answers" + "*" * 30)
    for answer in answers:
        if answer.score == 0:
            answer.pprint()


if __name__ == "__main__":
    # take the name of a answer file as argument
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("answer_file", type=str, help="Name of the answer file")

    # option to print the wrong answers or not, default to True
    parser.add_argument(
        "--print-wrong", action="store_true", help="Print wrong answers"
    )

    args = parser.parse_args()
    answers = load_answers(args.answer_file)

    print_scores(answers)
    if args.print_wrong:
        print_wrong_answers(answers)
