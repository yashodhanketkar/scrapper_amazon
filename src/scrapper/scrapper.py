import csv
import warnings
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup

from .constants import BASE_URL_PREFIX, URL
from .element_scrapper import (
    get_asin,
    get_description,
    get_manufacturer,
    get_price,
    get_product_description,
    get_ratings,
    get_reviews,
    get_title,
    get_url,
)
from .helper import get_soup


warnings.filterwarnings("ignore", category=UserWarning, module="bs4")


def get_main_items(base_url: str = "", base_url_prefix: str = ""):
    soup = get_soup(base_url)

    items: List[BeautifulSoup] = soup.find_all("div", attrs={"data-component-type": "s-search-result"})
    items_list = []

    for item in items:
        item_list = []

        title = get_title(item)
        price = get_price(item)
        ratings = get_ratings(item)
        url = get_url(item, base_url_prefix)
        reviews = get_reviews(item)

        item_list = [
            url,
            title,
            price,
            ratings,
            reviews,
        ]
        item_list += get_secondary_items(base_url=url)

        items_list.append(item_list)
        if len(items_list) > 1:
            break

    next_page_url_attrs = {"class": "s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"}
    next_page_url = base_url_prefix + soup.find("a", attrs=next_page_url_attrs, href=True)["href"]
    return items_list, next_page_url


def get_secondary_items(base_url: str = ""):
    soup = get_soup(url=base_url)

    items = []

    items.append(get_description(soup))
    items.append(get_asin(soup))
    items.append(get_product_description(soup))
    items.append(get_manufacturer(soup))

    return items


def store_csv(items: list):
    path = "./out.csv"
    fields = [
        "Product URL",
        "Product Name",
        "Product Price",
        "Rating",
        "Number of reviews",
        "Description",
        "ASIN",
        "Product Description",
        "Manufacturer",
    ]

    has_header = False

    if Path(path).is_file():
        with open(file=path, mode="r", newline="", encoding="utf-8") as csv_file:
            has_header = csv_file.readlines() > 0

    with open(file=path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if not has_header:
            writer.writerow(fields)
        writer.writerows(items)


def scrap_amazon_listing(next_page_url: str, base_url_prefix: str, page_limit: int = 20):
    try:
        page = 0
        items_list, next_page_url = get_main_items(base_url=next_page_url, base_url_prefix=base_url_prefix)
        while True:
            print(page, next_page_url)
            page += 1
            if page > page_limit:
                break
            items_list, next_page_url = get_main_items(base_url=next_page_url, base_url_prefix=base_url_prefix)
            items_list += items_list

    except Exception:
        print("Ending scrapping operation")

    finally:
        return items_list


def store_amazon_srapping(page_limit: int = 20):
    items = scrap_amazon_listing(next_page_url=URL, base_url_prefix=BASE_URL_PREFIX, page_limit=page_limit)
    store_csv(items)


if __name__ == "__main__":
    raise SystemExit(0)
