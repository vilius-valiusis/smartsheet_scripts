import requests
import datetime
import re
from time import sleep
import sys

# These are id's needing to be specific to project
smartSheetId = 5326193374324612
testRailProjectId = 12

month = datetime.date.today().strftime("%m")
date = datetime.date.today().strftime("%d")
year = datetime.date.today().strftime("%y")
dateHeader = month + "/" + date + "/" + year

# to be used in terminal / Jenkins:
testRailPassword = sys.argv[1]
testRailEmail = sys.argv[2]
jiraBasicAuth = sys.argv[3]
smartSheetPassword = sys.argv[4]

# This script needs the SmartSheet to be set up in advance per the below format
# It also needs to have Suites made in TestRail following a format as well.

# These are lists of how the smartsheet should stay formatted:
listOfColumnIds = [4561499973805956, 7141899682244484, 1512400148031364, 6015999775401860, 3764199961716612, 8267799589087108, 949450194610052, 5453049821980548, 3201250008295300, 7704849635665796, 2075350101452676, 6578949728823172, 4327149915137924, 8830749542508420, 245762752833412, 4749362380203908, 2497562566518660, 7001162193889156, 1371662659676036, 5875262287046532, 3623462473361284, 8127062100731780, 808712706254724, 5312312333625220, 3060512519939972, 7564112147310468, 1934612613097348, 6438212240467844, 4186412426782596, 8690012054153092, 527237729544068, 5030837356914564, 2779037543229316, 7282637170599812]
listOfColumnTitles =  ['Date', 'References', 'Cases w References', 'Cases w/o References', 'Percentage Covered', 'Percentage Not Covered', 'Refs for Tickets that are not Stories', 'Total JIRA', 'Bugs', 'Stories', 'Sub-Task', 'Task', 'Epic', 'Blocked', 'Code Review', 'Monitoring', 'Done', 'Draft', 'In Progress', 'Rejected', 'QA in Progress', 'Ready for DEV', 'Ready for QA', 'Total Bugs', 'Open: Low', 'Open: Medium', 'Open: High', 'Open: Critical', 'Open: No Severity', 'Open: P1', 'Open: P2', 'Open: P3', 'Open: P4', 'Open: P5']

# global lists created below
keyStatusDict = {}
keyTypeDict = {}
keyPriorityDict = {}
keySeverityDict = {}
notTestable = []
listOfReferences = []
listOfStatus = []
listOfReportTickets = []
listOfTicketsWithNoLabels = []
bugList = []
totalIssues = 0

# The below call to testrail gets a list of suites for ALT's Regression Sprint:---------------------------------------
listOfSuites = []
url = 'https://te2qa.testrail.net/index.php?/api/v2/get_suites/' + str(testRailProjectId)+ '&suite_id='
headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
if r.status_code != 200:
    print('Did not get a list of suites from testrail')
else:
    print("The call to TestRail to get a list of suites for Trident's Regression Sprint was successful.")
    for suite in r.json():
        #if 'Regression' in suite['name']:
        suiteId = suite['id']
        listOfSuites.append(suiteId)

# The below call to testrail goes through each suite and gets a list of references:-----------------------------------
for suiteIdFromList in listOfSuites:
    url = 'https://te2qa.testrail.net/index.php?/api/v2/get_cases/' + str(testRailProjectId) + '&suite_id=' + str(suiteIdFromList)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
    if r.status_code != 200:
        print('Did not get a list of references for this suite from testrail')
    else:
        print("The call to TestRail to get references for TestRail Suite ID: %s was successful" % str(suiteIdFromList))
        for testCase in r.json():
            if testCase['refs']:
                if 'CAR' in testCase['refs'] or 'car' in testCase['refs'] or 'AES' in testCase['refs'] or 'aes' in testCase['refs']:
                    reference = testCase['refs']
                    reference = reference.replace(" ", "")
                    reference = reference.replace(")", "")
                    reference = reference.replace("(", "")
                    reference = reference.replace("  ", "")
                    if ',' not in reference and '&' not in reference:
                        if reference not in listOfReferences:
                            listOfReferences.append(reference)
                    if ',' in reference:
                        reference = list(reference.split(','))
                        for refr in reference:
                            if 'CAR' in refr or 'car' in refr or 'AES' in refr or 'aes' in refr:
                                if refr not in listOfReferences:
                                    listOfReferences.append(refr)  # listOfReferences now contains all refs in testrail for Mobile Sprints
                    if '&' in reference:
                        reference = list(reference.split('&'))
                        for refr in reference:
                            if 'CAR' in refr or 'car' in refr or 'AES' in refr or 'aes' in refr:
                                if refr not in listOfReferences:
                                    listOfReferences.append(refr)

