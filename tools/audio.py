import base64
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


@tool
def analyze_audio(prompt: str, audio_file_path: str) -> str:
    """Analyzes an audio file using the provided prompt

    Args:
        prompt (str): The question to answer about the audio
        audio_file_path (str): The path to the audio file to analyze

    Returns:
        str: The analysis result.
    """
    if not os.path.exists(audio_file_path):
        raise ValueError(f"Audio file {audio_file_path} does not exist")

    with open(audio_file_path, "rb") as f:
        # b64 encode it
        audio = f.read()
        audio_b64 = base64.b64encode(audio).decode()

    format = os.path.splitext(audio_file_path)[1].strip(".")

    llm = ChatOpenAI(
        model="gpt-4o-audio-preview",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    output_message = llm.invoke(
        [
            (
                "human",
                [
                    {"type": "text", "text": prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_b64, "format": format},
                    },
                ],
            ),
        ]
    )
    return output_message.content


if __name__ == "__main__":
    audio_file_path = "data/99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3"
    prompt = input(f"Enter a question about {audio_file_path}: ")
    print(analyze_audio.invoke({"prompt": prompt, "audio_file_path": audio_file_path}))
