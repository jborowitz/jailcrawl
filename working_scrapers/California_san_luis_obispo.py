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

ROW_INDEX = 70 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'california'
        assert roster_row['County'].lower() == 'san luis obispo'
        time.sleep(np.random.uniform(5,10,1))
        today_dt = datetime.today()
        today_strft = today_dt.strftime('%m-%d-%Y')
        
        monthdict = {
        '01':'January', '02':'February', '03':'March', '04':'April',
        '05':'May', '06':'June', '07':'July', '08':'August', '09':'September',
        '10':'October', '11':'November', '12':'December'
        }    
        
        today_split = str(today_strft).split('-')
        today_formatted = '{} {}, {}'.format(
            monthdict[today_split[0]], today_split[1], today_split[2]
            )
        
        #Set Date
        date_dropdown = browser.find_element_by_xpath('//*[@id="Table1"]/tbody/tr[2]/td/div/select')
        date_dropdown.send_keys(today_formatted, Keys.RETURN)

        #Wait, set Time
        time.sleep(np.random.uniform(2,5,1))
        time_dropdown = browser.find_element_by_xpath('//*[@id="Table1"]/tbody/tr[3]/td/div/select')
        time_dropdown.send_keys('00:00', Keys.RETURN)

        #Wait, set Agency
        time.sleep(np.random.uniform(2,5,1))
        agency = browser.find_element_by_xpath('//*[@id="Table1"]/tbody/tr[4]/td/div/select')
        agency.send_keys('* All', Keys.RETURN)
    
        #Search
        get_log = browser.find_element_by_xpath('//*[@id="Table1"]/tbody/tr[5]/td/button')
        get_log.click()
        
        time.sleep(np.random.uniform(5,10,1))
        
        #Extract the HTML
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
    main(roster.iloc[ROW_INDEX])
