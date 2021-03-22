import sys
import requests
import getopt
import json
import calendar
import math

from datetime import datetime, timezone, timedelta
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

api_base = "https://api.veracode.com/was/configservice/v1/"
headers = {
    "User-Agent": "Dynamic Analysis API Example Client",
    "Content-Type": "application/json"
}

analysis_update_template= r'''{
    "schedule": {
        "duration": {
            "length": {duration_length},
            "unit": "{duration_unit}"
        },
        "end_date": "",
        "now": false,
        "scan_recurrence_schedule": {
            "day_of_week": "{day_of_week}",
            "recurrence_interval": {recurrence_interval},
            "recurrence_type": "{recurrence_type}",
            "schedule_end_after": {schedule_end_after},
            "week_of_month": "{week_of_month}"
        },
        "schedule_status": "ACTIVE",
        "start_date": "{start_date}"
    }
}'''

weekly_update_template= r'''{
    "schedule": {
        "duration": {
            "length": {duration_length},
            "unit": "{duration_unit}"
        },
        "end_date": "",
        "now": false,
        "scan_recurrence_schedule": {
            "day_of_week": "{day_of_week}",
            "recurrence_interval": {recurrence_interval},
            "recurrence_type": "{recurrence_type}",
            "schedule_end_after": {schedule_end_after}
        },
        "schedule_status": "ACTIVE",
        "start_date": "{start_date}"
    }
}'''

monthly_update_template= r'''{
    "schedule": {
        "duration": {
            "length": {duration_length},
            "unit": "{duration_unit}"
        },
        "end_date": "",
        "now": false,
        "scan_recurrence_schedule": {
            "day_of_week": "{day_of_week}",
            "recurrence_interval": {recurrence_interval},
            "recurrence_type": "{recurrence_type}",
            "schedule_end_after": {schedule_end_after},
            "week_of_month": "{week_of_month}"
        },
        "schedule_status": "ACTIVE",
        "start_date": "{start_date}"
    }
}'''

scan_update_hold = r'''{
    "name": "{name}"
}
'''


class RecurrenceSchedule:
    day_of_week = "MONDAY"
    recurrence_interval = 1
    recurrence_type = "MONTHLY"
    schedule_end_after = "12"
    week_of_month = ""

class Duration:
    length = 0
    unit = "DAY"

class CommandSettings:
    verbose = False
    dry_run = False
    interactive = False
    execute = False

cmdsettings = CommandSettings()

def http_get(uri):
    if cmdsettings.verbose:
        print(f"URI: {uri}")
    response = requests.get(uri, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers)
    
    # Error handling
    if response.status_code == 200:
        print("successfully request.")

    return response

def get_da_analyses():
    if cmdsettings.verbose:
        print(f"get_da_analyses")
    
    content = None
    path = api_base + f"analyses"
    response = requests.get(path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers)
    if response.status_code == 200:
        content = response.json()   
        
    if cmdsettings.verbose:
        print(f"status code {response.status_code}")
        result = response.text
        if result is not None:  
            print(json.dumps(result, indent=4, sort_keys=True))

    return content

def get_da_platform_applications(application_name):
    if cmdsettings.verbose:
        print(f"get_da_platform_applications(): {application_name}")

    content = None
    url = api_base + f"platform_applications"
    parameters = f"application_name={application_name}"
    response = requests.get(url, params=parameters, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers)
 
    if response.status_code == 200:
        content = response.json()   
        
    if cmdsettings.verbose:
        print(f"status code {response.status_code}")
        result = response.text
        if result is not None:  
            print(json.dumps(result, indent=4, sort_keys=True))

    return content

def patch_update_analysis(analysis_id, json_payload):
    bReturn = False
    
    if cmdsettings.verbose:
        print("patch_update_analysis")
        print(json_payload)
    
    if cmdsettings.dry_run is False:
        scan_path = api_base + "analyses/" + analysis_id + "?method=PATCH"
        response = requests.put(scan_path, auth=RequestsAuthPluginVeracodeHMAC(), headers=headers, json=json.loads(json_payload))
    
        if cmdsettings.verbose:
            print(f"status code: {response.status_code}")
            content = response.text
            if content is not None:  
                print("content:" + content)
    
        if response.status_code == 204:
           bReturn = True

    return bReturn

