import ipdb
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error, save_pages_array
import time
import math
import re
from bs4 import BeautifulSoup
import sys
import numpy as np
from functools import wraps, partial


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
        elif filetype=='xls':
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
    try:
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
    except:
        try:
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

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
        time.sleep(np.random.uniform(300,400,1))
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
            url = urlAddress+suffix.format((page+1)*num_per_page)
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
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        if 'omsweb' not in urlAddress:
            raise Exception("Appears that this site _%s_ is not a public safety web site" % urlAddress)
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

        #Close the browser
        browser.close()

        for store_source, page_index in zip(pages, range(len(pages))):
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)

        logger.info('complete!')
    except:
        try:
            try:
                page_index = len(pages)
            except:
                page_index = 0
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def basic_multipage(roster_row, next_type, next_string):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        logger.info('using basic_multipage crawler for _%s, %s_', roster_row['County'], roster_row['State']) # Log the chosen URL
        logger.info("Set next_type=_%s_, next_string=_%s_", next_type, next_string)
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

        browser.get(urlAddress)  
        time.sleep(np.random.uniform(5,10,1))
        
        pages = []
        
        store_source = browser.page_source
        pages.append(store_source)
        logger.info('found page _%s_', len(pages))

        finished = False
        
        while not finished:
                
            try:
                if next_type == 'id':
                    nextpage = browser.find_element_by_id(next_string)
                elif next_type == 'name':
                    nextpage = browser.find_element_by_name(next_string)
                elif next_type == 'xpath':
                    nextpage = browser.find_element_by_xpath(next_string)
                elif next_type == 'text':
                    nextpage = browser.find_element_by_link_text(next_string)
                elif next_type == 'ptext':
                    nextpage = browser.find_element_by_partial_link_text(next_string)
                elif next_type == 'tag':
                    nextpage = browser.find_element_by_tag_name(next_string)
                elif next_type == 'class':
                    nextpage = browser.find_element_by_class_name(next_string)
                elif next_type == 'css':
                    nextpage = browser.find_element_by_css_selector(next_string)
                    
                nextpage.click()
                time.sleep(np.random.uniform(10,15,1))
                store_source = browser.page_source
                if store_source not in pages:
                    pages.append(store_source)
                    logger.info('found page _%s_', len(pages))
                else:
                    finished = True
                
            except:
                finished = True

        #Close the browser
        browser.close()

        for store_source, page_index in zip(pages, range(len(pages))):
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)

        logger.info('complete!')

    except:
        try:
            try:
                page_index = len(pages)
            except:
                page_index = 0
            record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
        except:
            record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
        browser.close()
        # Record error in S3 for a general error
        logger.error('Error: %s', errorMessage)
        # Log error
        sys.exit(1)

def multipage_wrapper(func, roster_row=None, next_type=None, next_string=None):
    """
    Decorator for county-specific navigation/bypass function.
    Deploy using this format:
    
        wrapper = partial(crawlers.multipage_wrapper, roster_row=roster_row,
            next_type='ptext', next_string='Next')
        @wrapper
        def yuma_arizona(browser):

            #Click "search" button
            searchbutton = browser.find_element_by_xpath('//*[@id="Inmate_Index"]/div[1]/form/div/div/input[1]')
            searchbutton.click()
            
            #Wait
            time.sleep(np.random.uniform(5,10,1))

        yuma_arizona()

    """
    @wraps(func)
    def _multipage_wrapper(*args, **kwargs):
        try:
            logger = get_logger(roster_row) # Get a standard logger
            browser = get_browser() # Get a standard browser
            urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
            logger.info('using multipage_wrapper for _%s, %s_', roster_row['County'], roster_row['State']) # Log the chosen URL
            logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL

            browser.get(urlAddress)  
            time.sleep(np.random.uniform(5,10,1))

            func(browser, *args, **kwargs)
            
            pages = []
            
            store_source = browser.page_source
            pages.append(store_source)

            finished = False

            while not finished:
                
                try:
                    if next_type == 'id':
                        nextpage = browser.find_element_by_id(next_string)
                    elif next_type == 'name':
                        nextpage = browser.find_element_by_name(next_string)
                    elif next_type == 'xpath':
                        nextpage = browser.find_element_by_xpath(next_string)
                    elif next_type == 'text':
                        nextpage = browser.find_element_by_link_text(next_string)
                    elif next_type == 'ptext':
                        nextpage = browser.find_element_by_partial_link_text(next_string)
                    elif next_type == 'tag':
                        nextpage = browser.find_element_by_tag_name(next_string)
                    elif next_type == 'class':
                        nextpage = browser.find_element_by_class_name(next_string)
                    elif next_type == 'css':
                        nextpage = browser.find_element_by_css_selector(next_string)
                        
                    nextpage.click()
                    time.sleep(np.random.uniform(10,15,1))
                    store_source = browser.page_source
                    if store_source not in pages:
                        pages.append(store_source)
                    else:
                        finished = True
                    
                except:
                    finished = True

            #Close the browser
            browser.close()

            for store_source, page_index in zip(pages, range(len(pages))):
                save_to_s3(store_source, page_index, roster_row)
                logger.info('Saved page _%s_', page_index)
            
            logger.info('complete!')
        except:
            try:
                try:
                    page_index = len(pages)
                except:
                    page_index = 0
                record_error(message=str(errorMessage), roster_row=roster_row, page_number_within_scrape=page_index, browser=browser)
            except:
                record_error(message=str(errorMessage), roster_row=roster_row, browser=browser)
            browser.close()
            # Record error in S3 for a general error
            logger.error('Error: %s', errorMessage)
            # Log error
            sys.exit(1)

    return _multipage_wrapper

