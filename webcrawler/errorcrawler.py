# -*- coding: utf-8 -*-
from webcrawler import WebCrawler

class ErrorCrawler(WebCrawler):
    def __init__(self, **kwargs):
        super(ErrorCrawler, self).__init__(**kwargs)
        self.bad_urls = set()
        self.error_urls = set()

    def execute_page_job(self, page):
        if page['code'] == 0:
            self.error_urls.add(page['url'])
        elif page['code'] != 200:
            self.bad_urls.add(page['url'])
         
        self.output_result(page['code'], page['href'], page['url'], page['referer'])
        
    #output if one of the links on the page has already been identified as bad/connection error
    #but not if it's on a page that we're not allowed to check)
    def execute_link_job(self, page, link, link_url):
        if self.allowed_to_check(page, link_url):
            if link_url in self.bad_urls:
                code = 400
            elif link_url in self.error_urls:
                code = 0
            else:
                return

            self.output_result(code, link, link_url, page['url'])

    #the page's url must have the same netloc as its parent
    #links outside of the netloc will be checked but not traversed
    def allowed_to_check(self, page, link_url):
        return self.same_netloc(page['url'], page['referer'])

    def output_result(self, code, link, link_url, referer):
        if code == 0:
            link_desc = 'Connection Error'
        elif code != 200:
            link_desc = 'Bad Link'
        else:
            if self.config['debug'] == False:
                return
            link_desc = 'Working Link'
            
        print "\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
        print "{} Discovered: {}".format(link_desc, link.encode(self.encoding))
        print "    URL used: {}".format(link_url.encode(self.encoding))
        print "On page: {}".format(referer.encode(self.encoding))
        print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
