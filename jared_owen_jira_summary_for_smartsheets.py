import requests
import datetime
import sys
from time import sleep

# These are id's needing to be specific to project
smartSheetIdForCurrentStatus = 68091473356676
# listOfColumnIds = [3640701612255108, 2712963443386244, 7216563070756740, 8144301239625604]
# listOfColumnTitles =  ['Project Id', 'Current Sprint', 'Tickets in Current Sprint', 'Total Current EQ Points']

smartSheetIdForHistoricalStatus = 3853220381517700
# listOfColumnIds = [8801096765335428, 216109975660420, 4719709603030916, 2467909789345668]
# listOfColumnTitles =  ['Date', 'Control Room EQ Points', 'Identity EQ Points', 'Experience Platform EQ Points']

smartSheetIdForListOfStoriesWithNoPoints = 6246990339172228
#listOfColumnIds = [2666342647129988, 7169942274500484, 1540442740287364]
#listOfColumnTitles =  ['ROOM', 'IDEN', 'EXP']

# to be used in terminal / Jenkins:
jiraBasicAuth = sys.argv[1]
smartSheetPassword = sys.argv[2]

month = datetime.date.today().strftime("%m")
date = datetime.date.today().strftime("%d")
year = datetime.date.today().strftime("%y")
dateHeader = month + "/" + date + "/" + year

projectIds = ['ROOM','IDEN','EXP']
# This script needs the SmartSheet to be set up in advance per the below format

