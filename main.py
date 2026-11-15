
import os
import re
import asyncio
import requests
import subprocess
from pathlib import Path
from google import genai
import edge_tts
import time


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
    - Include [Visual: description] for every scene.
    - End with a surprising question.
    - Use historically accurate information.
    """

    for attempt in range(1, 4):
        try:
            print(f"Generating script. Attempt {attempt}/3")

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if response.text:
                return response.text

            raise Exception("Gemini returned an empty response")

        except Exception as error:
            print(f"Gemini error: {error}")

            if attempt == 3:
                raise

            time.sleep(20)



def download_scene_images(script):

    # Get scene descriptions from the Gemini story
    scenes = re.findall(
        r"\[Visual:\s*(.*?)\]",
        script,
        flags=re.IGNORECASE
    )

    if not scenes:
        scenes = [
            "mysterious island at night cartoon illustration",
            "dark lighthouse in fog cartoon illustration",
            "mysterious abandoned building cartoon illustration"
        ]

    image_files = []

    for index, scene in enumerate(scenes):

        print(f"Finding cartoon image for scene {index + 1}: {scene}")

        url = "https://pixabay.com/api/"

        params = {
            "key": PIXABAY_API_KEY,
            "q": " ".join(re.findall(r"[a-zA-Z0-9]+", scene)[:8]),
            "image_type": "illustration",
            "safesearch": "true",
            "per_page": 10
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data.get("hits"):
            raise Exception(f"No cartoon images found for: {scene}")

        image_url = data["hits"][0]["largeImageURL"]

        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()

        image_path = OUTPUT / f"scene_{index + 1:02d}.jpg"

        with open(image_path, "wb") as file:
            file.write(image_response.content)

        image_files.append(image_path)

        print(f"Scene {index + 1} image downloaded!")

    return image_files




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



def create_video(image_files):
def create_video(image_files):

    narration = str(OUTPUT / "narration.mp3")
    final_video = str(OUTPUT / "final_short.mp4")

    if not image_files:
        raise Exception("No scene images available!")

    for image in image_files:
        if not Path(image).exists():
            raise Exception(f"Missing image: {image}")

    # Get narration duration
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            narration
        ],
        capture_output=True,
        text=True,
        check=True
    )

    total_duration = float(result.stdout.strip())
    scene_duration = total_duration / len(image_files)

    command = ["ffmpeg", "-y"]

    # Load every image as a video input
    for image in image_files:
        command.extend([
            "-loop", "1",
            "-framerate", "30",
            "-t", str(scene_duration),
            "-i", str(image)
        ])

    # Add narration
    command.extend(["-i", narration])

    # Build video filter
    filters = []

    for i in range(len(image_files)):
        filters.append(
            f"[{i}:v]scale=1080:1920:"
            f"force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,"
            f"format=yuv420p[v{i}]"
        )

    inputs = "".join(
        f"[v{i}]" for i in range(len(image_files))
    )

    filters.append(
        f"{inputs}concat=n={len(image_files)}:v=1:a=0[outv]"
    )

    filter_complex = ";".join(filters)

    command.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{len(image_files)}:a:0",
        "-t", str(total_duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        final_video
    ])

    subprocess.run(command, check=True)

    print("CARTOON VIDEO CREATED:", final_video)




if __name__ == "__main__":

    print("Generating script...")

    script = generate_script()

    with open("output_script.txt", "w", encoding="utf-8") as file:
        file.write(script)

    print(script)

    print("Downloading cartoon scene images...")
    image_files = download_scene_images(script)

    print("Generating AI voice...")
    asyncio.run(generate_voice(script))

    print("Creating final YouTube Short...")
    create_video(image_files)

    print("AUTOMATION COMPLETED!")
