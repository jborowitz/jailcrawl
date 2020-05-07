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

ROW_INDEX = 49 # Change this for each scraper
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
        assert roster_row['State'].lower() == 'arkansas'
        assert roster_row['County'].lower() == 'perry'
        """
        Inmateaid's search doesn't depend on initial letter; it searches for
        all names that contain the selected letter. It's more efficient to
        search by vowels, given that nearly all surnames include vowels. 
        Surnames without vowels are rare. Searching "AEINORUY" catches
        'Ng' and 'Smrz'. 'letters' may be expanded if these 8 letters are
        insufficient.
        """
        
        letters = ['A', 'E', 'I', 'N', 'O', 'R', 'U', 'Y']
        
        
        #Create empty list to store page sources:
        pages = []
        #Create empty list to store index of {letter}_{pagenumber}
        for letter in letters:
            
            browser.get(urlAddress) 
            #Use elements like below to find xpath keys and click through 
            #Click I agree to terms
            time.sleep(np.random.uniform(5,10,1))
            searchbox = browser.find_element_by_xpath('/html/body/div/div/div/div[2]/div[2]/div[2]/form/div[2]/input')
            searchbox.send_keys(letter)
            
            searchbutton = browser.find_element_by_xpath('/html/body/div/div/div/div[2]/div[2]/div[2]/form/div[4]/button')
            searchbutton.click()
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))
        
            #Default variables for entry with no navigation bar:
            split_pages = False
            page_index = 1
            finished = False
            
            #Check for navigation bar:
            try:
                nextpage = browser.find_element_by_link_text('Next →')
                '/html/body/div/div/div/div[2]/div[3]/div[12]/ul/li[7]/a'
                split_pages = True
            except:
                pass
            
            #Extract the HTML
            store_source = browser.page_source
            pages.append(store_source)
            page_name = letter+'_{}'.format(page_index)
            save_to_s3(store_source, page_name, roster_row)
            logger.info('Saved page _%s_', page_name)
            

            #Perform subroutine if multiple pages are present
            if split_pages == True:
                while finished == False:
                    try:
                        nextpage = browser.find_element_by_link_text('Next →')
                        nextpage.click()
                        page_index += 1
                        
                        #Wait
                        time.sleep(np.random.uniform(5,10,1))
                        
                        #Extract the HTML
                        store_source = browser.page_source
                        pages.append(store_source)
                        page_name = letter+'_{}'.format(page_index)
                        save_to_s3(store_source, page_name, roster_row)
                        logger.info('Saved page _%s_', page_name)
                        
                        #Provide index in the format "S_4" for page 4 of letter S:
                        letters_pages.append(letter+'_{}'.format(page_index))
                                    
                    except:
                        finished = True
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