def CreateRows():
    # this function gets data from jira per project and updates a row in smartsheets with the data
    listOfProjectsAndEqPoints = []
    masterListOfTicketsWithNoEqPoints = []
    for projectId in projectIds:
        # this call establishes total number of tickets, so we can iterates through them in batches----------------------------
        url = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=' + projectId + '&maxResults=0'
        headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}
        r = requests.get(url, headers=headers)
        totalIssues = r.json()['total']
        if r.status_code != 200:
            print('Did not get a number of JIRA Tickets')

        # This loop runs through all the issues (limited by blocks of 100 by JIRA)
        # It creates 2 dictionaries for all tickets: JIRA ticket numbers & status, and JIRA ticket number and type
        ticketsInSprint = 0
        listOfTicketsInSprint = []
        listOfTicketsWithNoEqPoints = []
        eqPointsInSprint = 0
        eqPointsDoneInSprint = 0

        for i in range (0,totalIssues,100):
            url = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=' + projectId + '&fields=issuetype,customfield_12887,customfield_10007,key,status&maxResults=100&startAt=' + str(i)
            headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}
            print('URL VALUE')
            print(url)
            r = requests.get(url, headers=headers)
            if r.status_code != 200:
                print('Error: was unable to run through the first %i number of JIRA issues' % (i+100))
            else:
                for ticket in r.json()['issues']:
                    sprints = ticket['fields']['customfield_10007']
                    if sprints != None:
                        for sprint in sprints:
                            if 'ACTIVE' in sprint:
                                type = ticket['fields']['issuetype']['name']
                                if type == 'Story':
                                    id = ticket['key']
                                    eqPoints = ticket['fields']['customfield_12887']
                                    sprintName = sprint.split("name=")
                                    sprintName = sprintName[1]
                                    sprintName = sprintName.split(",")
                                    sprintName = sprintName[0]
                                    sprintName = sprintName.replace(projectId, "")
                                    if sprintName[0] == " ":
                                        sprintName = sprintName[1:]
                                    print(sprint)
                                    ticketsInSprint += 1
                                    if eqPoints == None:
                                        eqPoints = 0
                                        listOfTicketsWithNoEqPoints.append(id)
                                        masterListOfTicketsWithNoEqPoints.append(id)
                                    eqPointsInSprint += float(eqPoints)
                                    listOfTicketsInSprint.append(id)
                                    status= ticket['fields']['status']['name']
                                    print(status)
                                    if status == 'Done':
                                      if ticket['fields']['customfield_12887'] == None:
                                            eqPointsDoneInSprint = 0
                                      else:
                                            eqPointsDoneInSprint += float(ticket['fields']['customfield_12887'])

        # the below call adds each project's data to a new row on the smartsheet
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForCurrentStatus) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        summaryFormat = ",2,1,,,,1,,,8,,,,,,"
        normalFormat = ",,,,,,,,,18,,,,,,"
        true = 'true'
        json = {"toBottom": true, "cells":
            [
            {"columnId": 3640701612255108, "value": projectId, "format": summaryFormat},
            {"columnId": 2712963443386244, "value": sprintName, "format": summaryFormat},
          #  {"columnId": 7216563070756740, "value": eqPointsDone, "format": summaryFormat},
             {"columnId": 7216563070756740, "value": eqPointsDoneInSprint, "format": summaryFormat},
            {"columnId": 8144301239625604, "value": eqPointsInSprint, "format": summaryFormat}
            ]
                }
        r = requests.post(url, headers=headers, json=json)
        if r.status_code != 200:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
        print("")
        print("Number of Tickets in Current %s Sprint which is named %s:" % (projectId, sprintName), ticketsInSprint)
        print("List of the tickets in the current sprint:", listOfTicketsInSprint)
        print("Number of EQ Points in the current sprint:", eqPointsInSprint)
        print("Number of EQ Points done in the current sprint:", eqPointsDoneInSprint)
        print("")
        listOfProjectsAndEqPoints.append((projectId, eqPointsInSprint))

        # the below call adds each project's data to a smartsheet for a project pie chart
        dictionaryOfPieChartSheets = [
            {'project': 'ROOM', 'id': 7091007247411076, 'col1': 8628061122914180, 'col2': 465286798305156},
            {'project': 'IDEN', 'id': 6509829452785540, 'col1': 8316005979056004, 'col2': 997656584578948},
            {'project': 'EXP', 'id': 7653682322925444, 'col1': 7055278458857348, 'col2': 1425778924644228}
            ]
        for i in range (0,3):
            if projectId == dictionaryOfPieChartSheets[i]['project']:
                #print(projectId)
                smartSheetId = dictionaryOfPieChartSheets[i]['id']
                col1 = dictionaryOfPieChartSheets[i]['col1']
                col2 = dictionaryOfPieChartSheets[i]['col2']
        url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        json = {"toBottom": true, "cells":
            [
                {"columnId": col1, "value": 'Stories with EQ Points', "format": normalFormat},
                {"columnId": col2, "value": len(listOfTicketsInSprint) - len(listOfTicketsWithNoEqPoints), "format": normalFormat}
            ]
                }
        r = requests.post(url, headers=headers, json=json)
        if r.status_code != 200:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)
        json = {"toBottom": true, "cells":
            [
                {"columnId": col1, "value": 'Stories with No EQ Points', "format": normalFormat},
                {"columnId": col2, "value": len(listOfTicketsWithNoEqPoints), "format": normalFormat}
            ]
                }
        r = requests.post(url, headers=headers, json=json)
        if r.status_code != 200:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)

    # the below call adds each project's data to a new row on the historical smartsheet
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForHistoricalStatus) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    json = {"toBottom": true, "cells":
        [
            {"columnId": 8801096765335428, "value": dateHeader, "format": normalFormat},
            {"columnId": 216109975660420, "value": listOfProjectsAndEqPoints[0][1], "format": summaryFormat},
            {"columnId": 4719709603030916, "value": listOfProjectsAndEqPoints[1][1], "format": summaryFormat},
            {"columnId": 2467909789345668, "value": listOfProjectsAndEqPoints[2][1], "format": summaryFormat}
        ]
            }
    r = requests.post(url, headers=headers, json=json)
    if r.status_code != 200:
        print("The row in the sheet was not created")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)

    # the below call adds each project's lists of stories with no eq points to a sheet
    listOfRoomStories = []
    listOfIdenStories = []
    listOfExpStories = []
    for ticket in masterListOfTicketsWithNoEqPoints:
        if 'ROOM' in ticket:
            listOfRoomStories.append(ticket)
        if 'IDEN' in ticket:
            listOfIdenStories.append(ticket)
        if 'EXP' in ticket:
            listOfExpStories.append(ticket)
    longest = [len(listOfRoomStories), len(listOfIdenStories), len(listOfExpStories)]
    maxLength = max(longest)
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetIdForListOfStoriesWithNoPoints) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    for index in range(0, maxLength):
        try:
            roomTicketId = listOfRoomStories[index]
        except:
            roomTicketId = ""
        try:
            idenTicketId = listOfIdenStories[index]
        except:
            idenTicketId = ""
        try:
            expTicketId = listOfExpStories[index]
        except:
            expTicketId = ""
        json = {"toBottom": true, "cells": [
            {"columnId": 2666342647129988, "value": roomTicketId, "format": summaryFormat},
            {"columnId": 1540442740287364, "value": expTicketId, "format": summaryFormat},
            {"columnId": 7169942274500484, "value": idenTicketId, "format": summaryFormat}
        ]
                }
        r = requests.post(url, headers=headers, json=json)
        if r.status_code != 200:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)

def DeleteRows(smartSheetId):
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


listOfSheetsToDelete = [
    smartSheetIdForListOfStoriesWithNoPoints, smartSheetIdForCurrentStatus,
    6509829452785540, 7653682322925444, 7091007247411076
]  # the 3 numbers are pie chart sheets

for sheetId in listOfSheetsToDelete:
    DeleteRows(sheetId)

CreateRows()



# here are column id's for each pie chart sheet:

# SmartSheet Id:  6509829452785540 - iden
# listOfColumnIds = [8316005979056004, 997656584578948, 5501256211949444, 3249456398264196, 7753056025634692, 2123556491421572]
# listOfColumnTitles =  ['Primary Column', 'Column2', 'Column3', 'Column4', 'Column5', 'Column6']
# SmartSheet Id:  7653682322925444 - exp
# listOfColumnIds = [7055278458857348, 1425778924644228, 5929378552014724, 3677578738329476, 8181178365699972, 862828971222916]
# listOfColumnTitles =  ['Primary Column', 'Column2', 'Column3', 'Column4', 'Column5', 'Column6']
# SmartSheet Id:  7091007247411076 - room
# listOfColumnIds = [8628061122914180, 465286798305156, 4968886425675652, 2717086611990404, 7220686239360900, 1591186705147780]
# listOfColumnTitles =  ['Primary Column', 'Column2', 'Column3', 'Column4', 'Column5', 'Column6']
