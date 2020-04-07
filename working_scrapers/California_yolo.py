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

ROW_INDEX = 74 # Change this for each scraper
def main(roster_row):
    try:
        """
        PDF LINK IS OUT OF DATE
        
        OLD URL: http://www.yolocountysheriff.com/wp-content/uploads/2019/02/January-2019-webiste-upload.pdf
            
        NEW URL: https://www.yolocountysheriff.com/services/jail/booking-statistics/
        
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
        assert roster_row['State'].lower() == 'california'
        assert roster_row['County'].lower() == 'yolo'

        req = requests.get(urlAddress)
        store_source = req.content
        
        soup = BeautifulSoup(store_source, 'lxml')
        link_to_pdf = soup.find('article', {'id':'post-356'})
        pdf_url = link_to_pdf.find_all('a')[1]['href']
        
        time.sleep(np.random.uniform(5,10,1))
        req2 = requests.get(pdf_url)
        pdf_data = req2.content
        save_to_s3(pdf_data, page_index, roster_row, filetype='pdf')
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
