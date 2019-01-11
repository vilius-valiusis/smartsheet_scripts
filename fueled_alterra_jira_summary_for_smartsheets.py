import requests
import pprint
import datetime
import re
from time import sleep
import sys

# These are id's needing to be specific to project
smartSheetId = 1572782262773636
testRailProjectId = 21

# This script needs the SmartSheet to be set up in advance per the below format
# It also needs to have Suites made in TestRail following a format as well.

# to be used in terminal / Jenkins:
# testRailPassword = sys.argv[1]
# testRailEmail = sys.argv[2]
# jiraBasicAuth = sys.argv[3]
# smartSheetPassword = sys.argv[4]

# ...

# these are the different JIRA team labels
ios = 'FueledAlterra'
android = 'FueledAndroidAlterra'
aes = 'AESAlterra'

# These are lists of how the smartsheet should stay formatted:

COLUMN_MAPPINGS = dict({
    'References': 3751017230690180, 'Cases w References': 8254616858060676,
    'Cases w/o References': 936267463583620, 'Percentage Covered': 5439867090954116,
    'Percentage Not Covered': 3188067277268868, 'List of Stories that Need References': 5122451827910532,
    'List of Stories that Have References': 6002817044375428,
    'List of Refs for Stories in Draft/Blocked': 8417677304719236,
    'Refs in Draft/Blocked': 3914077677348740, 'Total JIRA': 7691666904639364, 'Total Fueled': 1612381081102212,
    'Bugs': 2062167370426244, 'Stories': 6565766997796740, 'Sub-Task': 4313967184111492, 'Task': 8817566811481988,
    'Epic': 232580021806980, 'Blocked': 4736179649177476, 'Code Review': 2484379835492228,
    'Defects Found': 6987979462862724, 'Done': 1358479928649604, 'Draft': 5862079556020100,
    'In Progress': 3610279742334852, 'QA Complete': 8113879369705348,
    'QA in Progress': 795529975228292, 'Ready for DEV': 5299129602598788, 'Ready for QA': 3047329788913540,
    'Total Bugs': 128513903748996, 'Open: Low': 3581201605781380, 'Open: Medium': 8084801233151876,
    'Open: High': 766451838674820, 'Open: Critical': 5270051466045316, 'Open: No Severity': 3018251652360068,
    'Open: P1': 7521851279730564, 'Open: P2': 1892351745517444, 'Open: P3': 6395951372887940,
    'Open: P4': 4144151559202692, 'Open: P5': 8647751186573188, 'List of Blocked': 7550929416284036,
    'List of Code Review': 1921429882070916, 'List of Defects Found': 6425029509441412,
    'List of Done': 4173229695756164, 'List of Draft': 8676829323126660,
    'List of In Progress': 514054998517636, 'List of QA Complete': 5017654625888132,
    'List of QA in Progress': 2765854812202884, 'List of Ready for DEV': 7269454439573380,
    'List of Ready for QA': 1639954905360260, 'List of ALT tickets with no label': 3522496919037828
})

# global-ish variables initialized here:
notTestable = []
listOfReferences = []
listOfStatus = set()
listOfReportTickets = []
listOfTicketsWithNoLabels = []
bugList = []

URL_TESTRAIL = 'https://te2qa.testrail.net/index.php?/api/v2/'
URL_TESTRAIL_SUITES = URL_TESTRAIL + 'get_suites/21/&suite_id='
URL_TESTRAIL_CASES = URL_TESTRAIL + 'get_cases/21/'
HEADER_TESTRAIL = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}

URL_JIRA = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=ALT'
HEADER_JIRA = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}

AUTH_TESTRAIL = (testRailEmail, testRailPassword)


# The below call to testrail gets a list of suites for fueled's Mobile Sprints:---------------------------------------
def get_testrail_suites():
    list_of_suites = []
    r = requests.get(URL_TESTRAIL_SUITES, headers=HEADER_TESTRAIL, auth=AUTH_TESTRAIL)
    if r.status_code != 200:
        print('Did not get a list of suites from testrail')
    else:
        print("The call to TestRail to get a list of suites for fueled's Mobile Sprints was successful.")
        for suite in r.json():
            if 'Mobile' in suite['name']:
                suite_id = suite['id']
                list_of_suites.append(str(suite_id))
    return list_of_suites