def convert_from_datetime_to_utc(utc_date_time):
    return utc_date_time.isoformat("T") + "Z"

def convert_from_utc_to_datetime(original_date_time):
    if cmdsettings.verbose:
        print("convert_from_vc_datetime....")
        print(f"Original DateTime: {original_date_time}")  

    # String off the ending 'Z[UTC]' value and append on timezone UTC
    date_time_str = original_date_time[:-6]
    date_time_str = date_time_str + "+00:00"

    if cmdsettings.verbose: 
        print(f"Converted DateTime {date_time_str}")
    
    # convert to datetime object for processing
    date_time_converted = datetime.fromisoformat(date_time_str)       

    if cmdsettings.verbose:
        print('Date:', date_time_converted.date())
        print('Time:', date_time_converted.time())
        print('Date-time:', date_time_converted)
    
    return date_time_converted

def find_week_of_month(week_of_month):
    weeksOfTheMonth = ["FIRST", "SECOND", "THIRD", "FOURTH", "LAST"]
    index_count = 1
    for week in weeksOfTheMonth:
        if week == week_of_month:
           break
        else:
            index_count= index_count + 1    

    return index_count

def find_day_of_week(day_of_the_week):
    daysOfTheWeek = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

    index_count = 0
    for day in daysOfTheWeek:
        if day == day_of_the_week:
            break
        else:
            index_count= index_count + 1    

    return index_count

def get_number_of_weeks_in_month(date):
    if cmdsettings.verbose:
        print("get_number_of_weeks_in_month....")
        print(f"Proposed Date: {date}")
        c = calendar.TextCalendar()
        print(c.formatmonth(date.year, date.month))   
        print(c.formatmonth(date.year, date.month+1)) 

    weeks_in_month = len(calendar.monthcalendar(date.year, date.month))
    return weeks_in_month

def get_week_of_month(date):
   first_day = date.replace(day=1)
   day_of_month = date.day

   if(first_day.weekday() == 6):
       adjusted_dom = (1 + first_day.weekday()) / 7
   else:
       adjusted_dom = day_of_month + first_day.weekday()

   return int(math.ceil(adjusted_dom/7.0))

def find_next_available_monthly(iso_current_datetime, original_time, recurrence_schedule):
    if cmdsettings.verbose:
        print("find_next_available_monthly....")
        print(f"Current Date Time: {iso_current_datetime}")
        print(f"Original Scheduled Day and Time: {recurrence_schedule.week_of_month} {recurrence_schedule.day_of_week} {original_time}")

    proposed_datetime = find_next_available_weekday(iso_current_datetime, original_time, recurrence_schedule.day_of_week)
    if cmdsettings.verbose:
        print("find_next_available_monthly....")
        print(f"Proposed Date and Time:{proposed_datetime}")
    
    proposed_date = proposed_datetime.date()
    proposed_time = proposed_datetime.time()

    scheduled_week_of_month_num = find_week_of_month(recurrence_schedule.week_of_month)
    scheduled_day_of_week_num = find_day_of_week(recurrence_schedule.day_of_week)

    proposed_week_of_month_num = get_week_of_month(proposed_date)

    if proposed_week_of_month_num < scheduled_week_of_month_num:
        if cmdsettings.verbose:
            print("proposed_week_of_month_num < scheduled_week_of_month_num")
        delta = scheduled_week_of_month_num - proposed_week_of_month_num
        proposed_date = proposed_date + timedelta(weeks=delta)
    elif proposed_week_of_month_num > scheduled_week_of_month_num:
        if cmdsettings.verbose:
            print("proposed_week_of_month_num > scheduled_week_of_month_num")
         
        # Must account if existing Monthy is 5 week or 4
        weeks_in_month = get_number_of_weeks_in_month(proposed_date)
        delta =  4 - (weeks_in_month - proposed_week_of_month_num)
        proposed_date = proposed_date + timedelta(weeks=delta)
    else:
        if cmdsettings.verbose:
            print("Proposed and Scheduled Weeks are the same.")

    returnDateTime = datetime.combine(proposed_date, proposed_time)
    if cmdsettings.verbose:
        print(f"Calculated Date and Time: {returnDateTime}")

    return returnDateTime

