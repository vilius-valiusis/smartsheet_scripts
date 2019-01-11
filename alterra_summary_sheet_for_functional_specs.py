import requests
from time import sleep
import sys

# These are id's needing to be specific to project
smartSheetIdWithFunctionalSpecs = 373717856479108
smartSheetIdForSummarySheet = 3742142863566724

# to be used in terminal / Jenkins:
smartSheetPassword = sys.argv[1]

listOfValues = [] # list of unique values
fullList = [] # list of all values from sheet
valueCountDict = {}
def ParseSheet():
    # This function goes through the smartsheet and gets all the  all the data in a sheet
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdWithFunctionalSpecs)
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    r = requests.get(url, headers=headers)
    if r.json() == [] or r.status_code != 200:
        print("No SmartSheet was returned, or a bad status")
        print("The Content is: ", r.content, 'and the status code is: ', r.status_code)
    else:
        for row in r.json()['rows'][2:48]: # first row has no data
            value = row['cells'][1].get('value')
            if value not in listOfValues:
                listOfValues.append(value)
            fullList.append(value)
    for valueInList in listOfValues:
        counter = 0
        for valueInFullList in fullList:
            if valueInList == valueInFullList:
                counter += 1
        valueCountDict.update({valueInList:counter})
    print("The Dictionary of Values and Counts is:", valueCountDict)
    keyList = []
    for key in valueCountDict:
        if key not in keyList:
            keyList.append(key)
    keyList = sorted(keyList)
    print(keyList)

    # This request populates the summary sheet:
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForSummarySheet) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    summaryFormat = ",2,1,,,,1,,,8,,,,,,"
    true = 'true'
    json = {"toBottom": true, "cells": []}
    json.setdefault("cells", []).append(
        {"columnId": 5127421776160644, "value": 'Functional Spec Status:', "format": summaryFormat})
    r = requests.post(url, headers=headers, json=json)
    if r.status_code == 200:
        print("Line 1 Created")
    else:
        print("The line was not created")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)
    rowNumber = 1
    for keyInKeyList in keyList:
        rowNumber += 1
        json = {"toBottom": true, "cells": []}
        json.setdefault("cells", []).append({"columnId": 2875621962475396, "value": valueCountDict[keyInKeyList], "format": summaryFormat})
        if keyInKeyList == None:
            keyInKeyList = "None"
        json.setdefault("cells", []).append({"columnId": 5127421776160644, "value": keyInKeyList, "format": summaryFormat})
        r = requests.post(url, headers=headers, json=json)
        if r.status_code == 200:
            print("Line %i Created" % rowNumber)
        else:
            print("The line was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)

def DeleteRows():
    # This function deletes all the data in a sheet
    listOfRowsToDelete = []
    listOfRowIndexes = []
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForSummarySheet)
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    r = requests.get(url, headers=headers)
    if r.json() == [] or r.status_code != 200:
        print("No SmartSheet was returned, or a bad status")
        print("The Content is: ", r.content, 'and the status code is: ', r.status_code)
    else:
        if r.json()['rows'] ==[]:
            print("No rows to delete")
        else:
            for row in r.json()['rows']:
                # makes a list of all rows
                rowId = row['id']
                listOfRowsToDelete.append(rowId)
    if len(listOfRowsToDelete) <= 450:
        listOfRowIndexes.append((0, len(listOfRowsToDelete)))
    else:
        for number in range (0,len(listOfRowsToDelete), 450):
            # this creates a list of indexes to run through in blocks of 450
            if number <= len(listOfRowsToDelete) - 450:
                listOfRowIndexes.append((number, number + 450))
            else:
                listOfRowIndexes.append((number, len(listOfRowsToDelete)))
    for rowIndex in listOfRowIndexes:
        # this runs through all rows to delete, 450 at a time as this is max url legnth.
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForSummarySheet) + '/rows?ids='
        beginningOfList = rowIndex[0]
        endOfList = rowIndex[1]
        smallerListOfRowsToDelete = listOfRowsToDelete[beginningOfList:endOfList] # creates a string with all the row id's in url
        for rowNumber in smallerListOfRowsToDelete:
            url = url + str(rowNumber) + ','
        url = url[:-1] # removes the last comma
        url = url + '&ignoreRowsNotFound=true'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        r = requests.delete(url, headers=headers)
        sleep(1) # adds delay to lessen load on server
        if r.json()['message'] == "SUCCESS":
            print("The data in the sheet was deleted for rows between index:", beginningOfList, "and: ",endOfList)
        else:
            print("The data in the sheet was not deleted")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)


DeleteRows()
ParseSheet()

