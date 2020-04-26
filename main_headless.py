import requests
from bs4 import BeautifulSoup
import re

import os
from threading import Thread
import json

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

config = {'head': your_main_account_id}

class LoginAccount(Thread):
    def __init__(self, login, password):
        Thread.__init__(self)
        self.login = login
        self.password = password
        
        self._return = None
    def run(self):
        session = requests.session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Lenovo K50a40 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.137 YaBrowser/17.4.1.352.00 Mobile Safari/537.36'})
        front = session.get("https://simple-mmo.com")
        csrf_token = re.findall(r'<input type="hidden" name="_token" value="(.*)"', front.text)[0]

        cookies = session.cookies

        payload = {"email":self.login, "password":self.password, '_token': csrf_token}
    
        r = session.post("https://simple-mmo.com/login", payload, cookies = cookies)
        
        if not "These credentials do not match our records." in r.text:
            new_cookies = session.cookies.get_dict()
    
            soup = BeautifulSoup(r.text, "lxml")
            token = soup.find("meta",  attrs = {'name': "csrf-token"})['content']
        
            self._return = [True, session, new_cookies, token]
        else:
            self._return = [False, None, None, None]
    def join(self):
        Thread.join(self)
        return self._return

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(Fore.WHITE + '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd.center(os.get_terminal_size().columns))
    # Print New Line on Complete
    if iteration == total: 
        print()

def work(session, cookie, jid, csrf_token):
    session.headers.update({"X-CSRF-TOKEN": csrf_token})
    r = session.post("https://simple-mmo.com/api/job/perform/"+ str(jid) +"/10", cookies = cookie)
    
    if r.text == "Success":
        return True
    else:
        return False
    
    return json.loads(r.text)

def transfer(session, cookie, csrf_token):
    session.headers.update({"X-CSRF-TOKEN": csrf_token})
    r = session.get("https://simple-mmo.com/api/mob", cookies = cookie)
    
    gold = json.loads(r.text)['gold']
    
    payload = {'_token': csrf_token, 'GoldAmount':gold, 'source':'equipped'}
    
    r = session.post("https://simple-mmo.com/sendgold/{}/action".format(config['head']), payload, cookies = cookie)

def claim(session, cookie, csrf_token):
    session.headers.update({"X-CSRF-TOKEN": csrf_token})
    payload = {'_token': csrf_token}
    
    r = session.post("https://simple-mmo.com/api/dailyreward/claim", payload, cookies = cookie)

accounts = [
    {'email': your_account_email, 'passw': your_account_password, 'job': id_of_job_to_perform}, 
]

datas = []


for i in range(len(accounts)):
    login = LoginAccount(accounts[i]['email'], accounts[i]['passw'])
    login.start()
    status, session, cookie, token = login.join()
    job = accounts[i]['job']
    
    if status == True:
        datas.append({'session': session, 'cookie':cookie, 'token': token, 'job': job})


@sched.scheduled_job('interval', hours=1)
def do_job():
    for i in range(len(datas)):
        work(datas[i]['session'], datas[i]['cookie'], datas[i]['job'], datas[i]['token'])
        transfer(datas[i]['session'], datas[i]['cookie'], datas[i]['token'])

@sched.scheduled_job('interval', hours=24)
def do_claim():
    for i in range(len(datas)):
        claim(datas[i]['session'], datas[i]['cookie'], datas[i]['token'])

sched.start()