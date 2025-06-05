import os
import json
import requests


# (Keep Constants as is)
# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
API_URL = DEFAULT_API_URL
QUESTION_URL = f"{API_URL}/questions"
FILE_BASE_URL = f"{API_URL}/files/"
SUBMIT_URL = f"{API_URL}/submit"

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")


def download_questions():
    """Fetches all questions from the API.

    Returns:
        list: List of questions.
    """
    print(f"Fetching questions from: {QUESTION_URL}")
    try:
        response = requests.get(QUESTION_URL, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching questions: {e}")
        return []
    except requests.exceptions.JSONDecodeError as e:
        print(f"Error decoding JSON response from questions endpoint: {e}")
        print(f"Response text: {response.text[:500]}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred fetching questions: {e}")
        return []


def download_file(task_id: str, filename: str):
    """
    Download a file from the API.

    Args:
        task_id (str): The ID of the task to download the file for.
        filename (str): The name of the file to download.
    """
    print(f"Downloading file {filename} for task ID: {task_id}")
    try:
        response = requests.get(f"{FILE_BASE_URL}{task_id}", timeout=15)
        response.raise_for_status()
        # save the content to DATA_FOLDER
        file_path = os.path.join(DATA_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file for task ID {task_id}: {e}")
        return None
    except Exception as e:
        print(
            f"An unexpected error occurred downloading file for task ID {task_id}: {e}"
        )
        return None


def build_answers_payload(results_log: list[dict]):
    """Generate the payload for submission on Hugging Face"""
    answers_payload = []
    for item in results_log:
        task_id = item.get("Task ID")
        submitted_answer = item.get("Submitted Answer")
        if task_id and submitted_answer:
            answers_payload.append(
                {"task_id": task_id, "submitted_answer": submitted_answer}
            )
    return answers_payload


def load_questions():
    with open(os.path.join(DATA_FOLDER, "questions.json"), "r") as f:
        return json.load(f)


if __name__ == "__main__":
    question_data = download_questions()

    # save the questions to disk
    with open(os.path.join(DATA_FOLDER, "questions.json"), "w") as f:
        json.dump(question_data, f, indent=4)

    # download all files
    for item in question_data:
        task_id = item.get("task_id")
        filename = item.get("file_name")
        if filename:
            download_file(task_id, filename)
