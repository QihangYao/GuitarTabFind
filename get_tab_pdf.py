import os
import argparse
from io import BytesIO

from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image


def get_dwjita_tab_urls(url):
    # Open the webpage
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(class_="entry-content", id="details-tab")
    ps = results.find_all("p")
    print(f"Found {len(ps)} pages")

    # Locate images
    img_urls = []
    for p in ps:
        img_urls.append(p.find("img").get("src"))
    print(img_urls)

    return img_urls


def get_images(img_urls):
    # Download images
    images = []
    for url in img_urls:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        bytesio = BytesIO(response.content)
        assert bytesio.readable()

        # If GIF, these steps seems to extract what we see in the browser
        image = Image.open(bytesio)
        rgb_im = image.convert("RGB")

        images.append(rgb_im)

    return images


if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(
        prog="Tab-PDF", description="Download tab as a PDF"
    )
    parser.add_argument("url", type=str, help="URL of the post")
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Output directory",
        default=os.path.join(os.path.expanduser("~"), "Downloads"),
    )
    args = parser.parse_args()

    # Parse webpage and get image URLs
    domain = urlparse(args.url).netloc
    if domain == "www.daweijita.com":
        img_urls = get_dwjita_tab_urls(args.url)
    else:
        raise ValueError(f"Unsupported domain: {domain}")

    if len(img_urls) > 0:
        # get PIL image objects for each page of tab
        images = get_images(img_urls)

        # Compose PDF and save
        pdf_name = os.path.commonprefix(
            [os.path.basename(url) for url in img_urls]
        ).rstrip("-")
        pdf_path = os.path.join(args.output_dir, f"{pdf_name}.pdf")
        images[0].save(
            pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
        )
