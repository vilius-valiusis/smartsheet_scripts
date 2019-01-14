import requests
import datetime
import sys
from time import sleep

# These are id's needing to be specific to project
smartSheetId = 1572782262773636
testRailProjectId = 21

# This script needs the SmartSheet to be set up in advance per the below format
# It also needs to have Suites made in TestRail following a format as well.

# to be used in terminal / Jenkins:
testRailPassword = sys.argv[1]
testRailEmail = sys.argv[2]
jiraBasicAuth = sys.argv[3]
smartSheetPassword = sys.argv[4]

# these are the different JIRA team labels
ios = 'FueledAlterra'
android = 'FueledAndroidAlterra'
aes = 'AESAlterra'

# These are lists of how the smartsheet should stay formatted:

COLUMN_MAPPINGS = {
    'References': 3751017230690180,
    'Cases w References': 8254616858060676,
    'Cases w/o References': 936267463583620,
    'Percentage Covered': 5439867090954116,
    'Percentage Not Covered': 3188067277268868,
    'List of Stories that Need References': 5122451827910532,
    'List of Stories that Have References': 6002817044375428,
    'List of Refs for Stories in Draft/Blocked': 8417677304719236,
    'Refs in Draft/Blocked': 3914077677348740,
    'Total JIRA': 7691666904639364,
    'Total Fueled': 1612381081102212,
    'Bugs': 2062167370426244,
    'Stories': 6565766997796740,
    'Sub-Task': 4313967184111492,
    'Task': 8817566811481988,
    'Epic': 232580021806980,
    'Blocked': 4736179649177476,
    'Code Review': 2484379835492228,
    'Defects Found': 6987979462862724,
    'Done': 1358479928649604,
    'Draft': 5862079556020100,
    'In Progress': 3610279742334852,
    'QA Complete': 8113879369705348,
    'QA in Progress': 795529975228292,
    'Ready for DEV': 5299129602598788,
    'Ready for QA': 3047329788913540,
    'Total Bugs': 128513903748996,
    'Open: Low': 3581201605781380,
    'Open: Medium': 8084801233151876,
    'Open: High': 766451838674820,
    'Open: Critical': 5270051466045316,
    'Open: No Severity': 3018251652360068,
    'Open: P1': 7521851279730564,
    'Open: P2': 1892351745517444,
    'Open: P3': 6395951372887940,
    'Open: P4': 4144151559202692,
    'Open: P5': 8647751186573188,
    'List of Blocked': 7550929416284036,
    'List of Code Review': 1921429882070916,
    'List of Defects Found': 6425029509441412,
    'List of Done': 4173229695756164,
    'List of Draft': 8676829323126660,
    'List of In Progress': 514054998517636,
    'List of QA Complete': 5017654625888132,
    'List of QA in Progress': 2765854812202884,
    'List of Ready for DEV': 7269454439573380,
    'List of Ready for QA': 1639954905360260,
    'List of ALT tickets with no label': 3522496919037828
}
TESTRAIL_SUIT_FILTERS = ['Functional Verification - Release', 'Mobile']

URL_TESTRAIL = 'https://te2qa.testrail.net/index.php?/api/v2/'
URL_TESTRAIL_SUITES = URL_TESTRAIL + 'get_suites/21/&suite_id='
URL_TESTRAIL_CASES = URL_TESTRAIL + 'get_cases/21/'
HEADER_TESTRAIL = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}

URL_JIRA = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=ALT'
URL_PARAMS_JIRA = '&fields=customfield_12825,priority,issuetype,status,labels,key,summary&maxResults=100&startAt='
HEADER_JIRA = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}

URL_SMARTSHEETS = 'https://api.smartsheet.com/2.0/sheets/'
HEADER_SMARTSHEETS = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}

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
            if 'Mobile' in suite['name'] or 'Functional Verification - Release' in suite['name']:
                suite_id = suite['id']
                list_of_suites.append(suite_id)
    return list_of_suites


def get_testrail_list_of_references(list_of_suites):
    # The below call to testrail goes through each suite from above and gets a list of references:--------------------
    list_of_references = []
    for suiteIdFromList in list_of_suites:
        url = 'https://te2qa.testrail.net/index.php?/api/v2/get_cases/' + str(testRailProjectId) + '&suite_id=' + str(
            suiteIdFromList)
        headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
        r = requests.get(url, headers=headers, auth=AUTH_TESTRAIL)
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
                        if reference not in list_of_references:
                            list_of_references.append(reference)
                    else:
                        reference = list(reference.split(','))

                        for refr in reference:
                            if refr not in list_of_references:
                                list_of_references.append(refr)
                                # listOfReferences now contains all refs in testrail for Mobile Sprints

    return list(set(list_of_references))


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


