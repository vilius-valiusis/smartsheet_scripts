# the below are to be used outside of terminal:

import re
import requests
import sys
import datetime
from time import sleep

# to be used in terminal:
smartSheetPassword = sys.argv[1]
jenkinsAuthString = sys.argv[2]

# it is essential that a new test rail group / suite id is created & the app id from buddy build obtained:
smartSheetId = 853976536115076
jenkinsJobName = 'build-alterra-proxy-service-master'

month = datetime.date.today().strftime("%B")
date = datetime.date.today().strftime("%d")
year = datetime.date.today().strftime("%Y")
dateHeader = date + " " + month + " " + year

# the below call to jenkins gets the last successful build number, the test summary details
url = 'https://ci.te2.biz/jenkins/job/' + jenkinsJobName + '/lastSuccessfulBuild/api/json'
headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + jenkinsAuthString}
print (url)
print(headers)
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print("Error: The request to get the last Jenkins build was not successful. The response code was: ", r.status_code)
    print("The Response content was: ", r.content)
    exit()
else:
    buildNumber = r.json()['id']
    lastSuccessfulBuildUrl = r.json()['url'] + 'testReport/api/json'
    testsCount = r.json()['actions'][6]['totalCount']
    testsPassed = r.json()['actions'][6]['totalCount'] - r.json()['actions'][6]['failCount']
    print("Alterra Proxy Service Master Build Number %s is returning %i unit tests with %i tests that have passed." % (buildNumber, testsCount, testsPassed))
    print("This program will now create a fresh SmartSheet from this Alterra branch build.")

# the below call updates the smartsheet name
# url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
# headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + smartSheetPassword}
# json = {"name": "ALT Back-End Unit Tests"}
# r = requests.put(url, headers=headers, json=json)
# print("Build Number %s is returning %s unit tests with %s tests that have passed." % (buildNumber, testsCount, testsPassed))
# print("This program will now populate a smartsheet from this DEV branch build, pointing to Alterra QA.")
# if r.status_code == 200:
#     print("The smartsheet name was successfully changed")
# else:
#     print("The smartsheet name was NOT successfully changed")
#     print('The status code was: ', r.status_code, 'and the content was: ', r.content)

listOfStringsForSmartsheet = ["Unit Tests Passed", "Unit Tests Failed"]
listOfResults = [testsPassed, testsCount - testsPassed]

def CreateRows():
    # This function parses a jenkins log file and lists each test category, test name & test result
    # It then populated a smartsheet ID with this data as columns
    # the below call to buddybuild gets the test results
    status_id = 0
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + jenkinsAuthString}
    r = requests.get(lastSuccessfulBuildUrl, headers=headers)
    suites = r.json()['childReports'][0]['result']['suites']
    testCount = 0
    rowCount = 0
    for suite in suites: # runs through each suite listed
        suiteName = suite['cases'][0]['className']
        suiteName = re.sub(r"(?<=\w)([A-Z])", r" \1", suiteName)  # puts a space in front of a capitol letter
        suiteName = (suiteName[31:]).replace('.', ' ').capitalize()
        # this removes the 'biz.te2.services.alterra.proxy.' part of the string, makes spaces
        tests = suite['cases'] # runs through each test in each suite
        for test in tests:
            testCount += 1
            testName = test['name']
            testName = re.sub(r"(?<=\w)([A-Z])", r" \1", testName) # puts a space in front of a capitol letter
            testName = testName.capitalize()
            testStatus = test['status']

            # the below call to smartsheets creates each row

            url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
            headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
            true = 'true'
            summaryFormat = ",2,1,,,,1,,,8,,,,,,"
            normalFormat = ",,,,,,,,,18,,,,,,"
            if rowCount == 0:
                json = {"toBottom": true, "cells": []}
                json.setdefault("cells", []).append(
                    {"columnId": 1191047071065988, "value": listOfStringsForSmartsheet[0], "format": summaryFormat})
                json.setdefault("cells", []).append(
                    {"columnId": 5694646698436484, "value": listOfResults[0], "format": summaryFormat})
                # json.setdefault("cells", []).append({"columnId": 2024339445966724, "value": testStatus, "format": normalFormat})
                # json.setdefault("cells", []).append({"columnId": 6527939073337220, "value": suiteName, "format": normalFormat})
                json.setdefault("cells", []).append(
                    {"columnId": 3442846884751236, "value": buildNumber, "format": summaryFormat})
                # json.setdefault("cells", []).append({"columnId": 4276139259651972, "value": testName, "format": normalFormat})
                print("  ~~  Summary Line Created  ~~  ")
            else:
                json = {"toBottom": true, "cells": []}
                if len(listOfStringsForSmartsheet) > rowCount:
                    json.setdefault("cells", []).append(
                        {"columnId": 1191047071065988, "value": listOfStringsForSmartsheet[rowCount],
                         "format": summaryFormat})
                if len(listOfResults) > rowCount:
                    json.setdefault("cells", []).append(
                        {"columnId": 5694646698436484, "value": listOfResults[rowCount], "format": summaryFormat})
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
        if rowCount == 2:
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
