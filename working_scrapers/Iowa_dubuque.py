#!/usr/bin/python
'''
This is a template script
MG
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

# NOTE: These are imports. They ideally don't change very often. 
# It's OK to have a large, maximal set here and to bulk-edit files to add to these.

# MG - Extra imports
import selenium as sm
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


ROW_INDEX = 233 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'iowa' # Change the current state/county information. 
THIS_COUNTY = 'dubuque'
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

        ####################################
        
        # Begin core specific scraping code
        if roster_row['State'].lower() != THIS_STATE or roster_row['County'].lower() != THIS_COUNTY:
            raise Exception("Expected county definition info from _%s, %s_, but found info: _%s_" % (THIS_COUNTY, THIS_STATE, roster_row))
       
        # Open Browser
        browser.get(urlAddress)
        time.sleep(np.random.uniform(7,10,1))
        
        num_rows_found = 1000000
        rownum = 1
        store_source = browser.page_source
        row_sources = []
        row_texts = []
        while rownum < num_rows_found:
            # Clicking to show all options. The page actually is buggy.
            # If you click on detail, and click "back", then there is
            # only 10 rows. And clicking "All" again doesn't help. YOu
            # have to click a different number of rows first...
            elem = browser.find_element_by_xpath('//*[@id="pager_center"]/table/tbody/tr/td[5]/select')
            elem.click()      
            time.sleep(np.random.uniform(1,2,1))
            
            elem = browser.find_element_by_xpath('//*[@id="pager_center"]/table/tbody/tr/td[5]/select/option[3]')
            elem.click()      
            time.sleep(np.random.uniform(1,2,1))

            elem = browser.find_element_by_xpath('//*[@id="pager_center"]/table/tbody/tr/td[5]/select')
            elem.click()      
            time.sleep(np.random.uniform(1,2,1))
            
            elem = browser.find_element_by_xpath('//*[@id="pager_center"]/table/tbody/tr/td[5]/select/option[5]')
            elem.click()      
            time.sleep(np.random.uniform(1,2,1))
            
            elem = browser.find_element_by_xpath('//*[@id="refresh_tblII"]/div/span')
            elem.click()      
            time.sleep(np.random.uniform(1,2,1))
            
            #initial_rows = browser.find_elements_by_xpath('/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td[2]/div/div[2]/div[2]/div/div[3]/div[3]/div/table/tbody/tr') 
            #Extract the HTML#
            rows = browser.find_elements_by_xpath('/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td[2]/div/div[2]/div[2]/div/div[3]/div[3]/div/table/tbody/tr') 
            logger.info('found %s rows on parse', len(rows))
            if num_rows_found == 1000000:
                num_rows_found = len(rows)
                logger.info('Found _%s_ total records', num_rows_found)

            row_texts.append(rows[rownum].text)
            elem = rows[rownum].click()
            time.sleep(np.random.uniform(1,5,1))
            row_sources.append(browser.page_source)
            logger.info('Logged id page _%s_', len(row_sources))
            browser.execute_script("window.history.go(-1)")
            time.sleep(np.random.uniform(1,5,1))
            rownum += 1
        save_to_s3(store_source, "MAINPAGE", roster_row)
        logger.info('Saved page _%s_', page_index)
        save_pages_array(row_sources, roster_row)



        ## Code to save a page and log appropriately
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        
        # End core specific scraping code
        
        ####################################

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

