import logging
import random
from datetime import datetime
from datetime import datetime as dt
from pathlib import Path
from subprocess import call
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def notify_by_slack(date):
    message = "Found an earlier date: " + date
    param = "-X POST -H 'Content-type: application/json' --data \"{'text':'" + message + "'}\" " + webhook_url
    call("curl " + param, shell=True)


def wait_a_bit():
    sleep(random.uniform(0.1, 1.0))


Log_Format = "%(levelname)s %(asctime)s - %(message)s"
log_dir = "/Users/cli/test/"
#log_dir = "/home/ubuntu/log/"
logging.basicConfig(filename = log_dir + datetime.now().strftime('logfile_%Y-%m-%d_%H-%M-%S.log'),
                    #stream = sys.stdout,
                    filemode = "w",
                    format = Log_Format,
                    level = logging.INFO)
logger = logging.getLogger()

# prepare properties
separator = "="
properties = {}

# http://stackoverflow.com/questions/27945073/how-to-read-properties-file-in-python
#properties_path = '/home/cliff/.secret/properties'
properties_path = '/Users/cli/.secret/properties'

my_file = Path(properties_path)
if not my_file.is_file():
    properties_path = '/home/ubuntu/.secret/properties'

with open(properties_path) as f:
    for line in f:
        if separator in line:
            name, value = line.split(separator, 1)
            properties[name.strip()] = value.strip()
appt_url = properties.get('appt_url')
order_number = properties.get('order_number')
email = properties.get('email')
pw = properties.get('pw')
webhook_url = properties.get('webhook_url')

date_pattern = '%m/%d/%Y'
scheduled_date_str = '1/23/2024'
available_xpath = "//*[@id='weekDiv']//*[@class='span2 calday ']"
next_week_button_xpath = "//*[@id='nextWeekButton']//a[@href='#futureAppointmentSub']"

logger.info("to start browser")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(appt_url)

# login tracking
logger.info("Login")
wait_a_bit()
driver.find_element(By.ID, "orderid").send_keys(order_number)
driver.find_element(By.NAME, "email").send_keys(email)
driver.find_element(By.ID, "password").send_keys(pw)
driver.find_element(By.ID, "loginButton").click()

# reschedule
logger.info("Reschedule")
wait_a_bit()
driver.find_element(By.ID, "rescheduleButton").click()
found_slot = False
while not found_slot:
    wait_a_bit()
    dayBoxes = driver.find_elements(By.XPATH, available_xpath)
    if dayBoxes:
        dayBox = dayBoxes[0]
        text = dayBox.text
        found_date_str = text.splitlines()[1]
        scheduled_date = dt.strptime(scheduled_date_str, date_pattern)
        found_date = dt.strptime(found_date_str, date_pattern)
        if found_date < scheduled_date:
            logger.info("Found an early slot!!!")
            notify_by_slack(found_date_str)
            # send slack message here!!!
        else:
            logger.info("Not found a better one...")
        found_slot = True
    else:
        driver.find_element(By.XPATH, next_week_button_xpath).click()

wait_a_bit()

driver.close()

# TODO: scan yesterday's log to ensure it does not missing running more than 1 day