def get_testrail_list_of_references(list_of_suites):
    # The below call to testrail goes through each suite from above and gets a list of references:--------------------
    for suiteIdFromList in list_of_suites:
        url = 'https://te2qa.testrail.net/index.php?/api/v2/get_cases/' + str(testRailProjectId) + '&suite_id=' + str(
            suiteIdFromList)
        headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
        r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
        if r.status_code != 200:
            print('Did not get a list of references for this suite from testrail')
        else:
            print("The call to TestRail to get references for TestRail Suite ID: %s was successful" % str(
                suiteIdFromList))
            for testCase in r.json():
                if testCase['refs']:
                    reference = testCase['refs']
                    reference = reference.replace(" ", "")
                    reference = reference.replace(")", "")
                    reference = reference.replace("(", "")
                    reference = reference.replace("  ", "")
                    if ',' not in reference:
                        if reference not in listOfReferences:
                            listOfReferences.append(reference)
                    else:
                        reference = list(reference.split(','))

                        for refr in reference:
                            if refr not in listOfReferences:
                                listOfReferences.append(refr)
                                # listOfReferences now contains all refs in testrail for Mobile Sprints
    return listOfReferences


def get_total_jira_issues():
    # this call establishes total number of tickets, so we can iterates through them in batches------------------------
    url = URL_JIRA + '&maxResults=0'
    r = requests.get(url, headers=HEADER_JIRA)
    total_issues = r.json()['total']
    if r.status_code != 200:
        print('Did not get a number of JIRA Tickets')
    else:
        print("The call to get the total number of JIRA tickets was successful for ALT.")
    return total_issues


def build_jira_ticket_dict(total_jira_issues):
    jira_ticket_dict = dict()
    for i in range(0, total_jira_issues, 100):
        url = URL_JIRA + '&fields=customfield_12825,priority,issuetype,status,labels,key,summary&maxResults=100&startAt=' \
              + str(i)
        r = requests.get(url, headers=HEADER_JIRA)
        if r.status_code != 200:
            print('Error: was unable to run through the first %i number of JIRA issues' % (i + 100))
        else:
            for ticket in r.json()['issues']:
                label = ticket['fields']['labels']
                if android in label or ios in label:  # labels specific to the team
                    key = ticket['key']
                    status = ticket['fields']['status']['name']
                    listOfStatus.add(status)

                    jira_ticket_dict[key] = {
                        'Label': label,
                        'priority': ticket['fields']['priority']['name'],
                        'severity': ticket['fields']['customfield_12825']['value'],
                        'status': ticket['fields']['status']['name'],
                        'type': ticket['fields']['issuetype']['name'],
                        'isTestable': 'Not-Testable' in label,
                        'isOpenBug': ticket['fields']['issuetype']['name'] == 'Bug' and status != 'Done',
                        'isLabeled': label != []
                    }
            print('The call to run through the first %i number of JIRA issues was successful.' % (i + 100))
    return jira_ticket_dict


# Build a severity dictionary(none, low, medium, high, critical) of open bugs
def build_severity_dict(jira_ticket_dict):
    severity_dict = dict({'none': [], 'low': [], 'medium': [], 'high': [], 'critical': [], })
    for key, ticket in jira_ticket_dict.items():
        if ticket['isOpenBug']:
            if ticket['severity'] == 'Low':
                severity_dict['low'].append(key)
            elif ticket['severity'] == 'Medium':
                severity_dict['medium'].append(key)
            elif ticket['severity'] == 'High':
                severity_dict['high'].append(key)
            elif ticket['severity'] == 'Critical':
                severity_dict['critical'].append(key)
            else:
                severity_dict['none'].append(key)
    return severity_dict


def get_open_bug_list(jira_ticket_dict):
    open_bug_list = []
    for key, val in jira_ticket_dict.items():
        if val['isOpenBug']:
            open_bug_list.append(key)
    pass


