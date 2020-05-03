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

ROW_INDEX = 615 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'new mexico' # Change the current state/county information. 
THIS_COUNTY = 'san miguel'
def main(roster_row):
    try:
        """
        This site required a longer wait time so navigation elements would
        load.
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
        
        pages = {}
        letters = ['A', 'B', 'C', 'D',  'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                   'Y', 'Z'] 
        
        #Wait
        time.sleep(np.random.uniform(10,15,1))
        
        xpath_template = '//*[@id="ctl00_ContentPlaceHolder1_rptSearchBtns_ctl{}_rptbtnSearch_input"]'

        '//*[@id="ctl00_ContentPlaceHolder1_rptSearchBtns_ctl02_rptbtnSearch_input"]'
        for letter in letters:
            
            #Find element based on alphabetical index:
            letter_index = ('0'+str(letters.index(letter)+1))[-2:]
            elem = browser.find_element_by_xpath(xpath_template.format(letter_index))
            elem.click()
            
            #Wait
            time.sleep(np.random.uniform(10,15,1))
            
            #Show more entries per page *if* button appears:
            try:
                store_source = browser.page_source
                soup = BeautifulSoup(store_source, 'lxml')
                page_size = int(soup.find_all('input', {'class':'rcbInput radPreventDecorate'})[1]['value'])
                
                if page_size != 50:
                
                    more_entries = browser.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_gridResults_ctl00_ctl03_ctl01_PageSizeComboBox_Input"]')
                    more_entries.send_keys('50')
                    more_entries.send_keys(Keys.RETURN)
            except:
                pass
            
            #Wait
            time.sleep(np.random.uniform(3,6,1))
            
            #If letter with multiple pages is not already on first page, 
            #click to first page.
            try:
                firstpage = browser.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_gridResults_ctl00_Pager"]/tbody/tr/td/table/tbody/tr/td/div[2]/a[1]')
                firstpage.click()
                time.sleep(np.random.uniform(10,15,1))
            except:
                pass
            
            page_index = 1
            
            #Extract the HTML
            store_source = browser.page_source
            pagename = letter+'_{}'.format(page_index)
            pages[pagename] = store_source
            logger.info('stored page _%s_', pagename)
            page_index += 1
            
            finished = False
            
            while finished == False:
                try:
                    
                    nextpage = browser.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_gridResults_ctl00_Pager"]/tbody/tr/td/table/tbody/tr/td/div[3]/input[1]')
                    nextpage.click()
                    time.sleep(np.random.uniform(10,15,1))
                    store_source = browser.page_source
                    if store_source not in pages.values():
                        pagename = letter+'_{}'.format(page_index)
                        pages[pagename] = store_source
                        logger.info('stored page _%s_', pagename)
                        page_index += 1
                    else:
                        finished = True

                except:
                    finished = True
                    time.sleep(np.random.uniform(10,15,1))

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
