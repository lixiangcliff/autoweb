import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# prepare properties
separator = "="
properties = {}
# http://stackoverflow.com/questions/27945073/how-to-read-properties-file-in-python
with open('/home/cliff/.secret/properties') as f:
    for line in f:
        if separator in line:
            name, value = line.split(separator, 1)
            properties[name.strip()] = value.strip()
travel_url = properties.get('travel_url')
travel_number = properties.get('travel_number')
travel_answer = properties.get('travel_answer')
webhook_url=properties.get('webhook_url')

driver = webdriver.Chrome('/usr/local/bin/chromedriver')
driver.get(travel_url)

# 登陆
driver.find_element_by_link_text("继续未完成的申请预约").click()
driver.find_element_by_id("recordNumberHuifu").send_keys(travel_number)
select = Select(driver.find_element_by_id('questionIDHuifu'))
# select by visible text
select.select_by_visible_text('您的第一份工作在哪个城市或城镇？')

driver.find_element_by_id("answerHuifu").send_keys(travel_answer)
elements = driver.find_elements_by_class_name("ui-button-text")
elements[1].click()  # 提交

# click 进入预约
try:
    enter_reservation = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='myButton']"))
    )
    enter_reservation.click()
except:
    print("fail to enter reservation")

# in 三月
# need to wait it to show
try:
    cur_month = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, "fc-header-title"))
    )
    if cur_month.text == "三月 2017":
        print("it is march now")
except:
    print("fail to get cur_month")

available_date = []
march_page = ['3/27', '3/28', '3/29', '3/30', '3/31', '4/3', '4/4', '4/5', '4/6', '4/7']
reservation_dates = driver.find_elements_by_xpath("//div[@class='fc-event-inner']/span")
found_one = False
for idx, reservation_date in enumerate(reservation_dates):
    if int(reservation_date.text[0:-3]) < 85:
        found_one = True
        print ("find one day!: " + march_page[idx])
        available_date.append(march_page[idx])

if not found_one:
    print("failed to find any day in march!")

# go to next page(April)
driver.find_element_by_class_name("ui-icon-circle-triangle-e").click()
try:
    cur_month = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, "fc-header-title"))
    )
    if cur_month.text == "四月 2017":
        print("it is April now")
except:
    print("fail to get cur_month")

april_slots = []
last_to_check = 24  # 20 at the most 24
my_date = 28  # 24
april_page = ['3/27', '3/28', '3/29', '3/30', '3/31', '4/3', '4/10', '4/17', '4/24', '4/4', '4/11', '4/18', '4/25', '4/5', '4/12', '4/19', '4/26', '4/6', '4/13', '4/20', '4/27', '4/7', '4/14', '4/21', '4/28']
reservation_dates = driver.find_elements_by_xpath("//div[@class='fc-event-inner']/span")
for idx, reservation_date in enumerate(reservation_dates):
    if idx > last_to_check: # my date is 24 -_-|||
        break
    if int(reservation_date.text[:-3]) < 85:
        if int(april_page[idx][2:]) < my_date: # my date is 24 -_-|||
            found_one = True
            available_date.append(april_page[idx])
        else:
            print('on ', april_page[idx], 'there are ', str(85 - int(reservation_date.text[0:-3])), 'slot(s) left.')

if not found_one:
    print("failed to find any day in april!")

# date_boxes = driver.find_elements_by_class_name("ui-widget-content")
# for idx, date_box in enumerate(date_boxes):
#     # if idx < 5: # dup
#     #     continue
#     if idx > last_to_check: # my number is 20 -_-|||
#         break
#     if idx in april_slots:
#         available_date.append('4/' + str(date_box.text).strip())

if available_date:
    print ("all available dates: ", available_date)
else:
    print ("No available slot at all!")

#post to slack
if found_one:
    message = "available date(s) found: " + str(available_date)
    from subprocess import call
    call(["ls", "-l"])
    call(["home/cliff/repo/script/bash/post_to_slack.sh", "-t 'Found available date!' -b message -c 'ccjenkin' -u " + webhook_url + "-r 'good'"])
    pass

driver.close()
