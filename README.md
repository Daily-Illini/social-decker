# social-decker
This is a python script that generates images for the Daily Illini's social media feeds, using OpenAI to generate body copy.

## Dependencies
There are quite a few dependencies as of now, including
* Pillow, for python image generation
* requests, for simple HTTP requests
* feedparser, for getting RSS feeds
* BeautifulSoup, for getting images from raw HTML 
* openai for, well, AI
* Built-in libraries like logging and textwrap

You also need to ensure you've made a file in the same directory called `secret_api_keys.py` with the `openai_key` variable set.
