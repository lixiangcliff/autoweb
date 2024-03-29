import logging
import random
import sys
from datetime import datetime
from datetime import datetime as dt
from pathlib import Path
from subprocess import call
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import platform
from selenium import webdriver


def notify_by_slack(date):
    message = "Found an earlier date: " + date
    param = "-X POST -H 'Content-type: application/json' --data \"{'text':'" + message + "'}\" " + webhook_url
    call("curl " + param, shell=True)


def wait_a_bit():
    sleep(random.uniform(0.1, 1.0))


options = Options()
# browser is Chromium instead of Chrome
options.BinaryLocation = "/usr/bin/chromium-browser"


# options.add_argument("--remote-debugging-port=9222")
# options.add_argument('--disable-features=VizDisplayCompositor')
# options.add_argument("--disable-infobars")  # disabling infobars
# options.add_argument("--disable-extensions")  # disabling extensions
# options.add_argument("start-maximized")  # open Browser in maximized mode
# options.add_argument("--disable-gpu")  # applicable to windows os only

log_dir = ''
properties_path = ''

if platform.system() == "Linux" and platform.machine() == "armv7l":
    # if raspi
    options.add_argument("--headless")  # if you want it headless
    options.add_argument("--window-size=1024,768")  # set resolution
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    # options.add_argument("--window-size=1024,768")  # set resolution
    options.binary_location = ("/usr/bin/chromium-browser")
    service = Service("/usr/bin/chromedriver")
    log_dir = "/home/cliff/log/get_appt/"
    properties_path = '/home/cliff/.secret/properties'
else:  # if not raspi and considering you're using Chrome
    service = Service(ChromeDriverManager().install())
    if platform.system() == "Darwin":
        log_dir = "/Users/cli/log/"
        properties_path = '/Users/cli/.secret/properties'

Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(filename = log_dir + datetime.now().strftime('get_appt_%Y-%m-%d_%H-%M-%S.log'),
                    #stream = sys.stdout,
                    filemode = "w",
                    format = Log_Format,
                    level = logging.INFO)
logger = logging.getLogger()

# prepare properties
separator = "="
properties = {}

# http://stackoverflow.com/questions/27945073/how-to-read-properties-file-in-python

my_file = Path(properties_path)
if not my_file.is_file():
    properties_path = '/home/cliff/.secret/properties'

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
earliest_date_str = '5/23/2023'
scheduled_date_str = '6/1/2023'
available_xpath = "//*[@id='weekDiv']//*[@class='col-md-2 calday ']"
next_week_button_xpath = "//*[@id='nextWeekButton']//a[@href='#futureAppointmentSub']"

try:
    logger.info("to start browser")

    driver = webdriver.Chrome(
        service=service,
        options=options,
        )
    driver.get(appt_url)

    # login tracking
    logger.info("Login")
    wait_a_bit()
    driver.find_element(By.ID, "orderid").send_keys(order_number)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(pw)
    wait_a_bit()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    wait_a_bit()
    # driver.save_screenshot(log_dir + "screenshot1.png")
    driver.find_element(By.ID, "loginButton").click()
    driver.execute_script("window.scrollTo(0, 500);")
    wait_a_bit()
    # driver.save_screenshot(log_dir + "screenshot2.png")

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
            found_date = dt.strptime(found_date_str, date_pattern)
            earliest_date = dt.strptime(earliest_date_str, date_pattern)
            scheduled_date = dt.strptime(scheduled_date_str, date_pattern)
            if earliest_date <= found_date < scheduled_date:
                logger.info("Found an early slot with date: ", found_date_str)
                notify_by_slack(found_date_str)
                # send slack message here!!!
            else:
                logger.info("Not found a better one...")
            found_slot = True
        else:
            driver.find_element(By.XPATH, next_week_button_xpath).click()

    wait_a_bit()
    logger.info("Completed successfully")
    driver.close()
except Exception as e:
    logger.error("Errors: ", str(e))

# TODO: scan yesterday's log to ensure it does not missing running more than 1 day


