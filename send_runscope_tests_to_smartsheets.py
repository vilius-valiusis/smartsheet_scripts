# script to run this: python send_buddybuild_tests_to_testrail.py qoSvL7k03PrOruS33BtO-gQnhuTH6YkLwpSq1B499 aNWQiuLXxbIuVsoyIEAuSjXtc9FKkPnLGVGl5DM0eiNsI34B6lumFEIfOprIIuBuKH7kh7yjbydBhql2IIC15KIRwRHrjXWj6pgHduYwYoT4sPGufsFBtWt2WAr3

import requests
import sys
import datetime
from time import sleep

# to be used in terminal:
smartSheetPassword = sys.argv[1]
runScopePassword = sys.argv[2]

listOfColumnIds = [3916597212538756, 8420196839909252, 1101847445432196, 5605447072802692, 2298030197106564, 6801629824477060]
listOfColumnTitles =  ['Pass vs. Fail', 'Most Recent Test Results', 'Current Alterra Endpoint Status',
                       'Time & Date of Last Alterra Endpoint Test', 'List of Alterra Endpoints Tested', 'Last Status']

# it is essential that a new test rail group / suite id is created & the app id from buddy build obtained:
smartSheetId = 2920629436475268
smartSheetSummaryId = 1719428015515524
smartSheetHistoricalId = 857155348785028
runScopeBucketId = '77lvn1mrcmle'
runScopeTestIdList = []
listOfUrls = []
updatedUrlList = []
endPointTestsPassed = 0
endPointTestsFailed = 0

# This call gets the full list of test uuid's for the bucket:
url = 'https://api.runscope.com/buckets/' + str(runScopeBucketId) + '/tests'
headers = {'Authorization': 'Bearer ' + runScopePassword}
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print("Request for list of Runscope Test id's Failed")
    print(r.status_code)
    print(r.content)
    exit()
else:
    for test in r.json()['data']:
        testId = test['id']
        runScopeTestIdList.append(testId)


# the below call to runscope gets the last test summary details
for runScopeTestId in runScopeTestIdList:
    url = 'https://api.runscope.com/buckets/' + str(runScopeBucketId) + '/tests/' + str(runScopeTestId) + '/results/latest'
    headers = {'Authorization': 'Bearer ' + runScopePassword}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("Request for latest Runscope Test %s Failed" % runScopeTestId)
        print(r.status_code)
        print(r.content)
        exit()
    else:
        print("Request for latest Runscope Test %s was successful" % runScopeTestId)
        data = r.json()['data']
        endPointTestsPassed += int(data['assertions_passed'])
        endPointTestsFailed += int(data['assertions_failed'])
        if data['finished_at'] is not None:
            currentTime = float(data['finished_at'])
            print("Current Time is: ", currentTime)
            timeFinished = datetime.datetime.utcfromtimestamp(currentTime).strftime('%H:%M:%S %m/%d/%y UTC')
        else:
            print("Current Time Was Null")
            currentTime = 1544190478.588956
            timeFinished = datetime.datetime.utcfromtimestamp(1544190478.588956).strftime('%H:%M:%S %m/%d/%y UTC')
        for request in data['requests']:
            if (request['url'],request['result']) not in listOfUrls and request['url'] is not None:
                listOfUrls.append((request['url'],request['result']))

        print("""
        The runscope test with the id: %s
        run on %s results were successfully parsed with:
        %i tests have now failed in total,
        %i tests passed in total, 
        '%s' is the current status of this one test
        and %i urls have now been tested in total. 
        """ % (
        runScopeTestId, timeFinished, endPointTestsFailed, endPointTestsPassed, data['result'], len(listOfUrls)))

for item in listOfUrls: # makes all links unclickable
    updatedUrlList.append((item[0].replace("https://", ""), item[1]))

if endPointTestsFailed != 0:
    currentEndpointStatus = "All Alterra Endpoints are NOT working - %i / %i failing" % (endPointTestsFailed, endPointTestsPassed + endPointTestsFailed)
else:
    currentEndpointStatus = "All Alterra Endpoints are working - %i / %i passing" % (endPointTestsPassed, endPointTestsPassed + endPointTestsFailed)


# The below call returns the list of columns for the sheet, making a dictionary of ID's and Titles
# This allows the script to confirm colums are correct before populating them
idTitleDict = {}
url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/columns'
headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print('Error: The SmartSheet was not found.')
else:
    for column in r.json()['data']:
        columnId = column['id']
        columnTitle = column['title']
        if columnTitle not in listOfColumnTitles:
            print("The Column with title: %s did not show up in the preset list. The sheet may need updating..." % (columnTitle))
            break
        if columnId not in listOfColumnIds:
            print("The Column with id: %i did not show up in the preset list. The sheet may need updating..." % (columnId))
            break
        idTitleDict.update({columnId: columnTitle})

listOfStringsForSmartsheet = ["Endpoint Tests Passed","Endpoint Tests Failed"]
listOfTestResults = [endPointTestsPassed, endPointTestsFailed]

