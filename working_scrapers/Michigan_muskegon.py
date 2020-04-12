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

ROW_INDEX = 420 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'michigan'
        assert roster_row['County'].lower() == 'muskegon'
        """
        Site requres 'Load More' to be cicked multiple times; even with long
        wait times, it does not reliably load in time.
        
        Resulting file is large (~100 MB), and may not render inmate names
        visually.
        Search for phrase: "name of the inmate" to find roster of names.
        """
        
        #urlAddress = roster['Working Link'].values[index]
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        #Use elements like below to find xpath keys and click through 
        
        finished = False
        
        prev_entries_loaded = 0
        #Iterate until the "Load More" button disappears:
        #(Button takes a few seconds to appear, hence longer wait time)
        while finished == False:
            store_source = browser.page_source
            soup = BeautifulSoup(store_source, 'lxml')
            entries_loaded = len(soup.find_all('div', {'class':'md-headline p2c-card-title ng-binding'}))
            if entries_loaded == prev_entries_loaded:
                finished = True
            else:
                #Wait
                logger.info('Waiting to load more...')
                time.sleep(np.random.uniform(15,30,1))
                secondtry = 2
                while secondtry > 0:
                    try:
                        elem = browser.find_element_by_xpath('//*[@id="inmatesCatalog"]/div[2]/div[2]/div[6]/button/span')
                        elem.click()
                        secondtry = 0
                    except:
                        secondtry -= 1
                        time.sleep(np.random.uniform(15,30,1))
                        
            
            #Wait
            time.sleep(np.random.uniform(30,45))
            try:
                elem = browser.find_element_by_xpath('//*[@id="inmatesCatalog"]/div[2]/div[2]/div[6]/button/span')
                elem.click()
            except:
                finished = True
    	    
            
        page_data = browser.page_source
        save_to_s3(page_data, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
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
