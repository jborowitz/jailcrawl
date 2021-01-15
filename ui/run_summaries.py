import pandas
import glob
state_name_to_code = {'Alabama':'AL',
'Alaska':'AK',
'Arizona':'AZ',
'Arkansas':'AR',
'California':'CA',
'Colorado':'CO',
'Connecticut':'CT',
'Delaware':'DE',
'Florida':'FL',
'Georgia':'GA',
'Hawaii':'HI',
'Idaho':'ID',
'Illinois':'IL',
'Indiana':'IN',
'Iowa':'IA',
'Kansas':'KS',
'Kentucky':'KY',
'Louisiana':'LA',
'Maine':'ME',
'Maryland':'MD',
'Massachusetts':'MA',
'Michigan':'MI',
'Minnesota':'MN',
'Mississippi':'MS',
'Missouri':'MO',
'Montana':'MT',
'Nebraska':'NE',
'Nevada':'NV',
'New Hampshire':'NH',
'New Jersey':'NJ',
'New Mexico':'NM',
'New York':'NY',
'North Carolina':'NC',
'North Dakota':'ND',
'Ohio':'OH',
'Oklahoma':'OK',
'Oregon':'OR',
'Pennsylvania':'PA',
'Rhode Island':'RI',
'South Carolina':'SC',
'South Dakota':'SD',
'Tennessee':'TN',
'Texas':'TX',
'Utah':'UT',
'Vermont':'VT',
'Virginia':'VA',
'Washington':'WA',
'West Virginia':'WV',
'Wisconsin':'WI',
'Wyoming':'WY'}
out_list = []
for f in glob.glob('daily_run_summaries/*.csv'):
    df = pandas.read_csv(f)
    date_str = f.split('/')[1].split('-run')[0] 
    df['date'] = date_str
    df['filename'] = f.split('/')[1]
    out_list.append(df)
df = pandas.concat(out_list)
df['county'] = df['script'].apply(lambda x: x.split('_')[1].replace('.py',''))
def get_state_from_script(scriptname):
    words = scriptname.replace('.py','').split('_')
    if words[0] == 'Hawai':
        return 'Hawaii'
    if words[0] in state_name_to_code.keys():
        return words[0]
    else:
        if ' '.join(words[0:2]) in state_name_to_code.keys():
            return' '.join(words[0:2])
        else:
            print(words)
def get_county_from_script(scriptname):
    words = scriptname.replace('.py','').split('_')
    if words[0] == 'Hawai':
        return words[1]
    if words[0] in state_name_to_code.keys():
        return ' '.join(words[1:])
    else:
        if ' '.join(words[0:2]) in state_name_to_code.keys():
            return ' '.join(words[2:])
        else:
            print(words)
df['state'] = df['script'].apply(get_state_from_script)
df['county_match'] = df['script'].apply(get_county_from_script)
df['state_code'] = df['state'].apply(lambda x: state_name_to_code[x])
# df.loc[df['state'] == 'Hawai','state'] = 'Hawaii'
countypop = pandas.read_csv('countypop.csv')
countypop['cn'] = countypop['county'].apply(lambda x: x.replace('County','').lower().strip())                          
me = df.merge(countypop, left_on=['state_code','county_match'], right_on=['abbr','cn'], how='left')
print(me[me['fips'].isnull()]['script'].unique())
me = df.merge(countypop, left_on=['state_code','county_match'], right_on=['abbr','cn'])
me = me.drop_duplicates('fips')
me['fips'] = me['fips'].apply(lambda x: '%05.0f' % x) 
me.to_csv('summaries_merged.csv', index=False)


df = df.drop('Unnamed: 0', axis=1)
df = df.drop_duplicates(['date','script'])
df.to_csv('run_summary_panel.csv', index=False)
