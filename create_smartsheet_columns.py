import requests

smartSheetId =  5326193374324612 # input here
smartSheetPassword = # need to insert passwords

listOfColumnTitles =  ['References', 'Cases w References', 'Cases w/o References', 'Percentage Covered', 'Percentage Not Covered', 'List of Trident Stories that Need References', 'List of Stories that Have References', 'List of Refs for Tickets that are not Stories', 'Refs for Tickets that are not Stories', 'Total JIRA', 'Bugs', 'Stories', 'Sub-Task', 'Task', 'Epic', 'Blocked', 'Code Review', 'Monitoring', 'Done', 'Draft', 'In Progress', 'Rejected', 'QA in Progress', 'Ready for DEV', 'Ready for QA', 'Total Bugs', 'Open: Low', 'Open: Medium', 'Open: High', 'Open: Critical', 'Open: No Severity', 'Open: P1', 'Open: P2', 'Open: P3', 'Open: P4', 'Open: P5', 'List of Blocked', 'List of Code Review', 'List of Rejected', 'List of Done', 'List of Draft', 'List of In Progress', 'List of Monitoring', 'List of QA in Progress', 'List of Ready for DEV', 'List of Ready for QA']

def CreateColumns():
    #This function creates columns from a list

    url = "https://api.smartsheet.com/2.0/sheets/" + str(smartSheetId) + "/columns"
    headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
    json = []
    for title in listOfColumnTitles:
        if 'List' not in title:
            jsonAddon = {"title": title,"type": "TEXT_NUMBER","index": 1,"width": 80}
            json.append(jsonAddon)
    r = requests.post(url, headers=headers, json=json)
    if r.status_code != 200:
        print("error: ", r.status_code, r.content)
    else:
        print("columns successfully updated")
CreateColumns()