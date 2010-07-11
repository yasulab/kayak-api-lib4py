# -*- coding: utf-8 -*-
#!/usr/bin/env python


"""Kayak Search API Library for Python
"""

import sys
import urllib2
from time import sleep
from lxml import etree
from lxml.html import tostring, html5parser

TOKEN = 'KBHCF2zy2ti9FdO9nvd8kA'
HOSTNAME = 'api.kayak.com'
BASE_URL = 'http://' + HOSTNAME
SESSION_URL = BASE_URL + '/k/ident/apisession?token=' + TOKEN
SEARCH_URL_BASE = BASE_URL + '/s/apisearch?basicmode=true&'
PORT = 80

def get_session(token, parser=html5parser):
    """Get session id
    >>> sid = get_session(TOKEN)
    >>> sid != ""
    """
    response = urllib2.urlopen(SESSION_URL).read()
    root = parser.fromstring(response)
    sid = root.find('sid').text
    return sid

def _start_search(url, parser=html5parser):
    """Generic search function
    """
    import httplib
    #response = urllib2.urlopen(url).read()
    h = httplib.HTTPConnection('api.kayak.com')
    h.request('GET', url)
    response = h.getresponse()
    if response.status == httplib.OK:
        data = response.read()
        print "Response Data: "
        print data
    else:
        print "HTTP Connection failed because of " + str(response.status)
        exit()
    print "Query Result: " + url
    print response
    try:
        f = open("ksearchid.xml", "w")
        f.write(response)
        f.flush()
    finally:
        f.close()
    xml = parser.fromstring(response)
    searchid = xml.find('searchid')
    if searchid:
        searchid = searchid.text
    else:
        print "search error:"
        print response
        return None
    return searchid

def start_flight_search(sid, oneway, origin,
                        destination, dep_date, ret_date, travelers):
    """Start to search flight
    """
    url = SEARCH_URL_BASE + 'oneway=n&origin=%(origin)s' \
          '&destination=%(destination)s&destcode=&depart_date=%(dep_date)s' \
          '&depart_time=a&return_date=%(ret_date)s&return_time=a' \
          '&travelers=%(travelers)s&cabin=f&action=doflights&' \
          '&apimode=1&_sid_=%(sid)s' \
          % {'origin': origin, 
             'destination': destination, 
             'dep_date': dep_date, 
             'ret_date': ret_date,  
             'travelers': travelers, 
             'sid': sid}
           
    return _start_search(url)

def start_hotel_search(sid, citystatuecountry, dep_date, ret_date, travelers):
    """Start to search hotel
    """
    csc = urllib2.quote(citystatuecountry)
    dep_date = urllib2.quote(dep_date)
    ret_date = urllib2.quote(ret_date)
    url = SEARCH_URL_BASE + '/s/apisearch?basicmode=true&othercity=%(csc)s' \
          '&checkin_date=%(dep_date)s&checkout_date=%(ret_date)s&minstars=-1' \
          '&guests1=%(travelers)s&guests2=1&rooms=1&action=dohotels&apimode=1' \
          '&_sid_=%(sid)s' \
          % {'csc': csc, 'dep_date': dep_date, 'ret_date': ret_date,
             'travelers': travelers, 'sid': sid }
          
    return _start_search(url)

RESULTS = []
LAST_COUNT = 0

def _poll_results_file(search_type):
    """Load results from a file, for debugging only.
    """
    f = open("ksearchresults.xml", "r")
    xml_text = f.read()
    return handle_results(search_type, xml_text)

def poll_results(search_type, sid, searchid, count):
    """Poll results and write them to file.
    """
    more = None
    url_f = '/s/apibasic/%(search_type)s?searchid=%(searchid)s&apimode=1&_sid_=%(sid)s' \
            % {'searchid': searchid, 'sid': sid }    
    if search_type == 'f':
        url = url_f % {'search_type': 'flight'}
    elif search_type == 'h':
        url = url_f % {'search_type': 'hotel'}
        
    url = (url + "&c=%s" % count) if count else url
    response = urllib2.urlopen(BASE_URL + url)
    print BASE_URL + url
    try:
        f = open("ksearchbody.xml", "w")
        f.write(response)
        f.flush()
    finally:
        f.close()
    more = handle_results(search_type, response)
    if more != 'true':
        # save the response, so we can test without doing an actual
        # search.
        try:
            f = open("ksearchresults.xml", "w")
            f.write(response)
            f.flush()
        finally:
            f.close()
    return more

# body = response = urllib2.urlopen(BASE_URL + url)
def handle_results(search_type, body, parser=html5parser):
    """Process the xml result string.
    """
    xml = parse.fromstring(body)
    more = xml.find('searchresult/morepending')
    last_count = xml.find('searchresult/count').text
    more = more.text if more else None
    if more != 'true':
        results = []
        if search_type == 'f':
            # This loop over the XML is just for illustration.
            # Once you have the XML, the rest is not that interesting.
            for e in xml.findall('searchresult/trips/trip'):
                for t in e.findall('price'):
                    print t.text
                    # print t.at
                for legs in e.findall('legs'):
                    # Do something with the leg XML element
                    for l in legs:
                        for ld in l:
                            # leg XML contains detail info
                            pass
        if search_type == 'h':
            for e in xml.findall('searchresult/hotels/hotel'):
                # Do something interesting with the hotel XML
                for t in e.findall("price"):
                    print t.text
                    # print t.att
    return more

if __name__ == '__main__':
    if len(sys.argv) < 5 or len(sys.argv) > 6:
        print "usage:"
        print "python kayak.py f ORIGIN_AIRPORT DESTINATION_AIRPORT " \
              "DEPART_DATE [RETURN_DATE]"
        print "python kayak.py h \"city, RC, CC\" CHECKIN_DATE CHECKOUT_DATE"
        exit(1)

    search_type = sys.argv[1]

    sid = get_session(TOKEN)
    if not sid:
        print "bad token, sorry"
        exit(1)
    print "session id = %s" % sid
            
    if search_type == 'f':
        origin = sys.argv[2]
        destination = sys.argv[3]
        depart_date = sys.argv[4]
        return_date = sys.argv[5]
        searchid = start_flight_search(
            sid, 'n', origin, destination, depart_date, return_date, 1)
    elif search_type == 'h':
        citystatuecountry = sys.argv[2]
        depart_date = sys.argv[3]
        return_date = sys.argv[4]
        searchid = start_hotel_search(
            sid, citystatuecountry, dep_date, ret_date, 1)
    else:
        print "unknown search type %s should be 'f' or 'h'" % search_type

    if not searchid:
        print "search failed. see error document."
        exit(1)
    print "search id = %s" % (searchid)
    sleep(2)

    while more == 'true':
        more = poll_results(search_type, sid, searchid, None)
        print "more to come: %s %s so far" % (more, last_count)
        sleep(3)
    # one final call to get all results (instead of only 10)
    poll_results(search_type, sid, searchid, last_count)
    print "Results stored in ksearchresults.xml"
