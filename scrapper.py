import json
import os
import random
import threading
import time
from MaxiumMain import *
from urllist import genlist, genTaskList
import gc
from bs4 import BeautifulSoup
import requests

# <form action="" method="post" name="indi_graph">
# Warning!! Don't know how secure it is to access proxies with http (https doesn't work) with requests!

import re
 



def rationalize(rat):
# str -> float, else return None
    if rat.replace('.', '', 1).replace('-', '', 1).isnumeric():
        return float(rat)
    else: 
        return None

def parseData(wb):
    index = {}
    sp = BeautifulSoup(wb, "html.parser")

    # <div class="outsideLinks">
    divs = iter(sp.findAll("div"))
    for div in divs:
        if div.get("class", None)==["outsideLinks"]:
            break

    countries = []
    for a in div('a'):
        if (country := a.get("href", None)) == None:
            continue
        countries.append(country.split('/')[1])

    # <div class="fl" style="max-width:600px; margin-top:5px; background-color:#FFFFFF;">
    for div in divs:
        if div.get("class", None)==["fl"]:
            break
    
    index = {}
    value = 0.0
    for country in countries:
        for div in divs:
            if (value:=rationalize(div.text)):
                break
        index[country] = value

    return (countries, index)


def testWB():
    wb = open("scrap_test.html", encoding='utf-8').read()
    return wb

fromy = 2020
toy = 2020
url = 'https://www.theglobaleconomy.com/rankings/GDP_per_capita_PPP/'
headers = {'User-Agent': 'Mozilla/5.0'}
Scp = tuple[set, dict, dict]
def scrape(url : str
           , span : tuple[int, int]=(fromy, toy)
           , proxy = None)-> Scp: 
    # import requests
    # proxies = {'http': 'http://10.11.4.254:3128'}
    # s = requests.session()
    # s.proxies.update(proxies)
    # s.get("http://www.example.com")   # Here the proxies will also be automatically used because we have attached those to the session object, so no need to pass separately in each call

    session = requests.Session()
    session.proxies.update(proxy)
    resp = session.get(url, headers=headers)

    sp = BeautifulSoup(resp.text, "html.parser")

    forms = sp('form')
    mprint(forms, "\nforms")
    form = None
    for fm in forms:
        if fm.attrs['name'] == 'indi_graph':
            form = fm
    mprint(form, "\nform")
    assert form!=None, "Error: Form \"indi_graph\" doesn't exist."

    # construct select id list
    payload = {}
    yearSet = set()
    for sls in form('select'):
        mprint(sls, "\nsls")
        id = sls.attrs['id']
        if id == "year":
            for opt in sls('option'):
                yearSet.add(rationalize(opt.get("value", None)))
        else:
            payload[id] = sls('option')[0].attrs['value']

    index_timeseries = {}
    countrySet_contained = {}
    # did this for first to get the cookies from the page, stored them with next line:
    cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    for year in range(span[0], span[1]+1):
        if year not in yearSet:
            continue
        payload['year'] = str(year)
        stime = time.time()
        resp = session.post(url, headers=headers, data=payload, cookies=cookies)
        mprint("Retriving takes:\n", time.time()-stime, '\n')
        wb = resp.text
        countrySet_contained[year], index = parseData(wb)
        index_timeseries[year] = index
        resp.close()

        time.sleep(random.random()*0.001)
    
    # not in use
    yearSet_contained = yearSet.intersection(set(index_timeseries.keys()))
        
    session.close()
    #used firebug to check POST data, password, was actually 'pass', under 'net' in param.  
    #and to move forward from here after is:
    # rst = session.get(url)

    # type: scp(set, dict, dict)
    return (yearSet_contained, countrySet_contained, index_timeseries)

def getProxies():
    response = requests.get("https://www.sslproxies.org/")
    proxy_ips = re.findall('\d+\.\d+\.\d+\.\d+:\d+', response.text)
    ips = list(proxy_ips)
    mprint('ip list length\n', len(ips))
    return ips


