"""Run the agent on specific questions.

To use it:

python evaluate.py <task_id>

Where <task_id> is the ID of the task to run. Runs all if not specified.

"""

import argparse

from agent import Agent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate agent on specified questions."
    )
    # add an option to either load the validation or test dataset
    parser.add_argument(
        "--dataset",
        choices=["validation", "test"],
        default="validation",
        help="Dataset to use for evaluation. Defaults to 'validation'.",
    )
    # option to only load questions for level 1, 2, or 3. Default to all
    parser.add_argument(
        "--level",
        choices=[1, 2, 3],
        default=None,
        type=int,
        help="Optional: Level of the questions to run. Runs all if not specified.",
    )
    parser.add_argument(
        "task_id",
        nargs="?",
        default=None,
        help="Optional: ID of the task to run. Runs all if not specified.",
    )
    # optional argument to save the answers, default to True
    parser.add_argument(
        "--nosave", action="store_true", help="If set, do not save results"
    )
    args = parser.parse_args()

    # answers = evaluate_agent(args.dataset, args.level, args.task_id, debug=True)
    # if not args.nosave:
    #     save_answers(answers, args.dataset, args.level, args.task_id)
    from agent import Agent

    question = "I read a paper about multiwavelength observations of fast radio bursts back in March 2021 on Arxiv, and it had a fascinating diagram of an X-ray time profile. There was a similar burst-1 diagram in another paper from one of the same authors about fast radio bursts back in July 2020, but I can't recall what the difference in seconds in the measured time span was. How many more seconds did one measure than the other? Just give the number."
    agent = Agent(debug=True)
    print(agent(question))
