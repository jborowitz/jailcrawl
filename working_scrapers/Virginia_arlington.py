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

ROW_INDEX = 1016 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'virginia' # Change the current state/county information. 
THIS_COUNTY = 'arlington'
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
        #crawlers.save_single_page(roster_row) # try to call a known crawler if possible
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        letters = ['A', 'E', 'I', 'N', 'O', 'R', 'U', 'Y']
        
        
        #Create empty list to store page sources:
        pages = []
        
        #Create empty list to store index of {letter}_{pagenumber}
        letters_pages = []
        
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        
        for letter in letters:
            
            browser.get(urlAddress) 
            #Use elements like below to find xpath keys and click through 
            #Click I agree to terms
            time.sleep(np.random.uniform(5,10,1))
            searchbox = browser.find_element_by_xpath('//*[@id="uxName"]')
            searchbox.send_keys(letter)
            
            searchbutton = browser.find_element_by_xpath('//*[@id="Inmate_Index"]/div[1]/form/div/div/input[1]')
            searchbutton.click()
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))
        
            #Default variables for entry with no navigation bar:
            split_pages = False
            page_index = 1
            finished = False
            
            #Check for navigation bar:
            try:
                nextpage = browser.find_element_by_link_text('Next')
                split_pages = True
            except:
                pass
            
            #Extract the HTML
            store_source = browser.page_source
            pages.append(store_source)
            page_name = letter+'_{}'.format(page_index)
            page_index += 1
            save_to_s3(store_source, page_name, roster_row)
            logger.info('Saved page _%s_', page_name)

            #Perform subroutine if multiple pages are present
            if split_pages == True:
                while finished == False:
                    try:
                        nextpage = browser.find_element_by_partial_link_text('Next')
                        nextpage.click()
                        
                        #Wait
                        time.sleep(np.random.uniform(5,10,1))
                        
                        #Extract the HTML
                        store_source = browser.page_source
                        pages.append(store_source)
                        
                        #Provide index in the format "S_4" for page 4 of letter S:
                        page_name = letter+'_{}'.format(page_index)
                        save_to_s3(store_source, page_name, roster_row)
                        logger.info('Saved page _%s_', page_name)
                                    
                        index = browser.find_element_by_xpath('//*[@id="Inmate_Index"]/div[2]/div[1]')
                        last_num_and_total = index.text.split(' to ').strip()
                        last_num, total = last_num_and_total.split(' of ')
                        if last_num == total:
                            finished = True
                        page_index += 1
                    except:
                        finished = True
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)
        ## Code to save a page and log appropriately
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
    main(roster[roster['index'] == ROW_INDEX].iloc[0])
