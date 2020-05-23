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

ROW_INDEX = 1 # Change this for each scraper
def main(roster_row):
    try:
        """
        OLD URL: http://www.calcoso.org/divisions-jail-inmate-roster/
        UPDATED URL: https://www.calcoso.org/inmate-roster/
        
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
        assert roster_row['County'].lower() == 'calhoun'
        pages = []
        #Wait        
        time.sleep(np.random.uniform(5,10,1))
        store_source = browser.page_source
        pages.append(store_source)
        
        page_index = 2
        finished = False
        while not finished:
        
            try:
                navigation = browser.find_element_by_link_text(str(page_index))
                navigation.click()
            except:
                finished = True

            #Wait
            time.sleep(np.random.uniform(5,10,1))

            store_source = browser.page_source
            if store_source not in pages:
                pages.append(store_source)
            else:
                finished = True
            
            if page_index % 5 == 0:
                
                #Hit '...' button to see next five pages
                next_block = browser.find_elements_by_link_text('...')[1]
                next_block.click()
                
                #Wait
                time.sleep(np.random.uniform(5,10,1))
    
            #Increment page number    
            page_index += 1
            save_to_s3(browser.page_source, page_index, roster_row)
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
    main(roster[roster['index'] == ROW_INDEX].iloc[0])
