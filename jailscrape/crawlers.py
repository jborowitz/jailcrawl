import ipdb
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error
import time
from bs4 import BeautifulSoup
import sys
import numpy as np


def save_single_page(roster_row, filetype='html'):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        logger.info('using save_single_html_page for _%s, %s', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        #Boilerplate code setting up logger, getting initial URL
        time.sleep(np.random.uniform(5,10,1))

        #Given the urlAddress passed to the function we will navigate to the page
        if filetype=='html':
            browser.get(urlAddress) 
            store_source = browser.page_source
        else:
            response = requests.get(urlAddress)
            response.raise_for_status()
            store_source = response.content
        save_to_s3(store_source, page_index, roster_row, filetype=filetype) # Safe result to s3. This call includes logging and file formatting
        logger.info('Saved page _%s_', page_index)
        return True
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def mugshots_crawler(roster_row):
    '''
    For pages on mugshots.com
    '''
    try:
        logger = get_logger(roster_row) # get a standard logger
        browser = get_browser() # get a standard browser
        logger.info('using mugshots_crawler for _%s, %s', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        pages = []
        suffixes = []

        #Extract the HTML
        req = requests.get(urlAddress)
        store_source = req.content
        
        pages.append(store_source)
        
        soup = BeautifulSoup(store_source, 'lxml')
        nextpage = soup.find_all('a', {'class':'next page'})
        
        finished = False

        try:
            new_suffix = nextpage[0]['href']
        except:
            finished = True
        
        
        while finished == False and new_suffix not in suffixes:
            
            req = requests.get(urlAddress+new_suffix)
            suffixes.append(new_suffix)
            store_source = req.content
            pages.append(store_source)
            soup = BeautifulSoup(store_source, 'lxml')
            nextpage = soup.find_all('a', {'class':'next page'})
            
            try:
                new_suffix = nextpage[0]['href']
            except:
                finished = True
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))
            
        if len(pages) > 1 and pages[0] == pages[-1]:
            pages.pop()
        for page in pages:
            save_to_s3(store_source, page_index, roster_row, filetype='html') # Safe result to s3. This call includes logging and file formatting
            logger.info('Saved page _%s_', page_index)
            page_index += 1
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def public_safety_web_crawler(roster_row):
    logger = get_logger(roster_row) # Get a standard logger
    browser = get_browser() # Get a standard browser
    urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
    if 'omsweb' not in urlAddress:
        raise Exception("Appears that this site _%s_ is not a public safety web site" % urlAddress)
    page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
    logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

    browser.get(urlAddress) 
    #Use elements like below to find xpath keys and click through 
    time.sleep(np.random.uniform(5,10,1))
    
    lastpage = False
    pages = []
    names = []
    #Get first page
    store_source = browser.page_source
    pages.append(store_source)
    soup = BeautifulSoup(store_source, 'lxml')
    firstentry = soup.find('div', {'class': 'x-grid3-cell-inner x-grid3-col-3'})
    
    try:
        names.append(firstentry.text)
    except:
        lastpage = True
    
    while lastpage == False:
        time.sleep(np.random.uniform(5,10,1))
        #Navigate to next page
        nextpage = browser.find_element_by_xpath('//*[@id="ext-gen110"]')
        nextpage.click()
        
        #Wait
        time.sleep(np.random.uniform(5, 10, 1))
        
        #Extract the HTML
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        firstentry = soup.find('div', {'class': 'x-grid3-cell-inner x-grid3-col-3'})
        
        
        if names[-1] == firstentry.text:
            lastpage = True
        else:
            pages.append(store_source)
            names.append(firstentry.text)

    for store_source in pages:
        save_to_s3(store_source, page_index, roster_row)
        page_index += 1
        logger.info('Saved page _%s_', page_index)

    #Close the browser
    logger.info('complete!')
