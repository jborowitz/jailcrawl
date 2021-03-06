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

ROW_INDEX = 31 # Change this for each scraper
def main(roster_row):
    try:
        """
        OLD URL: https://www.boonesheriff.com/mobile/roster.php
        UPDATED URL: https://www.boonesheriff.com/roster.php
        
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
        assert roster_row['County'].lower() == 'boone'
        suffix = '?grp={}'
        req = requests.get(urlAddress)
        #Extract the HTML
        store_source = req.content
        soup = BeautifulSoup(store_source, 'lxml')
        #Extract number of inmates:
        inmate_roster = int(re.sub("\D", "", soup.find('h2', {"class":"large-6 columns ptitles"}).text))
        #10 entries per page; get number of pages by dividing by 10, rounding up.
        num_pages = math.ceil(inmate_roster/10)
        #Mark the time the file is collected
        for page in range(0, num_pages):
            page_index += 1
            time.sleep(np.random.uniform(5,10,1))
            req = requests.get(urlAddress+suffix.format((page+1)*10))
            store_source = req.content
            save_to_s3(store_source, page_index, roster_row)
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
