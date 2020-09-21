from selenium.webdriver.common.keys import Keys
import pandas
import json
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import selenium as sm
import boto3
import boto.s3
from datetime import datetime 
import watchtower
import logging
import time
import traceback
import io
import ipdb
import numpy as np
# from fake_useragent import UserAgent

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
client = boto3.client(
    's3',
    region_name='us-east-1',
    )

def get_logger(roster_row=None):
    logging.basicConfig(level=logging.INFO)
    if roster_row:
        logger = logging.getLogger('%s_%s' % (roster_row['State'],roster_row['County']))
    else:
        logger = logging.getLogger('noncounty')
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
    user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36']
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    #ua = UserAgent(cache=False)
    user_agent = np.random.choice(user_agents)
    # chrome_options.add_argument("user-agent=%s" % user_agent)
    browser = webdriver.Chrome(options=chrome_options)
    return browser

def save_pages_array(pages, roster_row):
    page_index = 0
    for store_source in pages:
        save_to_s3(store_source, page_index, roster_row)
        logger.info('Saved page _%s_', page_index)
        page_index += 1

def _try_date_split(date_str):
    try:
        out = datetime.strptime(date_str.split('.')[0].split('_')[0], '%Y-%m-%d %H:%M:%S')
        return out
    except:
        return np.nan
def summarize_page_counts():
    print(datetime.now())
    files = get_all_s3_keys('s3://jailcrawl/')
    print(datetime.now())
    files = [i for i in files if 'html' in i or 'pdf' in i or 'xml' in i or 'xls' in i]         
    df = pandas.DataFrame(files)
    print(df.shape[0])
    df = df[df[0].apply(lambda x: x[0] != '/')]
    print(df.shape[0])
    df = df[df[0].apply(lambda x: 'county' not in x.lower())]
    print(df.shape[0])
    df['State'] = df[0].apply(lambda x: x.split('/')[0])
    df['County'] = df[0].apply(lambda x: x.split('/')[1])
    df['year'] = df[0].apply(lambda x: x.split('/')[2])
    df['month'] = df[0].apply(lambda x: x.split('/')[3])
    df['filestr'] = df[0].apply(lambda x: x.split('/')[4])
    df['date'] = df['filestr'].apply(_try_date_split)
    df = df[df['State'] != 'Errors']
    df = df[df['date'].notnull()]
    df['month'] = df['date'].apply(lambda x: x.month)
    df['day'] = df['date'].apply(lambda x: x.day)
    page_counts = df.groupby(['State','County','year','month','day']).size()
    return page_counts

def get_all_s3_keys(s3_path):
    """
    Get a list of all keys in an S3 bucket.

    :param s3_path: Path of S3 dir.
    """
    s3 = boto3.client('s3')
    keys = []

    if not s3_path.startswith('s3://'):
        s3_path = 's3://' + s3_path

    bucket = s3_path.split('//')[1].split('/')[0]
    prefix = '/'.join(s3_path.split('//')[1].split('/')[1:])

    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            keys.append(obj['Key'])

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

    return keys
