#!/usr/bin/env python
from xpdeint.XSILFile import XSILFile

def firstElementOrNone(enumerable):
  for element in enumerable:
    return element
  return None

def writeToFile(filename, steps, err_y):
   f = open(filename, 'w')

   for i in range(len(steps)):
      f.write(("%1.1f" % steps[i]) + "," + ("%.12e" % err_y[i]) + "\n")

   f.close() 

xsilFile_2ndOrder = XSILFile("exponential_scaling_2ndOrder_expected.xsil")
xsilFile_4thOrder = XSILFile("exponential_scaling_4thOrder_expected.xsil")
xsilFile_6thOrder = XSILFile("exponential_scaling_6thOrder_expected.xsil")
xsilFile_8thOrder = XSILFile("exponential_scaling_8thOrder_expected.xsil")
xsilFile_10thOrder = XSILFile("exponential_scaling_10thOrder_expected.xsil")

steps_2ndOrder = firstElementOrNone(_["array"] for _ in xsilFile_2ndOrder.xsilObjects[0].dependentVariables if _["name"] == "stepsR")
err_y_2ndOrder = firstElementOrNone(_["array"] for _ in xsilFile_2ndOrder.xsilObjects[0].dependentVariables if _["name"] == "err_yR")

steps_4thOrder = firstElementOrNone(_["array"] for _ in xsilFile_4thOrder.xsilObjects[0].dependentVariables if _["name"] == "stepsR")
err_y_4thOrder = firstElementOrNone(_["array"] for _ in xsilFile_4thOrder.xsilObjects[0].dependentVariables if _["name"] == "err_yR")

steps_6thOrder = firstElementOrNone(_["array"] for _ in xsilFile_6thOrder.xsilObjects[0].dependentVariables if _["name"] == "stepsR")
err_y_6thOrder = firstElementOrNone(_["array"] for _ in xsilFile_6thOrder.xsilObjects[0].dependentVariables if _["name"] == "err_yR")

steps_8thOrder = firstElementOrNone(_["array"] for _ in xsilFile_8thOrder.xsilObjects[0].dependentVariables if _["name"] == "stepsR")
err_y_8thOrder = firstElementOrNone(_["array"] for _ in xsilFile_8thOrder.xsilObjects[0].dependentVariables if _["name"] == "err_yR")

steps_10thOrder = firstElementOrNone(_["array"] for _ in xsilFile_10thOrder.xsilObjects[0].dependentVariables if _["name"] == "stepsR")
err_y_10thOrder = firstElementOrNone(_["array"] for _ in xsilFile_10thOrder.xsilObjects[0].dependentVariables if _["name"] == "err_yR")

writeToFile("exponential_scaling_2ndOrder.csv", steps_2ndOrder, err_y_2ndOrder)
writeToFile("exponential_scaling_4thOrder.csv", steps_4thOrder, err_y_4thOrder)
writeToFile("exponential_scaling_6thOrder.csv", steps_6thOrder, err_y_6thOrder)
writeToFile("exponential_scaling_8thOrder.csv", steps_8thOrder, err_y_8thOrder)
writeToFile("exponential_scaling_10thOrder.csv", steps_10thOrder, err_y_10thOrder)

from subprocess import call

call(["gnuplot", "logplotall.gp"])
