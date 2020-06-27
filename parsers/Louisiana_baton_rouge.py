import pandas
from bs4 import BeautifulSoup
import datetime
import glob
filestr = '2020/May/2020-05-02 20:50:05_page_0.html'
out_dfs_list = []
for filestr in glob.glob('*/*/*html'):
    print(filestr)
    parsedate = datetime.datetime.strptime(filestr.split('_')[0].split('/')[-1], '%Y-%m-%d %H:%M:%S')
    soup = BeautifulSoup(open(filestr ,'r').read(), 'lxml')
    rows = soup.find_all('tr')
    table_rows = [row for row in rows if 'color:Black;background-color:#F9FCE6' in row.attrs.get('style','') ]
    out_list = []
    for table_row in table_rows:
        out = {}
        table_cells = table_row.find_all('td')
        out['lastname'] = table_cells[0].text.strip()
        out['firstname'] = table_cells[1].text.strip()
        out['booking_date'] = table_cells[3].text.strip()
        out_list.append(out)


    df = pandas.DataFrame(out_list)
    df['crawl_time'] = datetime.datetime.strftime(parsedate, '%Y-%m-%d %H:%M:%S')
    df['file'] = filestr
    out_dfs_list.append(df)

df = pandas.concat(out_dfs_list)
