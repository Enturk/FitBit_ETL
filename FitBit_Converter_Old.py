import pandas as pd
import os
import csv
import time
import datetime
import logging

Verbose = True
format_file = "REDCap Column Format.csv"
existing_file = "Existing_data.csv"
existing_time_format = '%m/%d/%Y %H:%M'
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
daily_time_format = '%m/%d/%Y %H:%M:%S %p'
hourly_file = "hourlySteps_merged.csv"
expected_hourly_columns = ['Id','ActivityHour','StepTotal']
hourly_time_format = daily_time_format
# TODO add expected hourly columns
week_start = 'valid_wk_01'
second_week = 'valid_wk_02'

ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

def validate(date_text, context, time_format = '%m/%d/%Y'):
    # validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
    if type(date_text) == datetime.datetime:
        return(date_text)
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
def get_event_descr(number):
    if number == 0:
        return 'baseline_arm_1'
    elif number == 1:
        return '8_weeks_arm_1'
    elif number == 2:
        return '16_weeks_arm_1'
    elif number == 3:
        return '24_weeks_arm_1'
    elif number == 4:
        return '32_weeks_arm_1'
    elif number == 5:
        return '40_weeks_arm_1'
    elif number == 6:
        return '48_weeks_arm_1'
    else: return -1

# data containers:
class Subject_Record:
    def __init__(self, name, date, multiple_devices):
        self.name = name
        # The start date for each subject is the "date" field from the "Clinical Exam" instrument + 1 day.
        self.start_date = validate(date, f"Creation of new subject {self.name}"
        self.end_date = self.start_date + datetime.timedelta(days = 363)
        self.multiple_devices = multiple_devices
        self.weeks = [] # list of Week instances
        for i in range(52):
            new_date = 
            self.add_week(

    def add_week(self, date, *kwargs):
        
    
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
            else: # add missing week
                if i == 0:
                    date = self.start_date
                    event = 0
                else:
                    date = self.weeks[-1].date + timedelta(days=7)
                    event = 0 #self.weeks[-1].event # FIXME this needs to be reviewed when adding new events
                new_week = Week(date, i, event, 0, 0, 0.0, 0.0, 0.0, 0.0)
                self.weeks.append(new_week) 
        
    def get_week_by_number(self, event, number):
        if number < 0 or number > 51:
            logging.error(f"Weeks are numbered between 0 and 51, and {number} isn't in that range.")
            return -1
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
        date = validate(date, f'Was trying to get week with date for subject {self.name}')
        if len(self.weeks) == 0:
            logging.info(f'Subject {self.name} has no weeks, so none can be provided for the date requested.')
            return -1
        for week in self.weeks:
            # logging.debug(f'Looking for week in subject {self.name}. Currently on week {week}, for {date}')
            delta = int(difference_days(week.date, date))
            if delta >= 0 and delta < 7:
                return week
        logging.info(f'Subject {self.name} has no week that contains the date {date}.')
        self.sort_weeks()
        return get_week_by_date(self, date)
        
class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files
    def __init__(self, date, number, event, valid, days, steps, low, moderate, high):
        self.date = validate(date, f'Creating new week with {date}', '%m/%d/%Y')# date it begins on
        self.number = number
        self.event = event # meaning baseline or 8_weeks_arm_1 etc.
        self.days = [] # list of Day instances
        self.valid = valid
        self.days = days
        self.avg_daily_steps = steps
        self.avg_low_intensity = low
        self.avg_moderate_intensity = moderate
        self.avg_high_intensity = high

    def get_day_by_date(self, date):
        date = validate(date, f'Was trying to get day of week with date for week starting on {self.date}')
        if len(self.days) == 0:
            return -1
        for day in self.days:
            logging.debug(f'Trying to get a day by date in week {self.number}, starting on {self.date}, is looking at day {day}, which is type {type(day)}')
            if date == day.ActivityDay:
                return day
        return -1

class Activity_Day:
    # SedentaryMinutes	LightlyActiveMinutes	FairlyActiveMinutes	VeryActiveMinutes	SedentaryActiveDistance	LightActiveDistance	ModeratelyActiveDistance	VeryActiveDistance
    def __init__(self, date, SedentaryMinutes,LightlyActiveMinutes,FairlyActiveMinutes,VeryActiveMinutes,SedentaryActiveDistance,LightActiveDistance,ModeratelyActiveDistance,VeryActiveDistance):
        self.ActivityDay = validate(date, f'Creating new day dated {date}', daily_time_format)
        self.SedentaryMinutes = SedentaryMinutes
        self.LightlyActiveMinutes = LightlyActiveMinutes
        self.FairlyActiveMinutes = FairlyActiveMinutes
        self.VeryActiveMinutes = VeryActiveMinutes
        self.SedentaryActiveDistance = SedentaryActiveDistance
        self.LightActiveDistanceself = LightActiveDistance
        self.ModeratelyActiveDistance = ModeratelyActiveDistance
        self.VeryActiveDistance = VeryActiveDistance
        self.hours = {} # dict of Hours

    def add_hour(self, date, steps):
        date = validate(date, 'Was trying to get hour for day {self.ActivityDay} from date.')
        this_hour = date.hour
        if this_hour in self.hours:
            logging.error(f'Day {self.ActivityDay} for this subject already has activity for hour {this_hour}')
            return -1
        else:
            self.hours[this_hour] = steps
            return this_hour
#unused
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
        logging.error(f'CSV file is in UTF-8-BOM format. Fixing...')
        if isBOM == 1:
            return_list[0] = return_list[0][3:]
        elif isBOM == 2:
            return_list[0][0] = return_list[0][0][3:]
        else:
            logging.error('List may have more than two dimensions, or something else is the matter:')
            logging.error(return_list[0])
    return return_list

if Verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(filename='fitbit_pipe.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# get existing data
subjects = []
subject_names = {}
current_data = CSVtolist(existing_file)
# logging.debug(current_data[:3])
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
        logging.debug(f'Found existing subject {subject.name}')
        if len(subject.weeks)>0 and row[2] == '':
            logging.debug('Moving on to next row')
            continue
    else:
        date = row[5][:-5]
        if date == '':
            continue
        logging.debug(f'The date is {date}')
        date = validate(date, 'Happened while trying to get the week number from {date} of subject {self.name}')
        name = row[0]
        multi_fitbits = row[7]
        new_subject = Subject_Record(name, date, multi_fitbits)
        logging.debug(f'New subject is {new_subject.name}')
        subject_names[name] = new_subject # add to dictionary
        subject = new_subject # update current subject
        subjects.append(subject) # add new subject to list of subjects
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
            logging.debug(f'At week number {week_num}, this row has no data for subject {subject.name}')
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

    # FIXME tracking down bug where days are string types
    logging.debug(f'For subject {subject.name}, last processed column was {col} and we got to week {week_num}')
    if subject.name == 'ATX023' and len(subject.weeks) > 0:
        break
    
##    if len(subject.weeks) > 0:
##        logging.debug(f"First and last week of subject {subject.name}'s weekly records (event, week number, start date, validity, valid days, number of steps, and low, moderate and high intensity):")
##        week = subject.weeks[0]
##        logging.debug(f'{week.event}\t{week.number}\t{week.date}\t{week.valid}\t{week.days}\t{week.avg_daily_steps}\t{week.avg_low_intensity}\t{week.avg_moderate_intensity}\t{week.avg_high_intensity}')
##        week = subject.weeks[-1]
##        logging.debug(f'{week.event}\t{week.number}\t{week.date}\t{week.valid}\t{week.days}\t{week.avg_daily_steps}\t{week.avg_low_intensity}\t{week.avg_moderate_intensity}\t{week.avg_high_intensity}')
##    else:
##        logging.debug(f'This row for subject {subject.name} has no weekly data: {subject.weeks}')

for subject in subjects:
    subject.sort_weeks()
    
# debug for ATX23
subject = subject_names['ATX023']
for week in subject.weeks:
    logging.debug(f"For {subject.name}, week {week.number}'s date is {week.date}")

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
    name = row[0]
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

    new_day = Activity_Day(date, SedentaryMinutes,LightlyActiveMinutes,FairlyActiveMinutes,VeryActiveMinutes,SedentaryActiveDistance,LightActiveDistance,ModeratelyActiveDistance,VeryActiveDistance)
    logging.debug(f'New day is {new_day}, and to make it I fed it {date, SedentaryMinutes,LightlyActiveMinutes,FairlyActiveMinutes,VeryActiveMinutes,SedentaryActiveDistance,LightActiveDistance,ModeratelyActiveDistance,VeryActiveDistance}')
    if type(new_day) == str:
        logging.debug(f'That day is a string.')
        exit()
    week = subject.get_week_by_date(date)
    logging.debug(f'Week is {week}.')
    week.days.append(new_day)

# debugging days that are strings
##days = 0
##string_days = 0
##for subject in subjects:
##    for week in subject.weeks:
##        for day in week.days:
##            days += 1
##            if type(day) == str:
##                string_days += 1
##logging.debug(f'Out of {days} days, {string_days} are strings.')

# get hourly data
hourly_data = CSVtolist(hourly_file)
first_row = True
hourly_columns = []
subject = subjects[0]
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
    week = subject.get_week_by_date(date_time)
    if week == -1:
        logging.debug(f'Subject {subject} has no week containing {date_time}')
        #FIXME add new week
        continue # remove when fixed
    day = week.get_day_by_date(date_time)
    if day == -1:
        logging.debug(f'Subject {subject} has no day for {date_time}')
        #FIXME add new day
        continue # remove when fixed
    
    steps = row[2]

    # identify new day unnecessary?
    # day = subject.weeks[-1].days[-1].ActivityDay #FIXME
    # if day != 

    new_hour = day.add_hour(date_time, steps)
    if new_hour == -1:
        logging.error(f'Duplicate hour for subject {subject}')
    
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


# TODO optionally, save all data that was taken in, including hourly data
