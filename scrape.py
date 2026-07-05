import requests
import os
from dotenv import load_dotenv
from slugify import slugify
from markdownify import markdownify


load_dotenv()

# DOMAIN = os.getenv("ZENDESK_API_URL")
DOMAIN = 'https://support.optisigns.com'

def getAllArticles():
    url = f"{DOMAIN}/api/v2/help_center/en-us/articles.json"
    articles = []
    while url:

        response = requests.get(url).json()

        articles.extend(response["articles"])

        url = response["next_page"]

    return articles


def getArticlesPage(page=1,per_page=30):  
    url = f"{DOMAIN}/api/v2/help_center/en-us/articles.json?page={page}&per_page={per_page}"
    articles = []
    response = requests.get(url).json()
    articles.extend(response["articles"])
    print(len(articles))
    return articles

def getArticle(article_id):
    url = f"{DOMAIN}/api/v2/help_center/en-us/articles/{article_id}"
    article = response = requests.get(url).json()
    return article['article']


def saveArticle(article, dir='articles'):
    os.makedirs(dir, exist_ok=True)
    md_content = markdownify(article["body"])
    slug = slugify(article["title"])
    filename = f"{dir}/{slug}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {article['title']}\n\n")
        f.write(f"**Original URL:** {article['html_url']}\n\n")
        f.write(md_content)
    print(f'Saved file: {filename}')


def getDemoArticles():
    articles = getArticlesPage()
    # the article about how to add a YouTube video
    articles.append(getArticle('360051014713'))

    return articles






