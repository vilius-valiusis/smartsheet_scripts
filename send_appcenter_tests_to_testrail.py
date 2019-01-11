import re
import requests
import sys
from time import sleep

# to be used in terminal:
testRailPassword = sys.argv[1]
appCenterPassword = sys.argv[2]


# it is essential that a new test rail group / suite id is created & the app id from app center obtained:
testRailGroupId = 69634
testRailEmail = 'engineering@theexperienceengine.com'
testRailProjectId = 21
testRailSuiteId = 2581
latestSuccessfulBuild = 0

branch = 'develop'
# the below call to app center gets the last successful build number, - needs to be configured per app
url = 'https://api.appcenter.ms/v0.1/apps/te2org-qc1x/Alterra/branches/%s/builds' % (branch)
headers = {'Cache-Control': 'no-cache', 'X-API-Token': appCenterPassword}
r = requests.get(url, headers=headers)
if len(r.json()) == 0:
    print("There are no builds listed.")
for build in r.json():
    if build['result'] == 'succeeded':
        latestSuccessfulBuild = (build['id'])
        break

#buildNumber = r.json()[0]['build_number']
#testsCount = r.json()[0]['test_summary']['tests_count']

#branch =  r.json()[0]['commit_info']['branch']
#buddyBuildId = r.json()[0]['_id']
#print("Build Number %i is returning %i unit tests with %i tests that have passed." % (buildNumber, testsCount, testsPassed))
#print("This program will now create test cases from this ___ branch build, pointing to ___.")

def DeleteTestCasesInSuite():
    # This function parses the test cases from the last population and deletes them before adding the new ones
    url = 'https://te2qa.testrail.net/index.php?/api/v2/get_cases/' + str(testRailProjectId) + '&suite_id=' + str(testRailSuiteId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
    if r.json() == []:
        print("No Test Cases to delete")
    else:
        for testCaseDetails in r.json():
            testCaseId = testCaseDetails['id']
            url = 'https://te2qa.testrail.net/index.php?/api/v2/delete_case/' + str(testCaseId)
            headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword))
            print("Test case: ", testCaseId, " was successfully deleted.")
            sleep(1)
    if r.status_code != 200:
        print(r.status_code, r.content)

def DeleteTestRun():
    # This Function finds test runs for a project and suite id, then deletes them
    url = 'https://te2qa.testrail.net/index.php?/api/v2/get_runs/' + str(testRailProjectId) + '&suite_id=' + str(testRailSuiteId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
    if r.json() == []:
        print("No Test Runs to delete")
    else:
        for testRunDetails in r.json():
            testRunId = testRunDetails['id']
            url = 'https://te2qa.testrail.net/index.php?/api/v2/delete_run/' + str(testRunId)
            headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
            r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword))
            print ("Test run: ", testRunId, " was successfully deleted.")

def CreateTestRun():
    # This function creates a test run in Test Rail
    url = 'https://te2qa.testrail.net/index.php?/api/v2/add_run/%i' % (testRailProjectId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    json = {"suite_id": testRailSuiteId,"name": "Android Unit Test Automation Test Suite Run","assignedto_id": 55}
    r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword), json=json)
    status_code = r.status_code
    if status_code != 200:
        print("Error: The Test Run was not created. The response code was: ", r.status_code)
        print("The Response content was: ", r.content)
    else:
        testRunId = r.json()['id']
        return testRunId


