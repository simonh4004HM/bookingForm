import unittest
import pdb
import time
from modules.logger import GoogleLog

# run from shell using python -m unittest test/testLogger.py
print("running testLogger.py")

testCase = 0; testPass = 0; testCaseNumber = 0;

testCaseExecute = [
  True, 	# 0:  create instance of class
  True, 	# 1:  add log entry - named sheet and tab
  True, 	# 2:  add log entry - default sheet and tab name 
  True, 	# 3:  
  False, 	# 4:  
  False, 	# 5:  
  False, 	# 6:  
  True, 	# 7:  
  ]    

# This test replies on the logs sheet being available to write to.

# googleLogTest = GoogleLog(sheetName="logs", tabName="test")
#googleLogTest.log("unit test entry for test", sheetName="logs", tabName="test")
#googleLogTest.log("test entry (test1) explict name sheet and tab", sheetName="logs", tabName="test")

# 0:  create instance of class
if testCaseExecute[testCaseNumber] :
  # testCase += 1; localTestPass = 0; res = "fail"

  global googleLogTest
  googleLogTest = GoogleLog(sheetName="logs", tabName="test")
  #if True:
  #  localTestPass += 1; res = "pass"; testPass += 1
  print(f"Test {testCaseNumber}: create instance of class (not checked) \n")

# 1: add log entry
testCaseNumber += 1
if testCaseExecute[testCaseNumber] :
  testCase += 1; localTestPass = 0; res = "fail"

  googleLogTest.log("test entry (test1) explict name sheet and tab", sheetName="logs", tabName="test")
  allRows = googleLogTest.getAllRows()
  lastRow = allRows.pop()['LogEntry'];  # print(f"lastRow:{lastRow}:")
  if lastRow == "test entry (test1) explict name sheet and tab":
    res = "pass"; localTestPass += 1;
  print(f"Test {testCaseNumber}: create instance of class ==> {res} \n")

  if localTestPass == 1: testPass += 1;

# 2: add log entry - default sheet and tab name
testCaseNumber += 1
if testCaseExecute[testCaseNumber] :
  testCase += 1; localTestPass = 0; res = "fail"

  # breakpoint()
  googleLogTest.log("add log entry - default sheet and tab name")
  allRows = googleLogTest.getAllRows()
  lastRow = allRows.pop()['LogEntry'];  # print(f"lastRow:{lastRow}:")
  
  if lastRow == "add log entry - default sheet and tab name":
    res = "pass"; localTestPass += 1; 
  print(f"Test {testCaseNumber}: add log entry - default sheet and tab name lastEntry ==> {res} \n")
  if localTestPass == 1: testPass += 1;

print(f"\nTest: Exit testGoogleAccess.py run:{testCase}, passes:{testPass}")


if __name__ == '__main__':
  unittest.main()