import requests
import datetime
import re
from time import sleep
import sys

# These are id's needing to be specific to project
smartSheetId = 2809732844021636
testRailProjectId = 21

# to be used in terminal / Jenkins:
testRailPassword = sys.argv[1]
testRailEmail = sys.argv[2]
jiraBasicAuth = sys.argv[3]
smartSheetPassword = sys.argv[4]

# This script needs the SmartSheet to be set up in advance per the below format
# It also needs to have Suites made in TestRail following a format as well.

# these are the different JIRA team labels
ios = 'FueledAlterra'
android = 'FueledAndroidAlterra'
aes = 'AESAlterra'

# These are lists of how the smartsheet should stay formatted:
listOfColumnIds = [5437891405997956, 3186091592312708, 7689691219683204, 2060191685470084, 6563791312840580, 5538655633729412, 87049215731588, 934291778627460, 6631342424254340, 2127742796883844, 4311991499155332, 4379542610569092, 8883142237939588, 8815591126525828, 230604336850820, 4734203964221316, 2482404150536068, 6986003777906564, 1356504243693444, 5860103871063940, 3608304057378692, 8111903684749188, 793554290272132, 5297153917642628, 3045354103957380, 7548953731327876, 1919454197114756, 6423053824485252, 5903767448119172, 5489966676502404, 3238166862817156, 7741766490187652, 2112266955974532, 6615866583345028, 8867666397030276, 71573374822276, 4575173002192772, 4364066769659780, 2323373188507524, 4171254010800004, 8674853638170500, 512079313561476, 5015678940931972, 2763879127246724, 7267478754617220, 1637979220404100, 6141578847774596, 3889779034089348, 8393378661459844, 4590648843102084]
listOfColumnTitles =  ['References', 'Cases w References', 'Cases w/o References', 'Percentage Covered', 'Percentage Not Covered', 'List of Fueled Stories that Need References', 'List of AES Stories that Need References', 'List of Stories that Have References', 'List of Refs for Stories in Draft/Blocked', 'Refs in Draft/Blocked', 'Total JIRA', 'Total AES', 'Total Fueled', 'Bugs', 'Stories', 'Sub-Task', 'Task', 'Epic', 'Blocked', 'Code Review', 'Defects Found', 'Done', 'Draft', 'In Progress', 'QA Complete', 'QA in Progress', 'Ready for DEV', 'Ready for QA', 'Total Bugs', 'Open: Low', 'Open: Medium', 'Open: High', 'Open: Critical', 'Open: No Severity', 'Open: P1', 'Open: P2', 'Open: P3', 'Open: P4', 'Open: P5', 'List of Blocked', 'List of Code Review', 'List of Defects Found', 'List of Done', 'List of Draft', 'List of In Progress', 'List of QA Complete', 'List of QA in Progress', 'List of Ready for DEV', 'List of Ready for QA', 'List of ALT tickets with no label']

# global lists created below
totalAesIssues = 0
totalFueledIssues = 0
listOfAesTickets = []
listOfFueledTickets = []
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

# The below call to testrail gets a list of suites for ALT's Regression Sprint:---------------------------------------
listOfSuites = []
url = 'https://te2qa.testrail.net/index.php?/api/v2/get_suites/' + str(testRailProjectId)+ '&suite_id='
headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
if r.status_code != 200:
    print('Did not get a list of suites from testrail')
else:
    print("The call to TestRail to get a list of suites for ALT's Regression Sprint was successful.")
    for suite in r.json():
        if 'Regression' in suite['name']:
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
                        if refr not in listOfReferences:
                            listOfReferences.append(refr)  # listOfReferences now contains all refs in testrail for Mobile Sprints
                if '&' in reference:
                    reference = list(reference.split('&'))
                    for refr in reference:
                        if refr not in listOfReferences:
                            listOfReferences.append(refr)

#this call establishes total number of tickets, so we can iterates through them in batches----------------------------
url = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=ALT&maxResults=0'
headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + jiraBasicAuth}
r = requests.get(url, headers=headers)
totalIssues = r.json()['total']
if r.status_code != 200:
    print('Did not get a number of JIRA Tickets')