def CreateTestCasesFromLogFile():
    # This function parses a app center log file and lists each test category, test name & test result
    # It then populated a TestRail Group ID with these as test cases
    # It adds the results to the newly created test run
    # It then returns a formatted list of all the created test case numbers
    global testRunId # makes the created test run number available to all functions
    testRunId = CreateTestRun() # creates the test run
    status_id = 0
    print("Test Run:", testRunId, "was created with a 200 API Response from TestRail")
    # the below call to testrail is used to get the test run id:
    #url = 'https://te2qa.testrail.net/index.php?/api/v2/get_runs/' + str(testRailProjectId) + '&suite_id=' + str(testRailSuiteId)
    #headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    #r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
    #if r.json() == []:
        #print("No Test Runs Found")
    #else:
        #for testRunDetails in r.json():
           # testRunId = int(testRunDetails['id'])

    # the below call to buddybuild gets the test results
    url = 'https://api.appcenter.ms/v0.1/apps/te2org-qc1x/Alterra/builds/' + str(latestSuccessfulBuild) + '/logs'
    headers = {'Cache-Control': 'no-cache', 'X-API-Token': appCenterPassword}
    r = requests.get(url, headers=headers)
    lines = r.json()['value']
    testsCount =0
    testsPassed = 0
    for line in lines:
        if 'mtnco.ikonpass.logic.' in line:
            line = line[57:] # removes part of the log line not needed
            suiteName, sep, testNameAndResult = line.partition('Test >') # separates out the suite name
            suiteName = suiteName.replace('.', ' ')
            suiteName = re.sub(r"(?<=\w)([A-Z])", r" \1", suiteName)  # puts a space in front of a capitol letter
            suiteName = re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), suiteName, 1) # makes the first word a cap
            testNameAndResult = testNameAndResult.replace(' test','')
            testNameAndResult = testNameAndResult.replace('  ',' ')
            if testNameAndResult[:1] == ' ':
                testNameAndResult = testNameAndResult[1:] # takes the space
            testResult = testNameAndResult[-6:] # defines the result as last 6 char in string
            testName = testNameAndResult[0:-7] # takes off the result
            testName = re.sub(r"(?<=\w)([A-Z])", r" \1", testName)  # puts a space in front of a capitol letter
            testName = testName.title() # makes the first letters caps
            testsCount += 1
            if testResult == "PASSED":
                status_id = 1
                testsPassed += 1
            if testResult == "FAILED":
                status_id = 5

            # the below call to testrail creates each case
            url = 'https://te2qa.testrail.net/index.php?/api/v2/add_case/%i=' % (testRailGroupId)
            headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
            title = "Unit Test Suite Name: %s & Unit Test Name: %s" % (suiteName, testName)
            if len(title) >=250:
                title = "Test Name: %s" % (testName)
                if len(title) >= 250:
                    title = title[:249] # limits length of title

            json = {'title': title,
                       'template_id': 1,
                       'type_id': 1,
                       'priority_id': 2,
                       'refs': 'No JIRA Stories are referenced as this is an automated unit test from ios',
                       'custom_testmethod': 3,
                       'custom_test_status': 3,
                       'custom_automation_type': 0,
                       'custom_steps': """
                       
                       For Android Build %i:
    
                       For the Test Suite: %s:
    
                       a Unit Test named: %s was run.
                       """ % (latestSuccessfulBuild, suiteName, testName),
                       'custom_expected': """
                       The Result of the Unit Test: %s
                       
                       
                       """ % (testResult),
                       'custom_ios_options': 6,
                       'custom_preconds': """
                       
                       This test case was created from a unit test run in Android during the build process.
                        
                       This is for build %i on the %s branch for Alterra.
                                                               
                       This test was test number %i, with %i passing so far in the run.
                                                                   
                       The name of the test suite is: %s.
                       
                       The name of the unit test is: %s
                       
                       """ % (latestSuccessfulBuild, branch, testsCount, testsPassed, suiteName, testName)}

            r = requests.post(url, headers = headers, auth =(testRailEmail, testRailPassword), json = json)

            if r.json() == []:
                print("No Test Case Created")
            else:
                testCaseId = r.json()['id']
                url = 'https://te2qa.testrail.net/index.php?/api/v2/add_result_for_case/' + str(testRunId) + '/' + str(testCaseId)
                headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}

                json = {'status_id': status_id,
                        'comment': """
                           The Result of the Unit Test: %s
    
                           """ % (testResult),
                        "defects": "No Defects Will be Logged as this is an automated unit test result",
                        "version": "Alterra Android build number %i" % (latestSuccessfulBuild),
                        "user": 55
                        }
                r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword), json=json)


            if r.status_code != 200:
                print("Error: The request was not successful. The response code was: " , r.status_code)

                break
            else:
                print ("Test case", testCaseId, "was successfully added. It's result:", testResult, "was added to test run:", testRunId, "Total Cases Created:", testsCount)
                sleep(1)
    print("Android build Number %i's %i unit tests have now been added to TesrRail with %i passing tests." % (latestSuccessfulBuild, testsCount, testsPassed))
    print("This program is now complete for the Alterra branch build, pointing to QA.")

def CloseTestRun():
    # This Function closes out the test run just created
    url = 'https://te2qa.testrail.net/index.php?/api/v2/close_run/' + str(testRunId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword))
    print ("Test run: ", testRunId, " was successfully closed.")

DeleteTestCasesInSuite()
DeleteTestRun()
CreateTestCasesFromLogFile()
CloseTestRun()



#CreateTestRun() - not sure if I need this !