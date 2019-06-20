from datetime import datetime
import re
from datetime import tzinfo
import datetime as DT
import pytz
import operator
import time
import random


INDIAN_TZ = pytz.timezone('Asia/Kolkata')
PATTERN = r'(.*) (.*) (.*) \[(.*)\] "(.*)" (.*) (.*)\n'


def search_new_line(log_file):
    while (log_file.read(1) != '\n'):
        pass
        
    return log_file.tell()


def reverse_line_read(pointer_position, log_file):
    position = pointer_position -80
   
    log_file.seek(position)
    while (log_file.read(1) != '\n'):
        position = log_file.tell()-2
        pass

    line = log_file.readline()
    return match_groups(line)[1]
   

def get_timestamp(line):
    return datetime.strptime(match_groups(line)[1], "%d/%b/%Y:%H:%M:%S %z")


def match_groups(log_file_line):
    match = re.match(PATTERN, log_file_line, re.S)

    ip = match.group(1)
    timestamp = match.group(4)
    if(len(match.group(5).split(' ')) == 1):
        url = match.group(5).split(' ')[0]
    else:
        url = match.group(5).split(' ')[1]
    status = match.group(6)
    response_size = match.group(7)
    if response_size != '-':
        response_size = int(response_size)
    else:
        response_size = 0
    return [ip, timestamp, url, status, response_size]


def subtract_exact_position(multiplier, start_date, timestamp_second, pointer_position_second):
    return pointer_position_second -(multiplier*(timestamp_second-start_date).days)


def add_exact_position(multiplier, start_date, timestamp_second, pointer_position_second):
    return pointer_position_second + (multiplier*(start_date - timestamp_second).days)


def printTable(myDict, colList=None, sep='\uFFFA'):
   
   if not colList: colList = list(myDict[0].keys() if myDict else [])
   myList = [colList] # 1st row = header
   for item in myDict: myList.append([str(item[col] or '') for col in colList])
   colSize = [max(map(len,(sep.join(col)).split(sep))) for col in zip(*myList)]
   formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
   line = formatStr.replace(' | ','-+-').format(*['-' * i for i in colSize])
   item=myList.pop(0); lineDone=False
   while myList:
      if all(not i for i in item):
         item=myList.pop(0)
         if line and (sep!='\uFFFA' or not lineDone): print(line); lineDone=True
      row = [i.split(sep,1) for i in item]
      print(formatStr.format(*[i[0] for i in row]))
      item = [i[1] if len(i)>1 else '' for i in row]


