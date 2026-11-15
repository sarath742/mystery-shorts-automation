
import os
import requests
from pathlib import Path
from google import genai

# API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_script():

    prompt = """
    Create a 45-second YouTube Shorts mystery story.

    Requirements:
    - Powerful opening hook.
    - Interesting and suspenseful.
    - Simple English.
    - Include visual scene descriptions.
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
        raise Exception("No Pixabay videos found")

    video_url = data["hits"][0]["videos"]["medium"]["url"]

    print("Downloading video...")

    video = requests.get(video_url, timeout=120)
    video.raise_for_status()

    Path("output").mkdir(exist_ok=True)

    with open("output/background.mp4", "wb") as file:
        file.write(video.content)

    print("Video downloaded successfully!")


if __name__ == "__main__":

    print("Generating mystery script...")

    script = generate_script()

    print("\nGENERATED SCRIPT:\n")
    print(script)

    with open("output_script.txt", "w", encoding="utf-8") as file:
        file.write(script)

    print("\nSearching Pixabay footage...")

    download_video()

    print("\nAutomation step completed!")
