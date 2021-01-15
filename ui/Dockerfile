FROM python:3.7.7-stretch

# upgrade pip
ADD credentials /root/.aws/credentials
RUN pip install --upgrade pip


RUN pip install pandas numpy boto3 boto joblib requests ipdb awscli watchtower beautifulsoup4 lxml html5lib dash geopandas
RUN pip install matplotlib
RUN pip install dash_tabulator dash_extensions dash_bootstrap_components



