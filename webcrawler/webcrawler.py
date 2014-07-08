# -*- coding: utf-8 -*-
import sys
import socket
import requests
from lxml import etree
from lxml.html import fromstring
from urlparse import urlparse, urljoin
from urllib3.exceptions import LocationParseError

class WebCrawler(object):
    def __init__(self, **kwargs):
        self.config = {}
        self.config['debug'] = kwargs.get('debug', False)
        self.config['ignore'] = kwargs.get('ignore', [])
        self.config['fake_header'] = kwargs.get('fake_header', False)
        self.identified_urls = set()
        self.allowed_schemes = ('http', 'https')
        self.allowed_content_types = ('text/html', 'application/xhtml+xml')
        self.encoding = 'utf-8'

    # build url from base url and link with the anchor stripped
    # if the netlocs are different, the link url prevails
    def build_url(self, base_url, link):
        return self.strip_anchor(urljoin(base_url, link))
    
    # removes all characters after a name anchor from url
    def strip_anchor(self, url):
        return url.split('#', 1)[0]

    # checks if content type is html or xhtml
    # returns true if valid content type strings are in the content type
    def html_content_type(self, content_type):
        if not content_type:
            return False
        return any(allowed_type in content_type.lower() for allowed_type in self.allowed_content_types)

    # check if args have the same netloc, args are urls
    # 'www' prefix is stripped and not compared
    # returns true if netlocs match
    def same_netloc(self, *args):
        netlocs = []

        for url in args:
            netloc = urlparse(url).netloc
            if netloc.lower().startswith('www.'):
                netlocs.append(netloc[4:])
            else:
                netlocs.append(netloc)
        return all(netloc == netlocs[0] for netloc in netlocs)
    
    # checks if a link is an http link
    # returns false if the link has a non-http/https scheme or if the link is empty
    def http_link(self, link):
        scheme = urlparse(link.lower()).scheme

        if (scheme and scheme not in self.allowed_schemes) or not link:
            return False
        
        return True

    # checks if a url contains a string in the ignore list
    def ignored_path(self, url):
        return any(ignore_path in url for ignore_path in self.config['ignore'])
    
    # print page url and links
    def execute_page_job(self, page):
        print "\nPage {}".format(page['url'].encode(self.encoding))
        for link in page['links']:
            print "==> {}".format(link.encode(self.encoding))
            
    # intentionally empty
    def execute_link_job(self, page, link, link_url):
        return
    
    # link must have the same netloc as parent in base WebCrawler class
    def allowed_to_check(self, page, link_url):
        return self.same_netloc(page['url'], link_url)

    # returns a list of links from html
    # returns an empty list upon failure
    def extract_links(self, html):
        links = []

        try:
            myparser = etree.HTMLParser(encoding=self.encoding)
            dom = etree.HTML(html, parser=myparser)
        except (TypeError, etree.ParserError, etree.XMLSyntaxError):
            return links
        if dom is not None:
            for link in dom.xpath('//a/@href | //area/@href'):
                if not self.http_link(link):
                    continue
                links.append(link)
        return links

    def request_page(self, target):
        page = {'href' : target['href'], 
            'referer' : target['referer'],
            'depth': target['depth']}
        fake_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)'
        real_agent = 'Bad Link Finder'
        if self.config['fake_header'] == True:
            header = {'User-Agent': fake_agent}
        else:
            header = {'User-Agent': real_agent}

        try:
            response = requests.get(
                target['url'], 
                headers=header, 
                timeout=30, 
                stream=True, 
                verify=False)
            page['url'] = response.url
            page ['code'] = response.status_code

            # do not retrieve content if page is not html/xhtml
            if not self.html_content_type(response.headers['Content-Type']):
                response.close
            else:
                page['content'] = response.content
    
        except (requests.RequestException, LocationParseError, socket.timeout, socket.error):
            page['url'] = target['url']
            page['code'] = 0
    
        page['links'] = self.extract_links(page.get('content', ''))
        return page

    def crawl(self, target):
        urls_to_crawl = set()
        page = self.request_page(target)

        # handle redirection
        self.identified_urls.add(page['url'])
        
        # build a list of newly identified links to crawl and add entries to identified urls
        for link in page['links']:
            link_url = self.build_url(page['url'], link)
            if link_url not in self.identified_urls and\
            self.allowed_to_check(page, link_url) and \
            not self.ignored_path(link_url):
                urls_to_crawl.add(link_url)
                self.identified_urls.add(link_url)
                
        self.execute_page_job(page)
        
        # recursively crawl links on page that are newly identified
        for link in page['links']:
            link_url = self.build_url(page['url'], link)
            
            self.execute_link_job(page, link, link_url)

            if link_url in urls_to_crawl:
                next_target = {'url':link_url,
                    'href':link, 
                    'referer':page['url'],
                    'depth':page['depth'] + 1}
                urls_to_crawl.remove(link_url)

                try:
                    self.crawl(next_target)
                except RuntimeError as e:
                    print "{}, exiting...".format(e)
                    raise SystemExit
