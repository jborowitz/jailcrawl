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

ROW_INDEX = 638 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'new york' # Change the current state/county information. 
THIS_COUNTY = 'onondaga'
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
        2-3 entries per page. They definitely made it this way on purpose.
        """
        pages = {}
        letters = ['A', 'B', 'C', 'D',  'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                   'Y', 'Z']
        letters_pages = []
        
        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        
        for letter in letters:
            #Locate "Last Name" field
            time.sleep(np.random.uniform(1,3,1))
            search_field = browser.find_element_by_xpath('//*[@id="searchForm:form1:lastNameInput"]')
            search_field.send_keys(letter)
            
            #Locate "Search" button
            time.sleep(np.random.uniform(1,3,1))
            search_button = browser.find_element_by_xpath('//*[@id="searchForm:form1:button1"]')
            search_button.click()
            
            #Navigation xpaths:
            
            nav_xpath = '//*[@id="form1:table1:web1__pagerWeb__{}"]'
            
            #Extract the HTML
            time.sleep(np.random.uniform(4,8,1))
            
            #Check if letter has more than one page:
            split_pages = False
            
            #Check to see if multiple pages appear and current page is "1"
            try:
                navigation = browser.find_element_by_xpath('//*[@id="form1:table1:statistics1"]/span')
                split_pages = True
            except:
                pass
            
            #Check to see if multiple pages appear and current page is not 1
            #Make sure each letter starts on its first page before progressing.
            try:
                navigation = browser.find_element_by_xpath(nav_xpath.format(0))
                navigation.click()
                split_pages = True
            except:
                pass
            
            store_source = browser.page_source
            page_index = 1
            name = letter+'_{}'.format(page_index)
            pages[name] = store_source
            
            #Wait
            time.sleep(np.random.uniform(2,4,1))
            
            #Subroutine runs if there are multiple pages for a given letter:
            if split_pages == True:
                page_index += 1
                time.sleep(np.random.uniform(1,3,1))
                
                finished = False
                while finished == False:
                    try:
                        nextpage = browser.find_element_by_xpath(nav_xpath.format(page_index-1))
                        nextpage.click()
                        #Wait
                        time.sleep(np.random.uniform(4,8,1))
                        
                        #Extract HTML
                        store_source = browser.page_source
                        name = letter+'_{}'.format(page_index)
                        pages[name] = store_source
                        page_index += 1
                    except:
                        finished = True
                        
            new_search = browser.find_element_by_xpath('//*[@id="nav:formNav:navText1"]')
            new_search.click()
                        
        for page_index, store_source in pages.items():
        ## Code to save a page and log appropriately
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
    main(roster[roster['index'] == ROW_INDEX].iloc[0])