def build_jira_ticket_dict(total_jira_issues, list_of_references):
    jira_ticket_dict = dict()
    for i in range(0, total_jira_issues, 100):
        url = URL_JIRA + URL_PARAMS_JIRA + str(i)
        r = requests.get(url, headers=HEADER_JIRA)
        if r.status_code != 200:
            print('Error: was unable to run through the first %i number of JIRA issues' % (i + 100))
        else:
            for ticket in r.json()['issues']:
                label = ticket['fields']['labels']
                if android in label or ios in label:  # labels specific to the team
                    key = ticket['key']
                    status = ticket['fields']['status']['name']

                    jira_ticket_dict[key] = {
                            'Label': label,
                            'priority': ticket['fields']['priority']['name'],
                            'severity': ticket['fields']['customfield_12825']['value'],
                            'status': ticket['fields']['status']['name'],
                            'type': ticket['fields']['issuetype']['name'],
                            'isTestable': 'Not-Testable' in label,
                            'isOpenBug': ticket['fields']['issuetype']['name'] == 'Bug' and status != 'Done',
                            'isLabeled': label != [],
                            'hasTestCase': key in list_of_references
                        }
            print('The call to run through the first %i number of JIRA issues was successful.' % (i + 100))
    return jira_ticket_dict


# Build a severity dictionary(none, low, medium, high, critical) of open bugs
def build_severity_dict(jira_ticket_dict):
    severity_dict = {
        'none':     {'tickets': []},
        'low':      {'tickets': []},
        'medium':   {'tickets': []},
        'high':     {'tickets': []},
        'critical': {'tickets': []}
    }

    for key, ticket in jira_ticket_dict.items():
        if ticket['isOpenBug']:
            if ticket['severity'] == 'Low':
                severity_dict['low']['tickets'].append(key)

            elif ticket['severity'] == 'Medium':
                severity_dict['medium']['tickets'].append(key)

            elif ticket['severity'] == 'High':
                severity_dict['high']['tickets'].append(key)

            elif ticket['severity'] == 'Critical':
                severity_dict['critical']['tickets'].append(key)

            else:
                severity_dict['none']['tickets'].append(key)
    return severity_dict


def build_open_bug_list(jira_ticket_dict):
    open_bug_list = []
    for key, val in jira_ticket_dict.items():
        if val['isOpenBug']:
            open_bug_list.append(key)
    return open_bug_list


def build_unlabeled_list(jira_ticket_dict):
    unlabeled_list = []
    print('*** UNLABELED LIST ***')
    for key, val in jira_ticket_dict.items():

        if not val['isLabeled']:
            print(key)
            unlabeled_list.append(key)
    return unlabeled_list


# Build a priority dictionary(P1, P2, P3, P4, P5) of open bugs
def build_priority_dict(jira_ticket_dict):
    priority_dict = {
        'P1': {'tickets': []},
        'P2': {'tickets': []},
        'P3': {'tickets': []},
        'P4': {'tickets': []},
        'P5': {'tickets': []}}

    for key, ticket in jira_ticket_dict.items():
        if ticket['isOpenBug']:
            if ticket['priority'] == 'P1 - Blocker':
                priority_dict['P1']['tickets'].append(key)

            elif ticket['priority'] == 'P2 - Critical':
                priority_dict['P2']['tickets'].append(key)

            elif ticket['priority'] == 'P3 - Major':
                priority_dict['P3']['tickets'].append(key)

            elif ticket['priority'] == 'P4 - Minor':
                priority_dict['P4']['tickets'].append(key)

            elif ticket['priority'] == 'P5 - Trivial':
                priority_dict['P5']['tickets'].append(key)
    return priority_dict


