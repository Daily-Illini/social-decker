
# TODO: make buzz purple, fix image clipping, add error catching and logging, make more functions
from PIL import Image, ImageFont, ImageDraw, ImageOps
import logging
import requests
import feedparser
from secret_api_keys import smmry_key, openai_key
import textwrap
from bs4 import BeautifulSoup 
import openai
logging.basicConfig(filename="logs.txt", level=logging.INFO)

FEED_LINK = "http://dailyillini.com/feed"
FEED_LINK_PAGED = "http://dailyillini.com/feed/?paged=1"

INSTAGRAM_PORTRAIT_DIM = (1080, 1350)
REELS_TIKTOK_DIM = (1080, 1920)
TWITTER_DIM = (1600, 900)
FACEBOOK_TIMELINE_DIM = (820, 312)
SQUARE_DIM = (1080, 1080)

DI_ORANGE = "#ff6400"
LINE_HEIGHT = 4
PADDING = 5

# Authenticate OpenAI API - documentation @ https://openai.com/api/
openai.api_key = openai_key

# Fetch recent stories, or fetch older stories via pagination
try:
    NewsFeed = feedparser.parse(FEED_LINK_PAGED)

except Exception as e:
    logging.critical(e)

# Function to generate an image of canvas_size
# canvas_size - (width, height) of the image to be generated, in pixels
# headline, byline, category - basic strings
# summary - a brief, 1-2 line summary of the story
# image_link - a direct link to the image, to be downloaded
def generate_image(canvas_size, headline, byline, category, summary, image_link):

    # First, define our fonts and their respenctive sizes
    gibson_headline = ImageFont.truetype(font="design_resources\gibson_font\Gibson SemiBold.ttf", size=72)
    gibson_byline = ImageFont.truetype(font="design_resources\gibson_font\Gibson Medium.ttf", size=32)
    gibson_cat = ImageFont.truetype(font="design_resources\gibson_font\Gibson SemiBold.ttf", size=50)
    calluna_rg = ImageFont.truetype(font="design_resources\calluna_font\Calluna Regular.ttf", size=32)

    # Create a new canvas based on canvas_size. Create a draw obj to interact with the canvas 
    canvas = Image.new(mode='RGB', size=canvas_size, color='#000000')
    draw = ImageDraw.Draw(im=canvas)

    # Wrap the text in case it's too long for one line, and store the line counts
    wrapped_headline = "\n".join(textwrap.wrap(headline, width=25))
    wrapped_summary = "\n".join(textwrap.wrap(summary, width=70))

    wrapped_headline_lines = wrapped_headline.count("\n") + 1
    wrapped_summary_lines = wrapped_summary.count("\n") + 1

    # Make the category text uppercase
    category = category.upper()

    # Now it's time for image generation. Let's create an anchor coordinate for our text. We'll increment the y-value every time we draw text, hence the name "running" anchor
    # Note: coordinates start in the top left of the image, so (10,65) would mean 10 pixels right, 65 pixels down. 
    running_anchor = [50,50]

    # Draw the category text. Increment the anchor's y-value
    draw.text(xy= tuple(running_anchor), text=category, font = gibson_cat, fill=DI_ORANGE, anchor='la',)
    running_anchor[1] += gibson_cat.size + LINE_HEIGHT

    # Draw the (wrapped) headline text. Increment the anchor's y-value, this time using the amount of lines we calculated earlier
    draw.multiline_text(xy=tuple(running_anchor), text=wrapped_headline, font=gibson_headline, fill='white', anchor='la', align="left")
    running_anchor[1] += (wrapped_headline_lines * gibson_headline.size) + (PADDING * LINE_HEIGHT)

    # And so on, this time for the byline
    draw.text(xy= tuple(running_anchor), text=byline, anchor='la', font = gibson_byline, fill=DI_ORANGE)
    running_anchor[1] += gibson_byline.size + (PADDING * LINE_HEIGHT)

    # ... and finally the body copy
    draw.multiline_text(xy=tuple(running_anchor), text=wrapped_summary, font=calluna_rg, fill='white', anchor='la', align="left")
    running_anchor[1] += (wrapped_summary_lines * calluna_rg.size) + ((PADDING * 3) * LINE_HEIGHT)

    # attempt to download the story's image from the link, if it exists.
    if (image_link is not None):
        try:
            image = Image.open(requests.get(image_link, stream=True).raw)
        except Exception as e:
            logging.critical(e)

        # Resize the image proportionally so it fits a bounding box, place image on  canvas
        param = max(canvas_size[0], canvas_size[1] - running_anchor[1])
        image = ImageOps.contain(image, (param, param), Image.BICUBIC)
        canvas.paste(image, box=(0, running_anchor[1]))

    # Show or save the resulting image
    # canvas.show()
    filename = f"samples/{canvas_size[0]}x{canvas_size[1]}{headline[:3]}{byline[:5]}.png"
    canvas.save(filename)
    logging.info(f"Image saved as {filename}")

# Driver code. Take every story and extract metadata/generate summaries, then pass to generate_image(...)
for entry in NewsFeed.entries:
    # Fallback image
    img_link = None

    # Parse the HTML extracted from the RSS feed and grab the first image's link
    try:
        tree = BeautifulSoup(entry["summary"], features="html.parser").find_all('img')
        if len(tree) > 0:
            img_link = tree[0]["src"]
            logging.info(f"Image successfully downloaded: {img_link}")
    except Exception as e:
        logging.warning(f"NO IMAGE! {e}")

    # Set some defaults
    content = entry["content"]
    summary = "To read this story, and many others like it, visit dailyillini.com."
    print(entry["title"])

    # Attempt to generate a summary of the story.
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{content}\n\n Write a 2 sentence maximum tl;dr of this newspaper article. Your audience is students at the University of Illinois. Always refer to the University as \"The University\" (not \"the university of Illinois\") and the student body as \"Illini\" when appropriate. Your response must follow AP style. Us proper punctuation, use complete sentences, and use contractions. Do not use passive voice in your response.",
            temperature=0.56,
            max_tokens=100,
            frequency_penalty=1.0,
            presence_penalty=1
        )
        summary = response["choices"][0]["text"]
        print(summary)
        logging.debug(response)
    except Exception as e:
        logging.critical(e)

    # generate_image(INSTAGRAM_PORTRAIT_DIM, entry["title"], entry["author"], entry["tags"][0]["term"], summary.strip(), img_link)

    generate_image(REELS_TIKTOK_DIM, entry["title"], entry["author"], entry["tags"][0]["term"], summary.strip(), img_link)
