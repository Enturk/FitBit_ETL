import csv
import time

ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

class Subject_Record:
    def __init__(self, name, date, multiple_devices):
        self.name = name
        self.date = date
        self.multiple_devices = multiple_devices
        self.baseline_weeks = [] # list of Week instances
        #TODO implement other arm week lists

    def get_week(self, date):
        # TODO return week given date
        return -1

class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files