# Build a priority dictionary(P1, P2, P3, P4, P5) of open bugs
def build_priority_dict(jira_ticket_dict):
    priority_dict = dict({'P1': [], 'P2': [], 'P3': [], 'P4': [], 'P5': [], })
    for key, ticket in jira_ticket_dict.items():
        if ticket['isOpenBug']:

            if ticket['priority'] == 'P1':
                priority_dict['P1'].append(key)
            elif ticket['priority'] == 'P2':
                priority_dict['P2'].append(key)
            elif ticket['priority'] == 'P3':
                priority_dict['P3'].append(key)
            elif ticket['priority'] == 'P4':
                priority_dict['P4'].append(key)
            elif ticket['priority'] == 'P5':
                priority_dict['P5'].append(key)
    return priority_dict


# Build a status dictionary of jira tickets
def build_status_dict(jira_ticket_dict):
    priority_dict = dict({'Draft': [], 'In Progress': [], 'Ready for QA': [], 'QA Complete': [],
                          'Done': [], 'Code Review': [], 'Blocked': [], 'Defects Found': [],
                          'Ready for DEV': [], 'QA in Progress': []})
    report_ticket_list = set()
    for key, ticket in jira_ticket_dict.items():
        status = ticket['status']
        is_testable = ticket['isTestable']
        # Makes a list of tickets that don't have the 'not-testable' tag and are not in draft or blocked
        if status != "Draft" and status != "Blocked" and is_testable:
            report_ticket_list.add(key)
        if status == 'Draft':
            priority_dict['Draft'].append(key)
        elif status == 'In Progress':
            priority_dict['In Progress'].append(key)
        elif status == 'Ready for QA':
            priority_dict['Ready for QA'].append(key)
        elif status == 'QA Complete':
            priority_dict['QA Complete'].append(key)
        elif status == 'Done':
            priority_dict['Done'].append(key)
        elif status == 'Code Review':
            priority_dict['Code Review'].append(key)
        elif status == 'Blocked':
            priority_dict['Blocked'].append(key)
        elif status == 'Defects Found':
            priority_dict['Defects Found'].append(key)
        elif status == 'Ready for DEV':
            priority_dict['Ready for DEV'].append(key)
        elif status == 'QA in Progress':
            priority_dict['QA in Progress'].append(key)

    return priority_dict, report_ticket_list


# sorts only by number
listOfReportTickets = sorted(listOfReportTickets,key=lambda x: int(re.search(r'\d+$', x).group()))
listOfReportTickets = listOfReportTickets[::-1]  # reverses the list

# this is made as a decision was made that refs should only be for the fueled 'story' tickets
listOfStories = []
totalBugCount = 0
totalStoryCount = 0
totalSubTaskCount = 0
totalTaskCount = 0
totalEpicCount = 0
for ticketNumber, ticketType in jira_ticket_dict.items():
    if ticketType['type'] == 'Bug':
        totalBugCount += 1
    if ticketType['type'] == 'Story':
        totalStoryCount += 1
    if ticketType['type'] == 'Sub-task':
        totalSubTaskCount += 1
    if ticketType['type'] == 'Task':
        totalTaskCount += 1
    if ticketType['type'] == 'Epic':
        totalEpicCount += 1
    if ticketNumber in listOfReportTickets:
        if ticketType['type'] == 'Story':
            listOfStories.append(ticketNumber)  # makes a list of stories that need test cases for testrail

    # for reportTicket in listOfReportTickets:
    #     if ticketNumber == reportTicket:  # this runs through the stories not in draft or blocked
    #         if ticketType == 'Story':
    #             listOfStories.append(reportTicket)  # makes a list of stories that need test cases for testrail
print("A count was created for each of the JIRA ticket types.")

#
# below is the basic calculation for stories in JIRA vs. References in TestRail:
listOfStoriesWithRefs = []
listOfStoriesWithNORefs = []
listOfRefsForStoriesNotNeedingRefs = []
for num in listOfStories:
    if num in listOfReferences:
        listOfStoriesWithRefs.append(num)  # list of jira stories that are referenced in testrail
    else:
        listOfStoriesWithNORefs.append(num)  # list of jira stories that are not referenced in testrail
for num in listOfReferences:
    if num not in listOfStories and num not in listOfStoriesWithRefs:
        listOfRefsForStoriesNotNeedingRefs.append(num)
        # list of jira stories that are referenced in testrail, but are in draft or blocked
