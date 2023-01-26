
# TODO: make buzz purple, fix image clipping, add error catching and logging, make more functions
from PIL import Image, ImageFont, ImageDraw, ImageOps
import logging
import requests
import feedparser
from secret_api_keys import smmry_key, openai_key
import textwrap
from bs4 import BeautifulSoup 
import openai

openai.api_key = openai_key

INSTAGRAM_PORTRAIT_DIM = (1080, 1350)
REELS_TIKTOK_DIM = (1080, 1920)
TWITTER_DIM = (1600, 900)
FACEBOOK_TIMELINE_DIM = (820, 312)
SQUARE_DIM = (1080, 1080)

DI_ORANGE = "#ff6400"

LINE_HEIGHT = 4

logging.basicConfig(filename="logs.txt", level=logging.DEBUG, format="%(asctime)s %(message)s")

NewsFeed = feedparser.parse("http://dailyillini.com/feed")

# NewsFeed = feedparser.parse("http://dailyillini.com/feed/?paged=6")

def generate_image(canvas_size, headline, byline, category, summary, image_link):
    category = category.upper()
    # gibby
    gibson_headline = ImageFont.truetype(font="design_resources\gibson_font\Gibson SemiBold.ttf", size=72)
    gibson_byline = ImageFont.truetype(font="design_resources\gibson_font\Gibson Medium.ttf", size=32)
    gibson_cat = ImageFont.truetype(font="design_resources\gibson_font\Gibson SemiBold.ttf", size=50)

    calluna_rg = ImageFont.truetype(font="design_resources\calluna_font\Calluna Regular.ttf", size=32)

    canvas = Image.new(mode='RGB', size=canvas_size, color='#000000')
    draw = ImageDraw.Draw(im=canvas)

    wrapped_headline = "\n".join(textwrap.wrap(headline, width=25))
    wrapped_summary = "\n".join(textwrap.wrap(summary, width=70))

    wrapped_headline_lines = wrapped_headline.count("\n") + 1
    wrapped_summary_lines = wrapped_summary.count("\n") + 1

    running_anchor = [50,50]

    draw.text(xy= tuple(running_anchor), text=category, font = gibson_cat, fill=DI_ORANGE, anchor='la',)

    running_anchor[1] += gibson_cat.size + LINE_HEIGHT

    draw.multiline_text(xy=tuple(running_anchor), text=wrapped_headline, font=gibson_headline, fill='white', anchor='la', align="left")

    running_anchor[1] += (wrapped_headline_lines * gibson_headline.size) + (5 * LINE_HEIGHT)

    draw.text(xy= tuple(running_anchor), text=byline, anchor='la', font = gibson_byline, fill=DI_ORANGE)

    running_anchor[1] += gibson_byline.size + (5 * LINE_HEIGHT)

    draw.multiline_text(xy=tuple(running_anchor), text=wrapped_summary, font=calluna_rg, fill='white', anchor='la', align="left")

    running_anchor[1] += (wrapped_summary_lines * calluna_rg.size) + (15 * LINE_HEIGHT)

    image = Image.open(requests.get(image_link, stream=True).raw)

    param = max(canvas_size[0], canvas_size[1] - running_anchor[1])
    image = ImageOps.contain(image, (param, param), Image.BICUBIC)

    canvas.paste(image, box=(0, running_anchor[1]))

    # canvas.show()
    canvas.save(f"samples/{headline[:3]}{byline[:5]}.png")


for entry in NewsFeed.entries:
    img_link = "https://dailyillini.com/wp-content/uploads/2022/10/apply-ad-300x300.png"

    tree = BeautifulSoup(entry["summary"], features="html.parser").find_all('img')
    if len(tree) > 0:
        img_link = tree[0]["src"]
        print(img_link)

    content = entry["content"]
    summary = "To read this story, and many others like it, visit dailyillini.com."
    print(entry["title"])
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
    except:
        print('error')


    generate_image(INSTAGRAM_PORTRAIT_DIM, entry["title"], entry["author"], entry["tags"][0]["term"], summary.strip(), img_link)

