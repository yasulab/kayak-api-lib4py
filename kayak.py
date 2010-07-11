# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""Kayak Search API Library for python"""

import sys
import xml.dom.minidom
import time
import urllib2

kayakkey = 'KBHCF2zy2ti9FdO9nvd8kA'

def getkayaksession():
    # Construct the URL to start a session
    url = 'http://www.kayak.com/k/ident/apisession?token=%s&version=1' % kayakkey

    # Parse the resulting XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Find <sid>xxxxx</sid>
    sid = doc.getElementsByTagName('sid')[0].firstChild.data
    return sid


def flightsearch(sid, origin, destination, depart_date):
    # Construct search URL
    url = 'http://api.kayak.com/s/apisearch'
    url += '?basicmode=true&oneway=y&origin=%s' % origin
    url += '&destination=%s&depart_date=%s' % (destination, depart_date)
    url += '&return_data=none&depart_time=a&return_time=a'
    url += '&travelers=1&cabin=e&action=doFlights&apimode=1'
    url += '&_sid_=%s&version=1' % (sid)

    # Get the XML
    doc = xml.dom.minidom.parseString(urllib2.urlopen(url).read())

    # Extract the search ID
    searchid = doc.getElementsByTagName('searchid')[0].firstChild.data

    return searchid

"""
you'll need a function that requests the results
until there are no more. Kayak privides another URL,
flight, which gives these results. In the returned XML,
there is a tag called morepending, which contains
the word 'true' until the search is complete.
The function has to request the page until morepending
is no longer true, and then the functions get the complete results.
"""

def flightsearchresults(sid, searchid):
    # Removes leading $, commas and converts number to a float
    def parseprice(p):
        return float(p[1:].replace(',',''))

    # Polling loop
    while 1:
        time.sleep(2)

        # Construct URL for pollng
        url = 'http://www.kayak.com/s/basic/flight?'
        url += 'searchid=%s&c=5&apimode=1&_sid_=%s&version=1' % (searchid, sid)
        response = urllib2.urlopen(url).read()
        doc = xml.dom.minidom.parseString(response)

        # Look for morepending tag, and wait until it is no longer true
        morepending = doc.getElementsByTagName('morepending')[0].firstChild
        if morepending == None or morepending.data == 'false':
            break

    # Now download the complete list
    url = 'http://ww.kayak.com/s/basic/flight?'
    url += 'searchid=%s&c=999&apimode=1&_sid_=%s&version=1' % (searchid, sid)
    response = urllib2.urlopen(url).read()
    doc = xml.dom.minidom.parseString(response)

    # Write the results
    try:
        fd = open("results.xml", "w")
        fd.write(response)
        fd.flush()
    finally:
        fd.close()
    
    # Get the various elements as lists
    prices = doc.getElementsByTagName('price')
    departures = doc.getElementsByTagName('depart')
    arrivals = doc.getElementsByTagName('arrive')
    airlines = doc.getElementsByTagName('airline_display')

    # Zip them together
    return zip([p.firstChild.data for p in departures],
               [p.firstChild.data for p in arrivals],
               [parseprice(p.firstChild.data) for p in prices],
               [p.firstChild.data for p in airlines])

# If you want to take ONLY DT time, you can type:
# [p.firstChild.data.split(' ')[1] for p in departures],

"""
Notice that at the end the function just gets all the price, depart,
and arrive tags. There will be an equal number of them - one for
each flight - so the zip function can be used to join them all together
into tuples in a big list. The departure and arrival information is
given as date and time separated by a space, so the function splits
the string to get only the time. The function also converts the price
to a float by passing it to parseprice().
"""


"""
To create a full schedule for all the different people in the Glass
family with the same structure that was originally loaded in from the
file. This is just a matter of looping over the people in the list and
performing the flight search for their outbound and return flights.
"""

def createschedule(people, dest, dep, ret):
    # Get a session id for these searches
    sid = getkayaksession()
    flights = {}

    for p in people:
        name, origin = p
        # Outbound flight
        searchid = flightsearch(sid, origin, dest, dep)
        flights[(origin,dest)] = flightsearchresults(sid, searchid)

    return flights

        
def test_search():
    sid = getkayaksession()
    searchid = flightsearch(sid, 'NRT', 'PRG', '09/10/2010')
    flights = flightsearchresults(sid, searchid)
    print " DT | AT | Price($) | Airline" 
    for f in flights:
        print f
        

    
test_search()
