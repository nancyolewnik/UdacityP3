
# coding: utf-8

# # 1. Data Audit

# In[1]:

# %%writefile mapparser.py
#!/usr/bin/env python

import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import collections


# In[2]:

import os
datadir = "."
datafile = "DenverCO.osm"
denver_data = os.path.join(datadir, datafile)

OSM_FILE = "./DenverCO.osm"
SAMPLE_FILE = "DenverCO_sample.osm"


# In[3]:

#Parse through the file with ElementTree and count the number of unique element types to understand overall structure.
def count_tags(filename):
        tags = {}
        print filename
        
        for event, elem in ET.iterparse(filename):
            
            if elem.tag in tags:
                tags[elem.tag] += 1
            else:
                tags[elem.tag] = 1
        return tags
    
tags = count_tags(SAMPLE_FILE)
pprint.pprint(tags)


# In[4]:

import re

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def get_element(osm_file, tags=('node','way')):
     context = ET.iterparse(osm_file, events=('start','end'))
     _, root = next(context) 
     for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def key_type(element, keys):
    if element.tag == "node" or element.tag == "way":
        for tag in element.iter('tag'):
            k = tag.get('k')
            if lower.search(k):
                keys['lower'] += 1
            elif lower_colon.search(k):
                keys['lower_colon'] += 1
            elif problemchars.search(k):
                keys['problemchars'] += 1
            else:
                keys['other'] += 1
    return keys


def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in enumerate(get_element(filename)):
        keys = key_type(element, keys)

    return keys

denver_keys = process_map(SAMPLE_FILE)
pprint.pprint(denver_keys)


# In[5]:

#people invovlved in the map editing.
def process_map(filename):
    users = set()
    for __, element in ET.iterparse(filename):
        for e in element:
            if 'uid' in e.attrib:
                users.add(e.attrib['uid'])
                
    return users

users = process_map(SAMPLE_FILE)
len(users)


# # 2. Problems Encountered

#    # 2.1. Street Abbreviations

# In[6]:

from collections import defaultdict

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Avenue", "Boulevard", "Commons", "Court", "Drive", "Lane", "Parkway", 
                         "Place", "Road", "Square", "Street", "Trail"]

mapping = {'Ave'  : 'Avenue',
           'Blvd' : 'Boulevard',
           'Dr'   : 'Drive',
           'Ln'   : 'Lane',
           'Pkwy' : 'Parkway',
           'Rd'   : 'Road',
           'Rd.'   : 'Road',
           'St'   : 'Street',
           'street' :"Street",
           'Ct'   : "Court",
           'Cir'  : "Circle",
           'Cr'   : "Court",
           'ave'  : 'Avenue',
           'Hwg'  : 'Highway',
           'Hwy'  : 'Highway',
           'Sq'   : "Square"}


# In[7]:

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])

    return street_types


# In[8]:

denver_street_types = audit(denver_data)


# In[9]:

pprint.pprint(dict(denver_street_types))


# In[10]:

def update_name(name, mapping, regex):
    m = regex.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            name = re.sub(regex, mapping[street_type], name)

    return name

for street_type, ways in denver_street_types.iteritems():
    for name in ways:
        better_name = update_name(name, mapping, street_type_re)
        print name, "=>", better_name


#    # 2.2. Zip Code

# In[11]:

from collections import defaultdict

def audit_zipcode(invalid_zipcodes, zipcode):
    twoDigits = zipcode[0:2]
    
    if not twoDigits.isdigit():
        invalid_zipcodes[twoDigits].add(zipcode)
    
    elif twoDigits != 95:
        invalid_zipcodes[twoDigits].add(zipcode)
        
def is_zipcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

def audit_zip(osmfile):
    osm_file = open(osmfile, "r")
    invalid_zipcodes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zipcode(tag):
                    audit_zipcode(invalid_zipcodes,tag.attrib['v'])

    return invalid_zipcodes

denver_zipcode = audit_zip(denver_data)


# In[12]:

pprint.pprint(dict(denver_zipcode))


# In[13]:

def update_name(zipcode):
    testNum = re.findall('[a-zA-Z]*', zipcode)
    if testNum:
        testNum = testNum[0]
    testNum.strip()
    if testNum == "C)":
        convertedZipcode = (re.findall(r'\d+', zipcode))
        if convertedZipcode:
            if convertedZipcode.__len__() == 2:
                return (re.findall(r'\d+', zipcode))[0] + "-" +(re.findall(r'\d+', zipcode))[1]
            else:
                return (re.findall(r'\d+', zipcode))[0]

for street_type, ways in denver_zipcode.iteritems():
    for name in ways:
        better_name = update_name(name)
        print name, "=>", better_name


# In[ ]:



