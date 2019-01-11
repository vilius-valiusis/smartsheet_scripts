# script to run this: python send_buddybuild_tests_to_testrail.py qoSvL7k03PrOruS33BtO-gQnhuTH6YkLwpSq1B499 aNWQiuLXxbIuVsoyIEAuSjXtc9FKkPnLGVGl5DM0eiNsI34B6lumFEIfOprIIuBuKH7kh7yjbydBhql2IIC15KIRwRHrjXWj6pgHduYwYoT4sPGufsFBtWt2WAr3

import re
import requests
import sys
import datetime
from time import sleep

# to be used in terminal:
smartSheetPassword = sys.argv[1]
appCenterPassword = sys.argv[2]

# it is essential that a new test rail group / suite id is created & the app id from buddy build obtained:
smartSheetId = 1135760750471044
buildNumber = 0

month = datetime.date.today().strftime("%B")
date = datetime.date.today().strftime("%d")
year = datetime.date.today().strftime("%Y")
dateHeader = date + " " + month + " " + year

branch = 'develop'
# the below call to app center gets the last successful build number, - needs to be configured per app
url = 'https://api.appcenter.ms/v0.1/apps/te2org-qc1x/Alterra/branches/%s/builds' % (branch)
headers = {'Cache-Control': 'no-cache', 'X-API-Token': appCenterPassword}
r = requests.get(url, headers=headers)
if r.status_code == 200:
    print("An Android build was successfully found")
else:
    print("An Android build was NOT successfully found")
    print('The status code was: ', r.status_code, 'and the content was: ', r.content)
if len(r.json()) == 0:
    print("There are no builds listed.")
for build in r.json():
    if build['status'] == 'completed':
        if build['result'] == 'succeeded':
            buildNumber = (build['id'])
            break


def CreateRows():
    # This function parses a app center log file and lists each test category, test name & test result
    # It then populated a smartsheet ID with this data as columns
    url = 'https://api.appcenter.ms/v0.1/apps/te2org-qc1x/Alterra/builds/' + str(buildNumber) + '/logs'
    headers = {'Cache-Control': 'no-cache', 'X-API-Token': appCenterPassword}
    r = requests.get(url, headers=headers)
    lines = r.json()['value']
    testsCount =0
    testsPassed = 0
    rowCount = 0
    for lineForPassedAndCount in lines:
        if 'mtnco.ikonpass.logic.' in lineForPassedAndCount:
            testsCount += 1
        if "PASSED" in lineForPassedAndCount:
            testsPassed += 1
    print("Build Number %i is returning %i unit tests with %i tests that have passed." % (buildNumber, testsCount, testsPassed))
    listOfStringsForSmartsheet = ["Unit Tests Passed", "Unit Tests Failed"]
    listOfResults = [testsPassed, testsCount - testsPassed]
    for line in lines:
        if 'mtnco.ikonpass.logic.' in line:
            line = line[57:] # removes part of the log line not needed
            suiteName, sep, testNameAndResult = line.partition('Test >') # separates out the suite name
            suiteName = suiteName.replace('.', ' ')
            suiteName = re.sub(r"(?<=\w)([A-Z])", r" \1", suiteName)  # puts a space in front of a capitol letter
            suiteName = re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), suiteName, 1) # makes the first word a cap
            testNameAndResult = testNameAndResult.replace(' test','')
            testNameAndResult = testNameAndResult.replace('  ',' ')
            if testNameAndResult[:1] == ' ':
                testNameAndResult = testNameAndResult[1:] # takes the space
            testResult = testNameAndResult[-6:] # defines the result as last 6 char in string
            testName = testNameAndResult[0:-7] # takes off the result
            testName = re.sub(r"(?<=\w)([A-Z])", r" \1", testName)  # puts a space in front of a capitol letter
            testName = testName.title() # makes the first letters caps
            normalFormat = ",,,,,,,,,18,,,,,,"
            summaryFormat = ",2,1,,,,1,,,8,,,,,,"

            # the below call to smartsheets creates each row
            url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
            headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
            true = 'true'
            if rowCount == 0:
                json = {"toBottom": true, "cells": []}
                json.setdefault("cells", []).append({"columnId": 5422066598995844, "value": listOfStringsForSmartsheet[0], "format": summaryFormat})
                json.setdefault("cells", []).append({"columnId": 3170266785310596, "value": listOfResults[0], "format": summaryFormat})
                json.setdefault("cells", []).append({"columnId": 7673866412681092, "value": buildNumber, "format": summaryFormat})
                print("  ~~  Summary Line Created  ~~  ")
            else:
                json = {"toBottom": true, "cells": []}
                if len(listOfStringsForSmartsheet) > rowCount:
                    json.setdefault("cells", []).append({"columnId": 5422066598995844, "value": listOfStringsForSmartsheet[rowCount],"format": summaryFormat})
                if len(listOfResults) > rowCount:
                    json.setdefault("cells", []).append({"columnId": 3170266785310596, "value": listOfResults[rowCount], "format": summaryFormat})
                if rowCount == 2:
                    print("There are no more rows to create. There were %i rows created in total" % rowCount)
                    break
            r = requests.post(url, headers=headers, json=json)
            sleep(1)  # adds delay to lessen load on server
            if r.status_code == 200:
                rowCount += 1
                print("Row: " + str(rowCount) + " was created.")
            else:
                print("The row in the sheet was not created")
                print('The status code was: ', r.status_code, 'and the content was: ', r.content)
        if rowCount == testsCount:
            print("Finished - All rows were successfully updated")


def DeleteRowData():
    # This function deletes all the data in a sheet
    listOfRowsToDelete = []
    listOfRowIndexes = []
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
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
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows?ids='
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




DeleteRowData()
CreateRows()
