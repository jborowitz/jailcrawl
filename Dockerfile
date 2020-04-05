FROM python:3.7

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
RUN pip install selenium

RUN pip install pandas numpy boto3 boto joblib requests ipdb awscli watchtower

# Begin Jeff work
ADD david_scrapers/jail_roster_final_rmDuplicates.csv /opt/
ADD working_scrapers/ /opt/

#david_scrapers
#david_scrapers/jail_roster_final_rmDuplicates.csv
#david_scrapers/Alabama-Connecticut Complete.zip
#david_scrapers/Louisiana-Minnesota-Complete.zip
#david_scrapers/Mississippi-Nevada-Complete.zip
#david_scrapers/New Hampshire-Oregon-Complete.zip
#david_scrapers/Alabama-Connecticut.zip
#david_scrapers/Louisiana-Minnesota.zip
#david_scrapers/Mississippi-Nevada.zip
#david_scrapers/New Hampshire-Oregon.zip
#david_scrapers/Alabama-Connecticut Complete
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_talladega_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_elmore_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_randolph_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_chilton_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_shelby_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_cleburne_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_marshall_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_franklin_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_coosa_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_jefferson_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_fayette_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_dekalb_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_coffee_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_marion_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_clarke_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_houston_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_colbert_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_mobile_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/geckodriver.log
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_Lamar_201982.py
#david_scrapers/Alabama-Connecticut Complete/Alabama-Complete/Alabama_calhoun.py
#david_scrapers/Alabama-Connecticut Complete/.DS_Store
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_greene_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_poinsett_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_carroll_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_craighead_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_van buren_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_johnson_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_howard_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_lee_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_stone_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_faulkner_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_hempstead_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_marion_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_pike_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_monroe_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_boone_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_jefferson_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_ouachita_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_cross_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_saline_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_st francis_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_columbia_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_newton_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_st. francis_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_washington_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_lonoke_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_searcy_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_pope_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_baxter_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arkansas-Complete/Arkansas_perry_201982.py
#david_scrapers/Alabama-Connecticut Complete/Connecticut-Complete
#david_scrapers/Alabama-Connecticut Complete/Connecticut-Complete/Connecticut_hartford_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_phillips_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_garfield_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_douglas_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_elbert_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_adams_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_broomfield_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_boulder_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_arapahoe_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_san miguel_201982.py
#david_scrapers/Alabama-Connecticut Complete/Colorado-Complete/Colorado_gunnison_201982.py
#david_scrapers/Alabama-Connecticut Complete/CSV as of August 23 2019
#david_scrapers/Alabama-Connecticut Complete/CSV as of August 23 2019/jail_roster_final_rmDuplicates.csv
#david_scrapers/Alabama-Connecticut Complete/California-Complete
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_lake_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_kings_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_placer_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_Hayward_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_napa_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_tehama_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_monterey_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_Yolo_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_yuba_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_san luis obispo_201982.py
#david_scrapers/Alabama-Connecticut Complete/California-Complete/California_amador_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_phoenix_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_cochise 1_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_st luis_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_navajo_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_greenlee_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_graham_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_yuma_201982.py
#david_scrapers/Alabama-Connecticut Complete/Arizona-Complete/Arizona_cochise 2_201982.py
ADD jailscrape /opt/jailscrape
ADD conf.env /opt/jailscrape/
ADD credentials /root/.aws/credentials

ADD docker-entrypoint.sh /opt/

ENTRYPOINT ["/opt/docker-entrypoint.sh"]

