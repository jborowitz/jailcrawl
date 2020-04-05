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
import watchtower

ROW_INDEX = 21 # Change this for each scraper
def main(roster_row):
    try:
        """
        If there are no inmates' names for a particular letter, the previous
        letter will be stored.
        """
        logger = get_logger(roster_row)
        browser = get_browser()
        urlAddress = roster_row['Working Link']
        logger.info('Set working link to _%s_', urlAddress)
        #Boilerplate code setting up logger, getting initial URL

        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 

        ##########
        # Begin core specific scraping code
        assert roster_row['State'].lower() == 'alabama'
        assert roster_row['County'].lower() == 'shelby'
        pages = []
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                   'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
                   'Y', 'Z']
        time.sleep(np.random.uniform(5,10,1))
        store_source = browser.page_source
        pages.append(store_source)
        for letter in letters[0:]:
            pagelink = browser.find_element_by_xpath('//*[@id="btn_{}"]'.format(letter))
            pagelink.click()
            time.sleep(np.random.uniform(5,10,1))
            store_source = browser.page_source
            save_to_s3(browser.page_source, letter, roster_row)
            logger.info('Saved page _%s_', letter)
        # End core specific scraping code
        ##########

        #Close the browser
        logger.info('complete!')
        browser.close()
        
    except Exception as errorMessage:
        browser.close()
        import ipdb; ipdb.set_trace()
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
