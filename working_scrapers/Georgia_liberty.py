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


ROW_INDEX = 139 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'georgia' # Change the current state/county information. 
THIS_COUNTY = 'liberty'
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
        
        #Extract the HTML#
        store_source = browser.page_source

        ## Code to save the first page and log appropriately
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        
        # Finding the last page
        soup = BeautifulSoup(store_source, 'lxml')
        page=0
        for link in soup.findAll("td", {"style":"white-space:nowrap;"}):
            page=str(link.text)
            page=re.sub("Page 1 of ", "", page)
            page=page[:page.index(" ")]
            page=int(page)

        #Crawling through all the pages
        string = str(1)
        if page ==0: 
            print("No inmate")
        if page <=10:
            for i in range(2,page+1):
                try:
                    elem = browser.find_element_by_xpath('//*[@id="Content_MainContent_ASPxGridView3_DXPagerTop"]/tbody/tr/td/table/tbody/tr/td['+str((i*2)+3)+']')
                    elem.click()        
                    time.sleep(np.random.uniform(5,7,1))
                    store_source = browser.page_source
                    string=str(i)
                    ## Code to save a page and log appropriately
                    page_index = int(string) -1
                    save_to_s3(store_source, page_index, roster_row)
                    logger.info('Saved page _%s_', page_index) 
                # If error then webcrawl needs update
                except NoSuchElementException as errorMessage:
                    print("Please review script for this county.")
                    try:
                        browser.close()
                        record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
                    except:
                        record_error(message=str(errorMessage), roster_row=roster_row)
                
                    # Record error in S3 for a general error
                    logger.error('Error: %s', errorMessage)
                    # Log error
                    sys.exit(1)   
                    
        elif page >10:
            for i in range(2,page+1):
                try:
                    elem = browser.find_element_by_xpath('//*[@id="Content_MainContent_ASPxGridView3_DXPagerTop"]/tbody/tr/td/table/tbody/tr/td[27]/img')
                    elem.click()        
                    time.sleep(np.random.uniform(5,7,1))
                    store_source = browser.page_source
                    string=str(i)
                    ## Code to save a page and log appropriately
                    page_index = int(string) - 1
                    save_to_s3(store_source, page_index, roster_row)
                    logger.info('Saved page _%s_', page_index)
                    # If error -> Sometimes the image is not td[27] but td[29]
                except NoSuchElementException:
                    elem = browser.find_element_by_xpath('//*[@id="Content_MainContent_ASPxGridView3_DXPagerTop"]/tbody/tr/td/table/tbody/tr/td[29]/img')
                    elem.click()        
                    time.sleep(np.random.uniform(5,7,1))
                    store_source = browser.page_source
                    string=str(i)
                    ## Code to save a page and log appropriately
                    page_index = int(string) - 1
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
    main(roster.iloc[ROW_INDEX])