def zuercher_crawler(roster_row):
    try:
        logger = get_logger(roster_row)
        urlAddress = roster_row['Working Link']
        logger.info('Choosing Zuercherportal crawler with url _%s_', urlAddress)
        if 'zuercherportal' not in urlAddress:
            raise Exception("Appears that this site _%s_ is not a Zuercherportal URL" % urlAddress)
        browser = get_browser()
        page_index = 0
        #Boilerplate code setting up logger, getting initial URL

        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 

        time.sleep(np.random.uniform(5,10,1))
        
        lastpage = False
        pages = []
        names = []
        #Get first page
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        firstentry = soup.find('td', {'ordered-tag':'name'})
        names.append(firstentry.text)
        pages.append(store_source)
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
           
        
        while lastpage == False:
            time.sleep(np.random.uniform(5,10,1))
            #Navigate to next page
            try:
                nextpage = browser.find_element_by_xpath('//*[@id="primary-container"]/div/div/div/zt-collectionview/div[1]/div/div[2]/div[1]/button[2]')
                nextpage.click()
                page_index += 1
            except:
                lastpage = True
            
            time.sleep(np.random.uniform(5, 10, 1))
            
            #Extract the HTML
            store_source = browser.page_source
            soup = BeautifulSoup(store_source, 'lxml')
            save_to_s3(store_source, page_index, roster_row)
            logger.info('Saved page _%s_', page_index)
            firstentry = soup.find('td', {'ordered-tag':'name'})
            
            
            if names[-1] == firstentry.text:
                lastpage = True
            else:
                pages.append(store_source)
                names.append(firstentry.text)
        ###
        # End core specific scraping code
        ##########

        #Close the browser
        logger.info('complete!')
        browser.close()
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

def jailinmates_aspx(roster_row):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        logger.info('Choosing jailinmates_aspx crawler with url _%s_', urlAddress)
        if 'jailinmates' not in urlAddress:
            raise Exception("Appears that this site _%s_ is not a jailinmates URL" % urlAddress)
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages

        ##########
        # Begin core specific scraping code
        browser.get(urlAddress) 
        
        pages = []
        names = []
        
        #Wait
        time.sleep(np.random.uniform(5,10,1))

        #Extract the HTML
        store_source = browser.page_source
        soup = BeautifulSoup(store_source, 'lxml')
        table = soup.find('table', {'class':'p2c-datagrid'})
        cells = table.find_all('td')
        names.append(cells[5].text)
        pages.append(store_source)
        logger.info('added page _%s_', names[0])
        
        finished = False
        
        while not finished:
            try:
                try:
                    nextpage = browser.find_element_by_link_text(str(len(pages)+1))

                    nextpage.click()
                    time.sleep(np.random.uniform(5,10,1))
                    store_source = browser.page_source
                    soup = BeautifulSoup(store_source, 'lxml')
                    table = soup.find('table', {'class':'p2c-datagrid'})
                    cells = table.find_all('td')
                    name = cells[5].text
                    if name not in names:
                        pages.append(store_source)
                        names.append(name)
                        logger.info('added page _%s_', name)
                    else:
                        finished = True
                except:
                    time.sleep(np.random.uniform(5,10,1))
                    try:
                        nextpage = browser.find_elements_by_link_text('...')[-1]
                        nextpage.click()
                        store_source = browser.page_source
                        soup = BeautifulSoup(store_source, 'lxml')
                        table = soup.find('table', {'class':'p2c-datagrid'})
                        cells = table.find_all('td')
                        name = cells[5].text
                        if name not in names:
                            pages.append(store_source)
                            names.append(name)
                            logger.info('added page _%s_', name)
                        else:
                            finished = True
                    except:
                        finished = True
                        
            except:
                finished = True
        ## Code to save a page and log appropriately
        save_pages_array(pages, roster_row)
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
