
import os
import requests
from google import genai

# API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_script():

    prompt = """
    Create a 45-second YouTube Shorts script.

    Topic: A mysterious unexplained event.

    Requirements:
    - Start with a powerful hook.
    - Make it interesting and suspenseful.
    - Use simple English.
    - End with a surprising question.
    - Return only the script.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text


def search_video():

    url = "https://pixabay.com/api/videos/"

    params = {
        "key": PIXABAY_API_KEY,
        "q": "mystery dark",
        "per_page": 5
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    if data["hits"]:
        video = data["hits"][0]["videos"]["medium"]["url"]
        return video

    return None


if __name__ == "__main__":

    print("Generating mystery script...")

    script = generate_script()

    print("\nGENERATED SCRIPT:\n")
    print(script)

    print("\nSearching Pixabay footage...")

    video_url = search_video()

    if video_url:
        print("\nVideo found:")
        print(video_url)
    else:
        print("No footage found.")
