import os
import gradio as gr
import requests
import pandas as pd

# (Keep Constants as is)
# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"
API_URL = DEFAULT_API_URL
QUESTION_URL = f"{API_URL}/questions"
SUBMIT_URL = f"{API_URL}/submit"


def get_questions():
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