def find_next_available_weekday(iso_current_datetime, original_time, day_of_the_week):
    if cmdsettings.verbose:
        print("find_next_available_weekly....")
        print(f"Current Date Time: {iso_current_datetime}")
        print(f"Original Scheduled Day and Time: {day_of_the_week} {original_time}")
    
    current_weekday_num = iso_current_datetime.weekday()
    scheduled_weekday_num = find_day_of_week(day_of_the_week)

    current_weekday = calendar.day_name[current_weekday_num] 
    scheduled_weekday = calendar.day_name[scheduled_weekday_num] 
    
    current_date = iso_current_datetime.date()

    scheduled_date = current_date
    if current_weekday_num > scheduled_weekday_num:
        if cmdsettings.verbose:
            print(f"today: {current_weekday} > scheduled: {scheduled_weekday}")

        delta = scheduled_weekday_num - current_weekday_num + 7
        scheduled_date = current_date + timedelta(days=delta)
    elif current_weekday_num < scheduled_weekday_num:
        if cmdsettings.verbose:
            print(f"today: {current_weekday} < scheduled: {scheduled_weekday}")

        delta = scheduled_weekday_num - current_weekday_num
        scheduled_date = current_date + timedelta(days=delta)
    else:
        if cmdsettings.verbose:
            print(f"today: {current_weekday} == scheduled: {scheduled_weekday}")

        if iso_current_datetime.time() > original_time:
            scheduled_date = current_date + timedelta(days=7)
          
    scheduled_datetime = datetime.combine(scheduled_date, original_time)
    if cmdsettings.verbose:
        print(f"Next Available {scheduled_weekday}: {scheduled_datetime}")
   
    return scheduled_datetime

def calculate_next_available_datetime(iso_date_time_now, original_date_time, recurrence_schedule):
    if cmdsettings.verbose:
        print("calculate_next_available_datetime....")

    start_datetime = original_date_time
    iso_date_time_scheduled = original_date_time

    # update only if the scheduled time is in the past
    if iso_date_time_now > iso_date_time_scheduled: 
        scheduled_date = iso_date_time_scheduled.date()
        scheduled_time = iso_date_time_scheduled.time()

        if recurrence_schedule.recurrence_type == "WEEKLY":
            # find the next available day
            start_datetime = find_next_available_weekday(iso_date_time_now, scheduled_time, recurrence_schedule.day_of_week)
        else:
            # find the next available monthly day
            start_datetime = find_next_available_monthly(iso_date_time_now, scheduled_time, recurrence_schedule)
            
    return start_datetime

def copy_scan_recurrence(analysis):
    analysis_id = analysis["analysis_id"]
    # Duration represents scan window
    # Start Date must be just prior the recurrence cadence
    # End Date not needed as system will calculate value based on start date

    # May have to retrieve exiting duration