# Build a status dictionary of jira tickets e.g. Draft, Done, QA in Progress etc..
def build_status_dict(jira_ticket_dict):
    status_dict = {
        'Draft':            {'tickets': []},
        'In Progress':      {'tickets': []},
        'Ready for QA':     {'tickets': []},
        'QA Complete':      {'tickets': []},
        'Done':             {'tickets': []},
        'Code Review':      {'tickets': []},
        'Blocked':          {'tickets': []},
        'Defects Found':    {'tickets': []},
        'Ready for DEV':    {'tickets': []},
        'QA in Progress':   {'tickets': []}}

    report_ticket_list = set()
    for key, ticket in jira_ticket_dict.items():
        status = ticket['status']
        is_testable = ticket['isTestable']

        # Makes a list of tickets that don't have the 'not-testable' tag and are not in draft or blocked
        if status != "Draft" and status != "Blocked" and is_testable:
            report_ticket_list.add(key)

        if status == 'Draft':
            status_dict['Draft']['tickets'].append(key)

        elif status == 'In Progress':
            status_dict['In Progress']['tickets'].append(key)

        elif status == 'Ready for QA':
            status_dict['Ready for QA']['tickets'].append(key)

        elif status == 'QA Complete':
            status_dict['QA Complete']['tickets'].append(key)

        elif status == 'Done':
            status_dict['Done']['tickets'].append(key)

        elif status == 'Code Review':
            status_dict['Code Review']['tickets'].append(key)

        elif status == 'Blocked':
            status_dict['Blocked']['tickets'].append(key)

        elif status == 'Defects Found':
            status_dict['Defects Found']['tickets'].append(key)

        elif status == 'Ready for DEV':
            status_dict['Ready for DEV']['tickets'].append(key)

        elif status == 'QA in Progress':
            status_dict['QA in Progress']['tickets'].append(key)

    return status_dict, report_ticket_list


# Build a type dictionary(Bug, Story, Sub-task, Task, Epic)
def build_type_dict(jira_ticket_dict):
    type_dict = {
        'Bug':      {'tickets': []},
        'Story':    {'tickets': []},
        'Sub-task': {'tickets': []},
        'Task':     {'tickets': []},
        'Epic':     {'tickets': []}}

    for key, ticket in jira_ticket_dict.items():
        ticket_type = ticket['type']
        if ticket_type == 'Bug':
            type_dict['Bug']['tickets'].append(key)

        elif ticket_type == 'Story':
            type_dict['Story']['tickets'].append(key)

        elif ticket_type == 'Sub-task':
            type_dict['Sub-task']['tickets'].append(key)

        elif ticket_type == 'Task':
            type_dict['Task']['tickets'].append(key)

        elif ticket_type == 'Epic':
            type_dict['Epic']['tickets'].append(key)

    return type_dict


# Build a story reference dictionary of tickets that either:
# 1. hasReference: Have a testrail test case linking to the ticket
# 2. hasNoReference: Does not have a testrail test case linking to the ticket
# 3. hasReferenceButDraftOrBlocked: Has a testrail test case linking to the ticket, but is in draft or blocked
def build_story_reference_dict(jira_ticket_dict):
    story_reference_dict = {
        'hasReference': [],
        'hasNoReference': [],
        'hasReferenceButDraftOrBlocked': [],
    }

    for key, ticket in jira_ticket_dict.items():
        if ticket['type'] == 'Story':
            if ticket['hasTestCase'] and not (ticket['status'] == 'Blocked' or ticket['status'] == 'Draft'):
                story_reference_dict['hasReference'].append(key)

            elif not ticket['hasTestCase']:
                story_reference_dict['hasNoReference'].append(key)

            else:
                story_reference_dict['hasReferenceButDraftOrBlocked'].append(key)

    return story_reference_dict


def get_column_title_dict():
    column_title_dict = {}
    url = URL_SMARTSHEETS + str(smartSheetId) + '/columns'
    r = requests.get(url, headers=HEADER_SMARTSHEETS)
    if r.status_code != 200:
        print('Error: The SmartSheet was not found.')
    else:
        for column in r.json()['data']:
            column_id = column['id']
            column_title = column['title']
            column_title_dict[column_id] = column_title
    return column_title_dict


def set_column_data(json, desired_column_name, column_name, data, summary_format):
    if desired_column_name == column_name:
        json.setdefault("cells", []).append(
            {"columnId": COLUMN_MAPPINGS.get(column_name), "value": data, "format": summary_format})
    return json


