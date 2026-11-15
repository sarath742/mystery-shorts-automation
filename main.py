
import os
import re
import asyncio
import requests
import subprocess
from pathlib import Path
from google import genai
import edge_tts

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()

client = genai.Client(api_key=GEMINI_API_KEY)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)


def generate_script():

    prompt = """
    Create a 45-second mysterious YouTube Shorts story.

    Requirements:
    - Powerful opening hook.
    - Suspenseful storytelling.
    - Simple English.
    - Include [Visual: description] for scenes.
    - End with a surprising question.
    - Use historically accurate information.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text


def download_video():

    url = "https://pixabay.com/api/videos/"

    params = {
        "key": PIXABAY_API_KEY,
        "q": "mystery dark",
        "per_page": 5
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not data.get("hits"):
        raise Exception("No videos found")

    video_url = data["hits"][0]["videos"]["medium"]["url"]

    video = requests.get(video_url, timeout=120)
    video.raise_for_status()

    with open(OUTPUT / "background.mp4", "wb") as file:
        file.write(video.content)

    print("Video downloaded!")



async def generate_voice(script):

    # Remove visual instructions
    narration = re.sub(
        r"\[Visual:.*?\]",
        "",
        script,
        flags=re.IGNORECASE
    )

    # Remove title, duration and voiceover labels
    narration = re.sub(
        r"\*\*.*?\*\*",
        "",
        narration
    )

    narration = re.sub(r"---", "", narration)
    narration = re.sub(r"\s+", " ", narration).strip()

    voices = [
        "en-IN-PrabhatNeural",
        "en-US-GuyNeural",
        "en-GB-RyanNeural"
    ]

    for voice in voices:
        try:
            print(f"Trying AI voice: {voice}")

            communicate = edge_tts.Communicate(
                narration,
                voice=voice,
                rate="+0%"
            )

            output_file = OUTPUT / "narration.mp3"

            await communicate.save(str(output_file))

            if output_file.exists() and output_file.stat().st_size > 1000:
                print(f"AI voice generated using {voice}!")
                return

        except Exception as error:
            print(f"Voice failed: {voice}: {error}")

    raise Exception("All AI voice options failed")



def create_video():

    background = str(OUTPUT / "background.mp4")
    narration = str(OUTPUT / "narration.mp3")
    final_video = str(OUTPUT / "final_short.mp4")

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", background,
        "-i", narration,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        final_video
    ]

    subprocess.run(command, check=True)

    print("FINAL VIDEO CREATED:", final_video)


if __name__ == "__main__":

    print("Generating script...")

    script = generate_script()

    with open("output_script.txt", "w", encoding="utf-8") as file:
        file.write(script)

    print(script)

    print("Downloading footage...")
    download_video()

    print("Generating AI voice...")
    asyncio.run(generate_voice(script))

    print("Creating final YouTube Short...")
    create_video()

    print("AUTOMATION COMPLETED!")
