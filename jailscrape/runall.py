import glob
import ipdb
import subprocess
import math

scripts_to_run =glob.glob('*.py') 
print('There are %s scripts to run' % len(scripts_to_run))
num_simultaneous_scripts = 10
for n in range(math.ceil(len(scripts_to_run) / num_simultaneous_scripts )):
    process_list = []
    for script in scripts_to_run[(n*num_simultaneous_scripts):((n+1)*num_simultaneous_scripts)]:
        process = subprocess.Popen(['python', script], stdout=subprocess.PIPE)
        process_list.append(process)
        print('added %s' % process)
    for process in process_list:
        stdout = process.communicate()[0]
        print(stdout)

