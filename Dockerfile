FROM python:3.7.7-stretch

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

# upgrade pip
RUN pip install --upgrade pip

# install selenium
RUN pip install selenium fake-useragent

RUN pip install pandas numpy boto3 boto joblib requests ipdb awscli watchtower beautifulsoup4 lxml html5lib

# Begin Jeff work
ADD david_scrapers/jail_roster_final_rmDuplicates.csv /opt/
ADD david_scrapers/dubuque_dockets.csv /opt/
ADD david_scrapers/woodbury_dockets.csv /opt/
ADD david_scrapers/scott_dockets.csv /opt/

ADD working_scrapers/ /opt/

ADD dbc_api_python3/deathbycaptcha.py /opt/

ADD jailscrape /opt/jailscrape
ADD conf.env /opt/jailscrape/
ADD credentials /root/.aws/credentials

ADD docker-entrypoint.sh /opt/

ENTRYPOINT ["/opt/docker-entrypoint.sh"]

