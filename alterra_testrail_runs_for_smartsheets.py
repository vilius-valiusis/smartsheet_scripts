import requests
from time import sleep
import sys

# These are id's needing to be specific to project
smartSheetIdForOpenRuns = 6110252539111300
smartSheetIdForClosedRuns = 7117914143778692
testRailProjectId = 21
listOfSmartSheetIds = [smartSheetIdForOpenRuns, smartSheetIdForClosedRuns]

# This script needs the SmartSheet to be set up in advance per the below format
# It also needs to have Suites made in TestRail following a format as well.

# to be used in terminal / Jenkins:
test_rail_password = sys.argv[1]
test_rail_email = sys.argv[2]
smart_sheet_password = sys.argv[3]


def CreateOpenRunRows(type):
    # The below request gets a list of all the open test runs and current results
    # A request is then made to smartsheets, adding a row of data
    runCount = 0
    url = 'https://te2qa.testrail.net/index.php?/api/v2/' + type + '/' + str(testRailProjectId) + '&is_completed=0'
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(test_rail_email, test_rail_password))
    totalRuns = len(r.json())
    for run in r.json():
        if totalRuns != 0:
            name, passed_count, blocked_count, untested_count, retest_count, failed_count = run['name'], run[
                'passed_count'], run['blocked_count'], run['untested_count'], run['retest_count'], run['failed_count']
        else:
            name, passed_count, blocked_count, untested_count, retest_count, failed_count = '~ There are currently no ' \
                                                                                            'closed test runs listed ' \
                                                                                            '~', 0, 0, 0, 0, 0
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForOpenRuns) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smart_sheet_password}
        summary_format = ",2,1,,,,1,,,8,,,,,,"
        true = 'true'
        json = {"toBottom": true, "cells": []}
        json.setdefault("cells", []).append({"columnId": 4383007306999684, "value": name, "format": summary_format})
        json.setdefault("cells", []).append(
            {"columnId": 8886606934370180, "value": passed_count, "format": summary_format})
        json.setdefault("cells", []).append(
            {"columnId": 90513912162180, "value": blocked_count, "format": summary_format})
        json.setdefault("cells", []).append(
            {"columnId": 4594113539532676, "value": untested_count, "format": summary_format})
        json.setdefault("cells", []).append(
            {"columnId": 2342313725847428, "value": retest_count, "format": summary_format})
        json.setdefault("cells", []).append(
            {"columnId": 6845913353217924, "value": failed_count, "format": summary_format})
        r = requests.post(url, headers=headers, json=json)
        sleep(1)  # adds delay to lessen load on server
        if r.status_code == 200:
            runCount += 1
            print("Open Test Run Result Row: %i was created." % runCount)
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
            break
    if totalRuns == 0 or runCount == totalRuns:
        print("""
All %i Open TestRail Runs Have Been Published to Smartsheets.
            """ % runCount)


def CreateClosedRunRows():
    # The below request gets a list of all the open test runs and current results
    # A request is then made to smartsheets, adding a row of data
    runCount = 0
    url = 'https://te2qa.testrail.net/index.php?/api/v2/get_runs/' + str(testRailProjectId) + '&is_completed=1'
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(test_rail_email, test_rail_password))
    totalRuns = len(r.json())
    for run in r.json():
        if totalRuns != 0:
            name, passed_count, blocked_count, untested_count, retest_count, failed_count = run['name'], run[
                'passed_count'], run['blocked_count'], run['untested_count'], run['retest_count'], run['failed_count']
        else:
            name, passed_count, blocked_count, untested_count, retest_count, failed_count = '~ There are currently no closed test runs listed ~', 0, 0, 0, 0, 0
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForClosedRuns) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smart_sheet_password}
        summaryFormat = ",2,1,,,,1,,,8,,,,,,"
        true = 'true'
        json = {"toBottom": true, "cells": []}
        json.setdefault("cells", []).append({"columnId": 4838874598926212, "value": name, "format": summaryFormat})
        json.setdefault("cells", []).append(
            {"columnId": 2587074785240964, "value": passed_count, "format": summaryFormat})
        json.setdefault("cells", []).append(
            {"columnId": 7090674412611460, "value": blocked_count, "format": summaryFormat})
        json.setdefault("cells", []).append(
            {"columnId": 1461174878398340, "value": untested_count, "format": summaryFormat})
        json.setdefault("cells", []).append(
            {"columnId": 5964774505768836, "value": retest_count, "format": summaryFormat})
        json.setdefault("cells", []).append(
            {"columnId": 3712974692083588, "value": failed_count, "format": summaryFormat})
        r = requests.post(url, headers=headers, json=json)
        sleep(1)  # adds delay to lessen load on server
        if r.status_code == 200:
            runCount += 1
            print("Closed Test Run Result Row: %i was created." % runCount)
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
            break
    if totalRuns == 0 or runCount == totalRuns:
        print("""
All %i Closed TestRail Runs Have Been Published to Smartsheets.
            """ % runCount)


def DeleteRows():
    # This function deletes all the data in a sheet
    for smartSheetId in listOfSmartSheetIds:
        listOfRowsToDelete = []
        listOfRowIndexes = []
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smart_sheet_password}
        r = requests.get(url, headers=headers)
        if r.json() == [] or r.status_code != 200:
            print("No SmartSheet was returned, or a bad status")
            print("The Content is: ", r.content, 'and the status code is: ', r.status_code)
        else:
            if r.json()['rows'] == []:
                print("No rows to delete")
            else:
                for row in r.json()['rows']:
                    # makes a list of all rows
                    rowId = row['id']
                    listOfRowsToDelete.append(rowId)
        if len(listOfRowsToDelete) <= 450:
            listOfRowIndexes.append((0, len(listOfRowsToDelete)))
        else:
            for number in range(0, len(listOfRowsToDelete), 450):
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
            smallerListOfRowsToDelete = listOfRowsToDelete[
                                        beginningOfList:endOfList]  # creates a string with all the row id's in url
            for rowNumber in smallerListOfRowsToDelete:
                url = url + str(rowNumber) + ','
            url = url[:-1]  # removes the last comma
            url = url + '&ignoreRowsNotFound=true'
            headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smart_sheet_password}
            r = requests.delete(url, headers=headers)
            sleep(1)  # adds delay to lessen load on server
            if r.json()['message'] == "SUCCESS":
                print("The data in the sheet was deleted for rows between index:", beginningOfList, "and: ", endOfList)
            else:
                print("The data in the sheet was not deleted")
                print('The status code was: ', r.status_code, 'and the content was: ', r.content)


DeleteRows()
CreateOpenRunRows('get_runs')
CreateOpenRunRows('get_plans')
CreateClosedRunRows()
