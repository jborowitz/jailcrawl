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

ROW_INDEX = 400 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'louisiana'
        assert roster_row['County'].lower() == 'st. james'
        time.sleep(np.random.uniform(5,10,1))
        #Use first name on the page to check if last page has been reached:
        lastpage = False
        pages = []
        names = []
        #Get first page:
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        
        #Get first inmate name:
        firstentry = soup.find('td', {'ordered-tag':'name'})
        names.append(firstentry.text)
        
        #Store page contents:
        pages.append(store_source)
    	   
        #Iterate over following pages
        while lastpage == False:
            time.sleep(np.random.uniform(5,10,1))
            #Navigate to next page
            try:
                nextpage = browser.find_element_by_xpath('//*[@id="primary-container"]/div/div/div/zt-collectionview/div[1]/div/div[2]/div[1]/button[2]')
                nextpage.click()
            except:
                lastpage = True
            
            time.sleep(np.random.uniform(5, 10, 1))
            
            #Extract the HTML
            store_source = browser.page_source
            soup = BeautifulSoup(store_source, 'lxml')
            firstentry = soup.find('td', {'ordered-tag':'name'})
            
            
            if names[-1] == firstentry.text:
                lastpage = True
            else:
                pages.append(store_source)
                save_to_s3(store_source, page_index, roster_row)
                logger.info('Saved page _%s_', page_index)
                names.append(firstentry.text)
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
