import pandas as pd
import os
import csv
import time
import datetime
import logging

Verbose = True
format_file = "REDCap Column Format.csv"
existing_file = "Existing_data.csv"
daily_file = "dailyIntensities_merged.csv"
hourly_file = "hourlySteps_merged.csv"
week_start = 'valid_wk_01'
second_week = 'valid_wk_02'

ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

def validate(date_text, context):
    # validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
    try:
        datetime.datetime.strptime(date_text, '%m/%d/%Y')
    except ValueError:
        raise ValueError("Incorrect data format, should be MM/DD/YYYY")
        logging.error("Incorrect data format, should be MM/DD/YYYY", exc_info=True)
        logging.error(context)
        return -1
    return datetime.datetime.strptime(date_text, '%m/%d/%Y')

def difference_days(earlydate, latedate):
    earlydate = datetime.strptime(earlydate)
    latedate = datetime.strptime(latedate)
    delta = latedate - earlydate
    return delta.days

#these may be unnecessary:
def get_event(words):
    if words == 'baseline_arm_1':
        return 0
    elif words == '8_weeks_arm_1':
        return 1
    elif words == '16_weeks_arm_1':
        return 2
    elif words == '24_weeks_arm_1':
        return 3
    elif words == '32_weeks_arm_1':
        return 4
    elif words == '40_weeks_arm_1':
        return 5
    elif words == '48_weeks_arm_1':
        return 6
    else: return -1

def get_event_descr(words):
    if words == 0:
        return 'baseline_arm_1'
    elif words == 1:
        return '8_weeks_arm_1'
    elif words == 2:
        return '16_weeks_arm_1'
    elif words == 3:
        return '24_weeks_arm_1'
    elif words == 4:
        return '32_weeks_arm_1'
    elif words == 5:
        return '40_weeks_arm_1'
    elif words == 6:
        return '48_weeks_arm_1'
    else: return -1

# data containers:
class Subject_Record:
    def __init__(self, name, date, multiple_devices):
        self.name = name
        # The start date for each subject is the "date" field from the "Clinical Exam" instrument + 1 day.
        self.start_date = date
        self.end_date = date + datetime.timedelta(days = 363)
        self.multiple_devices = multiple_devices
        self.weeks = [] # list of Week instances
        
    def get_week_by_number(self, event, number):
        for weekly in self.weeks:
            if weekly.event == event and weekly.number == number:
                return weekly
        else:
            return -1
    def get_week_by_date(self, date):
        #FIXME
        
class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files
    def __init__(self, date, number, event, valid, days, steps, low, moderate, high):
        self.date = date  # date it begins on
        self.number = number
        self.event = event # i.e. baseline, or '8_weeks_arm_1' etc.
        self.days = [] # list of Day instances
        self.valid = valid
        self.days = days
        self.avg_daily_steps = steps
        self.avg_low_intensity = low
        self.avg_moderate_intensity = moderate
        self.avg_high_intensity = high

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

script_dir = os.getcwd()
def CSVtolist(filename):
    # if output has ï»¿ at the start of the first entry, format is UTF-8-BOM
    # see this: https://stackoverflow.com/questions/24568056/rs-read-csv-prepending-1st-column-name-with-junk-text
    if os.path.exists(os.path.join(script_dir, filename)):
        input_file = os.path.join(script_dir, filename)
        logging.debug(f'Current input file is {input_file}')
    else:
        logging.critical(f'Fatal Error: file not found: {filename}')
        exit()
    with open(filename, 'r') as csvfile:
        return_list = list(csv.reader(csvfile))
        isBOM = 0
        if type(return_list[0]) != list:
            if return_list[0][:3] == 'ï»¿':
                isBOM = 1
        elif type(return_list[0][0]) != list:
            if return_list[0][0][:3] == 'ï»¿':
                isBOM = 2
        else:
            isBOM = 3
    if isBOM > 0:
        logging.debug(f'CSV file is in UTF-8-BOM format. Fixing...')
        if isBOM == 1:
            return_list[0] = return_list[0][3:]
        elif isBOM == 2:
            return_list[0][0] = return_list[0][0][3:]
        else:
            logging.debug('List may have more than two dimensions, or something else is the matter:')
            logging.debug(return_list[0])
    return return_list

if Verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(filename='fitbit_pipe.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


subjects = []
subject_names = {}
# get existing data
current_data = CSVtolist(existing_file)
logging.debug(current_data[:3])

first_row = True
current_columns = []
col = 0
starting_col = 8
weekly_cols = 6
for row in current_data:

    # store the columns to check them later:
    if first_row:
        first_row = False
        for column in row:
            current_columns.append(column)
        
        # check weekly starting place
        for column in current_columns:
            if column == week_start:
                starting_col = col
                break
            else:
                col += 1

        # check number of columns in each week:
        i = 0
        for column in current_columns:
            if column == second_week:
                delta = i - starting_col
                if delta != weekly_cols:
                    logging.error(f'Number of columns per week is {delta} and not {weekly_cols}, as specified. Using the former instead.')
                    logging.debug(f'This was calculated by looking for the {week_start} column first, and then {second_week} column second.')
                    weekly_cols = delta
                break
            else:
                i += 1
                
        logging.debug(f'Found weekly fields starting on column {starting_col}, which is {row[starting_col]}. Looked for {week_start} until column {col}.')
        if starting_col == 0:
            break
        continue

    # identify if new or not
    if row[0] in subject_names:
        this_subject = subject_names[row[0]]
        subject = this_subject
        
    else:
        date = row[5][:-5]
        if date == '':
            continue
        logging.debug(f'The date is {date}')
        date = validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
        new_subject = Subject_Record(row[0], date, row[7])
        subject_names[row[0]] = new_subject
        subject = new_subject
    event = get_event(row[1])
    col = starting_col
    start_date = subject.start_date
    week_num = 0
    while (col < len(current_columns)) and (week_num < 52): # CHECK that last week is included
        date = start_date + datetime.timedelta(days = 7*week_num)
        number = week_num +1
        valid = row[col]
        if valid == '':
            break
        days = row[col +1]
        steps = row[col +2]
        low = row[col +3]
        moderate = row[col +4]
        high = row[col +5]
        new_week = Week(date, number, event, valid, days, steps, low, moderate, high)
        subject.weeks.append(new_week)
        week_num += 1
        col += weekly_cols

    logging.debug(f'Last processed column was {col} and we got to week {week_num}')

    if len(subject.weeks) > 0:
        logging.debug(f"First and last week of subject {subject.name}'s weekly records (event, week number, start date, validity, valid days, number of steps, and low, moderate and high intensity):")
        week = subject.weeks[0]
        logging.debug(f'{week.event}\t{week.number}\t{week.date}\t{week.valid}\t{week.days}\t{week.avg_daily_steps}\t{week.avg_low_intensity}\t{week.avg_moderate_intensity}\t{week.avg_high_intensity}')
        week = subject.weeks[-1]
        logging.debug(f'{week.event}\t{week.number}\t{week.date}\t{week.valid}\t{week.days}\t{week.avg_daily_steps}\t{week.avg_low_intensity}\t{week.avg_moderate_intensity}\t{week.avg_high_intensity}')
    else:
        logging.debug(f'This row for subject {subject.name} has no weekly data: {subject.weeks}')
        
# get daily data
hourly_data = CSVtolist(hourly_file)
first_row = True
expected_hourly_columns = ['Id','ActivityHour','StepTotal']
hourly_columns = []
subject = subjects[0]
date = subject.start_date
for row in hourly_data:
    # store the columns to check them later:
    if first_row:
        first_row = False
        for column in row:
            hourly_columns.append(column)

        # check data
        if hourly_columns ! = expected_hourly_columns
            logging.error('Columns in file are {hourly_columns}, and different from those expected, which are {expected_hourly_columns}')
                
        continue

    # identify if new or not
    if row[0] != subject.name:
        if row[0] in subject_names:
            subject = subject_names[row[0]]
        else:
            logging.error(f'New subject {row[0]} not in subject dictionary.'
    
    
# get hourly data
# transform it
# output csv for REDCap upload
columns = CSVtolist(format_file) # get from format file

# logging.debug("Columns are:")
# logging.debug(columns[:3])

df = pd.DataFrame(columns)
i=0
for subject in subjects:
    row = []
    for column in columns:
        row.append(0) # FIXME
    df.loc[i] = row
    i+=1
# save as 'FitBitData_Converted_' + timestamp
