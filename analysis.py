import csv
from sklearn import linear_model
import os
import json
import SelectData as sd
import pycountry_convert as pc
import statistics as stats
import numpy as np
from numpy import array as arr
from MaxiumMain import *

# data structure:
# matrix
# [{'index1':a11, ..., 'year':XXXX}, {'index1':a12, ..., 'year':XXXX}, ...]
# target Vec
# [v1, v2, v3, ...]
def loadIndexData(indexes):
    indexData = {}
    for index in indexes:
        indexPath = os.path.join('data', index)
        files = filter(lambda p: p.split('.')[0].isnumeric(), os.listdir(indexPath))
        indexData[index] = {}
        for file in files:
            filePath = os.path.join(indexPath, file)
            with open(filePath, 'r') as fh:
                data = json.loads(fh.read())
            year = file.split('.')[0]
            indexData[index][year] = data
    return indexData

def loadVecData():
    vecdict = {}
    for file in os.listdir('pressData'):
        year = file.split('.')[0]
        if year > '2019':
            continue
        vecdict[year] = {}

        filePath = os.path.join('pressData', file)
        with open(filePath, 'r', encoding='utf-8') as fh:
            for row in list(csv.reader(fh))[1:]:
                alpha3 = row[0].split(';')[1]
                score = float(f"{row[0].split(';')[-1]}.{row[1].split(';')[0]}")
                vecdict[year][alpha3] = score
    return vecdict

from matplotlib import pyplot as plt
def drawDataPoints():
    _, points = sd.autoPrune()
   
def country2alpha(countryName, mode=3):
    countryName = countryName.replace('-', ' ')
    if mode == 2:
        if countryName == 'Laos':
            countryName = 'LA'
        if countryName == 'Democratic Republic of the Congo':
            countryName = 'CD'
        if countryName == 'Burma Myanmar':
            countryName = 'MM'
        if countryName == 'Cape Verde':
            countryName = 'CV'
        if countryName.lower() == 'swaziland':
            countryName = 'SZ'
        alpha2 = pc.country_name_to_country_alpha2(countryName)
        return alpha2
    elif mode == 3:
        if countryName == 'Laos':
            countryName = 'LAO'
        if countryName == 'Democratic Republic of the Congo':
            countryName = 'COD'
        if countryName == 'Burma Myanmar':
            countryName = 'MMR'
        if countryName == 'Cape Verde':
            countryName = 'CPV'
        if countryName.lower() == 'swaziland':
            countryName = 'SWZ'
        alpha3 = pc.country_name_to_country_alpha3(countryName)
        return alpha3


def countryList_continent():
    allCountry = sd.allCountryList()
    cntDict = {}
    for country in allCountry:
        alpha2 = country2alpha(country, mode=2)
        continent = pc.country_alpha2_to_continent_code(alpha2)
        cntDict.setdefault(continent, []).append(country)
    allCountryList = []
    for continent in cntDict:
        allCountryList += cntDict[continent]
    return allCountryList
    
def loadMatrixVec():
    pruned = sd.autoPrune()
    indexes, points = pruned[0], pruned[1]
    indexData = loadIndexData(indexes)
    vecdict = loadVecData()
    
    mat = []
    vec = []
    for point in points:
        year, country = point[0], point[1]
        if year not in vecdict:
            continue
        

            
        try:
            score = vecdict[year][alpha2]
        except KeyError:
            maxy = max(vecdict.keys())
            miny = min(vecdict.keys())
            stepa, yeara = 0, year
            stepb, yearb = 0, year
            
            while yeara<maxy:
                stepa += 1
                yeara = str(int(year)+stepa)
                try:
                    scorea = vecdict[yeara][alpha3]
                    break
                except: pass
            else:
                continue
            
            while yearb>maxy:
                stepb += 1
                yearb = str(int(year)-stepb)
                try:
                    scoreb = vecdict[yearb][alpha3]
                    break
                except: pass
            else:
                continue
            
            score = (scorea*stepb + scoreb*stepa)/(stepa + stepb)
            
        vec.append(score)
        
        mat.append({})
        for index in indexes:
            mat[-1][index] = indexData[index][year]
        else:
            mat[-1]['year'] = float(year)
            
    return mat, vec

# return key list, matNd
def normalizeMat(mat):
    keys = []
    height = len(mat)
    width = len(mat[0].keys())
    matNd = np.zeros((height, width))
    for y, key in enumerate(mat[0].keys()):
        keys.append(key)
        for x, row in enumerate(mat):
            print(row)
            matNd[x, y] = row[key]
            
    for y, column in enumerate(matNd.T):
        std = stats.stdev(column)
        mean = stats.mean(column)
        matNd.T[y] = (column - arr(np.ones(len(column))*mean))/std
    return keys, matNd

def solveLasso(alf, gen=False):
    if gen:
        mat, vec = loadMatrixVec()
        paramKeys, matNd = normalizeMat(mat)
        np.save('matNd.npy', matNd)
        np.save('vec.npy', vec)
        def concat(_, new):
            return new
        msaveJson('paramKeys.json', paramKeys, concat)
    matNd = np.load('matNd.npy')
    vec = np.load('vec.npy')
    with open('paramKeys.json', 'r') as fh:
        paramKeys = json.loads(fh.read())
        
    lasso = linear_model.Lasso(alpha=alf, fit_intercept=False)
    lasso.fit(matNd, vec)
    coefs = lasso.coef_
    
    results = {}
    for n, k in enumerate(paramKeys):
        results[k] = coefs[n]
    return results