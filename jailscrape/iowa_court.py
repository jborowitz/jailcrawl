#!  usr/bin/python
'''
This is an template script

'''

from dateutil.relativedelta import relativedelta
import datetime
import pandas
from urllib.request import urlopen, Request
import json
import botocore
import boto3
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
s3 = boto3.resource( # Do not specificy keys for boto3. What's happening here is 
    's3',
    region_name='us-east-1',
)
# NOTE: These are imports. They ideally don't change very often. It's OK
# to have a large, maximal set here and to bulk-edit files to add to
# these.
logger = get_logger()
configs = {line.split('=')[0]:line.split('=')[1].strip() for line in open('/opt/jailscrape/conf.env').readlines()}
BUCKET = configs['BUCKET']

COUNTY_CODES = {
        'scott': '07821',
        'dubuque': '01311',
        'woodbury': '03971'
        }
DOCKET_MATCHES = {
        'MSM':'SMSM',
        'ECR': 'FECR',
        'RCR': 'SRCR',
        'MCR': 'SMCR',
        'GCR': 'AGCR',
        'TA': 'NTA',
        'WCR': 'OWCR'
        }
def solve_iowa_captcha(site_key_stripped):
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
            print('Captcha failed')
            raise KeyError("Failed Captcha")
        print('Found balance: %s' % balance)
        # dbc_params['token_params'] = json.dumps(dbc_page_params)
    except deathbycaptcha.AccessDeniedException as e:
        print(e)
    return captcha

def get_s3_filename(docket_row, days_ago=0):
    docket = docket_row['docket']
    state = docket_row['county']
    date_collected = datetime.datetime.now() - relativedelta(days=days_ago)
    date_collected_str = date_collected.strftime("%Y-%m-%d")
    filename = 'court_records/' + state + '/' + docket + '/' + str(date_collected.year) + '/' + date_collected.strftime("%B")+'/'+ date_collected_str + '.csv'
    return filename