#This call establishes total number of tickets, so we can iterates through them in batches----------------------------
urlList = [
'https://te2web.atlassian.net/rest/api/2/search?jql=project%20%3D%20AES%20AND%20"AES%20Customer"%20%3D%20Carnival&maxResults=0',
'https://te2web.atlassian.net/rest/api/2/search?jql=project=car&maxResults=0'
]
for url in urlList:
    headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}
    r = requests.get(url, headers=headers)
    totalIssues = totalIssues + r.json()['total']
    if r.status_code != 200:
        print("Did not get a number of JIRA Tickets")
    else:
        print("The call to get the total number of JIRA tickets was successful. Total issues: ", totalIssues)

# This loop runs through all the issues (limited by blocks of 100 by JIRA)
# It creates 2 dictionaries for all ALT tickets: JIRA ticket numbers & status, and JIRA ticket number and type

urlList = [
    'https://te2web.atlassian.net/rest/api/2/search?jql=project=CAR&fields=customfield_12825,priority,issuetype,status,labels,key,summary&maxResults=100&startAt=',
    'https://te2web.atlassian.net/rest/api/2/search?jql=project%20%3D%20AES%20AND%20"AES%20Customer"%20%3D%20Carnival&fields=customfield_12825,priority,issuetype,status,labels,key,summary&maxResults=100&startAt='
]
for singleUrl in urlList:
    for i in range(0, totalIssues, 100):
        url = singleUrl + str(i)
        headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print('Error: was unable to run through the first %i number of JIRA issues' % i)
        else:
            print('The call to run through the first %i number of JIRA issues was successful.' % (i+100))
            for ticket in r.json()['issues']:
                summary = ticket['fields']['summary']
                label = ticket['fields']['labels']
                priority = ticket['fields']['priority']['name']
                if ticket['fields']['customfield_12825'] is not None:
                    severity = ticket['fields']['customfield_12825']['value']
                else: severity = 'null'
                status = ticket['fields']['status']['name']
                type = ticket['fields']['issuetype']['name']
                key = ticket['key']
                if status not in listOfStatus:
                    listOfStatus.append(status)
                keyStatusDict.update({key: status})
                keyTypeDict.update({key: type})
                keyPriorityDict.update({key: priority})
                keySeverityDict.update({key: severity})
                if type == 'Bug' and status != 'Done':
                    bugList.append(key)
openBugCount = len(bugList)

# This loops through all Severities and creates a list / quantity for each
AltTicketList_NullSeverity = []
AltTicketList_LowSeverity = []
AltTicketList_MediumSeverity = []
AltTicketList_HighSeverity = []
AltTicketList_CriticalSeverity = []
for severityKey, severityValue in keySeverityDict.items():
    if severityKey in bugList:
        if severityValue == 'Low':
            AltTicketList_LowSeverity.append(severityKey)
        elif severityValue == 'Medium':
            AltTicketList_MediumSeverity.append(severityKey)
        elif severityValue == 'High':
            AltTicketList_HighSeverity.append(severityKey)
        elif severityValue == 'Critical':
            AltTicketList_CriticalSeverity.append(severityKey)
        else:
            AltTicketList_NullSeverity.append(severityKey)

# This loops through all priorities and creates a list / quantity for each
AltTicketList_MinorPriority = []
AltTicketList_BlockerPriority = []
AltTicketList_CriticalPriority = []
AltTicketList_MajorPriority = []
AltTicketList_TrivialPriority = []
for priorityKey, priorityValue in keyPriorityDict.items():
    if priorityKey in bugList:
        if priorityValue == 'P4 - Minor':
            AltTicketList_MinorPriority.append(priorityKey)
        if priorityValue == 'P1 - Blocker':
            AltTicketList_BlockerPriority.append(priorityKey)
        if priorityValue == 'P2 - Critical':
            AltTicketList_CriticalPriority.append(priorityKey)
        if priorityValue == 'P3 - Major':
            AltTicketList_MajorPriority.append(priorityKey)
        if priorityValue == 'P5 - Trivial':
            AltTicketList_TrivialPriority.append(priorityKey)

