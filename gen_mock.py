import csv
import os
from datetime import datetime, timedelta
from random import randrange



def get_midnight_date (date):
    return datetime(date.year, date.month, date.day, 0, 0, 0)


def datetime_range(start, end, delta):
    current = start
    while current < end:
        yield current
        current += delta


def get_result(section: int):
    return [[None, dt.strftime('%Y-%m-%d %H:%M'), 0, randrange(650, 750), randrange(45, 55), randrange(24, 26), section]
            for index, dt in
            enumerate(datetime_range(get_midnight_date(today), get_midnight_date(tomorrow), timedelta(minutes=5)))]


if __name__ == '__main__':
    today = datetime.today()
    tomorrow = datetime.today() + timedelta(days=1)

    if os.path.isfile("./mock.csv"):
        os.remove("./mock.csv")

    for num in [1, 2, 3]:
        with open(f"mock.csv", "a+") as my_csv:
            csvWriter = csv.writer(my_csv, delimiter=',')
            csvWriter.writerows(get_result(num))