def filteredProxies(trunc_len=40):
    proxies = getProxies()
    assert len(proxies)>=trunc_len, "filteredProxies: requested proxies exceeds capacity"
    validP = []
    for proxy in proxies:
        try:
            fproxy = {'http': '://'.join(['http', proxy])}
            resp = requests.get("https://www.theglobaleconomy.com/rankings/GDP_per_capita_PPP/"
                                , proxies=fproxy
                                , timeout=6)
            assert resp.status_code == 200, "filteredProxies: retrieved status error"
            resp.close()
            validP.append(proxy)
        except Exception as e:
            if len(e.__repr__())>1000:
                mprint(e.__repr__()[:100], '\n...')
            else:
                mprint(e)

        if len(validP) >= trunc_len:
            break

        time.sleep(0.1+random.random()*0.1)
    return validP

def saveJson(filePath, data, concat):
    try: 
        os.makedirs(os.path.dirname(filePath)) 
    except OSError as error: 
        print(error)

    try:
        open(filePath, 'x').close()
    except:
        print("saveIndex: file already exists")

    with open(filePath, 'r') as fh:
        data_written = fh.read()
        if data_written == '':
            data_written = '{}'
        data_written = json.loads(data_written)
        data_written = concat(data_written, data)
    with open(filePath, 'w') as fh:
        fh.write(json.dumps(data_written))

# scp == (yearSet_contained, countrySet_contained, index_timeseries)
def saveIndex(name, scp):
    directory = os.path.join('data', name)

    # yearSet_contained
    # filePath = os.path.join(directory, 'yearSet_contained.json')
    # def concat0(data_written, scp0):
    #     return list(set(data_written).union(scp0))
    # saveJson(filePath, scp[0], concat0)
    # gc.collect()

    # countrySet_contained
    filePath = os.path.join(directory, 'countrySet_contained.json')    
    def concat1(data_written, scp1):
        for knew in scp1.keys():
            data_written[knew] = scp1[knew]
        return data_written
    saveJson(filePath, scp[1], concat1)
    gc.collect()

    # index_timeseries
    indexes = scp[2]
    def concat2(data_written, scp2):
        return scp2
    for year, index in indexes.items():
        filePath = os.path.join(directory, f'{year}.json')
        saveJson(filePath, index, concat2)
        gc.collect()
        
def updateTaskLog(url):
    filePath = os.path.join('data', 'taskLog.json')
    def concat(old_logs, url):
        return list(set(old_logs).discard(url))
    saveJson(filePath, url, concat)

def initializeTaskLog(urllist):
    filePath = os.path.join('data', 'taskLog.json')
    def concat(_, urllist):
        return list(urllist)
    saveJson(filePath, urllist, concat)
        
def indexName(url):
    names = url.split('/')
    while not(name:=names.pop()): pass
    return name
    
def scrapeAll(urllist, span=(fromy, toy), nthd=40):
    proxies = set(filteredProxies(nthd))
    def target_method(url, span, proxy):
        try:
            scp = scrape(url, span, proxy)
            name = indexName(url)
            saveIndex(name, scp)
            updateTaskLog(url)
        except Exception as err: 
            mprint('Retrieving Task Unsuccessful:\n', url, '\n', err)
    
    while len(urllist) > 0:
        threads = []
        ul_threading, urllist = urllist[:len(proxies)], urllist[len(proxies):]
        pxySets = proxies.copy()
        for url in ul_threading:
            proxy = pxySets.pop()
            fproxy = {'http': '://'.join(['http', proxy])}
            threads.append(threading.Thread(target=target_method
                                            , args=(url, span, fproxy)))
            gc.collect()
            
        for thd in threads:
            time.sleep(random.random()+1)
            thd.start()
        for thd in threads:
            thd.join()
        gc.collect()
    

# Execution, scrapping year span, threading counts here
def main():
    urllist = genlist()
    initializeTaskLog(urllist)
    scrapeAll(urllist[:], (2000, 2020), 10)
    
    tasklist = genTaskList()

            
# import mechanize
# bws = mechanize.Browser()
# bws.set_handle_robots(False)
# bws.addheaders = [('User-agent'
#     , 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) \
#         Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
# bws.open(url)