# This loop goes through all the statuses and creates a list / quantity for each
AltTicketList_Draft = []
AltTicketList_InProgress = []
AltTicketList_ReadyforQA = []
AltTicketList_Monitoring = []
AltTicketList_Done = []
AltTicketList_CodeReview = []
AltTicketList_Blocked = []
AltTicketList_Rejected = []
AltTicketList_ReadyforDEV = []
AltTicketList_QAinProgress = []
for statusType in sorted(listOfStatus):
    print("A list of JIRA tickets was created for %s status type" % statusType)
    for dicKey, value in keyStatusDict.items():
        if value != "Draft" and value != "Blocked":
            if dicKey not in listOfReportTickets:
                listOfReportTickets.append(dicKey)
        if value == 'Draft':
            if dicKey not in AltTicketList_Draft:
                AltTicketList_Draft.append(dicKey)
        if value == 'In Progress':
            if dicKey not in AltTicketList_InProgress:
                AltTicketList_InProgress.append(dicKey)
        if value == 'Ready for QA':
            if dicKey not in AltTicketList_ReadyforQA:
                AltTicketList_ReadyforQA.append(dicKey)
        if value == 'Monitoring':
            if dicKey not in AltTicketList_Monitoring:
                AltTicketList_Monitoring.append(dicKey)
        if value == 'Done':
            if dicKey not in AltTicketList_Done:
                AltTicketList_Done.append(dicKey)
        if value == 'Code Review':
            if dicKey not in AltTicketList_CodeReview:
                AltTicketList_CodeReview.append(dicKey)
        if value == 'Blocked':
            if dicKey not in AltTicketList_Blocked:
                AltTicketList_Blocked.append(dicKey)
        if value == 'Rejected':
            if dicKey not in AltTicketList_Rejected:
                AltTicketList_Rejected.append(dicKey)
        if value == 'Ready for DEV':
            if dicKey not in AltTicketList_ReadyforDEV:
                AltTicketList_ReadyforDEV.append(dicKey)
        if value == 'QA in Progress':
            if dicKey not in AltTicketList_QAinProgress:
                AltTicketList_QAinProgress.append(dicKey)