def update_scan_recurrence(analysis_id, duration, recurrence_schedule, start_date):
    bResult = False

    if cmdsettings.verbose:
        print(f"update_scan_recurrence....")

    schedule_update = weekly_update_template
    if recurrence_schedule.recurrence_type == "MONTHLY":
        schedule_update = monthly_update_template
   
    schedule_update = schedule_update.replace("{duration_length}", str(duration.length), 1)
    schedule_update = schedule_update.replace("{duration_unit}", duration.unit, 1)

    schedule_update = schedule_update.replace("{recurrence_type}", recurrence_schedule.recurrence_type, 1)
    schedule_update = schedule_update.replace("{day_of_week}", recurrence_schedule.day_of_week, 1)
    schedule_update = schedule_update.replace("{recurrence_interval}", str(recurrence_schedule.recurrence_interval), 1)
    schedule_update = schedule_update.replace("{schedule_end_after}", str(recurrence_schedule.schedule_end_after), 1)
    
    if recurrence_schedule.recurrence_type == "MONTHLY":
        schedule_update = schedule_update.replace("{week_of_month}", recurrence_schedule.week_of_month, 1)

    schedule_update = schedule_update.replace("{start_date}", start_date, 1)

    if cmdsettings.verbose:
        print("updating to:")
        print(schedule_update)

    bResult = patch_update_analysis(analysis_id, schedule_update)
    
    return bResult

def process_analysis(analysis):
    bResult = False

    analysis_id = analysis["analysis_id"]
    analysis_name = analysis["name"]
    print(f"Procesing Started: ({analysis_id}) '{analysis_name}'")

    duration = Duration()
    duration.length = analysis["schedule_summary"]["duration"]["length"]
    duration.unit = analysis["schedule_summary"]["duration"]["unit"]

    recurrence_schedule = RecurrenceSchedule()
    recurrence_schedule.recurrence_type = analysis["schedule_summary"]["scan_recurrence_schedule"]["recurrence_type"]
    recurrence_schedule.recurrence_interval = analysis["schedule_summary"]["scan_recurrence_schedule"]["recurrence_interval"]
    recurrence_schedule.day_of_week = analysis["schedule_summary"]["scan_recurrence_schedule"]["day_of_week"]
    recurrence_schedule.schedule_end_after = analysis["schedule_summary"]["scan_recurrence_schedule"]["schedule_end_after"]

    if analysis["schedule_summary"]["scan_recurrence_schedule"]["recurrence_type"] == "MONTHLY":
        recurrence_schedule.week_of_month = analysis["schedule_summary"]["scan_recurrence_schedule"]["week_of_month"]

    # Calculate new date time based on recurrence schedule
    original_start_datetime_str = analysis["schedule_summary"]["start_date"]
    original_start_datetime = convert_from_utc_to_datetime(original_start_datetime_str)
    
    iso_date_time_now = datetime.now(timezone.utc)
    if original_start_datetime < iso_date_time_now:
        iso_start_date = calculate_next_available_datetime(iso_date_time_now, original_start_datetime, recurrence_schedule)
        
        print(f"    ({analysis_id}) '{analysis_name}' proposed next available scheduled date and time: {iso_start_date}")
        start_date = convert_from_datetime_to_utc(iso_start_date)
        bResult = update_scan_recurrence(analysis_id, duration, recurrence_schedule, start_date) 
        if bResult == True:
            print(f"Procesing Completed: Successfully updated ({analysis_id}) '{analysis_name}' is updated and scheduled for {start_date}.")
        else:
            print(f"Procesing Falied: Update for ({analysis_id}) '{analysis_name}' was not completed.")
    else:
        print(f"Procesing Completed: ({analysis_id}) '{analysis_name}' is scheduled for the future. Update not needed.")

    return bResult

def update_analyses_to_recur(analyses):
    if cmdsettings.verbose:
        print("update_analyses_to_recur....")

    analyses_updated = 0  
    analyses_not_updated = 0
    for analysis in analyses:
        if cmdsettings.verbose:
            print("Analysis content:")
            print(analysis)
 
        if process_analysis(analysis) == True:
            analyses_updated = analyses_updated + 1
        else:
            analyses_not_updated = analyses_not_updated + 1

    print(f"Analyses updated: {analyses_updated}")  
    print(f"Analyses not updated: {analyses_not_updated}")  

