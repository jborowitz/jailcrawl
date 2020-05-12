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
from selenium.webdriver.common.action_chains import ActionChains
# NOTE: These are imports. They ideally don't change very often. It's OK
# to have a large, maximal set here and to bulk-edit files to add to
# these.


ROW_INDEX = 730 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'ohio' # Change the current state/county information. 
THIS_COUNTY = 'belmont'
def main(roster_row):
    try:
        """
        https://bcsheriff.dyndns.org:8443/TDT_Viewer/
        
        "Your connection is not private
        Attackers might be trying to steal your information from bcsheriff.dyndns.org (for example, passwords, messages, or credit cards). Learn more
        NET::ERR_CERT_INVALID"

        
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
        
        pages = []
        
        #Mouse over menu for link to roster:
        time.sleep(np.random.uniform(5,10,1))
        
        menu = browser.find_element_by_xpath('//*[@id="art-main"]/nav/ul/li[6]/a')
        
        action = ActionChains(browser)
        
        action.move_to_element(menu).perform()
        roster_link = browser.find_element_by_xpath('//*[@id="art-main"]/nav/ul/li[6]/ul/li/a')
        roster_link.click()
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))

        inmate_info = browser.find_element_by_xpath('//*[@id="InmateInfoMenuHeader"]')
        inmate_info.click()
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        
        #Extract the HTML
        store_source = browser.page_source
        pages.append(store_source)
                
        finished = False

        while finished == False:
            try:
                next_page = browser.find_element_by_xpath('//*[@id="nextPageButton"]')
                next_page.click()
                logger.info('clicking next page...')
            except:
                finished = True
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))
            store_source = browser.page_source
            #Check whether current page has already been stored; if not, store
            if store_source in pages:
                finished = True
            else:
                pages.append(store_source)
                logger.info('appending page...')
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
