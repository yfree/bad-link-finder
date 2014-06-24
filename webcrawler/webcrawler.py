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
        self.encoding = sys.stdout.encoding or 'utf-8'

    #if the netlocs are different, the link_url prevails
    def build_url(self, base_url, link):
        return self.strip_anchor(urljoin(base_url, link))

    #checks if content type is html or xhtml
    #returns true if valid content type strings are in the content type
    def html_content_type(self, content_type):
        if not content_type:
            return False
        return any(allowed_type in content_type.lower() for allowed_type in self.allowed_content_types)

    #check if args have the same netloc, args are urls
    #'www' prefix is stripped and not compared
    #returns true if netlocs match
    def same_netloc(self, *args):
        netlocs = []
        for url in args:
            netloc = urlparse(url).netloc
            if netloc.lower().startswith('www.'):
                netlocs.append(netloc[4:])
            else:
                netlocs.append(netloc)

        return all(netloc == netlocs[0] for netloc in netlocs)
    
    def http_link(self, link):
        try:
            scheme = urlparse(link.lower()).scheme
        except (Exception, ValueError):
            return False
                
        if  scheme and scheme not in self.allowed_schemes:
            return False
        
        return True
    
    def extract_links(self, html):
        links = []

        try:
            myparser = etree.HTMLParser(encoding="utf-8")
            dom = etree.HTML(html, parser=myparser)
        except (TypeError, etree.ParserError, etree.XMLSyntaxError):
            return links
        if dom is not None:
            for link in dom.xpath('//a/@href | //area/@href'):
                if not self.http_link(link):
                    continue
         
                links.append(link)

        return links

    def strip_anchor(self, url):
        return url.split('#', 1)[0]
    
    def request_page(self, target):
        page = {'href' : target['href'], 
            'referer' : target['referer']}
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
    
            if not self.html_content_type(response.headers['Content-Type']):
                response.close
            
            page['content'] = response.content
    
        except (requests.RequestException, LocationParseError, socket.timeout, socket.error):
            page['url'] = target['url']
            page['code'] = 0
    
        page['links'] = self.extract_links(page.get('content', ''))
        
        return page

    def execute_page_job(self, page):
        print "\nPage {}".format(page['url'].encode(self.encoding))
        for link in page['links']:
            print "==> {}".format(link.encode(self.encoding))

    #intentionally empty
    def execute_link_job(self, page, link, link_url):
        return
    
    def ignored_path(self, url):
        return any(ignore_path in url for ignore_path in self.config['ignore'])
    
    #link must have the same netloc as parent
    def allowed_to_check(self, page, link_url):
        return self.same_netloc(page['url'], link_url)

    def crawl(self, target):
        urls_to_crawl = set()
        page = self.request_page(target)
        #handle redirection
        self.identified_urls.add(page['url'])

        for link in page['links']:
            link_url = self.build_url(page['url'], link)
            if link_url not in self.identified_urls and\
            self.allowed_to_check(page, link_url) and \
            not self.ignored_path(link_url):
                urls_to_crawl.add(link_url)
                self.identified_urls.add(link_url)
                
        self.execute_page_job(page)
        
        for link in page['links']:
            link_url = self.build_url(page['url'], link)
            
            self.execute_link_job(page, link, link_url)

            if link_url in urls_to_crawl:
                next_target = {'url':link_url,
                    'href':link, 
                    'referer':page['url']}
                urls_to_crawl.remove(link_url)
                try:
                    self.crawl(next_target)
                except RuntimeError as e:
                    print "{}, exiting...".format(e)
                    raise SystemExit