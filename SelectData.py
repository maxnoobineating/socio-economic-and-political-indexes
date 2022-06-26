from datetime import MAXYEAR
import gc
import os
import functools as ft
from MaxiumMain import*

# not in use
def get_yearPath(index):
    return os.path.join('data', index, 'yearSet_contained.json')

def get_countryPath(index):
    return os.path.join('data', index, "countrySet_contained.json")

def get_allIndexes():
    return list(filter(lambda p: len(p.split('.'))==1, os.listdir('data')))

def repairLog():    
    indexes = get_allIndexes()
    for index in indexes:
        indexPath = os.path.join('data', index)
        files = os.listdir(indexPath)
        ycountries = {}
        print(index)
        for file in files:
            filePath = os.path.join(indexPath, file)
            
            #
            file_repaired = file.replace('_discarded', '')
            filePath_repaired = os.path.join(indexPath, file_repaired)
            os.rename(filePath, filePath_repaired)
            #
            
            year = file_repaired.split('.')[0]
            if year.isnumeric():
                with open(filePath_repaired, 'r') as fh:
                    data = json.loads(fh.read())
                    ycountries[year] = list(data.keys())
        
        if 'yearSet_contained.json' in files:
            filePath = os.path.join(indexPath, 'yearSet_contained.json')
            os.remove(filePath)
        
        if 'contrySet_contained.json' in files:
            filePath = os.path.join(indexPath, 'contrySet_contained.json')
            filePath_repaired = os.path.join(indexPath, 'countrySet_contained.json')
            os.rename(filePath, filePath_repaired)
        
        def concat(_, new):
            return new
        msaveJson(filePath_repaired, ycountries, concat)
        

def prompt():
    dataPath = '.\\data'
    dirs = os.listdir(dataPath)
    print(dirs)
    selected_dir = []
    num = 0
    for dir in filter(lambda d: os.path.isdir(os.path.join(dataPath, d)), dirs):
        print(f"{num}.", dir)
        num+=1
        if input("Select? [y/n]: ") == '':
            selected_dir.append(dir)
        print()
    
    def concat(old, new):
        return new
    
    msaveJson('selectedIndexes_prime.json', selected_dir, concat)
    
selectedLog = ['selectedIndexes_prime.json']    
def loadSelectedIndex(selectedPath):
    with open(selectedPath, 'r') as fh:
        jlst = json.loads(fh.read())
    return jlst

def removeSelectedIndex(index):
    taskPath = selectedLog[0]
    def concat(old, _):
        old.remove(index)
        return old
    msaveJson(taskPath, None, concat)
    


def allCountryList(gen=False):
    filePath = os.path.join('allCountries.json')
    if gen:
        # for tup in os.walk('data'):
        #     if tup[0]=='data':
        #         continue
        #     year = map(lambda p: p.split('.')[0], tup[2])
        #     year = filter(lambda p: p.isnumeric(), year)
        countries = set()
        for index in filter(lambda p: len(p.split('.'))==1, os.listdir('data')):
            indexPath = get_countryPath(index)
            with open(indexPath) as fh:
                fld = lambda x, y: x.union(y)
                data = json.loads(fh.read())
                data = map(lambda x: set(x), data.values())
                countries = countries.union(ft.reduce(fld, data))
        def concat(_, new):
            return new            
        msaveJson(filePath, list(countries), concat)
    with open(filePath, 'r') as fh:
        data = json.loads(fh.read())
        return data


def countryCount():
    index = loadSelectedIndex(selectedLog[0])
    allcountries = set(allCountryList())
    
    for ind in index:
        filePath = get_countryPath(ind)    
        cntsCount = allcountries.copy()
        with open(filePath) as fh:
            
            data = json.loads(fh.read())
            for cnts in data.values():
                cntsCount.intersection_update(set(cnts))
        num = len(cntsCount)
        num = str(num) if num>=100 else (str(num)+' ' if num>=10 else str(num)+'  ')
        print(f'{num} {ind}')
        
def access(index, year=None):
    # yearPath = get_yearPath(index)
    # with open(yearPath) as fh:
    #     years = json.loads(fh.read())
    
    countryPath = get_countryPath(index)
    with open(countryPath) as fh:
        ycountries = json.loads(fh.read())
    years = list(ycountries.keys())
        
    countries = None
    while (not year) and (not countries):
        print('Available years:\n', years)
        year = input('Which year? > ')
        countries = ycountries.get(str(year), None)
        if countries == None:
            print("Invalid year!\n")
        else:
            break
    countries = ycountries.get(str(year))
    
    print(f"\n{index} {year}:")
    print(countries)
    print(f"total: {len(countries)} countries!")
    return countries
    