else:
    print("The call to get the total number of JIRA tickets was successful for ALT. Total issues: ", totalIssues)

# This loop runs through all the issues (limited by blocks of 100 by JIRA)
# It creates 2 dictionaries for all ALT tickets: JIRA ticket numbers & status, and JIRA ticket number and type
for i in range (0,totalIssues,100):
    url = 'https://te2web.atlassian.net/rest/api/2/search?jql=project=ALT&fields=customfield_12825,priority,issuetype,status,labels,key,summary&maxResults=100&startAt=' + str(i)
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
            severity = ticket['fields']['customfield_12825']['value']
            status = ticket['fields']['status']['name']
            type = ticket['fields']['issuetype']['name']
            key = ticket['key']
            if status not in listOfStatus:
                listOfStatus.append(status)
            keyStatusDict.update({key: status})
            keyTypeDict.update({key: type})
            keyPriorityDict.update({key: priority})
            keySeverityDict.update({key: severity})
            if aes in label:
                totalAesIssues += 1
                listOfAesTickets.append(key)
            if ios in label or android in label:
                totalFueledIssues += 1
                listOfFueledTickets.append(key)
            if type == 'Bug' and status != 'Done':
                bugList.append(key)
            if 'Not-Testable' in label:
                if key not in notTestable:
                    notTestable.append(key)
            if aes not in label and android not in label and ios not in label:
                if key not in listOfTicketsWithNoLabels:
                    listOfTicketsWithNoLabels.append(key)

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
AltTicketList_QAComplete = []
AltTicketList_Done = []
AltTicketList_CodeReview = []
AltTicketList_Blocked = []
AltTicketList_DefectsFound = []
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
        if value == 'QA Complete':
            if dicKey not in AltTicketList_QAComplete:
                AltTicketList_QAComplete.append(dicKey)
        if value == 'Done':
            if dicKey not in AltTicketList_Done:
                AltTicketList_Done.append(dicKey)
        if value == 'Code Review':
            if dicKey not in AltTicketList_CodeReview:
                AltTicketList_CodeReview.append(dicKey)
        if value == 'Blocked':
            if dicKey not in AltTicketList_Blocked:
                AltTicketList_Blocked.append(dicKey)
        if value == 'Defects Found':
            if dicKey not in AltTicketList_DefectsFound:
                AltTicketList_DefectsFound.append(dicKey)
        if value == 'Ready for DEV':
            if dicKey not in AltTicketList_ReadyforDEV:
                AltTicketList_ReadyforDEV.append(dicKey)
        if value == 'QA in Progress':
            if dicKey not in AltTicketList_QAinProgress:
                AltTicketList_QAinProgress.append(dicKey)

