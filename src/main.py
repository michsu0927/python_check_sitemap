"""Entry point for the automated website analysis system."""

from __future__ import annotations

import argparse
import logging

from sitemap_parser import SitemapParser

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a website via sitemap")
    parser.add_argument("url", help="Base URL of the website")
    args = parser.parse_args()

    sp = SitemapParser(args.url)
    entries = sp.parse()
    for e in entries:
        print(e.url)


if __name__ == "__main__":
    main()
