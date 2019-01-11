import re
import requests
import sys
from time import sleep

# to be used in terminal:
testRailPassword = sys.argv[1]
jenkinsAuthString = 'Bearer ' + sys.argv[2]
testRailEmail = sys.argv[3]

# it is essential that a new test rail group / suite id is created & the app id from buddy build obtained:
testRailGroupId = 69736
testRailProjectId = 21
testRailSuiteId = 2617
testRunId = 0
jenkinsJobName = 'build-alterra-proxy-service-master'

# the below call to jenkins gets the last successful build number, the test summary details
url = 'https://ci.te2.biz/jenkins/job/' + jenkinsJobName + '/lastSuccessfulBuild/api/json'
headers = {'Authorization': jenkinsAuthString}
r = requests.get(url, headers=headers)
print(url)
print(headers)
if r.status_code != 200:
    print("Error: The request to get the last Jenkins build was not successful. The response code was: ", r.status_code)
    print("The Response content was: ", r.content)
    exit()
else:
    buildNumber = r.json()['id']
    lastSuccessfulBuildUrl = r.json()['url'] + 'testReport/api/json'
    testsCount = r.json()['actions'][6]['totalCount']
    testsPassed = r.json()['actions'][6]['totalCount'] - r.json()['actions'][6]['failCount']
    print("Alterra Proxy Service Master Build Number %s is returning %i unit tests with %i tests that have passed." % (buildNumber, testsCount, testsPassed))
    print("This program will now create test cases from this Alterra branch build in TestRail.")

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

def DeleteTestRun():
    # This Function finds test runs for a project and suite id, then deletes them
    url = 'https://te2qa.testrail.net/index.php?/api/v2/get_runs/' + str(testRailProjectId) + '&suite_id=' + str(testRailSuiteId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, auth=(testRailEmail, testRailPassword))
    if r.json() == []:
        print("No Test Runs to delete")
    else:
        for testRunDetails in r.json():
            testRunSuiteNumber = testRunDetails['suite_id']
            if testRunSuiteNumber == testRailSuiteId:
                testRunId = testRunDetails['id']
                url = 'https://te2qa.testrail.net/index.php?/api/v2/delete_run/' + str(testRunId)
                headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
                r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword))
                print ("Test run: ", testRunId, " was successfully deleted.")

def CreateTestRun():
    # This function creates a test run in Test Rail
    url = 'https://te2qa.testrail.net/index.php?/api/v2/add_run/%i' % (testRailProjectId)
    headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
    json = {"suite_id": testRailSuiteId,"name": "Alterra Unit Test Automation Test Suite Run","assignedto_id": 55}
    r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword), json=json)
    status_code = r.status_code
    if status_code != 200:
        print("Error: The Test Run was not created. The response code was: ", r.status_code)
        print("The Response content was: ", r.content)
    else:
        testRunId = r.json()['id']
        return testRunId

def CreateTestCasesFromLogFile():
    # This function parses a buddybuild log file and lists each test category, test name & test result
    # It then populated a TestRail Group ID with these as test cases
    # It adds the results to the newly created test run
    # It then returns a formatted list of all the created test case numbers
    global testRunId # makes the created test run number available to all functions
    testRunId = CreateTestRun() # creates the test run
    status_id = 0
    print("Test Run:", testRunId, "was created with a 200 API Response from TestRail")

    # the below call to jenkins gets the test results
    headers = {'Cache-Control': 'no-cache', 'Authorization': jenkinsAuthString}
    r = requests.get(lastSuccessfulBuildUrl, headers=headers)
    suites = r.json()['childReports'][0]['result']['suites']
    testCount = 0
    for suite in suites: # runs through each suite listed
        suiteName = suite['cases'][0]['className']
        suiteName = re.sub(r"(?<=\w)([A-Z])", r" \1", suiteName)  # puts a space in front of a capitol letter
        suiteName = (suiteName[31:]).replace('.', ' ').capitalize()
        # this removes the 'biz.te2.services.alterra.proxy.' part of the string, makes spaces
        tests = suite['cases'] # runs through each test in each suite
        for test in tests:
            testCount += 1
            testName = test['name']
            testName = re.sub(r"(?<=\w)([A-Z])", r" \1", testName) # puts a space in front of a capitol letter
            testName = testName.capitalize()
            if test['status'] == "PASSED":
                status_id = 1
            if test['status'] == "FAILED":
                status_id = 5
            if test['status'] == "SKIPPED":
                status_id = 4
            # the below call to testrail creates each case
            url = 'https://te2qa.testrail.net/index.php?/api/v2/add_case/%i=' % (testRailGroupId)
            headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}
            title = "Unit Test Suite Name: %s & Unit Test Name: %s" % (suiteName, testName)
            if len(title) >=250:
                title = "Test Name: %s" % (testName)
                if len(title) >= 250:
                    title = title[:249]

            json = {'title': title,
                       'template_id': 1,
                       'type_id': 1,
                       'priority_id': 2,
                       'refs': 'No JIRA Stories are referenced as this is an automated unit test from Alterra',
                       'custom_testmethod': 3,
                       'custom_test_status': 3,
                       'custom_automation_type': 0,
                       'custom_steps': """
    
                       For Alterra Build %s:
    
                       For the Test Suite: %s:
    
                       a Unit Test named: %s was run.
                       """ % (buildNumber, suiteName, testName),
                       'custom_expected': """
                       The Result of the Unit Test: %s
    
    
                       """ % (test['status']),
                       'custom_preconds': """
    
                       This test case was created from a unit test run in Alterra during the build process.
    
                       This is for build %s for Alterra.
    
                       This is test case number %i out of %i tests, with %i passing in total.
    
                       The name of the test suite is: %s.
    
                       The name of the unit test is: %s
    
                       """ % (buildNumber, testCount, testsCount, testsPassed, suiteName, testName)}

            r = requests.post(url, headers = headers, auth =(testRailEmail, testRailPassword), json = json)

            if r.json() == []:
                print("No Test Case Created")
            else:
                testCaseId = r.json()['id']
                url = 'https://te2qa.testrail.net/index.php?/api/v2/add_result_for_case/' + str(testRunId) + '/' + str(testCaseId)
                headers = {'Cache-Control': 'no-cache', 'Content-Type': 'application/json'}

                json = {'status_id': status_id,
                        'comment': """
                           The Result of the Unit Test: %s.
                           
                           For test case %i out of %i unit tests.
    
                           """ % (test['status'], testCount, testsCount),
                        "defects": "No Defects Will be Logged as this is an automated unit test result",
                        "version": "Alterra build number %s" % (buildNumber),
                        "user": 55
                        }
                r = requests.post(url, headers=headers, auth=(testRailEmail, testRailPassword), json=json)


            if r.status_code != 200:
                print("Error: The request was not successful. The response code was: " , r.status_code)
                print("The Response content was: ", r.content)
                break
            else:
                print ("Test case", testCaseId, "was successfully added. It's result:", test['status'], "was added to test run:", testRunId, "Total Cases Created:", testCount)
                sleep(2)
    print("Build Number %s's %i unit tests have now been added to TesrRail with %i passing tests." % (buildNumber, testsCount, testsPassed))
    print("This program is now complete for this Alterra.")

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