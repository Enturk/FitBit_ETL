import pandas as pd
import os
import csv
import time
import datetime
import logging

Verbose = True
format_file = "REDCap Column Format.csv"
existing_file = "Existing_data.csv"
existing_time_format = "%m/%d/%Y, %H:%M:%S %p"
# TODO add expected existing columns
daily_file = "dailyIntensities_merged.csv"
expected_daily_columns = ['Id',
                          'ActivityDay',
                          'SedentaryMinutes',
                          'LightlyActiveMinutes',
                          'FairlyActiveMinutes',
                          'VeryActiveMinutes',
                          'SedentaryActiveDistance',
                          'LightActiveDistance',
                          'ModeratelyActiveDistance',
                          'VeryActiveDistance']
daily_time_format = existing_time_format
hourly_file = "hourlySteps_merged.csv"
expected_hourly_columns = ['Id','ActivityHour','StepTotal']
hourly_time_format = existing_time_format
# TODO add expected hourly columns
week_start = 'valid_wk_01'
second_week = 'valid_wk_02'

ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

def validate(date_text, context, time_format = '%m/%d/%Y'):
    # validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
    try:
        datetime.datetime.strptime(date_text, time_format)
    except ValueError:
        raise ValueError(f"Incorrect data format, should be {time_format}")
        logging.error(f"Incorrect data format, should be {time_format}", exc_info=True)
        logging.error(context)
        return -1
    return datetime.datetime.strptime(date_text, time_format)

def difference_days(earlydate, latedate):
    earlydate = validate(earlydate, 'Calculating difference in days between {earlydate} and {latedate}')
    latedate = validate(latedate, 'Calculating difference in days between {earlydate} and {latedate}')
    delta = latedate - earlydate
    return delta.days

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
        
    def sort_weeks(self):
        max_week_num = 0
        # TODO sort by event type
        week_numbers = {}
        for week in self.weeks:
            if week.number > max_week_num:
                max_week_num = week.number
            week_numbers[week.number] = week
        week_numbers = sorted(week_numbers)
        self.weeks = []
        
        for i in range(max_week_num):
            if i in week_numbers:
                self.weeks.append(week_numbers[i])
            else:
                self.weeks.append(-1) # missing week
        
    def get_week_by_number(self, event, number):
        if len(self.weeks) == 0:
            logging.info(f'Subject {self.name} has no weeks, so the week requested ({number}) cannot be provided.')
            return -1
        for weekly in self.weeks:
            if weekly.event == event and weekly.number == number:
                return weekly
        else:
            logging.info(f'Subject {self.name} has no week numbered {number}.')
            return -1

    def get_week_by_date(self, date):
        date = validate(date)
        if len(self.weeks) == 0:
            logging.info(f'Subject {self.name} has no weeks, so none can be provided for the date requested.')
            return -1
        for week in self.weeks:
            delta = difference_days(week.date, date)
            if delta >= 0 and delta < 7:
                return week
        logging.info(f'Subject {self.name} has no week that contains the date {date}. The last week examined started on {prior_week.date}.')
        return -1
        
class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files
    def __init__(self, date, number, event, valid, days, steps, low, moderate, high):
        self.date = date  # date it begins on
        self.number = number
        self.event = event # meaning baseline or 8_weeks_arm_1 etc.
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

# get existing data
subjects = []
subject_names = {}
current_data = CSVtolist(existing_file)
logging.debug(current_data[:3])
first_row = True
current_columns = []
col = 0
starting_col = 8
weekly_cols = 6
for row in current_data:
    # check columns:
    if first_row:
        first_row = False
        for column in row:
            current_columns.append(column)

        # TODO validate columns
##        if current_columns ! = expected_daily_columns
##            logging.error('Columns in file are {hourly_columns}, and different from those expected, which are {expected_hourly_columns}')
##            break # TODO adapt to new columns
        
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
        subjects.append(subject)
    event = get_event(row[1])
    if event == -1:
        logging.error(f'Skipping row because it contains improper event: {row[1]}')
        continue
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

for subject in subjects:
    subject.sort_weeks()

#get daily data
logging.debug(f'Starting with new daily data. We have {len(subjects)} subjects from existing data.')
daily_data = CSVtolist(daily_file)
first_row = True
daily_columns = []
subject = subjects[0]
date = subject.start_date
for row in daily_data:
    # check columns:
    if first_row:
        first_row = False
        for column in row:
            daily_columns.append(column)
        if daily_columns != expected_daily_columns:
            logging.critical('Columns in file are {hourly_columns}, and different from those expected, which are {expected_hourly_columns}')
            break # TODO adapt to new columns
        continue
    
    logging.debug(f'Daily row is {row}')
    name = int(row[0][3:]) # Removes 'ATX' from name
    if name != subject.name:
        if name in subject_names:
            subject = subject_names[name]
        else:
            logging.error(f'New subject {name} not in subject dictionary.')
            continue
            # FIXME add new subject
            # Do this next!

    date = validate(row[1], 'Checking row in daily data:' + str(row))
    if date == -1:
        logging.error(f'Moving on to next row because of bad date')
        continue
    SedentaryMinutes = int(row[2])
    LightlyActiveMinutes = int(row[3])
    FairlyActiveMinutes = int(row[4])
    VeryActiveMinutes = int(row[5])
    SedentaryActiveDistance = int(row[6])
    LightActiveDistance = float(row[7])
    ModeratelyActiveDistance = float(row[8])
    VeryActiveDistance = float(row[9])

    day = Day(date, SedentaryMinutes,LightlyActiveMinutes,FairlyActiveMinutes,VeryActiveMinutes,SedentaryActiveDistance,LightActiveDistance,ModeratelyActiveDistance,VeryActiveDistance)
    week = get_week_by_date(date)
    week.days.append(day)
    
# get hourly data
hourly_data = CSVtolist(hourly_file)
first_row = True
hourly_columns = []
subject = subjects[0]
date = subject.start_date
for row in hourly_data:
    # check columns:
    if first_row:
        first_row = False
        for column in row:
            hourly_columns.append(column)
        if hourly_columns != expected_hourly_columns:
            logging.error('Columns in file are {hourly_columns}, and different from those expected, which are {expected_hourly_columns}')
        continue

    # identify if new subject
    name = row[0]
    if name != subject.name:
        if name in subject_names:
            subject = subject_names[name]
        else:
            logging.error(f'New subject {name} not in subject dictionary.')
            # FIXME add new subject

    date_time = validate(row[1], f'Checking row in hourly data: {row}', hourly_time_format)
    steps = row[2]

    # identify if new day
    # day = subject.weeks[-1].days[-1].ActivityDay #FIXME
    # if day != datetime.datetime.st
        
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
