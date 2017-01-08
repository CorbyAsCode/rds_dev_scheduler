from datetime import datetime, timedelta, date
import calendar

week_we_want_to_run_in = 4
test_date = date(2017, 1, 27)

def check_week_number_of_month(date_to_check, week_number):
    number_of_full_weeks = 0
    weeks_list = []
    cal = calendar.Calendar()
    weeks_of_month = cal.monthdayscalendar(date_to_check.year, date_to_check.month)
    for week in weeks_of_month:
        if 0 in week:
            continue
        else:
            number_of_full_weeks += 1
            weeks_list.append(week)

    if date_to_check.day in weeks_list[week_number - 1]:
        print "%s is in week #%s of %s" % (date_to_check.day, week_number, date_to_check.strftime('%B'))

check_week_number_of_month(test_date, week_we_want_to_run_in)