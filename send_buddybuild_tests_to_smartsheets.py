# script to run this: python send_buddybuild_tests_to_testrail.py qoSvL7k03PrOruS33BtO-gQnhuTH6YkLwpSq1B499 aNWQiuLXxbIuVsoyIEAuSjXtc9FKkPnLGVGl5DM0eiNsI34B6lumFEIfOprIIuBuKH7kh7yjbydBhql2IIC15KIRwRHrjXWj6pgHduYwYoT4sPGufsFBtWt2WAr3

import re
import requests
import sys
import datetime
from time import sleep

# to be used in terminal:
smartSheetPassword = sys.argv[1]
buddyBuildPassword = sys.argv[2]

# it is essential that a new test rail group / suite id is created & the app id from buddy build obtained:
smartSheetId = 678999568476036
buddyBuildAppId = '5b7b167d204de90001cfaf68'

month = datetime.date.today().strftime("%B")
date = datetime.date.today().strftime("%d")
year = datetime.date.today().strftime("%Y")
dateHeader = date + " " + month + " " + year

# the below call to buddybuild gets the last successful build number, the test summary details
url = 'https://api.buddybuild.com/v1/apps/' + str(buddyBuildAppId) + '/builds?branch=dev&status=success&scheme=Alterra - QA&limit=20'
headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + str(buddyBuildPassword)}
r = requests.get(url, headers=headers)
if len(r.json()) == 0:
    print("There are no builds listed.")
buildNumber = r.json()[0]['build_number']
testsCount = r.json()[0]['test_summary']['tests_count']
testsPassed = r.json()[0]['test_summary']['tests_passed']
branch = r.json()[0]['commit_info']['branch']
buddyBuildId = r.json()[0]['_id']

print("Build Number %i is returning %i unit tests with %i tests that have passed." % (buildNumber, testsCount, testsPassed))
print("This program will now populate a smartsheet from this DEV branch build, pointing to Alterra QA.")


listOfStringsForSmartsheet = ["Unit Tests Passed","Unit Tests Failed"]
listOfResults = [testsPassed, testsCount - testsPassed]

def CreateRows():
    # This function parses a buddybuild log file and lists each test category, test name & test result
    # It then populated a smartsheet ID with this data as columns
    # the below call to buddybuild gets the test results

    url = 'https://api.buddybuild.com/v1/builds/' + str(buddyBuildId) + '/tests?showFailed=true&showPassing=true'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + str(buddyBuildPassword)}
    r = requests.get(url, headers=headers)
    tests = r.json()['tests']
    rowCount = 0

    for test in tests:
        suiteName = test['suite']
        suiteName = re.sub(r"(?<=\w)([A-Z])", r" \1", suiteName) # puts a space in front of a capitol letter
        suiteName = suiteName.replace('A M P A P I ', 'AMP API ')
        suiteName = suiteName.replace('T E2 A P I ', 'TE2 API ')
        suiteName = suiteName.replace('U I', 'UI')
        testName = test['test']
        testName = testName[:-2] # takes the last 2 char off of string, the ()
        testName = re.sub(r"(?<=\w)([A-Z])", r" \1", testName) # puts a space in front of a capitol letter
        testName = testName.replace('__', ' ')
        testName = testName.replace('_', ' ')
        testStatus= test['status']


        # the below call to smartsheets creates each row
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        true = 'true'
        summaryFormat = ",2,1,,,,1,,,8,,,,,,"
        normalFormat = ",,,,,,,,,18,,,,,,"
        if rowCount == 0:
            json = {"toBottom": true, "cells": []}
            json.setdefault("cells", []).append({"columnId": 5230159944017796,"value":listOfStringsForSmartsheet[0],"format":summaryFormat})
            json.setdefault("cells", []).append({"columnId": 1194581829150596, "value": listOfResults[0], "format": summaryFormat})
            #json.setdefault("cells", []).append({"columnId": 2024339445966724, "value": testStatus, "format": normalFormat})
            #json.setdefault("cells", []).append({"columnId": 6527939073337220, "value": suiteName, "format": normalFormat})
            json.setdefault("cells", []).append({"columnId": 7469219810961284, "value": buildNumber, "format": summaryFormat})
            #json.setdefault("cells", []).append({"columnId": 4276139259651972, "value": testName, "format": normalFormat})
            print("  ~~  Summary Line Created  ~~  ")
        else:
            json = {"toBottom": true, "cells": []}
            if len(listOfStringsForSmartsheet) > rowCount:
                json.setdefault("cells", []).append({"columnId": 5230159944017796,"value":listOfStringsForSmartsheet[rowCount],"format":summaryFormat})
            if len(listOfResults) > rowCount:
                json.setdefault("cells", []).append({"columnId": 1194581829150596, "value": listOfResults[rowCount], "format": summaryFormat})
            #json.setdefault("cells", []).append({"columnId": 2024339445966724, "value": testStatus, "format": normalFormat})
            #json.setdefault("cells", []).append({"columnId": 6527939073337220, "value": suiteName, "format": normalFormat})
            #json.setdefault("cells", []).append({"columnId": 4276139259651972, "value": testName, "format": normalFormat})
            if rowCount == 2:
                print("There are no more rows to create. There were %i rows created in total" % rowCount)
                break
        r = requests.post(url, headers=headers, json=json)
        sleep(1) # adds delay to lessen load on server
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

