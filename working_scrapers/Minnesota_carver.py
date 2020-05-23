from urllib.request import urlopen, Request
import pandas as pd
import os
import time
import numpy as np
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

ROW_INDEX = 431 # Change this for each scraper
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
        assert roster_row['County'].lower() == 'carver'
        """Click on the day of the week to view a list of the inmates who were
        in jail that day.  The previous day's roster will be updated by
        6:00 a.m. the following day.  For example, if today is Wednesday,
        the most current information that can be viewed is Tuesday's report. 
        Wednesday's report will be uploaded by 6:00 a.m. on Thursday.  You
        will be able to view the past seven days.  For example, if today is
        Wednesday and you click on Thursday, you will see last Thursday's
        report."""
        
        
        url_base = 'https://gis.co.carver.mn.us/digital_docs/SHRF/roster/InternetRoster_{}.pdf'
        days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        #urlAddress = roster['Working Link'].values[index]
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        #browser = start_driver(root_directory) #Defaults to chrome driver looking for tor proxy
        #Given the urlAddress passed to the function we will navigate to the page
        #browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        #Click I agree to terms
        #time.sleep(np.random.uniform(5,10,1))
        #elem = browser.find_element_by_xpath("//span[contains(text(),'I Agree')]")
        #elem.click()
    	    
        #Extract the HTML
        
        #Mark the time the file is collected
        date_collected = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #Create an html file with the name of the time stamp collected and write the page to a folder 
        #Within the root directory. Replace county and city with the county and city you are working on.
        
        day_of_week = dt.datetime.strftime(dt.datetime.today(), '%A')
        r = requests.get(urlAddress.format(day_of_week))
        store_source = r.content
        save_to_s3(store_source, page_index, roster_row, filetype='pdf')
        logger.info('Saved page _%s_', page_index)
        #Extract the HTML
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