listOfReportTickets = sorted(listOfReportTickets, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
listOfReportTickets = listOfReportTickets[::-1] # reverses the list

listOfStories=[] # this is made as a decision was made that refs should only be for the aes 'story' tickets
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
            #   this runs through the tickets not in draft or blocked - for AES it is more than stories.
            listOfStories.append(reportTicket)
print("A count was created for each of the JIRA ticket types.")

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
listOfRefsForStoriesNotNeedingRefs = sorted(listOfRefsForStoriesNotNeedingRefs, key=lambda x: int(re.search(r'\d+$',x).group())) # sorts only by number
listOfRefsForStoriesNotNeedingRefs = listOfRefsForStoriesNotNeedingRefs[::-1] # reverses the list


listOfAesTicketsWithNoRefs = []
for story in listOfAesTickets:
    if story in listOfStoriesWithNORefs and story not in listOfRefsForStoriesNotNeedingRefs:
        listOfAesTicketsWithNoRefs.append(story)

listOfFueledTicketsWithNoRefs = []
for story in listOfFueledTickets:
    if story in listOfStoriesWithNORefs and story not in listOfRefsForStoriesNotNeedingRefs:
        listOfFueledTicketsWithNoRefs.append(story)

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
                if columnTitle == 'References':
                    json.setdefault("cells", []).append({"columnId": columnId,"value":len(listOfReferences),"format":summaryFormat})
                if columnTitle == 'Cases w References':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfStoriesWithRefs), "format": summaryFormat})
                if columnTitle == 'Cases w/o References':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfAesTicketsWithNoRefs)+ len(listOfFueledTicketsWithNoRefs), "format": summaryFormat})
                if columnTitle == 'Percentage Covered':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": str(round(percentageCovered,2)) + " %", "format": summaryFormat})
                if columnTitle == 'Percentage Not Covered':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": str(round(float(float(100) - percentageCovered),2)) + " %", "format": summaryFormat})
                if columnTitle == 'List of AES Stories that Need References':
                    if len(listOfAesTicketsWithNoRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfAesTicketsWithNoRefs[0], "format": normalFormat})
                if columnTitle == 'List of Fueled Stories that Need References':
                    if len(listOfFueledTicketsWithNoRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfFueledTicketsWithNoRefs[0], "format": normalFormat})
                if columnTitle == 'List of Stories that Have References':
                    if len(listOfStoriesWithRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfStoriesWithRefs[0], "format": normalFormat})
                if columnTitle == 'List of Refs for Stories in Draft/Blocked':
                    if len(listOfRefsForStoriesNotNeedingRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfRefsForStoriesNotNeedingRefs[0], "format": normalFormat})

                if columnTitle == 'Refs in Draft/Blocked':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(listOfRefsForStoriesNotNeedingRefs), "format": summaryFormat})
                if columnTitle == 'Total JIRA':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalIssues, "format": summaryFormat})
                if columnTitle == 'Total Fueled':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalFueledIssues, "format": summaryFormat})
                if columnTitle == 'Total AES':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": totalAesIssues, "format": summaryFormat})

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
                if columnTitle == 'Defects Found':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_DefectsFound), "format": summaryFormat})
                if columnTitle == 'Done':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Done), "format": summaryFormat})
                if columnTitle == 'Draft':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_Draft), "format": summaryFormat})
                if columnTitle == 'In Progress':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_InProgress), "format": summaryFormat})
                if columnTitle == 'QA Complete':
                    json.setdefault("cells", []).append({"columnId": columnId, "value": len(AltTicketList_QAComplete), "format": summaryFormat})
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

                if columnTitle == 'List of Blocked':
                    if len(AltTicketList_Blocked) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Blocked[rowCount], "format": normalFormat})
                if columnTitle == 'List of Code Review':
                    if len(AltTicketList_CodeReview) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_CodeReview[rowCount], "format": normalFormat})
                if columnTitle == 'List of Defects Found':
                    if len(AltTicketList_DefectsFound) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_DefectsFound[rowCount], "format": normalFormat})
                if columnTitle == 'List of Done':
                    if len(AltTicketList_Done) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Done[rowCount], "format": normalFormat})
                if columnTitle == 'List of Draft':
                    if len(AltTicketList_Draft) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Draft[rowCount], "format": normalFormat})
                if columnTitle == 'List of In Progress':
                    if len(AltTicketList_InProgress) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_InProgress[rowCount], "format": normalFormat})
                if columnTitle == 'List of QA Complete':
                    if len(AltTicketList_QAComplete) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_QAComplete[rowCount], "format": normalFormat})
                if columnTitle == 'List of QA in Progress':
                    if len(AltTicketList_QAinProgress) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_QAinProgress[rowCount], "format": normalFormat})
                if columnTitle == 'List of Ready for DEV':
                    if len(AltTicketList_ReadyforDEV) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_ReadyforDEV[rowCount], "format": normalFormat})
                if columnTitle == 'List of Ready for QA':
                    if len(AltTicketList_ReadyforQA) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_ReadyforQA[rowCount], "format": normalFormat})
                if columnTitle == 'List of ALT tickets with no label':
                    if len(listOfTicketsWithNoLabels) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfTicketsWithNoLabels[0], "format": normalFormat})
            print("  ~~  Summary Line Created  ~~  ")
        else:
            json = {"toBottom":true,"cells":[]}
            for columnId in idTitleDict:
                columnTitle = idTitleDict[columnId]
                if columnTitle == 'List of AES Stories that Need References':
                    if len(listOfAesTicketsWithNoRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfAesTicketsWithNoRefs[rowCount], "format": normalFormat})
                if columnTitle == 'List of Fueled Stories that Need References':
                    if len(listOfFueledTicketsWithNoRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfFueledTicketsWithNoRefs[rowCount], "format": normalFormat})
                if columnTitle == 'List of Stories that Have References':
                    if len(listOfStoriesWithRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfStoriesWithRefs[rowCount], "format": normalFormat})
                if columnTitle == 'List of Refs for Stories in Draft/Blocked':
                    if len(listOfRefsForStoriesNotNeedingRefs) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfRefsForStoriesNotNeedingRefs[rowCount], "format": normalFormat})
                if columnTitle == 'List of Blocked':
                    if len(AltTicketList_Blocked) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Blocked[rowCount], "format": normalFormat})
                if columnTitle == 'List of Code Review':
                    if len(AltTicketList_CodeReview) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_CodeReview[rowCount], "format": normalFormat})
                if columnTitle == 'List of Defects Found':
                    if len(AltTicketList_DefectsFound) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_DefectsFound[rowCount], "format": normalFormat})
                if columnTitle == 'List of Done':
                    if len(AltTicketList_Done) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Done[rowCount], "format": normalFormat})
                if columnTitle == 'List of Draft':
                    if len(AltTicketList_Draft) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_Draft[rowCount], "format": normalFormat})
                if columnTitle == 'List of In Progress':
                    if len(AltTicketList_InProgress) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_InProgress[rowCount], "format": normalFormat})
                if columnTitle == 'List of QA Complete':
                    if len(AltTicketList_QAComplete) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_QAComplete[rowCount], "format": normalFormat})
                if columnTitle == 'List of QA in Progress':
                    if len(AltTicketList_QAinProgress) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_QAinProgress[rowCount], "format": normalFormat})
                if columnTitle == 'List of Ready for DEV':
                    if len(AltTicketList_ReadyforDEV) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_ReadyforDEV[rowCount], "format": normalFormat})
                if columnTitle == 'List of Ready for QA':
                    if len(AltTicketList_ReadyforQA) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": AltTicketList_ReadyforQA[rowCount], "format": normalFormat})
                if columnTitle == 'List of ALT tickets with no label':
                    if len(listOfTicketsWithNoLabels) > rowCount:
                        json.setdefault("cells", []).append({"columnId": columnId, "value": listOfTicketsWithNoLabels[rowCount], "format": normalFormat})
            if json["cells"] == []:
                print("There are no more rows to create. There were %i rows created in total" % rowCount)
                break
        r = requests.post(url, headers=headers, json=json)
        # sleep(1) # adds delay to lessen load on server
        if r.status_code == 200:
            rowCount +=1
            print("Row: " + str(rowCount) + " was created.")
        else:
            print("The row in the sheet was not created")
            print('The status code was: ', r.status_code, 'and the content was: ', r.content)

def DeleteRows():
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


DeleteRows()
CreateRows()

#####################################################################################################################

# if multiple editors use the sheet, it may be necessary to add the function 'DeleteColumns()'
# this would delete and create the columns per the specified list: 'listOfColumnTitles'

# Below are helper functions:

#ChangeSheetName()
def ChangeSheetName():
    # the below updates the smartsheet name
    month = datetime.date.today().strftime("%B")
    date = datetime.date.today().strftime("%d")
    year = datetime.date.today().strftime("%Y")
    dateHeader = date + " " + month + " " + year
    url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartSheetId)
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + smartSheetPassword}
    json = {"name": "ALT Regression Coverage - Daily"}
    r = requests.put(url, headers=headers, json=json)
    if r.status_code == 200:
        print("The smartsheet name was successfully changed")
    else:
        print("The smartsheet name was NOT successfully changed")
        print('The status code was: ', r.status_code, 'and the content was: ', r.content)