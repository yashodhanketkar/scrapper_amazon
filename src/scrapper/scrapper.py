import csv
import re
import warnings
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

URL = "https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_1"
BASE_URL_PREFIX = "https://www.amazon.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Accept-Language": "en-US, en;q=0.5",
}


def make_csv_safe(raw_string: str):
    clean_string = " ".join(raw_string.strip().split())
    csv_safe_string = clean_string.replace("\n", " ").replace(",", "")
    return csv_safe_string


def get_soup(url: str) -> BeautifulSoup:
    webpage = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "lxml")
    return soup


def get_asin(soup: BeautifulSoup) -> str:
    try:
        main_container = soup.find("div", attrs={"data-csa-c-asin": True, "id": "title_feature_div"})
        if main_container:
            return make_csv_safe(main_container["data-csa-c-asin"])
        else:
            main_container: BeautifulSoup = soup.find("div", attrs={"id": "detailBulletsWrapper_feature_div"})
            return make_csv_safe(main_container.find(string=re.compile("ASIN")).find_next().string)
    except Exception:
        return ""


def get_manufacturer(soup: BeautifulSoup) -> str:
    try:
        main_container: BeautifulSoup = soup.find("table", attrs={"id": "productDetails_detailBullets_sections1"})

        if not main_container:
            main_container: BeautifulSoup = soup.find("div", attrs={"id": "detailBulletsWrapper_feature_div"})

        if not main_container:
            # if manufacturer name missing not found in either feature table or product description
            # more performance intesive compared to above methods
            return make_csv_safe(soup.find("th", string=re.compile(r"^Manufacturer")).find_parent().find("td").string)

        return make_csv_safe(main_container.find(string=re.compile(r"^Manufacturer")).find_next().string)

    except Exception:
        return ""


def get_description(soup: BeautifulSoup) -> str:
    try:
        feautres_list = soup.find(attrs={"id": "feature-bullets"}).find_all("li")
        description = ""

        for feature in feautres_list:
            description += make_csv_safe(feature.string) + ". "

        return description[:-1]

    except Exception:
        return ""


def get_product_description(soup: BeautifulSoup) -> str:
    try:
        return make_csv_safe(soup.find("div", attrs={"id": "productDescription_feature_div"}).find("span").string)
    except Exception:
        return ""


def get_title(soup: BeautifulSoup) -> str:
    try:
        return make_csv_safe(soup.find("span", attrs={"class": "a-size-medium a-color-base a-text-normal"}).string)
    except Exception:
        return ""


def get_price(soup: BeautifulSoup) -> str:
    try:
        return make_csv_safe(
            soup.find("span", attrs={"class": "a-price"}).find("span", attrs={"class": "a-price-whole"}).string
        )
    except Exception:
        return ""


def get_ratings(soup: BeautifulSoup) -> str:
    try:
        return make_csv_safe(soup.find("span", attrs={"class": "a-icon-alt"}).string)
    except Exception:
        return ""


def get_url(soup: BeautifulSoup, base_url_prefix: str = "") -> str:
    try:
        url_raw = soup.find("div", attrs={"class": "aok-relative"}).find(
            "a",
            attrs={"class": "a-link-normal s-no-outline"},
        )["href"]
        url = base_url_prefix + url_raw
        return url
    except Exception:
        return ""


def get_reviews(soup: BeautifulSoup) -> str:
    try:
        reviews_raw = make_csv_safe(
            soup.find("div", {"class": "a-section a-spacing-none a-spacing-top-micro"})
            .find("a", attrs={"class": "a-link-normal s-underline-text s-underline-link-text s-link-style"})
            .find("span")
            .string
        )

        # remove paranthesis from number of reviews
        return re.sub(r"[()]", "", reviews_raw)
    except Exception:
        return ""


def get_main_items(base_url: str = "", base_url_prefix: str = "", dummy: bool = False):
    if dummy:
        print("Using dummy listing data")
        with open("html_listing.html", "r") as html_file:
            soup = BeautifulSoup(html_file, "lxml")

    else:
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
        item_list += get_secondary_items(base_url=url, dummy=False)

        items_list.append(item_list)
        if len(items_list) > 1:
            break

    next_page_url_attrs = {"class": "s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"}
    next_page_url = base_url_prefix + soup.find("a", attrs=next_page_url_attrs, href=True)["href"]
    return items_list, next_page_url


def get_secondary_items(base_url: str = "", dummy: bool = False, dummy_alt: bool = False):
    if dummy:
        print("Using dummy product data")
        if dummy_alt:
            name = "html_product_alt.html"
        else:
            name = "html_product.html"

        with open(name, "r", encoding="utf-8") as html_file:
            soup = BeautifulSoup(html_file, "lxml")

    else:
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


def test_secondary_items():
    print(
        get_secondary_items(
            dummy=True,
        )
    )

    print(
        get_secondary_items(
            dummy=True,
            dummy_alt=True,
        )
    )


def test_listing():
    items_list, next_page_url = get_main_items(base_url_prefix="https://www.amazon.in", dummy=True)
    print(items_list[0])
    print(next_page_url)


def test_storage():
    items_list, _ = get_main_items(base_url_prefix="https://www.amazon.in", dummy=True)
    store_csv(items_list)


def testing_main():
    test_listing()
    test_secondary_items()
    test_storage()


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
