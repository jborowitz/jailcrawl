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

ROW_INDEX = 47 # Change this for each scraper
def main(roster_row):
    try:
        """
        Roster has moved.
        
        OLD URL:
        https://www.newtoncountysheriff.org/roster.php
            
        NEW URL:
        http://www.myr2m.com/NewtonCoRoster/
        """
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
        assert roster_row['State'].lower() == 'arkansas'
        assert roster_row['County'].lower() == 'newton'
        time.sleep(np.random.uniform(20,30,1))
        pages = []
        page_size = browser.find_element_by_xpath('//*[@id="ContentPlaceHolder1_ddlPageSize"]')
        page_size.send_keys('30', Keys.RETURN)
        time.sleep(np.random.uniform(20,30,1))
        #Extract the HTML
        store_source = browser.page_source
        pages.append(store_source)
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        finished = False
        while not finished:
            next_page = browser.find_element_by_xpath('//*[@id="ContentPlaceHolder1_cmdNext2"]')
            try:
                next_page.click()
            except:
                pass
            time.sleep(np.random.uniform(20,30,1))
            store_source = browser.page_source
            if store_source not in pages:
                page_index += 1
                pages.append(store_source)
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
    main(roster[roster['index'] == ROW_INDEX].iloc[0])
