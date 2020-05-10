from selenium.webdriver.common.keys import Keys
import json
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import selenium as sm
import boto3
import boto.s3
from datetime import datetime 
import watchtower
import logging
import traceback
import io
import ipdb

configs = {line.split('=')[0]:line.split('=')[1].strip() for line in open('/opt/jailscrape/conf.env').readlines()}
BUCKET = configs['BUCKET']
FAILURE_SNS_TOPIC = configs['FAILURE_SNS_TOPIC']
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler())
logger.info('Set BUCKET to _%s_',BUCKET)
s3 = boto3.resource( # Do not specificy keys for boto3. What's happening here is 
    's3',
    region_name='us-east-1',
)

def get_logger(roster_row):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('%s_%s' % (roster_row['State'],roster_row['County']))
    logger.addHandler(watchtower.CloudWatchLogHandler())
    return logger

def save_to_s3(page_data, page_number_within_scrape, roster_row, filetype='html'):
    county = roster_row['County']
    state = roster_row['State']
    date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if filetype == 'pdf':
        filename = state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.pdf'.format(page_number_within_scrape)
    elif filetype == 'xls':
        filename = state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.xls'.format(page_number_within_scrape)
    else:
        filename = state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(page_number_within_scrape)
    print(filename)
    logger.info('Saved file: _%s_', filename)
    s3.Object(BUCKET,filename).put(Body=page_data)

def record_error(message,  roster_row, browser=None, page_number_within_scrape='NO_PAGE_FOUND'):
    county = roster_row['County']
    state = roster_row['State']
    date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = 'Errors/' + state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(page_number_within_scrape)
    print('Error on file: _%s_' % filename)
    logger.error('Error on file: _%s_', filename)
    if not browser:
        sns_message = {
                "County": county,
                "State": state,
                "Message": message
                }
        logger.error('Error message: _%s_', sns_message)

    try:
        s3.Object(BUCKET,filename).put(Body=browser.page_source)
    except:
        logger.warning("No browser defined, so no error page saved")
    sns_message = {
            "County": county,
            "State": state,
            "Message": message,
            "Traceback": traceback.format_exc(),
            }
    logger.error('Error message: _%s_', sns_message)
    #sio = io.StringIO()
    #print(json.dumps(sns_message), file=sio)
    #sio.seek(0)
    sns = boto3.client('sns')
    response = sns.publish(
                TargetArn=FAILURE_SNS_TOPIC,
                Message=json.dumps(sns_message, indent=2)
    )

def get_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(options=chrome_options)
    return browser

def save_pages_array(pages, roster_row):
    page_index = 0
    for store_source in pages:
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        page_index += 1