def save_to_s3(df, docket_row):
    filename = get_s3_filename(docket_row)
    print(filename)
    try:
        obj = s3.Object(BUCKET, filename).load()
        logger.info('File found, skipping save: _%s_', filename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            s3.Object(BUCKET,filename).put(Body=df.to_csv())
            logger.info('Saved file: _%s_', filename)
def docket_already_crawled(docket_row, days_ago=30):
    for i in range(days_ago + 1):
        filename = get_s3_filename(docket_row, days_ago=i)
        try:
            obj = s3.Object(BUCKET, filename).load()
            logger.info('File found, skipping save: _%s_', filename)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                continue

    logger.info('File not found for %s, continuing crawl: _%s_', docket_row['docket'],filename)
    return False
browser = get_browser() # Get a standard browser
def crawl_history(firstname, lastname, docket, countyname, query_approach):
        # Here are standard variable values/how to initialize them.
        # These aren't initialized here since in the save_single_page
        # case, they can be done in the called function
    urlAddress = 'https://www.iowacourts.state.ia.us/'
    #page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
    #logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

    ##########
    # Begin core specific scraping code
    logger.info('going to homepage')
    browser.get(urlAddress) 
    logger.info('waiting to click homepage')
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


    if query_approach=='name':
        browser.find_element_by_id('lastName').send_keys(lastname)
        browser.find_element_by_id('firstName').send_keys(firstname)
        print('firstname: %s' % firstname)
        print('lastname: %s' % lastname)
    elif query_approach=='id':
        browser.find_element_by_id('ui-id-2').click()  
        soup3 = BeautifulSoup(browser.page_source, 'lxml') 
        countycode = COUNTY_CODES[countyname]
        if countyname == 'woodbury':
            m=re.compile(r'([^\d]*)\d*')            
            code = m.match(docket).group(1)
            rest = docket.replace(code,'')
            try:
                code = DOCKET_MATCHES[code]
            except KeyError:
                pass
            fixed_docket = code + rest
            
        else: 
            fixed_docket = docket
        browser.find_element_by_name('caseid1').send_keys(countycode)
        browser.find_element_by_name('caseid2').send_keys('')
        browser.find_element_by_name('caseid3').send_keys(fixed_docket[0:2])
        browser.find_element_by_name('caseid4').send_keys(fixed_docket[2:])
        print('Field 1: %s' % countycode)
        print('Field 2: %s' % '')
        print('Field 3: %s' % fixed_docket[0:2])
        print('Field 4: %s' % fixed_docket[2:])


    grecaptcha_class = soup2.find("div", {'class':"g-recaptcha"})
    site_key = grecaptcha_class.attrs['data-sitekey']
    site_key_stripped = site_key.strip()
    for i in range(8):
        try:
            print('Trying to solve captcha, try %s' % i)
            captcha = solve_iowa_captcha(site_key_stripped)
            break
        except KeyError:
            continue
    # import ipdb; ipdb.set_trace()
    # BRowser.switch_to_frame('recaptcha challenge')
    # store_source = browser.page_source
    # soup9 = BeautifulSoup(store_source, 'lxml')


    print('waiting for page to finish after Captch click')
    time.sleep(10)
    inputs = browser.find_elements_by_tag_name('input')
    submits = [i for i in inputs if i.get_attribute('type').lower() == 'submit']
    search = [i for i in submits if i.get_attribute('name') == 'search'][0]

    try:
        browser.execute_script("document.getElementById('g-recaptcha-response').value = '%s';" % captcha['text'])  
    except Exception as e:
        logger.error('Error completing captcha, returning')
        raise(e)
    search.click()

    print('clicked search, waiting')
    time.sleep(5)
    store_source4 = browser.page_source
    soup5 = BeautifulSoup(store_source4, 'lxml') 
    try:
        matching_link = browser.find_element_by_partial_link_text(docket)
    except:
        logger.error('Failed to find docket %s', docket)
        try:
            df = pandas.read_html(store_source4)[0]
            if query_approach == 'name':
                raise NameError('problem querying by name')
            save_to_s3(df, {'county': countyname, 'docket': fixed_docket})
            return 
        except:
            return
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
            try:
                out[columns[i]] = data[i].strip()
            except:
                logger.info('Error parsing status: %s', ';'.join(data))
                out_list[-1]['Comment'] = ';'.join(data)
        out_list.append(out)
    df = pandas.DataFrame(out_list)
    df['firstname'] = firstname
    df['lastname'] = lastname
    df['docket'] = docket
    df['case'] = case_text
    df['crawl_date'] = '%s' % datetime.datetime.now()
    df['county'] = countyname

    # tab = soup5.find_all('table')[0]  
    # # /html/body/table[1]/tbody
    # rows = tab.findChildren('tr') 
    # for row in rows:
        # if docket in row.findChildren('td')[0].text:
        

    #Close the browser
    logger.info('Finished %s, (%s %s)', docket, firstname, lastname)
    return df

counties = ['scott','woodbury', 'dubuque']
# counties = ['woodbury']
np.random.shuffle(counties)
for countyname in counties:
    dockets = pd.read_csv('/opt/%s_dockets.csv' % countyname,encoding = "utf-8")
    dockets = dockets.drop_duplicates(['docket','name'])
    # dockets = dockets[dockets['docket'] == 'AGCR409847']
    dockets['county'] = countyname
    dockets = dockets.sample(frac=1)
    for index, row in dockets.iterrows():
        if ',' in row['name']:
            lastname = row['name'].split(',')[0].strip().lower()
            firstname = row['name'].split(',')[1].strip().split(' ')[0].split('-')[0].lower()
        else:
            lastname = row['name'].split(' ')[-1].strip().split('-')[0].lower()
            firstname = row['name'].split(' ')[0].strip().split('-')[0].lower()
        docket = row.fillna('')['docket']
        if len(docket) < 5:
            continue
        logger.info('Starting %s, (%s %s)', docket, firstname, lastname)
        print(firstname, lastname, docket)
        already_crawled = docket_already_crawled(row, days_ago=4)
        if already_crawled:
            logger.info('Found row _%s_, skipping', row)
            continue
        try:
            df = crawl_history(firstname, lastname, docket, countyname=countyname, query_approach='name')
            logger.info('Completed name query for %s, (%s %s)', docket, firstname, lastname)
        except NameError:
            try:
                df = crawl_history(firstname, lastname, docket, countyname=countyname, query_approach='id')
                logger.info('Completed id query for %s, (%s %s)', docket, firstname, lastname)
            except:
                logger.error('Falied query for %s, (%s %s)', docket, firstname, lastname)
                pass

        try:
            df['lastname'] = lastname
            df['firstname'] = firstname
            save_to_s3(df, row)
        except TypeError:
            continue
