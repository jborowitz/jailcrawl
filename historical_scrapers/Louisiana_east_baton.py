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

ROW_INDEX = 378 # Change this for each scraper
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
        assert roster_row['County'].lower() == 'east baton'
        xpath_template = '//*[@id="dnn_ctr611_InmateList_grvInmateList"]/tbody/tr[23]/td/a[{}]'
        pages = []
        page_numbers = [1]
        
        #Click next page:
        
        #Total number of inmates not listed; use loop to iterate.
        #Loop will stop if there is no forward link.
        finished = False
        
        #Ten links per segment. 'i=10' goes to next segment.
        #Keep track of iterations; link position changes.
        
        #Wait
        time.sleep(np.random.uniform(3,8,1))
        store_source = browser.page_source
        pages.append(store_source)
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        page_index += 1
        
        while finished == False:
                    
            #Extract the HTML
            store_source = browser.page_source
            
            soup = BeautifulSoup(store_source, 'lxml')
            #Get contents of page navigation section:
            navigator = soup.find('td', {'colspan':"6"})
            #Get individual links
            pagelinks = navigator.find_all('a', href=True)
            
            linknumbers = [int(link.text) if link.text != '...' else link.text for link in pagelinks]
            if linknumbers[0] == '...':
                linknumbers[0] = 'back'
                
            if linknumbers[-1] != '...':
                finished = True
                
            if linknumbers[-1] == '...':
                linknumbers[-1] = linknumbers[-2] + 1
            xpaths = [xpath_template.format(j) for j in range(1, len(linknumbers)+2)]
            
            page_ref = dict(zip(linknumbers, xpaths))
                                    
            for key in page_ref.keys():
                
                if (key != 'back') and (key not in page_numbers):
                
                    page_index += 1
                    print(key, page_ref[key])
                    page_numbers.append(key)
                    
                    print(page_numbers[-1])
                    elem = browser.find_element_by_xpath(page_ref[key])
                    elem.click()
                    
                    #Wait
                    time.sleep(np.random.uniform(3,10,1))
                    
                    #Extract next page's HTML
                    store_source = browser.page_source
                    #Store current page's HTML
                    if store_source not in pages:
                        pages.append(store_source)
                        save_to_s3(store_source, page_index, roster_row)
                        logger.info('Saved page _%s_', page_index)
                    
        ###
        req = requests.get(urlAddress)
        page_data = req.content
        save_to_s3(page_data, page_index, roster_row)
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
