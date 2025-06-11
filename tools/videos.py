import logging
import os
import re
from typing import Optional

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from yt_dlp import YoutubeDL
from openai import OpenAI
import requests

logger = logging.getLogger(__name__)


def get_youtube_video_id(url: str) -> Optional[str]:
    """Extracts the video ID from a YouTube URL."""

    patterns = [
        r"(?:v=|youtu.be/|embed/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_transcript(youtube_url: str) -> Optional[str]:
    """Retrieve transcript from YouTube video if available."""
    video_id = get_youtube_video_id(youtube_url)
    if not video_id:
        return None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        print(f"YouTube transcript error: {e}")
        return None


def transcribe_video_with_whisper(
    video_path_or_url: str, api_key: Optional[str] = None
) -> Optional[str]:
    """Transcribe video using OpenAI Whisper API."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if video_path_or_url.startswith("http://") or video_path_or_url.startswith(
        "https://"
    ):
        # Download video to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            response = requests.get(video_path_or_url)
            tmp.write(response.content)
            tmp_path = tmp.name
        file_path = tmp_path
    else:
        file_path = video_path_or_url
    try:
        with open(file_path, "rb") as f:
            client = OpenAI(api_key=api_key)
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe", file=f
            )
        return transcript.text if hasattr(transcript, "text") else transcript["text"]
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None
    finally:
        if video_path_or_url.startswith("http") and os.path.exists(file_path):
            os.remove(file_path)


def download_youtube_video(url: str) -> str:
    """Download youtube video

    Args:
        url (str): URL to the youtube video

    Returns:
        str: Path to the downloaded video

    """
    print(f"Downloading video from {url}...")
    ydl_opts = {
        "format": "bestaudio/best",  # choose best available audio
        "outtmpl": "%(id)s.%(ext)s",  # output filename template
        "postprocessors": [  # convert to MP3 after download
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # 0 = best
            }
        ],
        "quiet": True,  # suppress verbose CLI output
        "paths": {"home": "data"},
        # "progress_hooks": [my_hook],      # optional: see § Progress hooks
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
        print("Saved to:", filepath)
        return filepath


def get_transcript(
    video_file_path: Optional[str] = None, video_url: Optional[str] = None
) -> str:
    """Obtain a transcript from a video file or URL.

    Args:
        video_file_path (Optional[str], optional): Path to a video file.
        video_url (Optional[str], optional): URL to a video.

    Raises:
        ValueError: If neither video_file_path nor video_url is provided.

    Returns:
        str: The transcript of the video.
    """
    if not video_file_path and not video_url:
        raise ValueError("Either video_file_path or video_url must be provided.")
    transcript = None

    if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
        print(f"Fetching transcript from YouTube URL: {video_url}")
        transcript = get_youtube_transcript(video_url)
        if transcript is None:
            # revert to downloading the video
            video_file_path = download_youtube_video(video_url)
            video_url = None

    path_or_url = video_file_path or video_url
    print(f"Transcribing video: {path_or_url}")
    transcript = transcribe_video_with_whisper(path_or_url)
    if transcript is None:
        return "Failed to transcribe video with Whisper."

    return transcript


@tool
def analyze_video(
    prompt: str,
    video_file_path: Optional[str] = None,
    video_url: Optional[str] = None,
) -> str:
    """
    Analyze a video file or URL. For YouTube URLs, retrieves the transcript if available. For other videos, uses OpenAI Whisper to transcribe. Then passes the transcript and prompt to GPT-4o to answer the query.

    Args:
        prompt (str): The question to answer about the video.
        video_file_path (Optional[str]): Local path to a video file.
        video_url (Optional[str]): URL to a video (YouTube or direct link).

    Returns:
        str: The analysis result or error message.


    """
    try:
        transcript = get_transcript(video_file_path, video_url)
        logger.info(f"Transcript: {transcript}")
        if transcript is None:
            return "Failed to obtain a transcript of the video."
        # Use GPT-4o to answer the prompt about the transcript
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        response = llm.invoke(
            [
                (
                    "human",
                    [
                        {"type": "text", "text": prompt},
                        {"type": "text", "text": transcript},
                    ],
                )
            ]
        )
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"Error analyzing video: {e}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # transcript = get_transcript(video_url="https://www.youtube.com/watch?v=L1vXCYZAYYM")
    # print(transcript)

    video_url = "https://www.youtube.com/watch?v=L1vXCYZAYYM"
    prompt = "What is the main topic of the video?"
    print(analyze_video.invoke({"prompt": prompt, "video_url": video_url}))
