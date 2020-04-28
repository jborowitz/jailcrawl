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

ROW_INDEX = 574 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'montana' # Change the current state/county information. 
THIS_COUNTY = 'big horn'
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
        time.sleep(np.random.uniform(15,20,1))
        
        """This website is provided as a public service by the Big Horn County
        Sheriff’s Office. In an effort to protect victim privacy this website
        does not provide information regarding juvenile offenders, or specific
        information regarding calls for service that are sensitive in nature
        or prohibited by Montana State Statute. The Big Horn County Sheriff’s
        Office does not guarantee the accuracy, completeness, or timeliness of
        the information contained on this website regarding specific incidents,
        crimes, or people with respect to the omission of information that may
        have not yet been filed or is pending filing with a court of
        jurisdiction relating to criminal offenses. Any person who uses
        information contained in or accessed through this website to threaten,
        intimidate, or harass any individual, including registrants or family
        members, or who otherwise misuses this information may be subject to
        criminal prosecution or civil liability under federal code and/or
        Montana State Statute. """
        
        #Click to close warning
        elem = browser.find_element_by_xpath('//*[@id="cmdCloseMessage"]')
        elem.click()
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        
        #Click to select "inmates" tab
        inmates = browser.find_element_by_xpath('//*[@id="InmatesMenu"]')
        inmates.click()
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        
    	    
        #Extract the HTML
        store_source = browser.page_source
        save_to_s3(store_source, page_index, roster_row)
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