print(listOfRefsForStoriesNotNeedingRefs)
print(listOfStoriesWithRefs)
print(listOfStoriesWithNORefs)
#
casesWithRefs = len(listOfStoriesWithRefs)
casesWithNoRefs = len(listOfStoriesWithNORefs)
refsWithNoCases = len(listOfRefsForStoriesNotNeedingRefs)
#
# listOfStoriesWithNORefs = sorted(listOfStoriesWithNORefs,
#                                  key=lambda x: int(re.search(r'\d+$', x).group()))  # sorts only by number
# listOfStoriesWithNORefs = listOfStoriesWithNORefs[::-1]  # reverses the list
# listOfStoriesWithRefs = sorted(listOfStoriesWithRefs,
#                                key=lambda x: int(re.search(r'\d+$', x).group()))  # sorts only by number
# listOfStoriesWithRefs = listOfStoriesWithRefs[::-1]  # reverses the list
# listOfRefsForStoriesNotNeedingRefs = sorted(listOfRefsForStoriesNotNeedingRefs,
#                                             key=lambda x: int(re.search(r'\d+$', x).group()))  # sorts only by number
# listOfRefsForStoriesNotNeedingRefs = listOfRefsForStoriesNotNeedingRefs[::-1]  # reverses the list
#
# print("A calculation was made for stories in JIRA vs. References in TestRail")
#

# The below call returns the list of columns for the sheet, making a dictionary of ID's and Titles
# idTitleDict = {}
# url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/columns'
# headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
# r = requests.get(url, headers=headers)
# if r.status_code != 200:
#     print('Error: The SmartSheet was not found.')
# else:
#     for column in r.json()['data']:
#         columnId = column['id']
#         columnTitle = column['title']
#         if COLUMN_MAPPINGS[columnTitle]:
#             print("The Column with title: %s did not show up in the preset list. The sheet may need updating..." % (
#                 columnTitle))
#             break
#         if columnId not in listOfColumnIds:
#             print("The Column with id: %i did not show up in the preset list. The sheet may need updating..." % (
#                 columnId))
#             break
#         idTitleDict.update({columnId: columnTitle})
# #
percentageCovered = (float(len(listOfReferences)) - float(refsWithNoCases)) / float(len(listOfStories)) * float(100)


#
#

def set_column_data(json, column_name, data, summary_format):
    json.setdefault("cells", []).append(
        {"columnId": COLUMN_MAPPINGS.get(column_name), "value": data, "format": summary_format})