def pruning(index):
    # yearPath = get_yearPath(index)
    # with open(yearPath) as fh:
    #     years = json.loads(fh.read())
    
    countryPath = get_countryPath(index)
    with open(countryPath) as fh:
        ycountries = json.loads(fh.read())
    years = list(ycountries.keys())
    
    out=False
    year_cut = list()
    while not out:
        for year in set(years).difference(set(year_cut)):
            countries = ycountries.get(str(year), None)
            assert countries!=None, "pruning: fatal error!"
            print(f'\n{year}: {len(countries)}')
            
        print('\nAvailable years:\n', years)
        year = input('Which year to prune? > ')
        countries = ycountries.get(str(year), None)
        if countries == None:
            print("Invalid year!\n")
            continue
        print(f"\n{index} {year}:")
        print(countries)
        print(f"total: {len(countries)} countries!\n")
        
        if input('Don\'t remove this year? (Enter to revert / or type anything else)>'):
            indexPath = os.path.join('data', index, f"{year}.json")
            new_indexPath = os.path.join('data', index, f"{year}_discarded.json")
            os.rename(indexPath, new_indexPath)
            
            # def concat_y(_, new):
            #     return new
            # years.remove(int(year))
            # msaveJson(yearPath, years, concat_y)
            
            def concat_c(_, new):
                return new
            ycountries.pop(str(year))
            msaveJson(countryPath, ycountries, concat_c)
            
        out = input('Countinue? > ')
        if out == '\\':
            removeSelectedIndex(index)
            
def getFullDataLog(mode=False):
    indexes = get_allIndexes()
    miny, maxy = '2100', '0'
    tempLog = {}
    for index in indexes:
        countrySetPath = os.path.join('data', index, 'countrySet_contained.json')
        with open(countrySetPath, 'r') as fh:
            data = json.loads(fh.read())
        years = list(data.keys())
        miny = min(miny, min(years))
        maxy = max(maxy, max(years))
        tempLog[index] = data
    if mode:
        return tempLog
    
    arLog = {}
    for year in range(int(miny), int(maxy)+1):
        year = str(year)
        arLog[year] = {}
        for index in indexes:
            value = tempLog[index].get(year, None)
            arLog[year][index] = value if value!=None else []
    return arLog

def delete2020():
    indexes = get_allIndexes()
    for index in indexes:
        try:
            filePath = os.path.join('data', index, '2020.json')
            os.remove(filePath)
        except: pass
        countryPath = get_countryPath(index)
        def concat(old, _):
            try:
                old.pop('2020')
            except: pass
            return old
        msaveJson(countryPath, None, concat)
        

    
# index autoPruned
def autoPrune(indexNum=120, gen=False):
    if gen:
        fullLog = getFullDataLog()
        allCountries = set(allCountryList())
        def getDataPoints(ditched_indexes, gen=False):
            ditched_indexes = set(ditched_indexes)
            dataPoints = []
            count = 0
            for year in fullLog:
                countries = allCountries.copy()
                indexes =   set(fullLog[year].keys())
                for index in indexes.difference(ditched_indexes):
                    countries.intersection_update(set(fullLog[year][index]))
                count += len(countries)
                if gen:
                    dataPoints.extend([(year, country) for country in countries])
            return count, dataPoints
        
        ditched_indexes = initDitchList()
        indexes = list(set(get_allIndexes()).difference(set(ditched_indexes)))
        assert (indexNum>0) and (len(indexes)>=indexNum), "autoPrune: ..."    
        maxPoints = 0 
        # it shouldn't be possible for "ditching indexes" to produce a lower dataPoints count
        # but still...
        while len(indexes)>indexNum:
            gc.collect()
            # maxPoints = 0
            ditched_index = indexes[0]
            for index in indexes:
                gc.collect()
                tempPoints = getDataPoints(ditched_indexes+[index])[0]
                if tempPoints > maxPoints:
                    maxPoints = tempPoints
                    ditched_index = index
            print(f"# {ditched_index} removed!")
            print(f"# total {maxPoints} points. {len(indexes)} indexes remained.")

            indexes.remove(ditched_index)
            ditched_indexes.append(ditched_index)
        points = getDataPoints(ditched_indexes, gen=True)[1]
        def concat(_, new):
            return new
        msaveJson('autoPrune.json', [indexes, points], concat)
        
    with open('autoPrune.json', 'r') as fh:    
        autoPruned = json.loads(fh.read())
    indexes, points = autoPruned[0], autoPruned[1]
    return indexes, points



def initDitchList():
    fullLog = getFullDataLog(mode=True)
    ditched_indexes = []
    for index in fullLog:
        if len(list(filter(lambda x: len(x)>100, fullLog[index].values())))<19:
            ditched_indexes.append(index)
    return ditched_indexes

def getDataPoints_test(ditched_indexes, gen=False):
    fullLog = getFullDataLog()
    allCountries = set(allCountryList())
    
    ditched_indexes = set(ditched_indexes)
    dataPoints = []
    count = 0
    for year in fullLog:
        countries = allCountries.copy()
        print(f"Starts with: {len(countries)}\n")
        indexes =   set(fullLog[year].keys())
        # mprint(f"Remaining indexes: \n{indexes.difference(ditched_indexes)}")
        for index in indexes.difference(ditched_indexes):
            countries.intersection_update(set(fullLog[year][index]))
            print(f"Remained: {len(countries)}\n")
        # print(f"Intersected countries:{countries}\n")
        count += len(countries)
        if gen:
            dataPoints.extend([(year, country) for country in countries])
    return count, dataPoints
        
def select_perCapita():pass
    
def select_perlandArea():pass

def select_purchasingPower():pass


if __name__ == "__main__":
    prompt()