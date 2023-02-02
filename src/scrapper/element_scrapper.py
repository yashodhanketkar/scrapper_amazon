import re

from bs4 import BeautifulSoup

from .helper import make_csv_safe


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
