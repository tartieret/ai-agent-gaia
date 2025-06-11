import logging
import os
import re
from typing import Optional
from datetime import timedelta
import textwrap

from langchain_core.tools import tool
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from yt_dlp import YoutubeDL
from openai import OpenAI
from openai.types.audio import TranscriptionSegment
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


def sec_to_srt_time(seconds: float) -> str:
    """4.32  →  00:00:04,320"""
    td = timedelta(seconds=seconds)
    hrs, rem = divmod(td.seconds, 3600)
    mins, secs = divmod(rem, 60)
    millis = td.microseconds // 1000
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def segments_to_srt(segments: list[TranscriptionSegment], line_length: int = 42) -> str:
    """segments = response.segments or result['segments']"""
    srt_lines = []
    for idx, seg in enumerate(segments, 1):
        start = sec_to_srt_time(seg.start)
        end = sec_to_srt_time(seg.end)
        # Optional: re‑wrap long sentences so players don’t shrink the font
        wrapped_text = "\n".join(
            textwrap.wrap(seg.text.strip(), width=line_length) or [seg.text.strip()]
        )
        srt_lines.append(f"{idx}\n{start} --> {end}\n{wrapped_text}\n")
    return "\n".join(srt_lines)


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
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
            srt_text = segments_to_srt(transcript.segments)
            return srt_text
            # return (
            #     transcript.text if hasattr(transcript, "text") else transcript["text"]
            # )
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        raise e
        return None
    finally:
        if video_path_or_url.startswith("http") and os.path.exists(file_path):
            os.remove(file_path)


def download_youtube_video(url: str) -> tuple[str, str]:
    """Download youtube video

    Args:
        url (str): URL to the youtube video

    Returns:
        tuple[str, str]: Path to the downloaded video and the video title

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
        title = info["title"]
        print("Saved to:", filepath)
        return filepath, title


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
    title = None

    if video_url and ("youtube.com" in video_url or "youtu.be" in video_url):
        print(f"Fetching transcript from YouTube URL: {video_url}")
        transcript = get_youtube_transcript(video_url)
        if transcript is None:
            # revert to downloading the video
            video_file_path, title = download_youtube_video(video_url)
            video_url = None

    path_or_url = video_file_path or video_url
    print(f"Transcribing video: {path_or_url}")
    transcript = transcribe_video_with_whisper(path_or_url)
    if transcript is None:
        return "Failed to transcribe video with Whisper."

    if title:
        return f"Title: {title}\n\nTranscript: {transcript}"

    return transcript


@tool
def get_video_transcript(
    # prompt: str,
    video_file_path: Optional[str] = None,
    video_url: Optional[str] = None,
) -> str:
    """
    Retrieves the transcript of a video file or URL.

    Args:
        video_file_path (Optional[str]): Local path to a video file.
        video_url (Optional[str]): URL to a video (YouTube or direct link).

    Returns:
        str: the video transcript


    """
    try:
        transcript = get_transcript(video_file_path, video_url)
        logger.info(f"Transcript: {transcript}")
        if transcript is None:
            return "Failed to obtain a transcript of the video."
        # Use GPT-4o to answer the prompt about the transcript
        # llm = ChatOpenAI(
        #     model="gpt-4o",
        #     temperature=0,
        #     api_key=os.getenv("OPENAI_API_KEY"),
        # )
        # response = llm.invoke(
        #     [
        #         (
        #             "human",
        #             [
        #                 {"type": "text", "text": prompt},
        #                 {"type": "text", "text": transcript},
        #             ],
        #         )
        #     ]
        # )
        # return response.content if hasattr(response, "content") else str(response)
        return transcript
    except Exception as e:
        print(f"Error analyzing video: {e}")
        raise e
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # transcript = get_transcript(video_url="https://www.youtube.com/watch?v=L1vXCYZAYYM")
    # print(transcript)

    # video_url = "https://www.youtube.com/watch?v=L1vXCYZAYYM"
    video_file_path = "data/L1vXCYZAYYM.mp3"
    print(get_video_transcript.invoke({"video_file_path": video_file_path}))
