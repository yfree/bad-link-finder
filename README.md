# Bad Link Finder

## Overview
I wrote this in order to find bad links in my dad's website. Additionally, I made this toy for the sake of having fun with recursion.
It will not work on every site, especially sites which require deep recursion.  
Bad Link Finder locates and reports links that either return a bad status code or a connection error. A seperate instance is reported for each occurrence of a bad link.  
If a link does not have the same netloc as its parent, the link will be checked but it will not be traversed. Links are checked at the depth level they are first identified. I found that this creates less recursion depth.  
Non-html documents are checked, but their content is not downloaded.

## Requirements
Runs on Python 2.7.
Uses:
* argparse
* lxml
* requests
* urllib3

## Usage
usage: badlinkfinder.py [-h] [-d] [-f] [-i  [...]] url  

positional arguments:  
  url: The root url to crawl.  

optional arguments:
*  -h, --help
*  -d, --debug:           Shows every url as it is checked.  
*  -f, --fake-header:     Use a fake User Agent header.  
*  -i  [ ...], --ignore:  Ignore paths from being crawled. If these paths are found in the url, they will be ignored.  

##Tip
If you are having problems with a site, the ignore option may help you limit the scope of your web crawling.

##Example

Scan a site with a fake header and also output the working links as they are checked. Send the results to a file.
```bash
$ python badlinkfinder.py site.com -f -d > results.txt
```

And in another window...
```bash
$ tail -f results.txt
```

List the bad links and error links in our results.
```bash
$ grep "Bad\|Error" -C 2 results.txt
```

Count the total urls checked (given that -d was set)
```bash
$ grep "URL" results.txt | sort -u | wc -l
```

Search a site while ignoring links that contain popup or blog/tag in their path.
```bash
$ python badlinkfinder.py site.com -i popup blog/tag
```