def create_rows(jira_ticket_dict):
    # This function creates rows from the above data, per column
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    summary_format = ",2,1,,,,1,,,8,,,,,,"
    normal_format = ",,,,,,,,,18,,,,,,"
    json = {"toBottom": 'true', "cells": []}
    for rowCount in range(0, len(jira_ticket_dict)):
        if rowCount == 0:
            set_column_data(json, 'References', len(listOfReferences), summary_format)
            set_column_data(json, 'Cases w References', len(listOfStoriesWithRefs), summary_format)
            set_column_data(json, 'Cases w/o References', len(listOfStoriesWithNORefs), summary_format)
            set_column_data(json, 'Percentage Covered', str(round(percentageCovered, 2)) + " %", summary_format)
            set_column_data(json, 'Percentage Not Covered', str(round(float(float(100) - percentageCovered), 2)) + " %",
                            summary_format)
            set_column_data(json, 'List of Stories that Need References', listOfStoriesWithNORefs[0], normal_format)
            set_column_data(json, 'List of Stories that Have References', listOfStoriesWithRefs[0], normal_format)
            set_column_data(json, 'List of Refs for Stories in Draft/Blocked', listOfRefsForStoriesNotNeedingRefs[0],
                            normal_format)
            set_column_data(json, 'Refs in Draft/Blocked', len(listOfRefsForStoriesNotNeedingRefs), summary_format)
            set_column_data(json, 'Total JIRA', get_total_jira_issues(), summary_format)
            set_column_data(json, 'Total Fueled', len(jira_ticket_dict), summary_format)
            set_column_data(json, 'Bugs', totalBugCount, summary_format)
            set_column_data(json, 'Stories', totalStoryCount, summary_format)
            set_column_data(json, 'Sub-Task', totalSubTaskCount, summary_format)
            set_column_data(json, 'Task', totalTaskCount, summary_format)
            set_column_data(json, 'Epic', totalEpicCount, summary_format)
            set_column_data(json, 'Blocked', len(AltTicketList_Blocked), summary_format)
            set_column_data(json, 'Code Review', len(AltTicketList_CodeReview), summary_format)
            set_column_data(json, 'Defects Found', len(AltTicketList_DefectsFound), summary_format)
            set_column_data(json, 'Done', len(AltTicketList_Done), summary_format)
            set_column_data(json, 'Draft', len(AltTicketList_Draft), summary_format)
            set_column_data(json, 'In Progress', len(AltTicketList_InProgress), summary_format)
            set_column_data(json, 'QA Complete', len(AltTicketList_QAComplete), summary_format)
            set_column_data(json, 'QA in Progress', len(AltTicketList_QAinProgress), summary_format)
            set_column_data(json, 'Ready for DEV', len(AltTicketList_ReadyforDEV), summary_format)
            set_column_data(json, 'Ready for QA', len(AltTicketList_ReadyforQA), summary_format)
            set_column_data(json, 'Total Bugs', openBugCount, summary_format)
            set_column_data(json, 'Open: Low', len(AltTicketList_LowSeverity), summary_format)
            set_column_data(json, 'Open: Medium', len(AltTicketList_MediumSeverity), summary_format)
            set_column_data(json, 'Open: High', len(AltTicketList_HighSeverity), summary_format)
            set_column_data(json, 'Open: Critical', len(AltTicketList_CriticalSeverity), summary_format)
            set_column_data(json, 'Open: No Severity', len(AltTicketList_NullSeverity), summary_format)
            set_column_data(json, 'Open: P1', len(AltTicketList_BlockerPriority), summary_format)
            set_column_data(json, 'Open: P2', len(AltTicketList_CriticalPriority), summary_format)
            set_column_data(json, 'Open: P3', len(AltTicketList_MajorPriority), summary_format)
            set_column_data(json, 'Open: P4', len(AltTicketList_MinorPriority), summary_format)
            set_column_data(json, 'Open: P5', len(AltTicketList_TrivialPriority), summary_format)
            set_column_data(json, 'List of Blocked', AltTicketList_Blocked[0], normal_format)
            set_column_data(json, 'List of Code Review', AltTicketList_CodeReview[0], normal_format)
            set_column_data(json, 'List of Defects Found', AltTicketList_DefectsFound[0], normal_format)
            set_column_data(json, 'List of Done', AltTicketList_Done[0], normal_format)
            set_column_data(json, 'List of Draft', AltTicketList_Draft[0], normal_format)
            set_column_data(json, 'List of In Progress', AltTicketList_InProgress[0], normal_format)
            set_column_data(json, 'List of QA Complete', AltTicketList_QAComplete[0], normal_format)
            set_column_data(json, 'List of Ready for DEV', AltTicketList_ReadyforDEV[0], normal_format)
            set_column_data(json, 'List of Ready for QA', AltTicketList_ReadyforQA[0], normal_format)
            set_column_data(json, 'List of ALT tickets with no label', listOfTicketsWithNoLabels[0], normal_format)
            print("  ~~  Summary Line Created  ~~  ")
        else:
            set_column_data(json, 'List of Stories that Need References', listOfStoriesWithNORefs[rowCount],
                            normal_format)
            set_column_data(json, 'List of Stories that Have References', listOfStoriesWithRefs[rowCount],
                            normal_format)
            set_column_data(json, 'List of Refs for Stories in Draft/Blocked',
                            listOfRefsForStoriesNotNeedingRefs[rowCount], normal_format)
            set_column_data(json, 'List of Blocked', AltTicketList_Blocked[rowCount], normal_format)
            set_column_data(json, 'List of Code Review', AltTicketList_CodeReview[rowCount], normal_format)
            set_column_data(json, 'List of Defects Found', AltTicketList_DefectsFound[rowCount], normal_format)
            set_column_data(json, 'List of Done', AltTicketList_Done[rowCount], normal_format)
            set_column_data(json, 'List of Draft', AltTicketList_Draft[rowCount], normal_format)
            set_column_data(json, 'List of In Progress', AltTicketList_InProgress[rowCount], normal_format)
            set_column_data(json, 'List of QA Complete', AltTicketList_QAComplete[rowCount], normal_format)
            set_column_data(json, 'List of QA in Progress', AltTicketList_QAinProgress[rowCount], normal_format)
            set_column_data(json, 'List of Ready for DEV', AltTicketList_ReadyforDEV[rowCount], normal_format)
            set_column_data(json, 'List of Ready for QA', AltTicketList_ReadyforQA[rowCount], normal_format)
            set_column_data(json, 'List of ALT tickets with no label', listOfTicketsWithNoLabels[rowCount],
                            normal_format)

            if not json["cells"]:
                print("There are no more rows to create. There were %i rows created in total" % rowCount)
                break
        r = requests.post(url, headers=headers, json=json)
        # sleep(1) # adds delay to lessen load on server
        if r.status_code == 200:
            rowCount += 1
            print("Row: " + str(rowCount) + " was created.")
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)


