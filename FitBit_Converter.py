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
event_arm = 'baseline_arm_1'

import logging
if Verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(filename='fitbit_pipe.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

import time
ts = time.gmtime()
timestamp = time.strftime("%Y-%m-%d+%H-%M-%S", ts)

import datetime
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

import os
import csv
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

# data containers:
class Subject_Record:
    def __init__(self, name, date, multiple_devices):
        self.name = name
        # The start date for each subject is the "date" field from the "Clinical Exam" instrument + 1 day.
        self.start_date = validate(date, f"Creation of new subject {self.name}", existing_time_format)
        self.end_date = self.start_date + datetime.timedelta(days = 363)
        self.multiple_devices = multiple_devices
        self.weeks = {} # dict of Week instances
        new_date = self.start_date
        for i in range(52):
            week = Week(new_date, i)
            self.weeks[i] = week
            new_date = new_date + datetime.timedelta(days=7) # add seven days

    def get_week_by_date(self, date):
        date = validate(date, f'Was trying to get week with date for subject {self.name}')
        if len(self.weeks) == 0:
            logging.error(f'Subject {self.name} has no weeks, so none can be provided for the date requested.')
            return -1
        delta = difference_days(self.start_date, date)
        if delta > 52*7 or delta < 0:
            logging.error(f"Date {date} is bad for subject {self.name}, whose timeline starts on {self.start_date}. That would make it {delta} days away.")
            return -1
        week_num = int(delta/7)
        return self.weeks[week_num]

    def get_day_by_date(self, date):
        delta = difference_days(self.start_date, date)
        if delta > 52*7 or delta < 0:
            logging.error(f"Date {date} is bad for subject {self.name}, whose timeline starts on {self.start_date}. That would make it {delta} days away.")
            return -1
        week = self.get_week_by_date(date)
        day_num = int(delta%7)
        logging.debug(f"Trying to get day of week {week.number} for subject {self.name}, and looking for day {day_num} of that week, since we're looking for {date} and day zero was {self.start_date}")
        day = week.get_day_by_date(date)
        return day

    def update_week(self, date, **kwargs):
        week = self.get_week_by_date(date)
        for key, value in kwargs.items():
            if key == 'event':
                self.event = value
            elif key == 'valid':
                self.valid = value
            elif key == 'days':
                self.days = value
            elif key == 'steps':
                self.steps = value
            elif key == 'low':
                self.low = value
            elif key == 'moderate':
                self.moderate = value
            elif key == 'high':
                self.high = value
            else:
                logging.error(f'Bad kwarg when updating week {week.number} for subject {self.name} (key, value): {key}, {value}')

class Week:
    # TODO all those weekly parameters, plus all the parameters from the two data files
    def __init__(self, date, number, **kwargs):
        self.date = validate(date, f'Creating new week with {date}', '%m/%d/%Y')# date it begins on
        self.number = number # week number
        self.event = event_arm # meaning baseline or 8_weeks_arm_1 etc.
        self.valid = 0 # whether the week had at least 4 days of valid steps
        self.days = 0
        self.avg_daily_steps = 0.0
        self.avg_low_intensity = 0.0
        self.avg_moderate_intensity = 0.0
        self.avg_high_intensity = 0.0
        for key, value in kwargs.items():
            if key == 'event':
                self.event = value
            elif key == 'valid':
                self.valid = value
            elif key == 'days':
                self.days = value
            elif key == 'steps':
                self.steps = value
            elif key == 'low':
                self.low = value
            elif key == 'moderate':
                self.moderate = value
            elif key == 'high':
                self.high = value
            else:
                logging.error(f'Bad kwarg when making new week (key, value): {key}, {value}')
        new_date = self.date
        dicto = {}
        for i in range(7):
            new_day = Day(new_date)
            # logging.debug(f'Trying to add day {i} to list {dicto} of type {type(dicto)} of week {number}. Date is {new_date} of type {type(new_date)}, and it refers to day {new_day} of type {type(new_day)}')
            dicto[new_date] = new_day
            new_date = new_date + datetime.timedelta(days=1)
        self.days = dicto # dictionary of Day instances where key is date

    # not sure if used
    def get_day_by_date(self, date):
        date = validate(date, f'Was trying to get day of week with date for week starting on {self.date}')
        if len(self.days) == 0:
            return -1
        for day in self.days:
            logging.debug(f'Trying to get a day by date in week {self.number}, starting on {self.date}, is looking at day {day}, which is type {type(day)}')
            if date == day.ActivityDay:
                return day
        return -1

class Day:
    # SedentaryMinutes	LightlyActiveMinutes	FairlyActiveMinutes	VeryActiveMinutes	SedentaryActiveDistance	LightActiveDistance	ModeratelyActiveDistance	VeryActiveDistance
    def __init__(self, date, **kwargs):
        self.ActivityDay = validate(date, f'Creating new day dated {date}', daily_time_format)
        self.SedentaryMinutes = 0
        self.LightlyActiveMinutes = 0
        self.FairlyActiveMinutes = 0
        self.VeryActiveMinutes = 0
        self.SedentaryActiveDistance = 0
        self.LightActiveDistance = 0
        self.ModeratelyActiveDistance = 0
        self.VeryActiveDistance = 0
        self.hours = {} # dict of Hourly steps
        for key, value in kwargs.items():
            if key == 'SedentaryMinutes':
                self.SedentaryMinutes = value
            elif key == 'LightlyActiveMinutes':
                self.LightlyActiveMinutes = value
            elif key == 'FairlyActiveMinutes':
                self.FairlyActiveMinutes = value
            elif key == 'VeryActiveMinutes':
                self.VeryActiveMinutes = value
            elif key == 'SedentaryActiveDistance':
                self.SedentaryActiveDistance = value
            elif key == 'LightActiveDistance':
                self.LightActiveDistance = value
            elif key == 'ModeratelyActiveDistance':
                self.ModeratelyActiveDistance = value
            elif key == 'VeryActiveDistance':
                self.VeryActiveDistance = value
            else:
                logging.error(f'Bad kwarg when making new week (key, value): {key}, {value}')
##        for i in range(24):
##            new_hour = Hour(i,0)
##            self.hours[i] = new_hour

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'SedentaryMinutes':
                self.SedentaryMinutes = value
            elif key == 'LightlyActiveMinutes':
                self.LightlyActiveMinutes = value
            elif key == 'FairlyActiveMinutes':
                self.FairlyActiveMinutes = value
            elif key == 'VeryActiveMinutes':
                self.VeryActiveMinutes = value
            elif key == 'SedentaryActiveDistance':
                self.SedentaryActiveDistance = value
            elif key == 'LightActiveDistance':
                self.LightActiveDistance = value
            elif key == 'ModeratelyActiveDistance':
                self.ModeratelyActiveDistance = value
            elif key == 'VeryActiveDistance':
                self.VeryActiveDistance = value
            else:
                logging.error(f'Bad kwarg when making new week (key, value): {key}, {value}')
# unused
class Hour:
    def __init__(self, hour, steps):
        self.hour = hour
        self.stesps = steps

# get start dates from REDCap export file named in existing data
subjects = {}
current_data = CSVtolist(existing_file)
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
        continue

    # suck up data
    name = row[0]
    date = row[5]
    if date == '':
        logging.debug('Moving on to next row because this is a blank row for {name}')
        continue
    end_date = row[6]
    multiple_devices = row[7]
    if name in subjects:
        subject = subjects[name]
        logging.debug(f'Found existing subject {subject.name}')
    else:
        subject = Subject_Record(name, date, multiple_devices)
        subjects[name] = subject
        logging.debug(f'Created new frameworkd to hold data for {subject.name}')

    end_date = validate(end_date, f"Checking the end date for subject {subject.name}", existing_time_format)
    date_delta = difference_days(subject.end_date, end_date)
    if date_delta != 0:
        logging.error(f"End date {subject.end_date} for subject {subject.name} doesn't match that in row: {end_date}")
        subject.end_date = end_date

    col = starting_col
    start_date = subject.start_date
    for i in range(52):
        date = start_date + datetime.timedelta(days = 7*i)
        subject.update_week(date,
                            valid = row[col],
                            days = row[col +1],
                            steps = row[col +2],
                            low = row[col +3],
                            moderate = row[col +4],
                            high = row[col +5])
        col += weekly_cols

daily_data = CSVtolist(daily_file)
first_row = True
daily_columns = []
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
    if name in subjects:
        subject = subjects[name]
    else:
        logging.critical(f'New subject {name} not in subject dictionary.')
        continue
        # FIXME add new subject

    date = row[1]
    day = subject.get_day_by_date(date)
    day.update(SedentaryMinutes = int(row[2]),
               LightlyActiveMinutes = int(row[3]),
               FairlyActiveMinutes = int(row[4]),
               VeryActiveMinutes = int(row[5]),
               SedentaryActiveDistance = int(row[6]),
               LightActiveDistance = float(row[7]),
               ModeratelyActiveDistance = float(row[8]),
               VeryActiveDistance = float(row[9]))

hourly_data = CSVtolist(hourly_file)
subect = subjects['ATX002']
for row in hourly_data:
    # check columns:
    if first_row:
        first_row = False
        for column in row:
            daily_columns.append(column)
        if hourly_columns != expected_daily_columns:
            logging.critical('Columns in file are {hourly_columns}, and different from those expected, which are {expected_hourly_columns}')
            break # TODO adapt to new columns
        continue

    logging.debug(f'Hourly row is {row}')
    name = row[0]
    if name != subject.name:
        if name in subject_names:
            subject = subject_names[name]
        else:
            logging.critical(f'New subject {name} not in subject dictionary.')
            continue
            # FIXME add new subject

    date = validate(row[1], f'Trying to get date from hourly data', hourly_time_format)
    hour_number = date.hour
    day = subject.get_day_by_date(date)
    steps = row[2]
    day.hours[hour_number] = steps

# TODO update weekly averages

# make pandas dataframe
columns = CSVtolist(format_file) # get from format file
df = pd.DataFrame(columns)
i=0
for subject in subjects.items():
    row = [subject.name, event_arm, subject.start_date, subject.end_date, subject.multiple_devices]
    for h in range(52):
        week = subject.weeks[h]
        row.append(week.valid)
        row.append(week.days)
        row.append(week.avg_daily_steps)
        row.append(week.avg_low_intensity)
        row.append(week.avg_moderate_intensity)
        row.append(week.avg_high_intensity)
    df.loc[i] = row
    i+=1
if Verbose:
    print(df)
# save as 'FitBitData_Converted_' + timestamp
