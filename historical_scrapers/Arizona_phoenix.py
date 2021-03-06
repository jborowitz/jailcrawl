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

ROW_INDEX = 27 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'arizona'
        assert roster_row['County'].lower() == 'phoenix'

        today = datetime.today()
        current_date = today.strftime('%Y-%m-%d')
        """SET UP 'current_date" ENTRY INTO SEARCH, NAVIGATE THROUGH PAGES"""
        time.sleep(np.random.uniform(5,10,1))
        #booking_date_entry = browser.find_element_by_xpath('//*[@id="Arrest_bookDate"]')
        #booking_date_entry.send_keys(current_date)
        #search = browser.find_element_by_xpath('//*[@id="yw0"]/button')
        #search.click()
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        pages = []
        #Extract the HTML
        store_source = browser.page_source
        pages.append(store_source)
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        page_index += 1
        finished = False
        while not finished:
            nextpage = browser.find_element_by_xpath('//*[@id="yw1"]/li[12]/a')
            nextpage.click()
            time.sleep(np.random.uniform(5,10,1))
            store_source = browser.page_source
            if store_source not in pages:
                pages.append(store_source)
                page_index += 1
                save_to_s3(store_source, page_index, roster_row)
                logger.info('Saved page _%s_', page_index)
            else:
                finished = True
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
