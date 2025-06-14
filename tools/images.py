import os
import requests
from PIL import Image
import io
import base64
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


def download_image(image_url: str) -> Image:
    response = requests.get(image_url)
    return Image.open(io.BytesIO(response.content))


def analyze_image_url(llm, image_url: str, prompt="What's in this image?") -> str:
    """Analyzes an image from a URL using the provided LLM.

    Args:
        llm (ChatOpenAI): The LLM to use for analysis.
        image_url (str): The URL of the image to analyze.
        prompt (str, optional): The prompt to use for analysis. Defaults to "What's in this image?".

    Returns:
        str: The analysis result.
    """
    response = llm.invoke(
        [
            (
                "human",
                [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source_type": "url",
                        "url": image_url,
                    },
                ],
            )
        ]
    )
    return response.text()


def analyze_image_file(llm, file_path: str, prompt="What's in this image?") -> str:
    """Analyzes an image from a file using the provided LLM.

    Args:
        llm (ChatOpenAI): The LLM to use for analysis.
        file_path (str): The path to the image file to analyze.
        prompt (str, optional): The prompt to use for analysis. Defaults to "What's in this image?".

    Returns:
        str: The analysis result.
    """
    img = Image.open(file_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    image_data = base64.b64encode(buffered.getvalue()).decode()
    response = llm.invoke(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source_type": "base64",
                        "data": image_data,
                        "mime_type": "image/jpeg",
                    },
                ],
            }
        ],
    )
    return response.text()


@tool
def analyze_image(
    prompt: str,
    file_path: str | None = None,
    image_url: str | None = None,
) -> str:
    """Ask questions about an image.

    Args:
        prompt (str): The question to answer about the image
        file_path (str | None, optional): The path to the image file to analyze. Defaults to None.
        image_url (str | None, optional): The URL of the image to analyze. Defaults to None.

    Returns:
        str: The analysis result.
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        if file_path:
            return analyze_image_file(llm, file_path, prompt)
        elif image_url:
            return analyze_image_url(llm, image_url, prompt)
        else:
            raise ValueError("Either file_path or image_url must be provided")
    except Exception as e:
        print(f"Error describing image: {e}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    image_url_or_file_path = input("Enter a image URL or file path: ")
    prompt = input("Enter a prompt: ")

    if os.path.exists(image_url_or_file_path):
        print(analyze_image(prompt=prompt, file_path=image_url_or_file_path))
    else:
        print(analyze_image(prompt=prompt, image_url=image_url_or_file_path))
