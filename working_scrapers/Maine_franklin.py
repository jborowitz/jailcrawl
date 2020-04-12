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

ROW_INDEX = 415 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'maine'
        assert roster_row['County'].lower() == 'franklin'
        """
        Supplied URL was for June 2018 only
        
        OLD URL: http://www.franklincounty.maine.gov/june-2018-inmates
        UPDATED URL: https://www.franklincounty.maine.gov/dispatch-log-jail-bookings
        """
        #urlAddress = roster['Working Link'].values[index]
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        
        #Set up lists for stored page sources
        #as well as top name in list for each page
        pages = []
        names = []
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        current_month = browser.find_element_by_xpath('//*[@id="comp-iwma4msjlink"]')
        current_month.click()
        
        #Store HTML data
        time.sleep(np.random.uniform(3,6,1))
        store_source = browser.page_source
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        pages.append(store_source)
        
        soup = BeautifulSoup(store_source, 'lxml')
        firstname = soup.find_all('em', {'style':'font-style:normal;'})[0].text
        names.append(firstname)
        
        finished = False
        while finished == False:
            #First attempt at locating element fails
            tryagain = 2
            while tryagain > 0:
                try:
                    nextpage = browser.find_elements_by_class_name('paginationNext')
                    nextpage[0].click()
                    tryagain = 0 
                except:
                    tryagain -= 1
                    time.sleep(np.random.uniform(3, 6, 1))
                if tryagain == 0:
                    finished = True
            page_index += 1
            time.sleep(np.random.uniform(5,10,1))
            store_source = browser.page_source
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)
            soup = BeautifulSoup(store_source, 'lxml')
            firstname = soup.find_all('em', {'style':'font-style:normal;'})[0].text
            
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
