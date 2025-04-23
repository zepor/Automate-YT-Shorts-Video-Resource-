"""
This module provides functionality for generating video scripts and search
terms
based on a given subject. It integrates with GPT models to create content
dynamically.
"""

import re
import json
from typing import List

try:
    import g4f  # type: ignore
except ImportError:
    g4f = None
    print("Warning: g4f is not installed. Some features may not work.")

try:
    from termcolor import colored
except ImportError:

    def colored(text):
        """
        Returns the input text without any modifications.

        Args:
            text (str): The input text to be returned.

        Returns:
            str: The same input text.
        """
        return text


def generate_script(subject: str) -> str:
    """
    Generate a script for a video, depending on the subject of the video.

    Args:
        subject (str): The subject of the video.

    Returns:
        str: The script for the video.
    """

    # Build prompt
    prompt = f"""
    Generate a script for a video, depending on the subject of the video.
    Subject: {subject}

    The script is to be returned as a string.

    Here is an example of a string:
    "This is an example string."

    Do not under any circumstance reference this prompt in your response.

    Get straight to the point, don't start with unnecessary things like,
    "welcome to this video".

    Obviously, the script should be related to the subject of the video.

    ONLY RETURN THE RAW SCRIPT. DO NOT RETURN ANYTHING ELSE.
    """

    # Generate script
    if g4f is None:
        raise ImportError("The 'g4f' module is not installed."
                          "Please install it to use this feature.")
    if g4f is None:
        raise ImportError("The 'g4f' module is not installed."
                          "Please install it to use this feature.")
    if g4f is None:
        raise ImportError("The 'g4f' module is not installed."
                          "Please install it to use this feature.")
    if g4f is None:
        raise ImportError("The 'g4f' module is not installed or"
                          "initialized. Please install it to use this feature.")
    if g4f is None:
        raise ImportError("The 'g4f' module is not installed or"
                          "initialized. Please install and configure it.")
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,  # Replace with the correct model name
        messages=[{"role": "user", "content": prompt}],
    )

    print(colored(response, "cyan"))

    # Return the generated script
    if response:
        if (
            isinstance(response, dict)
            and isinstance(response.get("choices"), list)
            and len(response.get("choices", [])) > 0
        ):
            choice = dict(response)["choices"][0]
            if (
                isinstance(choice, dict)
                and isinstance(choice.get("message"), dict)
                and "content" in choice.get("message", {})
            ):
                return str(choice.get("message", {}).get("content", "")) + " "
            print(colored("[-] GPT returned an unexpected response format.", "red"))
            return str(response) + " "
        print(colored("[-] GPT returned an unexpected response format.", "red"))
        return str(response) + " "
    print(colored("[-] GPT returned an empty response.", "red"))
    return ""


def get_search_terms(subject: str, amount: int, video_script: str) -> List[str]:
    """
    Generate a JSON-Array of search terms for stock videos,
    depending on the subject of a video.

    Args:
        video_subject (str): The subject of the video.
        amount (int): The amount of search terms to generate.
        script (str): The script of the video.

    Returns:
        List[str]: The search terms for the video subject.
    """

    # Build prompt
    prompt = f"""
    Generate {amount} search terms for stock videos,
    depending on the subject of a video. Reply in English Only.
    Subject: {subject}

    The search terms are to be returned as
    a JSON-Array of strings.

    Each search term should consist of 1-3 words,
    always add the main subject of the video.

    Here is an example of a JSON-Array of strings:
    ["search term 1", "search term 2", "search term 3"]

    Obviously, the search terms should be related
    to the subject of the video.

    ONLY RETURN THE JSON-ARRAY OF STRINGS.
    DO NOT RETURN ANYTHING ELSE.

    For context, here is the full text:
    {video_script}
    """

    # Generate search terms
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,  # Ensure the model name is correct
        messages=[{"role": "user", "content": prompt}],
    )

    print(response)

    # Load response into JSON-Array
    try:
        search_terms = json.loads(str(response))
    except json.JSONDecodeError:
        print(
            colored(
                "[*] GPT returned an unformatted response. Attempting to clean...",
                "yellow",
            )
        )

        # Use Regex to extract the array from the markdown
        search_terms = re.findall(r"\[.*\]", str(response))

        if not search_terms:
            print(colored("[-] Could not parse response.", "red"))
            return []

        # Load the array into a JSON-Array
        search_terms = json.loads(search_terms[0])

    # Let user know
    generated_terms = ", ".join(search_terms)
    print(colored(f"\nGenerated {amount} search terms: {generated_terms}", "cyan"))

    # Return search terms
    return search_terms