def create_rows(jira_ticket_dict, severity_dict, priority_dict, status_dict, type_dict, story_reference_dict,
                list_of_references, total_jira_issues, open_bug_list, unlabeled_list):

    # This function creates rows from the above data, per column
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    sf = ",2,1,,,,1,,,8,,,,,,"
    nf = ",,,,,,,,,18,,,,,,"

    # Percentage of covered/not covered stories rounded to two decimal places
    stories_coverage_percent = round((float(len(story_reference_dict['hasReference'])))
                                     / float(len(list_of_references)) * float(100), 2)
    stories_percentage_not_covered = round(float(float(100) - stories_coverage_percent), 2)

    for i in range(0, len(jira_ticket_dict)):
        json = {"toBottom": 'true', "cells": []}
        for k, v in COLUMN_MAPPINGS.items():
            if i == 0:
                json = set_column_data(json, k, 'References', len(list_of_references), sf)
                json = set_column_data(json, k, 'Cases w References', len(story_reference_dict['hasReference']), sf)
                json = set_column_data(json, k, 'Cases w/o References', len(story_reference_dict['hasNoReference']), sf)
                json = set_column_data(json, k, 'Percentage Covered', str(stories_coverage_percent) + " %", sf)
                json = set_column_data(json, k, 'Percentage Not Covered', str(stories_percentage_not_covered) + " %", sf)

                json = set_column_data(json, k, 'Refs in Draft/Blocked',
                                       len(story_reference_dict['hasReferenceButDraftOrBlocked']), sf)

                json = set_column_data(json, k, 'Total JIRA', total_jira_issues, sf)
                json = set_column_data(json, k, 'Total Fueled', len(jira_ticket_dict), sf)
                json = set_column_data(json, k, 'Bugs', len(type_dict['Bug']['tickets']), sf)
                json = set_column_data(json, k, 'Stories', len(type_dict['Story']['tickets']), sf)
                json = set_column_data(json, k, 'Sub-Task', len(type_dict['Sub-task']['tickets']), sf)
                json = set_column_data(json, k, 'Task', len(type_dict['Task']['tickets']), sf)
                json = set_column_data(json, k, 'Epic', len(type_dict['Epic']['tickets']), sf)

                json = set_column_data(json, k, 'Blocked', len(status_dict['Blocked']['tickets']), sf)
                json = set_column_data(json, k, 'Code Review', len(status_dict['Code Review']['tickets']), sf)
                json = set_column_data(json, k, 'Defects Found', len(status_dict['Defects Found']['tickets']), sf)
                json = set_column_data(json, k, 'Done', len(status_dict['Done']['tickets']), sf)
                json = set_column_data(json, k, 'Draft', len(status_dict['Draft']['tickets']), sf)
                json = set_column_data(json, k, 'In Progress', len(status_dict['In Progress']['tickets']), sf)
                json = set_column_data(json, k, 'QA Complete', len(status_dict['QA Complete']['tickets']), sf)
                json = set_column_data(json, k, 'QA in Progress', len(status_dict['QA in Progress']['tickets']), sf)
                json = set_column_data(json, k, 'Ready for DEV', len(status_dict['Ready for DEV']['tickets']), sf)
                json = set_column_data(json, k, 'Ready for QA', len(status_dict['Ready for QA']['tickets']), sf)
    
                json = set_column_data(json, k, 'Total Bugs', len(open_bug_list), sf)
    
                json = set_column_data(json, k, 'Open: Low', len(severity_dict['low']['tickets']), sf)
                json = set_column_data(json, k, 'Open: Medium', len(severity_dict['medium']['tickets']), sf)
                json = set_column_data(json, k, 'Open: High', len(severity_dict['high']['tickets']), sf)
                json = set_column_data(json, k, 'Open: Critical', len(severity_dict['critical']['tickets']), sf)
                json = set_column_data(json, k, 'Open: No Severity', len(severity_dict['none']['tickets']), sf)
    
                json = set_column_data(json, k, 'Open: P1', len(priority_dict['P1']['tickets']), sf)
                json = set_column_data(json, k, 'Open: P2', len(priority_dict['P2']['tickets']), sf)
                json = set_column_data(json, k, 'Open: P3', len(priority_dict['P3']['tickets']), sf)
                json = set_column_data(json, k, 'Open: P4', len(priority_dict['P4']['tickets']), sf)
                json = set_column_data(json, k, 'Open: P5', len(priority_dict['P5']['tickets']), sf)

            if i < len(story_reference_dict['hasNoReference']):
                json = set_column_data(json, k, 'List of Stories that Need References',
                                       story_reference_dict['hasNoReference'][i], nf)
    
            if i < len(story_reference_dict['hasReference']):
                json = set_column_data(json, k, 'List of Stories that Have References',
                                       story_reference_dict['hasReference'][i], nf)
    
            if i < len(story_reference_dict['hasReferenceButDraftOrBlocked']):
                json = set_column_data(json, k, 'List of Refs for Stories in Draft/Blocked',
                                       story_reference_dict['hasReferenceButDraftOrBlocked'][i], nf)
    
            if i < len(status_dict['Blocked']['tickets']):
                json = set_column_data(json, k, 'List of Blocked', status_dict['Blocked']['tickets'][i], nf)
    
            if i < len(status_dict['Code Review']['tickets']):
                json = set_column_data(json, k, 'List of Code Review', status_dict['Code Review']['tickets'][i], nf)
    
            if i < len(status_dict['Defects Found']['tickets']):
                json = set_column_data(json, k, 'List of Defects Found', status_dict['Defects Found']['tickets'][i], nf)
    
            if i < len(status_dict['Done']['tickets']):
                json = set_column_data(json, k, 'List of Done', status_dict['Done']['tickets'][i], nf)
    
            if i < len(status_dict['Draft']['tickets']):
                json = set_column_data(json, k, 'List of Draft', status_dict['Draft']['tickets'][i], nf)
    
            if i < len(status_dict['In Progress']['tickets']):
                json = set_column_data(json, k, 'List of In Progress', status_dict['In Progress']['tickets'][i], nf)
    
            if i < len(status_dict['QA Complete']['tickets']):
                json = set_column_data(json, k, 'List of QA Complete', status_dict['QA Complete']['tickets'][i], nf)
    
            if i < len(status_dict['Ready for DEV']['tickets']):
                json = set_column_data(json, k, 'List of Ready for DEV', status_dict['Ready for DEV']['tickets'][i], nf)
    
            if i < len(status_dict['Ready for QA']['tickets']):
                json = set_column_data(json, k, 'List of Ready for QA', status_dict['Ready for QA']['tickets'][i], nf)
    
            if i < len(unlabeled_list):
                json = set_column_data(json, k, 'List of ALT tickets with no label', unlabeled_list[0], nf)
    
        if not json["cells"]:
            print("There are no more rows to create. There were %i rows created in total" % i)
            break

        r = requests.post(url, headers=headers, json=json)
        # sleep(1) # adds delay to lessen load on server
        if r.status_code == 200:
            i += 1
            print("Row: " + str(i) + " was created.")
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)


