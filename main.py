
import os
import re
import asyncio
import requests
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

    # Remove visual instructions from narration
    narration = re.sub(
        r"\[Visual:.*?\]",
        "",
        script,
        flags=re.IGNORECASE
    )

    narration = re.sub(r"\s+", " ", narration).strip()

    communicate = edge_tts.Communicate(
        narration,
        voice="en-IN-PrabhatNeural",
        rate="+5%"
    )

    await communicate.save(str(OUTPUT / "narration.mp3"))

    print("AI voice generated!")


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

    print("All tasks completed!")
