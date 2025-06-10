from generations import processGenerations

import schedule
import time


def addGenerationsSchedule() -> None:
    schedule.every().day.at("07:00").do(processGenerations, time_slot='morning')
    schedule.every().day.at("16:00").do(processGenerations, time_slot='evening')


def scheduler() -> None:
    addGenerationsSchedule()

    while True:
        schedule.run_pending()
        time.sleep(1)
