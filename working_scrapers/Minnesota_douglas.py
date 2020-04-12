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
from selenium.webdriver.common.keys import Keys
import watchtower
from bs4 import BeautifulSoup
import re
import math

ROW_INDEX = 439 # Change this for each scraper
def main(roster_row):
    try:
        logger = get_logger(roster_row)
        browser = get_browser()
        urlAddress = roster_row['Working Link']
        page_index = 0
        logger.info('Set working link to _%s_', urlAddress)
        #Boilerplate code setting up logger, getting initial URL

        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 

        ##########
        # Begin core specific scraping code
        assert roster_row['State'].lower() == 'minnesota'
        assert roster_row['County'].lower() == 'douglas'
        xpath_template = '//*[@id="cphBody_cphCenter_ctl01_paginationtop_paginationtop_lb{}"]'
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        #Extract the HTML
        store_source = browser.page_source
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        
        #Find number of entries, divide by 50, rounded up for number of pages
        soup = BeautifulSoup(store_source, 'lxml')
        pagination = soup.find('span', {'id':'cphBody_cphCenter_ctl01_paginationtop'})
        entries = pagination.find_all('div')
        num_entries = int((entries[0].text).split('of ')[-1])
        num_pages = math.ceil(num_entries/50)
        next_pages = np.arange(2, num_pages+1).tolist()
        logger.info('Found _%s_ pages for _%s_ inmates', num_pages, num_entries)
        
        for page_num in next_pages:
            try:
                page_index += 1
                elem = browser.find_element_by_xpath(xpath_template.format(str(page_num)))
                elem.click()
                #Wait
                time.sleep(np.random.uniform(5,10,1))
                #Extract the HTML
                store_source = browser.page_source
                save_to_s3(store_source, page_index, roster_row)
                logger.info('Saved page _%s_', page_index)
            except:
                pass
        # End core specific scraping code
        ##########

        #Close the browser
        logger.info('complete!')
        browser.close()
        
    except Exception as errorMessage:
        browser.close()
        record_error(str(errorMessage), page_index, roster_row)
        # Record error in S3
        logger.error('Error: %s', errorMessage)
        # Log error
        pass
        

if __name__ == "__main__":
    #This will load in the current jail roster list
    #Select the index of the roster this script is for:
    #Write the name of the county and state
    roster = pd.read_csv('/opt/jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    main(roster.iloc[ROW_INDEX])
