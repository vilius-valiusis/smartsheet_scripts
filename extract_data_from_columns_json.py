import requests

#smartSheetIdList = [8146483112372100, 6563023696488324, 4838533660731268, 1572782262773636, 1507223881967492, 2809732844021636] # input here
smartSheetPassword = #need to insert passwords
smartSheetIdList = [6633203462104964]

def Columns():
    #This function gets the sheet columns data for a list of sheets

    for smartSheetId in smartSheetIdList:
        listOfColumnIds = []
        listOfColumnTitles = []
        #print("smartSheetid:", smartSheetId)
        url = "https://api.smartsheet.com/2.0/sheets/" + str(smartSheetId) + "/columns"
        headers = {'Cache-Control': 'no-cache', 'Authorization': 'Bearer ' + smartSheetPassword}
        r = requests.get(url, headers=headers)
        #print(r.json())
        if r.status_code != 200:
            print("error: ", r.status_code, r.content)
        else:
            data = r.json()['data']
            for column in data:
                id = column['id']
                if id not in listOfColumnIds:
                    listOfColumnIds.append(id)
                title = column['title']
                if title not in listOfColumnTitles:
                    listOfColumnTitles.append(title)
            print('SmartSheet Id: ', smartSheetId)
            print('listOfColumnIds =', listOfColumnIds)
            print('listOfColumnTitles = ', listOfColumnTitles)

Columns()

