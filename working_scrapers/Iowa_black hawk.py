#!/usr/bin/python
'''
This is a template script
MG
'''

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
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error, save_pages_array
from jailscrape import crawlers
# jailscrape.common is a file that is part of the project which keeps
# most common boilerplate code out of this file
from selenium.webdriver.common.keys import Keys
import watchtower
from bs4 import BeautifulSoup
import re
import math

# NOTE: These are imports. They ideally don't change very often. 
# It's OK to have a large, maximal set here and to bulk-edit files to add to these.

# MG - Extra imports
import selenium as sm
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


ROW_INDEX = 100 # Change this for each scraper. This references the row
# of the main jailcrawl spreadsheet. This index will be used to look up
# the URL as well as state/county info
THIS_STATE = 'illinois' # Change the current state/county information. 
THIS_COUNTY = 'sara sota'
def main(roster_row):
    try:
        logger = get_logger(roster_row) # Get a standard logger

        # Here are standard variable values/how to initialize them.
        # These aren't initialized here since in the save_single_page
        # case, they can be done in the called function
        
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

        ####################################
        
        # Begin core specific scraping code
        if roster_row['State'].lower() != THIS_STATE or roster_row['County'].lower() != THIS_COUNTY:
            raise Exception("Expected county definition info from _%s, %s_, but found info: _%s_" % (THIS_COUNTY, THIS_STATE, roster_row))
       
        # Open Browser
        browser.get(urlAddress)
        time.sleep(np.random.uniform(7,10,1))
        
        # Clicking show result ->50
        elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_ddlPageSize"]')
        elem.click()    
        time.sleep(np.random.uniform(1,2,1))
        elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_ddlPageSize"]/option[5]')
        elem.click()    
        time.sleep(np.random.uniform(1,3,1))

        #Extract the HTML#
        store_source = browser.page_source

        ## Code to save the first page and log appropriately
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        
        #Second page
        page_index = 1
        try:
            elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_gvBookings"]/tbody/tr[51]/td/table/tbody/tr/td[2]/a')
            elem.click()   
            time.sleep(np.random.uniform(5,7,1)) 
            store_source = browser.page_source
            ## Code to save the second page and log appropriately
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)
        except NoSuchElementException:
                print("No 2nd page")
                

        #Crawling through all the pages
        #Per page is 50 inmates, just in case ,we limit to 20 pages to include until the 1000th inmate
        string = str(1)
        for i in range(3,20):
            try:
                elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_gvBookings"]/tbody/tr[52]/td/table/tbody/tr/td['+str(i)+']/a')
                elem.click()        
                time.sleep(np.random.uniform(5,7,1)) 
                store_source = browser.page_source
                string=str(i)
                ## Code to save the second page and log appropriate
                page_index = int(string)-1
                save_to_s3(store_source, page_index, roster_row)
                logger.info('Saved page _%s_', page_index)
            except NoSuchElementException:
                print("No subsequent page")
        
        # End core specific scraping code
        
        ####################################

        #Close the browser
        logger.info('complete!')

    except Exception as errorMessage:
        try:
            browser.close()
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row)

        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)


if __name__ == "__main__":
    #This will load in the current jail roster list
    #Select the index of the roster this script is for:
    #Write the name of the county and state
    roster = pd.read_csv('/opt/jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    main(roster.iloc[ROW_INDEX])


def main(urlAddress):
    try:


        #Mark the time the file is collected
        date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #Create an html file with the name of the time stamp collected and write the page to a folder 
        #Within the root directory. Replace county and city with the county and city you are working on.
        
        ##### Testing - Please omit this ######
        date_test = datetime.now().strftime("%Y-%m-%d")
        file_ = open(root_directory + '/scraper_test_update/' +state+"/"+ state +"_"+ county +"_"+ date_test + '_1.html', 'w', encoding='utf-8')
        file_.write(store_source)
        file_.close() #close the writing of the file
        
        # First page
        #s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_1.html').put(Body=store_source)
        
        #Second page
        try:
            elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_gvBookings"]/tbody/tr[51]/td/table/tbody/tr/td[2]/a')
            elem.click()   
            time.sleep(np.random.uniform(5,7,1)) 
            store_source = browser.page_source
            #s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_2.html').put(Body=store_source)
        except NoSuchElementException:
                print("No 2nd page")
                

        #Crawling through all the pages
        #Per page is 50 inmates, just in case ,we limit to 20 pages to include until the 1000th inmate
        string = str(1)
        for i in range(3,20):
            try:
                elem = browser.find_element_by_xpath('//*[@id="ctl00_ctl00_cphContentTemplate_cphSecondaryTemplate_gvBookings"]/tbody/tr[52]/td/table/tbody/tr/td['+str(i)+']/a')
                elem.click()        
                time.sleep(np.random.uniform(5,7,1)) 
                store_source = browser.page_source
                string=str(i)
                file_ = open(root_directory + '/scraper_test_update/' +state+"/"+ state +"_"+ county +"_"+ date_test +"_"+ string+ '.html', 'w', encoding='utf-8')
                file_.write(store_source)
                file_.close()
                #s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + "_"+ string+ '.html').put(Body=store_source)
            except NoSuchElementException:
                print("No subsequent page")

        #Close the browser
        browser.close()
    except Exception as errorMessage:
        #Post error to firebase server
        browser.close()
        #date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #data = {'Message':str(errorMessage)}
        #firebase.put('/ErrorLogs/'+locationInUse+'/',date_collected,data)
        pass
    
        

if __name__ == "__main__":
    #Will collect the data in parallel to speed up computation
    #num_cores = 12
    #inputs = range(len(all_urls))
    #getCounty = Parallel(n_jobs=num_cores)(delayed(main)(i) for i in tqdm(inputs))
    #This will load in the current jail roster list
    #Select the index of the roster this script is for:
    #Write the name of the county and state
    global roster, locations
    roster = pd.read_csv('/Users/matthewgomies/Downloads/allPrisonersProject/jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    locations = []
    for row in range(roster.shape[0] - 1):
        stp = str(roster['State'].values[row]) +', '+ str(roster['County'].values[row])
        locations.append(bytes(stp, 'utf-8').decode('utf-8', 'ignore').replace('.','').replace('/',''))
    
    global firebase, county, state
    firebase = loginToFirebase()
    index = 227
    locationInUse = locations[index]
    state = roster.State[index].replace(' ','_')
    county = roster.County[index].replace(' ','_')
    main(roster['Working Link'].values[index])
