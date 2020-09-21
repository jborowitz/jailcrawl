#!  usr/bin/python
'''
This is an template script

'''

import datetime
import pandas
from urllib.request import urlopen, Request
import json
import deathbycaptcha
import pandas as pd
import os
import time
import numpy as np
import sys
from io import StringIO
from joblib import Parallel, delayed
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error, save_pages_array
from jailscrape import crawlers
# jailscrape.common is a file that is part of the project which keeps
# most common boilerplate code out of this file
from selenium.webdriver.common.keys import Keys
import watchtower
from bs4 import BeautifulSoup
import re
import math
# NOTE: These are imports. They ideally don't change very often. It's OK
# to have a large, maximal set here and to bulk-edit files to add to
# these.
lastname = 'kammerude'
firstname = 'katie'
docket = 'FECR119155'
    # Here are standard variable values/how to initialize them.
    # These aren't initialized here since in the save_single_page
    # case, they can be done in the called function
browser = get_browser() # Get a standard browser
urlAddress = 'https://www.iowacourts.state.ia.us/'
#page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
#logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

##########
# Begin core specific scraping code
browser.get(urlAddress) 
print('waiting to click homepage')
time.sleep(np.random.uniform(2,4,1))

search = browser.find_element_by_partial_link_text('Start A')
search.click()
browser.switch_to_frame('main')

store_source = browser.page_source
soup = BeautifulSoup(store_source, 'lxml') 
old_soup = soup
links = browser.find_elements_by_tag_name('a')         
case_link = [i for i in links if 'TrialSimp' in i.get_attribute('href')][0]
print('found link to click: %s' % case_link.get_attribute('href'))
case_page = case_link.click()
browser.switch_to_frame('main')


store_source = browser.page_source
soup2 = BeautifulSoup(store_source, 'lxml') 

browser.find_element_by_id('lastName').send_keys(lastname)
browser.find_element_by_id('firstName').send_keys(firstname)



grecaptcha_class = soup2.find("div", {'class':"g-recaptcha"})
site_key = grecaptcha_class.attrs['data-sitekey']
site_key_stripped = site_key.strip()

# import ipdb; ipdb.set_trace()
# BRowser.switch_to_frame('recaptcha challenge')
# store_source = browser.page_source
# soup9 = BeautifulSoup(store_source, 'lxml')

dbc_page_params = {
        'googlekey': site_key_stripped,
        'pageurl':'https://www.iowacourts.state.ia.us/ESAWebApp/TrialSimpFrame',
        'proxy':'',
        'proxytype':''
        }

dbc_url = 'http://api.dbcapi.me/api/captcha'
dbc_client = deathbycaptcha.SocketClient('jborowitz', 'MDcHvM*$5nsW2Kf')

try:
    balance = dbc_client.get_balance()
    print('starting to solve captcha: %s' % datetime.datetime.now())
    captcha = dbc_client.decode(type=4, token_params=json.dumps(dbc_page_params))
    print('finished solving captcha: %s' % datetime.datetime.now())
    if captcha:
        print('Captcha solved!')
        print ("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))
    else:
        import ipdb; ipdb.set_trace()
    print('Found balance: %s' % balance)
    # dbc_params['token_params'] = json.dumps(dbc_page_params)
except deathbycaptcha.AccessDeniedException as e:
    print(e)

print('waiting for page to finish after Captch click')
time.sleep(10)
inputs = browser.find_elements_by_tag_name('input')
submits = [i for i in inputs if i.get_attribute('type').lower() == 'submit']
search = [i for i in submits if i.get_attribute('name') == 'search'][0]

browser.execute_script("document.getElementById('g-recaptcha-response').value = '%s';" % captcha['text'])  
search.click()

print('clicked search, waiting')
time.sleep(5)
store_source4 = browser.page_source
soup5 = BeautifulSoup(store_source4, 'lxml') 
matching_link = browser.find_element_by_partial_link_text(docket)
case_text = matching_link.text
print('Found case id %s' % case_text)
matching_link.click()
print('Found docket link, clicking')
time.sleep(5)
soup6 = BeautifulSoup(browser.page_source, 'lxml') 
browser.switch_to_frame('banner')
soup7 = BeautifulSoup(browser.page_source, 'lxml') 
# tabs = pandas.read_html(browser.page_source)      

filings_link = browser.find_element_by_partial_link_text('Filings')
filings_link.click()

time.sleep(5)
browser.switch_to_default_content()

time.sleep(5)
browser.switch_to_frame('main')
soup = BeautifulSoup(browser.page_source, 'lxml') 
table = soup.find_all('table')[0]
rows = table.find_all('tr')
columns = [i.text for i in rows[1].find_all('td')]
out_list = []
for row in rows[2:]:
    out = {}
    data = [i.text for i in row.find_all('td')]
    for i in range(len(columns)):
        if len(data) == 1:
            out_list[-1]['Comment'] = data[0].strip() # Comments are in their own whole row, which is a mess
            continue
        out[columns[i]] = data[i].strip()
    out_list.append(out)
df = pandas.DataFrame(out_list)
df['firstname'] = firstname
df['lastname'] = lastname
df['docket'] = docket
df['case'] = case_text
df['crawl_date'] = '%s' % datetime.datetime.now()
import ipdb; ipdb.set_trace()

# tab = soup5.find_all('table')[0]  
# # /html/body/table[1]/tbody
# rows = tab.findChildren('tr') 
# for row in rows:
    # if docket in row.findChildren('td')[0].text:
    

#Close the browser
logger.info('complete!')

