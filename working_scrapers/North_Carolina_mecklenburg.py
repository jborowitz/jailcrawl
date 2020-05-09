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

ROW_INDEX = 710 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'north carolina' # Change the current state/county information. 
THIS_COUNTY = 'mecklenburg'
def main(roster_row):
    try:
        """
        OLD URL: https://mecksheriffweb.mecklenburgcountync.gov/
        UPDATED URL: https://mecksheriffweb.mecklenburgcountync.gov/Inmate
        """
        logger = get_logger(roster_row) # Get a standard logger

        # Here are standard variable values/how to initialize them.
        # These aren't initialized here since in the save_single_page
        # case, they can be done in the called function
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages

        ##########
        # Begin core specific scraping code
        if roster_row['State'].lower() != THIS_STATE or roster_row['County'].lower() != THIS_COUNTY:
            raise Exception("Expected county definition info from _%s, %s_, but found info: _%s_" % (THIS_COUNTY, THIS_STATE, roster_row))
        ## Code to save a page and log appropriately
        browser.get(urlAddress) 
        
        #urlAddress = roster['Working Link'].values[index]
        
        pages = {}
        letters = ['A', 'B', 'C', 'D',  'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                   'Y', 'Z']
        
        
        
        for letter in letters:
            time.sleep(np.random.uniform(5,10,1))
            
            #Click checkbox for active (currently housed) inmates only:
            active_checkbox = browser.find_element_by_xpath('//*[@id="chk24hrs"]')
            active_checkbox.click()
            
            time.sleep(np.random.uniform(0.5,1,1))
            
            #Find search field for last name
            lastname = browser.find_element_by_xpath('//*[@id="txtLastName"]')
            lastname.send_keys(letter)

            time.sleep(np.random.uniform(0.5,1,1))

            #Select "State" for prisoner type; Federal also available.
            #See dropdown
            pristype = browser.find_element_by_xpath('//*[@id="ddlPrisType"]')
            pristype.send_keys('State')

            time.sleep(np.random.uniform(0.5,1,1))

            searchbutton = browser.find_element_by_xpath('//*[@id="btnSearch"]')
            searchbutton.click()
            
            #Long wait;
            time.sleep(np.random.uniform(10,15,1))
            
            store_source = browser.page_source
            page_index = 1
            name = letter+'_{}'.format(page_index)
            pages[name] = store_source
            logger.info('Saved page _%s_', name)
            page_index += 1
            
            #Wait
            time.sleep(np.random.uniform(2,4,1))
            
            finished = False
            
            nav_xpath = '//*[@id="ulPaging"]/li[{}]/a'
            
            while finished == False:
                try:
                    nextpage = browser.find_element_by_link_text(str(page_index))
                    nextpage.click()

                    #Wait
                    time.sleep(np.random.uniform(10,15,1))
                    
                    #Extract HTML
                    store_source = browser.page_source
                    if store_source not in pages:
                        name = letter+'_{}'.format(page_index)
                        pages[name] = store_source
                        logger.info('Saved page _%s_', name)
                        page_index += 1
                    else:
                        finished = True
                except:
                    finished = True
            
            #Reset search for next letter
            if letter != 'Z':
                resetbutton = browser.find_element_by_xpath('//*[@id="btnReset"]')
                resetbutton.click()
        for page_index, store_source in pages.items():
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