def read_apache_log():
    file_FILE = r'/home/loksuvidha/yash/logs/backup_access.log'

    REPORT = {}

    print('''The types of columns to scan and filter you can apply are as follows- 
    1)ip
    2)status
    3)url
    4)response_size
    5)timestamp
    6)top_10_entries
    7)response_size_data (Prints DATA according to the response size)

Enter the name of the filter name and column name below.''')

    filter_apply = input("Enter the filter name you want to apply:")
    
    
    if filter_apply != 'top_10_entries':

        if filter_apply == 'timestamp':
            filter_value = input("Enter the filter in format (DD/MM/YYYY:HRS:MINS:SEC):")
            filter_value = INDIAN_TZ.localize(datetime.strptime(filter_value , '%d/%m/%Y:%H:%M:%S'),'%d/%m/%Y:%H:%M:%S')
                         
        
        elif filter_apply == 'response_size_data':
            new_filter_apply = 'response_size'
            filter_value = int(input("Enter the value of filter:"))

        else:
            filter_value = input("Enter the value of filter:")
             

    column_to_scan = input("Enter the name of column name you want to scan:")
    start_date = input("Enter start date (format - DD/MM/YYYY) :")
    start_date = INDIAN_TZ.localize(datetime.strptime(start_date, '%d/%m/%Y'), "%d/%m/%Y")
    end_date = input("Enter end date (format - DD/MM/YYYY) :")
    end_date = INDIAN_TZ.localize(datetime.strptime(end_date, '%d/%m/%Y'), "%d/%m/%Y")


    with open(file_FILE, "r") as log_file:
        
        pointer_position_first = search_new_line(
            log_file)  # gets first pointer posoition
        log_file.seek(pointer_position_first)
        line = log_file.readline()
        timestamp_first = get_timestamp(line)  # gets first timestamp

        log_file.seek(random.randint(100000000,200000000))
        current_pointer_position = search_new_line(log_file)
        log_file.seek(current_pointer_position)
        line = log_file.readline()
        timestamp_second = get_timestamp(line)  # gets 2nd timestamp
        pointer_position_second = log_file.tell()  # second pointer position

        while True:
            position_difference = pointer_position_second - pointer_position_first
            date_difference = timestamp_second - timestamp_first
               
            if (date_difference.days != 0):
                multiplier = (position_difference)/(date_difference).days
            else:
                current_pointer_position = log_file.tell()
                break

            if (timestamp_second < start_date and date_difference.days >= 3):
                approx_position = add_exact_position(
                    multiplier, start_date, timestamp_second, pointer_position_second)
                log_file.seek(approx_position)
                current_position = search_new_line(log_file)
                log_file.seek(current_position)
                line = log_file.readline()
                new_timestamp = get_timestamp(line)
                current_pointer_position = log_file.tell()

            elif(timestamp_second > start_date ):
                approx_position = subtract_exact_position(
                    multiplier, start_date, timestamp_second, pointer_position_second)
                if approx_position < 0:
                    approx_position = random.randint(0,200)
                
                log_file.seek(approx_position)
                current_position = search_new_line(log_file)
                log_file.seek(current_position)
                line = log_file.readline()
                new_timestamp = get_timestamp(line)
                current_pointer_position = log_file.tell()

            elif(timestamp_second <= start_date and date_difference.days <= 3):
                current_pointer_position = log_file.tell()
                break

            pointer_position_first = pointer_position_second
            pointer_position_second = current_pointer_position

            timestamp_first = timestamp_second
            timestamp_second = new_timestamp

        
        log_file.seek(current_pointer_position)
        while True:
            line = log_file.readline()
            timestamp = get_timestamp(line)
            pointer_position = log_file.tell()

            if (timestamp >= start_date):
                reverse_timestamp = reverse_line_read(pointer_position, log_file)
                reverse_timestamp = datetime.strptime(
                    reverse_timestamp, "%d/%b/%Y:%H:%M:%S %z")
                difference = start_date - reverse_timestamp

                if (difference.days <= 1):
                
                    line = log_file.readline()
                    
                    timestamp = get_timestamp(line)
                    i = 0
                    while timestamp <= end_date:
                        i = i+1
                        line = log_file.readline()
                        line_report = {
                            'line': line ,
                            'ip' : match_groups(line)[0] ,
                            'url': match_groups(line)[2] ,
                            'status': match_groups(line)[3] ,
                            'response_size' : (match_groups(line)[4]) ,
                           'timestamp' : get_timestamp(line)
                        }

                        timestamp = line_report['timestamp']
                        if timestamp > end_date :
                            break
                      
                        if filter_apply == 'top_10_entries':
                            if line_report[column_to_scan] in REPORT.keys() :
                                REPORT[line_report[column_to_scan]] +=1
                            else:
                                REPORT[line_report[column_to_scan]] =1
                            
                        
                     
                        elif filter_apply == 'response_size_data':

                            if line_report[new_filter_apply] >= filter_value :
                    
                                
                                REPORT[line_report[column_to_scan]] = line_report[new_filter_apply]
                                

                        else:
                            if line_report[filter_apply] == filter_value :
                    
                                if line_report[column_to_scan] in REPORT.keys() :
                                    REPORT[line_report[column_to_scan]] += 1
                                else:
                                    REPORT[line_report[column_to_scan]] = 1



                        REPORTS = sorted(REPORT.items(), key=operator.itemgetter(1), reverse=True)[:10]
                        
                        if filter_apply == 'response_size_data':
                            NEW_REPORT = [{column_to_scan:items[0],'response_size':items[1]} for items in REPORTS]    
                        else:
                            NEW_REPORT = [{column_to_scan:items[0],'count':items[1]} for items in REPORTS]
                        
                        if i%400 == 0:
                            if filter_apply != 'top_10_entries':
                                print("\033[H\033[J")
                                print("Following table display is on :-")
                                print("Filter Applied on =>",filter_apply)
                                print("Filter Applied Value is =>",filter_value)
                                print("Column being scanned is =>",column_to_scan)
                                print("Start Date is:",start_date ," and End date is => ",end_date)
                                print("Current time (FORMAT - YYYY*MM-DD)=>",timestamp)
                                print('\n')
                                printTable(NEW_REPORT , sep=' ')    
                            else:
                                print("\033[H\033[J")
                                print("The table display is for count of top 10:",column_to_scan)
                                print("Start Date is:",start_date ," and End date is: ",end_date)
                                print("Current time (FORMAT - YYYY*MM-DD)=>",timestamp)
                                print('\n')
                                printTable(NEW_REPORT , sep=' ')

                        if filter_apply != 'top_10_entries':
                            print("\033[H\033[J")
                            print("Following table display is on :-")
                            print("Filter Applied on =>",filter_apply)
                            print("Filter Applied Value is =>",filter_value)
                            print("Column being scanned is =>",column_to_scan)
                            print("Start Date is:",start_date ," and End date is: ",end_date)
                            print("Current time (FORMAT - YYYY*MM-DD)=>",timestamp)
                            print('\n')
                            printTable(NEW_REPORT , sep=' ')    
                        else:
                            print("\033[H\033[J")
                            print("The table display is for count of top 10 =>",column_to_scan)
                            print("Start Date is:",start_date ," and End date is => ",end_date)
                            print("Current time (FORMAT - YYYY*MM-DD)=>",timestamp)
                            print('\n')
                            printTable(NEW_REPORT , sep=' ')
                
                    break        



if __name__ == "__main__":
    read_apache_log()