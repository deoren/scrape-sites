#!/usr/bin/env python2.7

# Purpose: 
#
#   Fetch web page content and write matching host links to output file
#   for further processing by another tool.

# TODO: Allow command-line and file input also?

# License: MIT

# References:
#
#   http://www.boddie.org.uk/python/HTML.html
#   http://stackoverflow.com/questions/753052/
#   http://www.crummy.com/software/BeautifulSoup/documentation.html
#   http://docs.python.org/library/os.html#files-and-directories
#   http://stackoverflow.com/questions/579687/
#   http://code.google.com/p/feedparser/source/browse/trunk/feedparser/feedparser.py
#   http://stackoverflow.com/questions/3947120/
#   http://www.noah.org/wiki/RegEx_Python#URL_regex_pattern
#   http://docs.python.org/library/re.html#re.findall
#   http://docs.python.org/faq/programming.html#how-do-you-remove-duplicates-from-a-list
#   http://stackoverflow.com/questions/1026199/regex-optional-groups
#   http://stackoverflow.com/a/1026209

import gzip
import os
import os.path
import re
import sys
import time
import urllib2
import zlib

from StringIO import StringIO

from pprint import pprint as ppr

# Access to OS clipboard
from Tkinter import Tk

# Prints various low level (verbose) debug statements
DEBUG_ON = True

# Prints various high level debug statements
INFO_ON = True

# Copy the matched lines to the clipboard for
# copy/paste use or for a download tool
# (such as JDownloader) to handle
COPY_TO_CLIPBOARD = False

# How many seconds this script should wait before
# scraping another link and then copying found
# links to the clipboard (too quicly and JDownloader
# won't be able to capture the clipboard copy requests
WAIT_TIME_BETWEEN_REQUESTS=3

class Hosts:
    """A container class for preferred, optional and excluded hosts"""

    def __init__(self):
        self.preferred = [
            'example.net',

        ]

        self.optional = [
            'example.com',
        ]

        # FIXME: Probably not necessary, may not implement
        self.excluded = []





REQUESTED_PAGE = []
try:
    REQUESTED_PAGE.append(sys.argv[1])
except IndexError:
    REQUESTED_PAGE = False



INPUT_FILE = 'urls_to_parse.txt'
OUTPUT_FILE='links_found.txt'


def write_to_clipboard(list):
    """Writes a list of items to the OS clipboard"""

    if INFO_ON: print "[I] Copying list to clipboard"

    r = Tk()
    r.withdraw()
    #r.clipboard_clear()

    for item in list:
        r.clipboard_append(item + '\n')
    r.destroy()


def remove_file(filename):
    """Remove the old output file before writing to it"""

    if INFO_ON: print "[I] Removing:\t%s" % filename

    if os.path.isfile(filename):
        # We only want to keep the results of a single run
        try:
            os.unlink(filename)
            return True
        except:
            print "\n[E] Unable to remove old output file. Please manually remove it."
            print sys.exc_info()[0]
            return False
    else:
        # It won't exist if it was manually removed or this is a first run
        return True

def read_file(filename):
    """Reads in a file and returns a list of links"""

    if INFO_ON: print "[I] Reading:\t%s" % filename

    input_content = []

    try:
        fh = open(filename)
    except:
        message = \
                 "\n[E] Input file could not be opened and you did not " \
                 "specify a url on the command-line\n\n"
        sys.exit(message)
    else:
        for line in fh:
            # Get rid of whitespace and quotes around urls
            stripped_line = line.strip().strip('"')

            # If line is commented out or is empty length ...
            if (len(stripped_line) <= 0) or (stripped_line[0] == '#'): 
                # ... do not add it to feedlist
                continue
            else:
                input_content.append(stripped_line)
        fh.close()

    if len(input_content) == 0:
        message = "\n[E] Nothing was found in the input file"
        sys.exit(message)
    else:
        return input_content


def write_file(filename, msg):
    """Wrapper to safely read/write content to source and cache files"""

    if INFO_ON: print "[I] Writing:\t%s" % filename

    # if os.access(filename, os.W_OK) and os.path.isfile(filename):
        # fh = open(filename, 'a')
        # fh.writelines(msg)
        # fh.close()
    # else:

    try:
        fh = open(filename,'a')
        for line in msg:
            fh.write(line + '\n')
        fh.close()
    except:
        print '\n'+'[E] Could not create/access/read file (' \
            + filename + '), ' + 'check permissions.'+'\n'
        print sys.exc_info()[0]

        return False

def fetch_page(url):
    """Fetches web page and returns matched strings"""

    if INFO_ON: print "\n[I] Fetching:\t%s" % url

    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    request.add_header('User-Agent', 
        'Mozilla/5.0 (Windows NT 5.1; rv:12.0) Gecko/20100101 Firefox/12.0')

    response = urllib2.urlopen(request)

    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO( response.read())
        fh = gzip.GzipFile(fileobj=buf)
        content = fh.read()
    elif zlib and 'deflate' in response.info().get('content-encoding', ''):
        try:
            content = zlib.decompress(data)
        except zlib.error, e:
            sys.exit('[E] ' + sys.exc_info()[0])
    else:
            html_page = urllib2.urlopen(url)
            content = html_page.read()
            html_page.close()

    return content


def find_matches(page_content, hosts):
    """Returns a list of valid host links"""

    matches = []
    links = []
    results = []

    for host in hosts.preferred:
        if INFO_ON: 
            print "[I] Looking for preferred host: %s" % host
        results = re.findall('"http://(?:www\.)?' + host + '.*?"', page_content, re.IGNORECASE)

        # Convert list to a set to get rid of duplicates then
        # convert back to a list and append to the links list
        links.extend(list(set(results)))


    for host in hosts.optional:
        if INFO_ON: 
            print "[I] Looking for optional host: %s" % host
        results = re.findall('"http://(?:www\.)?' + host + '.*?"', page_content, re.IGNORECASE)

        # Convert list to a set to get rid of duplicates then
        # convert back to a list and append to the links list
        links.extend(list(set(results)))

    if DEBUG_ON: 
        print "[I] %s links found" % (len(links))
        ppr(links)
        print "\n"

    return links



def main():

    # Create a Hosts object to hold valid hosts we want to include
    # links to in our output file
    hosts = Hosts()

    if not remove_file(OUTPUT_FILE):
        sys.exit()

    pages_to_parse = []

    if REQUESTED_PAGE:
        pages_to_parse = REQUESTED_PAGE
    else:
        pages_to_parse = read_file(INPUT_FILE)

    for page in pages_to_parse:
        page_content = fetch_page(page)
        links = find_matches(page_content, hosts)
        write_file(OUTPUT_FILE, links)

        if COPY_TO_CLIPBOARD:
            write_to_clipboard(links)

        # Wait a bit before fetching the next batch of links
        time.sleep(WAIT_TIME_BETWEEN_REQUESTS)


if __name__ == "__main__":
    main()
