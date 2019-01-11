import requests

smartSheetIdList = [8146483112372100, 6563023696488324, 4838533660731268, 1572782262773636, 1507223881967492, 2809732844021636] # input here
smartSheetPassword = #insert password here..

#listOfColumnTitles = ['Number of Low Severity', 'Number of Medium Severity', 'Number of High Severity', 'Number of Critical Severity', 'Number of P1 - Blocker Priority', 'Number of P2 - Critical Priority', 'Number of P3 - Major Priority', 'Number of P4 - Minor Priority', 'Number of P5 - Trivial Priority']
#columnUpdateDic = {}
def UpdateColumns():
    #This function gets the sheet columns
    for smartSheetId in smartSheetIdList:
        print("smartSheetid:", smartSheetId)
        url = "https://api.smartsheet.com/2.0/sheets/" + str(smartSheetId) + "/columns"
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        r = requests.get(url, headers=headers)
        #print(r.json())
        if r.status_code != 200:
            print("error: ", r.status_code, r.content)
        else:
            for column in r.json()['data']:
                oldTitle = column['title']
                title = column['title']
                # if title == "Total Number of Tickets in JIRA":
                #     title = "Total JIRA"
                # if title == "Total AES Tickets in JIRA":
                #     title = "Total AES"
                # if title == "Total Fueled Tickets in JIRA":
                #     title = "Total Fueled"
                # if title == "Open Bugs: Total Number":
                #     title = "Total Bugs"
                # if "Open Bugs: " in title:
                #     title = title.replace("Open Bugs: ", "Open: ")
                # if " Severity" in title:
                #     title = title.replace(" Severity", "")
                # if " Listed" in title:
                #     title = title.replace(" Listed", " Severity")
                # if "Number of " in title:
                #     title = title.replace("Number of ", "")
                # if "Tickets in JIRA" in title:
                #     title = title.replace(" Tickets in JIRA", "")
                # if 'P1 - Blocker Priority' in title:
                #     title = title.replace('P1 - Blocker Priority', 'P1')
                # if 'P2 - Critical Priority' in title:
                #     title = title.replace('P2 - Critical Priority', 'P2')
                # if 'P3 - Major Priority' in title:
                #     title = title.replace('P3 - Major Priority', 'P3')
                # if 'P4 - Minor Priority' in title:
                #     title = title.replace('P4 - Minor Priority', 'P4')
                # if 'P5 - Trivial Priority' in title:
                #     title = title.replace('P5 - Trivial Priority', 'P5')
                url = "https://api.smartsheet.com/2.0/sheets/" + str(smartSheetId) + "/columns/" + str(column['id'])
                headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
                json = {"title":title}
                r = requests.put(url, headers=headers, json=json)
                if r.status_code != 200:
                    print("error: ", r.status_code, r.content)
                else:
                    print("column name updated from ", oldTitle, "to: " , title)






UpdateColumns()

def CreateNewColumn():
    count = 0
    # This function creates a new column for each sheet
    for smartSheetId in smartSheetIdList:
        count +=1
        print("smartSheetid:", smartSheetId)
        url = "https://api.smartsheet.com/2.0/sheets/" + str(smartSheetId) + "/columns"
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        json = [{"title": "Open Bugs: Total Number","type": "TEXT_NUMBER","index": 1,"width": 92}]
        r = requests.post(url, headers=headers, json=json)
        if r.status_code != 200:
            print("error: ", r.status_code, r.content)
        else:
            print("success", count)

#CreateNewColumn()