def delete_rows():
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
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        r = requests.delete(url, headers=headers)
        sleep(1)  # adds delay to lessen load on server
        if r.json()['message'] == "SUCCESS":
            print("The data in the sheet was deleted for rows between index:", beginningOfList, "and: ", endOfList)
        else:
            print("The data in the sheet was not deleted")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)


def change_sheet_name():
    # the below updates the smartsheet name
    month = datetime.date.today().strftime("%B")
    date = datetime.date.today().strftime("%d")
    year = datetime.date.today().strftime("%Y")
    dateHeader = date + " " + month + " " + year
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + smartSheetPassword}
    json = {"name": "ALT in Sprint Mobile Coverage - Daily"}
    r = requests.put(url, headers=headers, json=json)
    if r.status_code == 200:
        print("The smartsheet name was successfully changed")
    else:
        print("The smartsheet name was NOT successfully changed")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)


def main():
    
    list_of_suites = get_testrail_suites()
    list_of_references = get_testrail_list_of_references(list_of_suites)
    total_jira_issues = get_total_jira_issues()
    jira_ticket_dict = build_jira_ticket_dict(total_jira_issues, list_of_references)

    open_bug_list = build_open_bug_list(jira_ticket_dict)
    unlabeled_list = build_unlabeled_list(jira_ticket_dict)

    severity_dict = build_severity_dict(jira_ticket_dict)
    priority_dict = build_priority_dict(jira_ticket_dict)
    status_dict, report_ticket_list = build_status_dict(jira_ticket_dict)
    type_dict = build_type_dict(jira_ticket_dict)
    story_reference_dict = build_story_reference_dict(jira_ticket_dict)

    delete_rows()
    create_rows(jira_ticket_dict, severity_dict, priority_dict, status_dict, type_dict, story_reference_dict,
                list_of_references, total_jira_issues, open_bug_list, unlabeled_list)


if __name__ == '__main__':
    main()

