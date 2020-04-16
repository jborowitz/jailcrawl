import ipdb
import requests
from jailscrape.common import save_to_s3, get_browser, get_logger, record_error
import sys


def save_single_page(roster_row, filetype='html'):
    try:
        logger = get_logger(roster_row) # Get a standard logger
        browser = get_browser() # Get a standard browser
        logger.info('using save_single_html_page for _%s, %s', roster_row['County'], roster_row['State']) # Log the chosen URL

        urlAddress = roster_row['Working Link'] # Set the main URL from the spreadsheet
        page_index = 0 # Set an initial value of "page_index", which we will use to separate output pages
        logger.info('Set working link to _%s_', urlAddress) # Log the chosen URL
        #Boilerplate code setting up logger, getting initial URL

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
