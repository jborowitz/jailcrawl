from urllib.request import urlopen, Request
import pandas as pd
import selenium as sm
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
import time
import numpy as np
from datetime import datetime
import datetime as dt
import sys
from io import StringIO
from joblib import Parallel, delayed
import boto3
import boto.s3
import requests

KEY_ID = 'AKIAIIJA7TBYB2EAMHQA'
ACCESS_KEY = 'ZlZqfd4nzTp1ystm99X/XZpbVCe0kE1fAKSUasfk'

s3 = boto3.resource(
    's3',
    region_name='us-east-1',
    aws_access_key_id=KEY_ID,
    aws_secret_access_key=ACCESS_KEY
)


#INSERT PATH TO THE FILE WHERE YOU WILL BE STORING YOUR FILES BELOW (allPrisonersProject)
#root_directory = '/Users/hisamsabouni/Documents/Deangelo_research/allPrisonersProject'
# root_directory = '/Users/davidmertenjones/Jupyter_Notebooks/Thinkful_Curriculum/CGU328/jailproject/allPrisonersProject'
root_directory = '.'

os.chdir(root_directory)
#from essentials import *

def main(urlAddress):
    try:
        """
        OLD URL: http://www.calcoso.org/divisions-jail-inmate-roster/
        UPDATED URL: https://www.calcoso.org/inmate-roster/
        
        """
        
        #urlAddress = roster['Working Link'].values[index]
        #This will use the root directory defined at the top of the script to identify where the chromdriver for selium is located
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        browser = webdriver.Chrome(chrome_options=chrome_options)
        #browser = start_driver(root_directory) #Defaults to chrome driver looking for tor proxy
        #Given the urlAddress passed to the function we will navigate to the page
        browser.get(urlAddress) 

        pages = []

        #Wait        
        time.sleep(np.random.uniform(5,10,1))
        store_source = browser.page_source
        pages.append(store_source)
        
        page_index = 2
        finished = False
        
        while not finished:
        
            try:
                navigation = browser.find_element_by_link_text(str(page_index))
                navigation.click()
            except:
                finished = True

            #Wait
            time.sleep(np.random.uniform(5,10,1))

            store_source = browser.page_source
            if store_source not in pages:
                pages.append(store_source)
            else:
                finished = True
            
            if page_index % 5 == 0:
                
                #Hit '...' button to see next five pages
                next_block = browser.find_elements_by_link_text('...')[1]
                next_block.click()
                
                #Wait
                time.sleep(np.random.uniform(5,10,1))
                
    
            #Increment page number    
            page_index += 1
    	    
        #Mark the time the file is collected
        date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #Create an html file with the name of the time stamp collected and write the page to a folder 
        #Within the root directory. Replace county and city with the county and city you are working on.
        #file_ = open(root_directory + '/County/City/' + date_collected + '.html', 'w', encoding='utf-8')
        #file_.write(store_source)
        #file_.close() #close the writing of the file

        #s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '.html').put(Body=store_source)
        
        #Toggle Local/S3 Storage
        aws = True
        
        for entry in pages:
        
            if aws == True:
                s3.Object('jailcrawl',state + '/' + county + '/' + str(datetime.now().year) + '/' + datetime.now().strftime("%B")+'/'+ date_collected + '_page_{}.html'.format(str(pages.index(entry)+1))).put(Body=entry)
            else:
                if not os.path.exists('./Scrapings/{}/{}/'.format(state, county)):
                    os.makedirs('./Scrapings/{}/{}/'.format(state, county))
                
                file_ = open(root_directory + '/Scrapings/{}/{}/'.format(state, county) + date_collected + '_page_{}.html'.format(str(pages.index(entry)+1)), 'w', encoding='utf-8')
                file_.write(str(entry))
                file_.close() #close the writing of the file
        
        #Close the browser
        browser.close()
        
    except Exception as errorMessage:
        #Post error to firebase server
        browser.close()
        date_collected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {'Message':str(errorMessage)}
        firebase.put('/ErrorLogs/'+locationInUse+'/',date_collected,data)
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
    import ipdb; ipdb.set_trace()
    roster = pd.read_csv('/opt/jail_roster_final_rmDuplicates.csv',encoding = "utf-8")
    locations = []
    for row in range(roster.shape[0] - 1):
        stp = str(roster['State'].values[row]) +', '+ str(roster['County'].values[row])
        locations.append(bytes(stp, 'utf-8').decode('utf-8', 'ignore').replace('.','').replace('/',''))
    
    global firebase, county, state
    #firebase = loginToFirebase()
    index = 1
    locationInUse = locations[index]
    state = roster.State[index]
    county = roster.County[index]
    main(roster['Working Link'].values[index])
