import ipdb
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error
import time
import math
import re
from bs4 import BeautifulSoup
import sys
import numpy as np


def save_single_page(roster_row, filetype='html'):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        logger.info('using save_single_html_page for _%s, %s', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        #Boilerplate code setting up logger, getting initial URL
        time.sleep(np.random.uniform(5,10,1))

        #Given the urlAddress passed to the function we will navigate to the page
        if filetype=='html':
            browser.get(urlAddress) 
            store_source = browser.page_source
        else:
            response = requests.get(urlAddress)
            response.raise_for_status()
            store_source = response.content
        save_to_s3(store_source, page_index, roster_row, filetype=filetype) # Safe result to s3. This call includes logging and file formatting
        logger.info('Saved page _%s_', page_index)
        return True
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def mugshots_crawler(roster_row):
    '''
    For pages on mugshots.com
    '''
    try:
        logger = get_logger(roster_row) # get a standard logger
        browser = get_browser() # get a standard browser
        logger.info('using mugshots_crawler for _%s, %s_', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        pages = []
        suffixes = []

        #Extract the HTML
        req = requests.get(urlAddress)
        store_source = req.content
        
        pages.append(store_source)
        
        soup = BeautifulSoup(store_source, 'lxml')
        nextpage = soup.find_all('a', {'class':'next page'})
        
        finished = False

        try:
            new_suffix = nextpage[0]['href']
        except:
            finished = True
        
        
        while finished == False and new_suffix not in suffixes:
            
            req = requests.get(urlAddress+new_suffix)
            suffixes.append(new_suffix)
            store_source = req.content
            pages.append(store_source)
            soup = BeautifulSoup(store_source, 'lxml')
            nextpage = soup.find_all('a', {'class':'next page'})
            
            try:
                new_suffix = nextpage[0]['href']
            except:
                finished = True
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))
            
        if len(pages) > 1 and pages[0] == pages[-1]:
            pages.pop()
        for page in pages:
            save_to_s3(store_source, page_index, roster_row, filetype='html') # Safe result to s3. This call includes logging and file formatting
            logger.info('Saved page _%s_', page_index)
            page_index += 1
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def public_safety_web_crawler(roster_row):
    logger = get_logger(roster_row) # Get a standard logger
    browser = get_browser() # Get a standard browser
    urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
    if 'omsweb' not in urlAddress:
        raise Exception("Appears that this site _%s_ is not a public safety web site" % urlAddress)
    page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
    logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

    browser.get(urlAddress) 
    #Use elements like below to find xpath keys and click through 
    time.sleep(np.random.uniform(5,10,1))
    
    lastpage = False
    pages = []
    names = []
    #Get first page
    store_source = browser.page_source
    pages.append(store_source)
    soup = BeautifulSoup(store_source, 'lxml')
    firstentry = soup.find('div', {'class': 'x-grid3-cell-inner x-grid3-col-3'})
    
    try:
        names.append(firstentry.text)
    except:
        lastpage = True
    
    while lastpage == False:
        time.sleep(np.random.uniform(5,10,1))
        #Navigate to next page
        nextpage = browser.find_element_by_xpath('//*[@id="ext-gen110"]')
        nextpage.click()
        
        #Wait
        time.sleep(np.random.uniform(5, 10, 1))
        
        #Extract the HTML
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        firstentry = soup.find('div', {'class': 'x-grid3-cell-inner x-grid3-col-3'})
        
        
        if names[-1] == firstentry.text:
            lastpage = True
        else:
            pages.append(store_source)
            names.append(firstentry.text)

    for store_source in pages:
        save_to_s3(store_source, page_index, roster_row)
        page_index += 1
        logger.info('Saved page _%s_', page_index)

    #Close the browser
    logger.info('complete!')

