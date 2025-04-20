from typing import List

import requests
from termcolor import colored


def search_for_stock_videos(tags: list, api_key_value: str) -> List[str]:
    """
    Searches for stock videos based on a query.

    """

    # Build headers
    headers = {
        "Authorization": api_key_value
    }

    video_links = []

    for tag in tags:

        # Build URL
        url = f"https://api.pexels.com/videos/search?query={tag}&per_page=1"

        # Send the request
        r = requests.get(url, headers=headers, timeout=10)

        # Parse the response
        response = r.json()

        # Get first video url
        video_urls = []
        video_url = ""
        try:
            video_urls = response["videos"][0]["video_files"]
            # print(video_urls)
        except KeyError:
            print(colored("[-] No Videos found.", "red"))
            print(colored(response, "red"))

        # Loop through video urls
        for video in video_urls:
            # Check if video has a download link
            if ".com/external" in video["link"]:
                # Set video url
                video_url = video["link"]
                # print(
                #     f"{video_url} | {video['quality']} | "
                #     f"{video['width']}/{video['height']}"
                # )

        # Let user know
        if video_url:
            print(colored(f"\t=> {video_url}", "cyan"))
            video_links.append(video_url)
        else:
            print(
                colored(f"\t=> No valid video found for tag: {tag}", "yellow")
            )

    return video_links


if __name__ == "__main__":
    pass  # Add meaningful code here if needed
    # Remove or comment out the following block:
    # search_tags = [
    #     "how to make money online videos",
    #     ...
    # ]
    # api_key = "your_api_key_here"
    # links = search_for_stock_videos(search_tags, api_key)
    # print(links)
