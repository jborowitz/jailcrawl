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

ROW_INDEX = 408 # Change this for each scraper
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
        assert roster_row['County'].lower() == 'vermillion'
        pages = []
        
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
           'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
           'u', 'v', 'w', 'x', 'y', 'z']
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        #Click dropdown menu for each letter:
        
        for letter in letters:
            
            elem = browser.find_element_by_xpath('//*[@id="s_bln"]')
            elem.click()
            elem.send_keys(letter)
        	   
            #Wait
            time.sleep(np.random.uniform(5,15,1))
            
            
            ##Click to open "More Info" tab for each inmate
            ##Buttons have unique ids, but are all nested within <td> tags
            #buttons = browser.find_elements_by_css_selector('td input')
            #for button in buttons:
                #button.click() 
                #time.sleep(np.random.uniform(0.4, 0.6, 1))
                #logger.info('Clicked button _%s_', button.text)
            
            
            #Extract the HTML
            store_source = browser.page_source
            pages.append(store_source)
            page_name = "%s_%s" % (letter, page_index)
            save_to_s3(store_source, page_name, roster_row)
            logger.info('Saved page _%s_', page_name)
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