listOfReportTickets = sorted(listOfReportTickets, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
listOfReportTickets = listOfReportTickets[::-1] # reverses the list

listOfStories=[]
totalBugCount = 0
totalStoryCount = 0
totalSubTaskCount = 0
totalTaskCount = 0
totalEpicCount = 0
for ticketNumber, ticketType in keyTypeDict.items():
    if ticketType == 'Bug':
        totalBugCount += 1
    if ticketType == 'Story':
        totalStoryCount += 1
    if ticketType == 'Sub-task':
        totalSubTaskCount += 1
    if ticketType == 'Task':
        totalTaskCount += 1
    if ticketType == 'Epic':
        totalEpicCount += 1
    for reportTicket in listOfReportTickets:
        if ticketNumber == reportTicket:
            if ticketType == 'Story':
            #   this runs through the tickets not in draft or blocked - for CAR & AES it is bugs and stories.
                listOfStories.append(reportTicket)
print("A count was created for each of the JIRA ticket types.")
print('listOfStories: ', listOfStories)
# below is the basic calculation for stories in JIRA vs. References in TestRail:
listOfStoriesWithRefs = []
listOfStoriesWithNORefs = []
listOfRefsForStoriesNotNeedingRefs = []
for num in listOfStories:
    if num in listOfReferences:
        listOfStoriesWithRefs.append(num) # list of jira stories that are referenced in testrail
    else:
        listOfStoriesWithNORefs.append(num) # list of jira stories that are not referenced in testrail
for num in listOfReferences:
    if num not in listOfStories:
        listOfRefsForStoriesNotNeedingRefs.append(num)
        # list of jira stories that are referenced in testrail, but are in draft or blocked

casesWithRefs = len(listOfStoriesWithRefs)
casesWithNoRefs = len(listOfStoriesWithNORefs)
refsWithNoCases = len(listOfRefsForStoriesNotNeedingRefs)

listOfStoriesWithNORefs = sorted(listOfStoriesWithNORefs, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
listOfStoriesWithNORefs = listOfStoriesWithNORefs[::-1] # reverses the list
listOfStoriesWithRefs = sorted(listOfStoriesWithRefs, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
listOfStoriesWithRefs = listOfStoriesWithRefs[::-1] # reverses the list
# listOfRefsForStoriesNotNeedingRefs = sorted(listOfRefsForStoriesNotNeedingRefs, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
# listOfRefsForStoriesNotNeedingRefs = listOfRefsForStoriesNotNeedingRefs[::-1] # reverses the list


print("A calculation was made for stories in JIRA vs. References in TestRail")

# The below call returns the list of columns for the sheet, making a dictionary of ID's and Titles
idTitleDict = {}
url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/columns'
headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print('Error: The SmartSheet was not found.')
else:
    print('The call to confirm that the SmartSheet was not altered per specification was successful.')
    for column in r.json()['data']:
        columnId = column['id']
        columnTitle = column['title']
        if columnTitle not in listOfColumnTitles:
            print("the Column with title: %s has changed. May need Updating..." % (columnTitle))
            break
        if columnId not in listOfColumnIds:
            print("the Column with id: %s has changed. May need Updating..." % (columnId))
            break
        idTitleDict.update({columnId: columnTitle})

percentageCovered = (float(len(listOfReferences)) - float(refsWithNoCases)) / float(len(listOfStories)) * float(100)

def CreateRows():
    # This function creates rows from the above data, per column
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId) + '/rows'
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    summaryFormat = ",2,1,,,,1,,,8,,,,,,"
    normalFormat = ",,,,,,,,,18,,,,,,"
    true = 'true'
    for rowCount in range(0,totalIssues):
        if rowCount == 0:
            json = {"toBottom":true,"cells":[]}
            for columnId in idTitleDict:
                columnTitle = idTitleDict[columnId]
                if columnTitle == 'Date':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": str(dateHeader), "format": summaryFormat})
                if columnTitle == 'References':
                    json.setdefault("cells", []).append({"columnId": columnId,"value":len(listOfReferences),"format":summaryFormat})
                if columnTitle == 'Cases w References':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfStoriesWithRefs), "format": summaryFormat})
                if columnTitle == 'Cases w/o References':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfStoriesWithNORefs), "format": summaryFormat})
                if columnTitle == 'Percentage Covered':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": str(round(percentageCovered,2)) + " %", "format": summaryFormat})
                if columnTitle == 'Percentage Not Covered':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": str(round(float(float(100) - percentageCovered),2)) + " %", "format": summaryFormat})
                if columnTitle == 'Refs for Tickets that are not Stories':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfRefsForStoriesNotNeedingRefs), "format": summaryFormat})
                if columnTitle == 'Total JIRA':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalIssues, "format": summaryFormat})


                if columnTitle == 'Bugs':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalBugCount, "format": summaryFormat})
                if columnTitle == 'Stories':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalStoryCount, "format": summaryFormat})
                if columnTitle == 'Sub-Task':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalSubTaskCount, "format": summaryFormat})
                if columnTitle == 'Task':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalTaskCount, "format": summaryFormat})
                if columnTitle == 'Epic':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalEpicCount, "format": summaryFormat})
                if columnTitle == 'Blocked':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Blocked), "format": summaryFormat})
                if columnTitle == 'Code Review':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_CodeReview), "format": summaryFormat})
                if columnTitle == 'Rejected':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Rejected), "format": summaryFormat})
                if columnTitle == 'Done':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Done), "format": summaryFormat})
                if columnTitle == 'Draft':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Draft), "format": summaryFormat})
                if columnTitle == 'In Progress':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_InProgress), "format": summaryFormat})
                if columnTitle == 'Monitoring':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Monitoring), "format": summaryFormat})
                if columnTitle == 'QA in Progress':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_QAinProgress), "format": summaryFormat})
                if columnTitle == 'Ready for DEV':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_ReadyforDEV), "format": summaryFormat})
                if columnTitle == 'Ready for QA':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_ReadyforQA), "format": summaryFormat})

                if columnTitle == 'Total Bugs':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": openBugCount, "format": summaryFormat})
                if columnTitle == 'Open: Low':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_LowSeverity), "format": summaryFormat})
                if columnTitle == 'Open: Medium':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_MediumSeverity), "format": summaryFormat})
                if columnTitle == 'Open: High':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_HighSeverity), "format": summaryFormat})
                if columnTitle == 'Open: Critical':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_CriticalSeverity), "format": summaryFormat})
                if columnTitle == 'Open: No Severity':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_NullSeverity), "format": summaryFormat})

                if columnTitle == 'Open: P1':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_BlockerPriority), "format": summaryFormat})
                if columnTitle == 'Open: P2':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_CriticalPriority), "format": summaryFormat})
                if columnTitle == 'Open: P3':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_MajorPriority), "format": summaryFormat})
                if columnTitle == 'Open: P4':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_MinorPriority), "format": summaryFormat})
                if columnTitle == 'Open: P5':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_TrivialPriority), "format": summaryFormat})


            print("  ~~  Summary Line Created  ~~  ")

            r = requests.post(url, headers=headers, json=json)
            sleep(1) # adds delay to lessen load on server
            if r.status_code == 200:
                rowCount += 1
                print("Summary row: was created.")
                break
            else:
                print("The row in the sheet was not created")
                print('The status code was: ', r.status_code, 'and the content was: ', r.content)
                break



CreateRows()

#####################################################################################################################

# if multiple editors use the sheet, it may be necessary to add the function 'DeleteColumns()'
# this would delete and create the columns per the specified list: 'listOfColumnTitles'


