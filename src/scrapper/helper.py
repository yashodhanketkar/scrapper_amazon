import requests
from bs4 import BeautifulSoup

from .constants import HEADERS


def make_csv_safe(raw_string: str) -> str:
    clean_string = " ".join(raw_string.strip().split())
    csv_safe_string = clean_string.replace("\n", " ").replace(",", "")
    return csv_safe_string


def get_soup(url: str) -> BeautifulSoup:
    webpage = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "lxml")
    return soup