#
#
# def DeleteRows():
#     # This function deletes all the data in a sheet
#     listOfRowsToDelete = []
#     listOfRowIndexes = []
#     url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
#     headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
#     r = requests.get(url, headers=headers)
#     if r.json() == [] or r.status_code != 200:
#         print("No SmartSheet was returned, or a bad status")
#         print("The Content is: ", r.content, 'and the status code is: ', r.status_code)
#     else:
#         if r.json()['rows'] == []:
#             print("No rows to delete")
#         else:
#             for row in r.json()['rows']:
#                 # makes a list of all rows
#                 rowId = row['id']
#                 listOfRowsToDelete.append(rowId)
#     if len(listOfRowsToDelete) <= 450:
#         listOfRowIndexes.append((0, len(listOfRowsToDelete)))
#     else:
#         for number in range(0, len(listOfRowsToDelete), 450):
#             # this creates a list of indexes to run through in blocks of 450
#             if number <= len(listOfRowsToDelete) - 450:
#                 listOfRowIndexes.append((number, number + 450))
#             else:
#                 listOfRowIndexes.append((number, len(listOfRowsToDelete)))
#     for rowIndex in listOfRowIndexes:
#         # this runs through all rows to delete, 450 at a time as this is max url legnth.
#         url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows?ids='
#         beginningOfList = rowIndex[0]
#         endOfList = rowIndex[1]
#         smallerListOfRowsToDelete = listOfRowsToDelete[
#                                     beginningOfList:endOfList]  # creates a string with all the row id's in url
#         for rowNumber in smallerListOfRowsToDelete:
#             url = url + str(rowNumber) + ','
#         url = url[:-1]  # removes the last comma
#         url = url + '&ignoreRowsNotFound=true'
#         headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
#         r = requests.delete(url, headers=headers)
#         sleep(1)  # adds delay to lessen load on server
#         if r.json()['message'] == "SUCCESS":
#             print("The data in the sheet was deleted for rows between index:", beginningOfList, "and: ", endOfList)
#         else:
#             print("The data in the sheet was not deleted")
#             print('The status code was: ', r.status_code, 'and the content was: ', r.content)
#
#
# DeleteRows()
# CreateRows()
#
#
# # if multiple editors use the sheet, it may be necessary to add the function 'DeleteColumns()'
# # this would delete and create the columns per the specified list: 'listOfColumnTitles'
#
# #####################################################################################################################
# # Below are helper functions:
# # ChangeSheetName()
#
# def ChangeSheetName():
#     # the below updates the smartsheet name
#     month = datetime.date.today().strftime("%B")
#     date = datetime.date.today().strftime("%d")
#     year = datetime.date.today().strftime("%Y")
#     dateHeader = date + " " + month + " " + year
#     url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
#     headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + smartSheetPassword}
#     json = {"name": "ALT in Sprint Mobile Coverage - Daily"}
#     r = requests.put(url, headers=headers, json=json)
#     if r.status_code == 200:
#         print("The smartsheet name was successfully changed")
#     else:
#         print("The smartsheet name was NOT successfully changed")
#         print('The status code was: ', r.status_code, 'and the content was: ', r.content)

def main():
    list_of_suites = get_testrail_suites()
    list_of_references = get_testrail_list_of_references(list_of_suites)
    total_jira_issues = get_total_jira_issues()
    jira_ticket_dict = build_jira_ticket_dict(total_jira_issues)


if __name__ == '__main__':
    main()