def CreateRows():
    # This function creates rows from the above data, per column
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    summaryFormat = ",2,1,,,,1,,,8,,,,,,"
    normalFormat = ",,,,,,,,,18,,,,,,"
    true = 'true'
    for rowCount in range(0,len(listOfUrls)):
        if rowCount == 0:
            json = {"toBottom":true,"cells":[]}
            for columnId in idTitleDict:
                columnTitle = idTitleDict[columnId]
                if columnTitle == 'Pass vs. Fail':
                    json.setdefault("cells", []).append({"columnId": columnId,"value":listOfStringsForSmartsheet[0],"format":summaryFormat})
                if columnTitle == 'Most Recent Test Results':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": listOfTestResults[0], "format": summaryFormat})
                if columnTitle == 'Current Alterra Endpoint Status':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": currentEndpointStatus, "format": summaryFormat})
                if columnTitle == 'Time & Date of Last Alterra Endpoint Test':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": timeFinished, "format": summaryFormat})
                if columnTitle == 'List of Alterra Endpoints Tested':
                    if len(updatedUrlList) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": updatedUrlList[0][0], "format": normalFormat})
                if columnTitle == 'Last Status':
                    if len(updatedUrlList) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": updatedUrlList[0][1], "format": normalFormat})
            print("  ~~  Summary Line Created  ~~  ")
        else:
            json = {"toBottom":true,"cells":[]}
            for columnId in idTitleDict:
                columnTitle = idTitleDict[columnId]
                if columnTitle == 'Pass vs. Fail':
                    if len(listOfStringsForSmartsheet) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId,"value":listOfStringsForSmartsheet[rowCount],"format":summaryFormat})
                if columnTitle == 'Most Recent Test Results':
                    if len(listOfTestResults) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfTestResults[rowCount], "format": summaryFormat})
                if columnTitle == 'List of Alterra Endpoints Tested':
                    if len(updatedUrlList) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": updatedUrlList[rowCount][0], "format": normalFormat})
                if columnTitle == 'Last Status':
                    if len(updatedUrlList) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": updatedUrlList[rowCount][1], "format": normalFormat})
            if json["cells"] == []:
                print("There are no more rows to create. There were %i rows created in total" % rowCount)
                break
        r = requests.post(url, headers=headers, json=json)
        #sleep(1) # adds delay to lessen load on server
        if r.status_code == 200:
            rowCount +=1
            print("Row: " + str(rowCount) + " was created.")
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
    if rowCount == len(listOfUrls):
        print("Finished - All rows were successfully updated")

def CreateHistoricalRows():
    # This function creates rows from the above data, per column - this is hard coded as it is only one row each time
    now = datetime.datetime.now()
    hour = now.strftime('%H')
    min = now.strftime('%M')
    today = now.strftime('%m/%d/%y')
    if int(hour) == 12 and int(min)>=30:
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetHistoricalId) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        summaryFormat = ",2,1,,,,1,,,8,,,,,,"
        true = 'true'
        json = {"toBottom":true,"cells":[]}
        json.setdefault("cells", []).append({"columnId": 3725536934553476, "value": currentEndpointStatus, "format": summaryFormat})
        json.setdefault("cells", []).append({"columnId": 5977336748238724, "value": today, "format": summaryFormat})
        json.setdefault("cells", []).append({"columnId": 3865896465786756, "value": endPointTestsPassed, "format": summaryFormat})
        json.setdefault("cells", []).append({"columnId": 8369496093157252, "value": endPointTestsFailed, "format": summaryFormat})
        r = requests.post(url, headers=headers, json=json)
        if r.status_code == 200:
            print("  ~~  Historical Summary Line Created  ~~  ")
        else:
            print("The historical row in the historical sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
    else:
        print("  ~~  Historical Summary Line was not created as it is not between 12:30 and 13:00 UTC  ~~  ")

def CreateSummaryRows():
    # This function creates 2 rows from the above data, per column, for a summary sheet
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetSummaryId) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    summaryFormat = ",2,1,,,,1,,,8,,,,,,"
    true = 'true'
    json = {"toBottom":true,"cells":[]}
    json.setdefault("cells", []).append({"columnId": 5109372712970116,"value":listOfStringsForSmartsheet[0],"format":summaryFormat})
    json.setdefault("cells", []).append({"columnId": 2857572899284868, "value": listOfTestResults[0], "format": summaryFormat})
    r = requests.post(url, headers=headers, json=json)
    if r.status_code == 200:
        print("  ~~  Summary Sheet Line 1 of 2 Created  ~~  ")
    else:
        print("The row in the sheet was not created")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)
    json = {"toBottom":true,"cells":[]}
    json.setdefault("cells", []).append({"columnId": 5109372712970116,"value":listOfStringsForSmartsheet[1],"format":summaryFormat})
    json.setdefault("cells", []).append({"columnId": 2857572899284868, "value": listOfTestResults[1], "format": summaryFormat})
    r = requests.post(url, headers=headers, json=json)
    if r.status_code == 200:
        print("  ~~  Summary Sheet Line 2 of 2 Created  ~~  ")
    else:
        print("The row in the sheet was not created")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)
    print("Finished - All summary sheet rows were successfully updated")

def DeleteRowData():
    # This function deletes all the data in a sheet
    listOfSmartSheetIdsToDelete = [smartSheetId, smartSheetSummaryId]
    for smartSheetIdInList in listOfSmartSheetIdsToDelete:
        listOfRowsToDelete = []
        listOfRowIndexes = []
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdInList)
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
            url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdInList) + '/rows?ids='
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
CreateHistoricalRows()
CreateSummaryRows()
CreateRows()
