#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from urlparse import urlparse
from webcrawler.errorcrawler import ErrorCrawler

def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('url', help="The root url to crawl.")
    arg_parser.add_argument(
        '-d', 
        '--debug', 
        help="Shows every url as it is checked.",
        action='store_true')
    arg_parser.add_argument(
        '-f', 
        '--fake-header', 
        help="Use a fake User Agent header.",
        action='store_true')
    arg_parser.add_argument(
        '-i', 
        '--ignore',
        default=[],
        nargs='+',
        metavar='',
        help="""Ignore paths from being crawled.
        If these paths are found in the url, they will be ignored.""")

    return arg_parser.parse_args()

def main():
    args = parse_args()
    crawler = ErrorCrawler(
        debug=args.debug,
        ignore=args.ignore,
        fake_header=args.fake_header)

    if not urlparse(args.url).scheme:
        url = 'http://' + args.url
    else:
        url = args.url

    target = {'url':url, 'href':'', 'referer':url}

    crawler.crawl(target)

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)