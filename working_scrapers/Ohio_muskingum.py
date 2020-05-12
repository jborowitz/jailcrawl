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

ROW_INDEX = 761 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'ohio' # Change the current state/county information. 
THIS_COUNTY = 'muskingum'
def main(roster_row):
    try:
        """
        OLD URL: http://www.ohiomuskingumsheriff.org/wp-content/uploads/2018/05/5-18-18-1.pdf
        UPDATED URL: http://www.ohiomuskingumsheriff.org/jail-division/inmate-registry/
        UPDATED URL 2:https://www.ohiomuskingumsheriff.org/Divisions/Jail/Inmate-Registry/
        """
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
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        store_source = browser.page_source

        #Find today's roster link
        link =  browser.find_element_by_partial_link_text("Download Inmate")
        link.click()

        time.sleep(np.random.uniform(5,10,1))     
        pdf_data = browser.page_source

        #soup = BeautifulSoup(store_source, 'lxml')
        #strong = soup.find('strong')
        #pdf_url = strong.find('a')['href']
        #logger.info('found PDF url _%s_', pdf_url)

        ##Wait
        #time.sleep(np.random.uniform(5,10,1))     
        #req = requests.get(pdf_url)
        #pdf_data = req.content
        ## Code to save a page and log appropriately
        save_to_s3(pdf_data, page_index, roster_row, filetype='pdf')
        logger.info('Saved page _%s_', page_index)
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
