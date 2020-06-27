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

ROW_INDEX = 243 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'iowa' # Change the current state/county information. 
THIS_COUNTY = 'scott'
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
        letters = ['A', 'E', 'I', 'N', 'O', 'R', 'U', 'Y'] 
        browser.get(urlAddress)
        ## Code to save a page and log appropriately
        #save_to_s3(store_source, page_index, roster_row)
        #logger.info('Saved page _%s_', page_index)
        # End core specific scraping code
        ##########
        num_rows_found = 1000000
        rownum = 1
        store_source = browser.page_source
        row_sources = []
        while rownum < num_rows_found:
            
                                                   
            rows = browser.find_elements_by_xpath('/html/body/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div/table/tbody/tr')
            logger.info('Found %s profiles', len(rows))
            try:
                link = browser.find_element_by_xpath('/html/body/div/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div/table/tbody/tr[%s]/td[1]/a' % rownum)
            except Exception as e:
                if abs(rownum - num_rows_found) <= 1:
                    break
                else:
                    raise(e)
            elem = link.click()
            time.sleep(np.random.uniform(1,5,1))
            row_sources.append(browser.page_source)
            logger.info('Logged id page _%s_', len(row_sources))
            browser.execute_script("window.history.go(-1)")
            time.sleep(np.random.uniform(1,5,1))
            rownum += 1
            
        save_to_s3(store_source, "MAINPAGE", roster_row)
        logger.info('Saved page _%s_', page_index)
        save_pages_array(row_sources, roster_row)

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
    main(roster[roster['index'] == ROW_INDEX].iloc[0])