def filter_list_for_recurring(scans):
    if cmdsettings.verbose:
        print("filter_list_for_recurring")
    
    # initialize return strcture
    analyses = []

    # process list for just recurring scheduled scans
    for analysis in scans:
        frequencyType = analysis["schedule_frequency"]["frequency_type"]
        if frequencyType == 'RECURRING' or frequencyType == 'RECURRING_WITH_PAUSE_AND_RESUME':
            # Check if recurring scheduled for a Year in either Monthly or Weekly modes
            recrurrenceType = analysis["schedule_summary"]["scan_recurrence_schedule"]["recurrence_type"]
            scheduleEndAfter = analysis["schedule_summary"]["scan_recurrence_schedule"]["schedule_end_after"]
            if (recrurrenceType == 'WEEKLY' and scheduleEndAfter == 52) or (recrurrenceType == 'MONTHLY' and scheduleEndAfter == 12):
                analyses.append(analysis)
    
    if cmdsettings.verbose:
        print("List of Recurring Scheduled Analyses")
        for analysis in analyses:
            print(f"   ({analysis['analysis_id']}) '{analysis['name']}'")

    return analyses

def execution_process():
    if cmdsettings.verbose:
        print("execution_process....")

    if cmdsettings.dry_run:
        print("Performing a Dry Run")

    #TODO: Refactor to add Interactive Functionality and Application Name
    #anaysis_result = get_da_platform_applications(application_name)
    #if anaysis_result is not None:
        # print("Have Scan!")

    # retrieve exising list of scans available
    result = get_da_analyses()
    if result is not None:
             # Iterate through each scan configuration and update to scan ?
        if len(result["_embedded"]["analyses"]) == 0:
            print("No analyses defined.")
            return

         # sort list of only recurring scheduled dynamic analysis scans
        filtered_list = filter_list_for_recurring(result["_embedded"]["analyses"])
        if len(filtered_list) > 0: 
            print(f"Discovered {len(filtered_list)} analyses for processing.")
            # process list of dynamic analysis scans            
            update_analyses_to_recur(filtered_list)
        else: 
            print("No recurring scheduled analyses defined")
            return

def print_help():
    """Prints command line options and exits"""
    print("""veracode-da-reset-scheduler.py [-h] [-d] [-v] -x 
        Updates all Dynamic Analysis Recurring Scheduled scans that have expired with recurrences for one year.
        Passing of the -x or --execute is required to run program
        Options: 
            -h --help       shows this help menu
            -d --dry-run    performs a dry run for updating content without committing changes
            -v --verbose    turns on the verbose debug logging for the program
            -x --execute    performs a live update to content        
            """)
    sys.exit()

def interactive_update_for_scan(scan):
    result = False
    print(scan)

    # while: True
        # entry = input("String [y] or [q] quit)")
        # if entry == "q":
        #     break
        # else
       #      break
    return result

def main(argv):
    """Simple command line support for creating, deleting, and listing DA scanner variables"""
    try:
        #TODO: Add to commandline functionality
        application_name = ''
        target_url = ''
        
        #print('ARGV      :', argv)

        options, args = getopt.getopt(argv, "hvdixa:u:",
                                   ["help","verbose","dry-run","execute"])
                                   #, "interactive","application_name=", "target_url="])
        #print('OPTIONS   :', options)

        for opt, arg in options:
            if opt == '-h':
                print_help()
            elif opt == '-v':
                cmdsettings.verbose = True
            elif opt in ('-d', '--dry-run'):
                cmdsettings.dry_run = True
            elif opt in ('-x', '--execute'):
                cmdsettings.dry_run = True
            #elif opt in ('-i', '--interactive'):
            #    cmdsettings.interactive = True
            
            #if opt in ('-a', '--application_name'):
            #    application_name = arg
            #if opt in ('-u', '--url'):
            #    target_url = arg

        #print('VERBOSE         :', cmdsettings.verbose)
        #print('DRY RUN         :', cmdsettings.dry_run)
        #print('INTERACTIVE     :', cmdsettings.interactive)        
        #print('APPLICATION NAME:', application_name)
        #print('TARGET URL      :', target_url)
        #print('REMAINING       :', args)

        if cmdsettings.execute or cmdsettings.dry_run:
            execution_process()
        else:
            print_help()

    except requests.RequestException as e:
        print("An error occurred!")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
