from json import detect_encoding
import json
import os
import random
import re
import subprocess
from sys import argv
from time import time
from bs4 import BeautifulSoup
from nltk import pos_tag, word_tokenize
from nltk.chunk import RegexpParser
import requests


def launch_text_editor():
    """
    Launches a URWID CLI-based text editor located at the given file path.

    :param file_path: The path to the Python file containing the text editor.
    """
    subprocess.run(["python", "text_editor_cli.py"])


def query_wolfram_alpha(query_input: str) -> (str):
    """
    Query the wolfram alpha api and return the response. Currently just prints the response to stdout and runs as main.

    :param query: The query to use. ("This is a query")
    :return: The response from the api.
    """
    api_key = os.getenv("WOLFRAM_API_KEY")
    query = query_input.replace(" ", "+")
    response = f"http://api.wolframalpha.com/v2/query?input={query}&appid={api_key}"

    print(response)


def remove_references(text: str) -> (str):
    """
    Remove citation references from wikipedia article text by removing text between square brackets and the square brackets themselves.

    :param text: The text to remove references from.
    """
    # Remove the square brackets and numbers inside them
    text = re.sub(r'\[\d+\]', '', text)
    return text


def parse_wikipedia_article(response: requests.Response) -> (str, str):
    """
    Parse http response for a wikipedia article.

    :param response: The http response to parse.
    :returns: The title and content of the wikipedia article.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    page_title = soup.find('title').text
    page_content = soup.find('div', {'id': 'mw-content-text'}).text
    return page_title, page_content


def wikipedia_get_random_article() -> None:
    # run loop to get random wikipedia articles and save to txt files
    while True:
        response = requests.get(url="https://en.wikipedia.org/wiki/Special:Random")
        page_title, page_content = parse_wikipedia_article(response)
        
        # check if the text is English
        try:
            if detect_encoding(page_content) != 'en':
                print(f"Skipping non-English article: {page_title}")
                continue
        except Exception as e:
            print(f"Skipping article due to error during language detection: {page_title}. Error: {str(e)}")
            time.sleep(random.randint(1, 12))
            continue

        # Remove citation references [*]
        page_content = remove_references(page_content)

        with open(f"wikipedia_{page_title}.txt", "x") as f:
            f.write(page_content)
        
        # wait between 1 to 5 seconds before next request to respect Wikipedia's server
        time.sleep(random.randint(1,12))


def wikipedia_get_search_article(search_query: str) -> None:
    """
    Search Wikipedia for the query and get the first result's title and content.

    :param query: The query to search Wikipedia for.
    :returns: A .txt file containing the article content saved to agent directory.
    """
    response = requests.get(url="https://en.wikipedia.org/wiki/...search...")
    page_title, page_content = parse_wikipedia_article(response)
    
    # check if the text is English
    try:
        if detect_encoding(page_content) != 'en':
            print(f"Skipping non-English article: {page_title}")
            return
    except Exception as e:
        print(f"Skipping article due to error during language detection: {page_title}. Error: {str(e)}")
        return
        
    # Remove citation references [*]
    page_content = remove_references(page_content)

    with open(f"wikipedia_{page_title}.txt", "x") as f:
        f.write(page_content)


def o_wikipedia_get_search_article(query: str) -> None:
    """
    A slightly beefier version of wikipedia_get_search_article() that also saves the article content to a file.

    :param query: The query to search Wikipedia for.
    :returns: A .txt file containing the article content saved to agent directory.
    """
    # Search Wikipedia for the query and get the first result's title
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
    search_response = requests.get(search_url).json()
    search_results = search_response.get('query', {}).get('search', [])
    if not search_results:
        print(f"No results found for {query}")
        return

    page_title = search_results[0]['title']

    # Fetch the article content
    page_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the main text content
    content = soup.find('div', {'class': 'mw-parser-output'})
    page_content = content.get_text() if content else ""

    # Optional: language detection and removing references can be implemented here
    
    # Save the content to a file
    with open(f"wikipedia_{page_title.replace('/', '_')}.txt", "w") as f:
        f.write(page_content)

    print(f"Article '{page_title}' saved to file.")


def analyze_sentence(sentence):
    """
    Analyzes a sentence to identify parts of speech and basic noun phrase structure.
    
    :param sentence: (str) A sentence to be analyzed.
    
    :returns output: (dict) A dictionary containing POS tags and a basic parse tree.
    """
    # Tokenize and POS tag
    tokens = word_tokenize(sentence)
    pos_tags = pos_tag(tokens)

    # Simple parser for noun phrases
    parser = RegexpParser("NP: {<DT>?<JJ>*<NN>}")
    result = parser.parse(pos_tags)

    # Prepare the output
    output_frame = {
        'pos_tags': pos_tags,
        'parse_tree': result
    }
    
    output = json.dumps(output_frame, indent=4)

    print(f"Output: {output}")

    return output