def roster_php(roster_row, num_per_page=20):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        if 'roster.php' not in urlAddress:
            raise Exception("Appears that this site _%s_ is not a roster.php website - using the wrong crawler" % urlAddress)
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Choosing roster_php crawler') # Name crawler
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

        suffix = '?grp={}'
        browser.get(urlAddress) 
        #Use elements like below to find xpath keys and click through 
        time.sleep(np.random.uniform(5,10,1))
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        try:
            inmate_roster = int(re.sub("\D", "", soup.find('span', {"class":"ptitles"}).text))        #10 entries per page; get number of pages by dividing by 10, rounding up.
        except:
            inmate_roster = int(re.sub("\D", "", soup.find('h2', {"class":"large-6 columns ptitles"}).text))        #10 entries per page; get number of pages by dividing by 10, rounding up.
#">Inmate Roster (151)</h2>
        num_pages = math.ceil(inmate_roster/num_per_page)
        pages = []

        for page in range(0, num_pages):
            
            time.sleep(np.random.uniform(5,10,1))
            url = urlAddress+suffix.format((page+1)*10)
            logger.info('getting url _%s_', url)
            browser.get(url)
            store_source = browser.page_source
            logger.info('Found page _%s_', page)
            pages.append(store_source)
        for store_source in pages:
            page_index += 1
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def inmate_aid(roster_row):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        if 'inmateaid' not in urlAddress:
            raise Exception("Appears that this site _%s_ is not an inmate aid website - using the wrong crawler" % urlAddress)
        logger.info('Choosing inmate_aid crawler') # Name crawler
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        letters = ['A', 'E', 'I', 'N', 'O', 'R', 'U', 'Y']
        
        
        #Create empty list to store page sources:
        pages = []
        
        #Create empty list to store index of {letter}_{pagenumber}
        letters_pages = []
        
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        
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
            page_index += 1
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
                        
                        #Provide index in the format "S_4" for page 4 of letter S:
                        page_name = letter+'_{}'.format(page_index)
                        save_to_s3(store_source, page_name, roster_row)
                        logger.info('Saved page _%s_', page_name)
                                    
                    except:
                        finished = True
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def smartweb_crawler(roster_row, filetype='html'):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        logger.info('using smartweb_crawler for _%s, %s', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        #Boilerplate code setting up logger, getting initial URL
        
        #Navigate to page
        browser.get(urlAddress)
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))
        
        #Assume there is a second page
        more_results = True
        
        #While a second page exists, click the "load more" button
        while more_results == True:
            try:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                load_more = browser.find_element_by_xpath('//*[@id="LoadMoreButton"]/p[1]')
                load_more.click()
                #Loading can be slow; if interrupted, it will yield partial alphabet:
                time.sleep(np.random.uniform(15, 20, 1))

            except:
                more_results = False
            
        #Expand "[+]" buttons:    
        finished = False
        
        while not finished:

            try:
                expandable = browser.find_element_by_xpath("//td[contains(text(),'[+]')]")
            except:
                finished = True
            time.sleep(np.random.uniform(0.05,0.2,1))
            try:
                expandable.click()
            except:
                pass
            time.sleep(np.random.uniform(0.05,0.2,1))

        store_source = browser.page_source
        
        save_to_s3(store_source, page_index, roster_row, filetype=filetype) # Safe result to s3. This call includes logging and file formatting
        logger.info('Saved page _%s_', page_index)
        return True
    except Exception as errorMessage:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def omsweb_crawler(roster_row):
    logger = get_logger(roster_row) # Get a standard logger
    browser = get_browser() # Get a standard browser
    urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
    if 'omsweb' not in urlAddress:
        raise Exception("Appears that this site _%s_ is not a public safety web site" % urlAddress)
    page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
    logger.info('using omsweb_crawler for _%s, %s_', roster_row['County'], roster_row['State']) # Log the chosen URL
    logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

    browser.get(urlAddress)  
    time.sleep(np.random.uniform(5,10,1))
    
    pages = []
    
    store_source = browser.page_source
    pages.append(store_source)

    finished = False
    
    while not finished:
        
        try:
            nextpage = browser.find_element_by_xpath('//*[@id="ext-gen110"]')
            nextpage.click()
            time.sleep(np.random.uniform(5,10,1))
            store_source = browser.page_source
            if store_source not in pages:
                pages.append(store_source)
            else:
                finished = True
            
        except:
            finished = True

    for store_source, page_index in zip(pages, range(len(pages))):
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)

    #Close the browser
    logger.info('complete!')