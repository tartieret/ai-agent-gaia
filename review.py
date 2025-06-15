"""Explore the results of the agent"""

import argparse
import json
import os

from evaluation import Answer, print_scores


def load_answers(filepath: str) -> list[Answer]:
    with open(os.path.join("data", "answers", filepath)) as f:
        answers_dict = json.load(f)
        return [Answer(**answer) for answer in answers_dict]


def print_wrong_answers(answers: list[Answer], level: int | None = None) -> None:
    print("*" * 30 + "Wrong Answers" + "*" * 30)
    for answer in answers:
        if answer.score == 0:
            if level is not None and answer.level != level:
                continue
            print("\n" + "-" * 30 + f"Question {answer.task_id}" + "-" * 30 + "\n")
            answer.pprint()


if __name__ == "__main__":
    # take the name of a answer file as argument

    parser = argparse.ArgumentParser()
    parser.add_argument("answer_file", type=str, help="Name of the answer file")

    # option to print the wrong answers or not, default to True
    parser.add_argument(
        "--no-print-wrong",
        action="store_true",
        help="Do not print wrong answers (default: print them)",
    )

    # filter by level
    parser.add_argument(
        "--level",
        choices=[1, 2, 3],
        default=None,
        type=int,
        help="Optional: Level of the questions to run. Runs all if not specified.",
    )

    args = parser.parse_args()
    answers = load_answers(args.answer_file)

    print_scores(answers)
    if not args.no_print_wrong:
        print_wrong_answers(answers, args.level)
