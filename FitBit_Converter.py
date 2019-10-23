import pandas as pd
import os
import csv
import time
import datetime

ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

def validate(date_text, context):
    try:
        datetime.datetime.strptime(date_text, '%m/%d/%Y')
    except ValueError:
        raise ValueError("Incorrect data format, should be MM/DD/YYYY")
        print(context)
        exit()

def difference_days(earlydate, latedate):
    earlydate = datetime.strptime(earlydate)
    latedate = datetime.strptime(latedate)
    delta = latedate - earlydate
    return delta.days

# data containers:
class Subject_Record:
    def __init__(self, name, date, multiple_devices):
        self.name = name
        # The start date for each subject is the "date" field from the "Clinical Exam" instrument + 1 day.
        self.start_date = datetime.strptime(date)
        self.end_date = datetime.striptime(date) + datetime.timedelta(days = 363)
        self.multiple_devices = multiple_devices
        self.baseline_weeks = [] # list of Week instances
        #TODO implement other arm week lists

    def get_week_number(self, date):
        # TODO return week given date
        # date = date + relativedelta(weeks=+1)
        validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
        if date >= self.date:
            difference = int(difference_days(self.date, date))
        else:
            print(f'Error: date')
            return -1

class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files
    def __init__(self, date):
        self.date = date  # date it begins on
        self.days = [] # list of Day instances

class Day:
    # SedentaryMinutes	LightlyActiveMinutes	FairlyActiveMinutes	VeryActiveMinutes	SedentaryActiveDistance	LightActiveDistance	ModeratelyActiveDistance	VeryActiveDistance
    def __init__(self, date, SedentaryMinutes,LightlyActiveMinutes,FairlyActiveMinutes,VeryActiveMinutes,SedentaryActiveDistance,LightActiveDistance,ModeratelyActiveDistance,VeryActiveDistance):
        self.ActivityDay = date
        self.SedentaryMinutes = SedentaryMinutes
        self.LightlyActiveMinutes = LightlyActiveMinutes
        self.FairlyActiveMinutes = FairlyActiveMinutes
        self.VeryActiveMinutes = VeryActiveMinutes
        self.SedentaryActiveDistance = SedentaryActiveDistance
        self.LightActiveDistanceself = LightActiveDistanceself
        self.ModeratelyActiveDistance = ModeratelyActiveDistance
        self.VeryActiveDistance = VeryActiveDistance
        self.hours = [] # list of Hour instances

class Hour:
    def __init__(self, date_time, StepTotal):
        self.ActivityHour = date_time
        self.StepTotal = StepTotal


Verbose = True
format_data = "REDCap Column Format.csv"
existing_data = ""
daily_data = "dailyIntensities_merged.csv"
hourly_data = "hourlySteps_merged.csv"
script_dir = os.getcwd()
def CSVtolist(filename):
    if os.path.exists(os.path.join(script_dir, filename)):
        input_file = os.path.join(script_dir, filename)
        if Verbose:
            print(f'Current input file is {input_file}')
    else:
        print(f'Fatal Error: file not found: {filename}')
        exit()
    with open(filename, 'r') as csvfile:
        return list(csv.reader(csvfile))

subjects = []
# get existing data
# get daily data
# get hourly data
# transform it
# output csv for REDCap upload
columns = CSVtolist(format_data) # get from format file
if Verbose:
    print("Columns are:")
    print(columns)
df = pd.DataFrame(columns)
i=0
for subject in subjects:
    row = []
    for column in columns:
        row.append(0) # FIXME
    df.loc[i] = row
    i+=1
