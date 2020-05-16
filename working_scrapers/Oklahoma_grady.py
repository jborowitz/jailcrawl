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

ROW_INDEX = 777 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'oklahoma' # Change the current state/county information. 
THIS_COUNTY = 'grady'
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
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 

        #Navigate to jail log
        time.sleep(np.random.uniform(5,10,1))
        logger.info('Clicking on jail log')
        jaillog = browser.find_element_by_xpath('//*[@id="AutoNumber2"]/tbody/tr[7]/td[2]/p/font/a[1]')
        jaillog.click()
        
        #Agree to disclaimer; click "Continue"
        time.sleep(np.random.uniform(3,8,1))
        logger.info('Clicking continue')
        agree = browser.find_element_by_xpath('/html/body/form/div/center/table/tbody/tr/td/center/table/tbody/tr[2]/td/a')
        agree.click() 
        
        #View all inmates:
        time.sleep(np.random.uniform(3,8,1))
        logger.info('clicking view all')
        viewall = browser.find_element_by_xpath('/html/body/div/center/table/tbody/tr/td/form/table/tbody/tr[3]/td/table/tbody/tr[2]/td[2]/input')
        viewall.click()
        
        #Create list for stored page sources:
        pages = []
        store_source = browser.page_source
        pages.append(store_source)
        logger.info('stored page _%s_', len(pages))
        
        time.sleep(np.random.uniform(3,8,1))
        
        #Site displays 16 records per page.
        #Click Next until page has already been stored
        finished = False
        while finished == False:
            nextpage = browser.find_element_by_xpath('/html/body/div/center/table/tbody/tr/td/form/table/tbody/tr[4]/td/table/tbody/tr[1]/td[2]/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td/a[5]/img')
            nextpage.click()
            time.sleep(np.random.uniform(3,8,1))
            #Select top button so identical pages won't register as different
            topbutton = browser.find_element_by_xpath('//*[@id="BROWSE_1$1"]')
            topbutton.click()
            store_source = browser.page_source
            if store_source in pages:
                finished = True
            else:
                pages.append(store_source)
        logger.info('stored page _%s_', len(pages))
        ## Code to save a page and log appropriately
        save_pages_array(pages, roster_row)
        #save_to_s3(store_source, page_index, roster_row)
        #logger.info('Saved page _%s_', page_index)
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
