#!/usr/bin/python
'''
This is an template script

'''

from urllib.request import urlopen, Request
import pandas as pd
import os
import time
import numpy as np
from datetime import datetime
import datetime as dt
import sys
from io import StringIO
from joblib import Parallel, delayed
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error
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

ROW_INDEX = 583 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'montana' # Change the current state/county information. 
THIS_COUNTY = 'glacier'
def main(roster_row):
    try:
        logger = get_logger(roster_row) # Get a standard logger

        # Here are standard variable values/how to initialize them.
        # These aren't initialized here since in the save_single_page
        # case, they can be done in the called function
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

        ##########
        # Begin core specific scraping code
        if roster_row['State'].lower() != THIS_STATE or roster_row['County'].lower() != THIS_COUNTY:
            raise Exception("Expected county definition info from _%s, %s_, but found info: _%s_" % (THIS_COUNTY, THIS_STATE, roster_row))
        """
        PDFs could not be extracted using requests, but they are saved within
        the html files.
        """
        pages = []
                
        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))

    	    
        #Extract the HTML
        store_source = browser.page_source
        
        soup = BeautifulSoup(store_source, 'lxml')
        linkbox = soup.find_all("div", {'class':'content-container'})
        pdf_links = linkbox[3].find_all('a', href=re.compile("pdf"))
        
        pdf_urls = []
        
        for pdf_link in pdf_links:
            pdf_urls.append(pdf_link['href'].replace(' ', '%20'))
            
        for pdf_url in pdf_urls:
            browser.get(pdf_url)
            #Wait
            time.sleep(np.random.uniform(10,15,1))
            pdf_data = browser.page_source
            pages.append(pdf_data)
            save_to_s3(store_source, page_index, roster_row, filetype='pdf')
            logger.info('Saved page _%s_', page_index)
            page_index += 1
        # End core specific scraping code
        ##########

        #Close the browser
        logger.info('complete!')

    except Exception as errorMessage:
        try:
            browser.close()
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row)

        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)


if __name__ == "__main__":
    #This will load in the current jail roster list
    #Select the index of the roster this script is for:
    #Write the name of the county and state
    roster = pd.read_csv('/opt/jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    main(roster.iloc[ROW_INDEX])
