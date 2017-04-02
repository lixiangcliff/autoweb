from subprocess import call
from time import localtime, strftime

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# prepare properties
separator = "="
properties = {}
# http://stackoverflow.com/questions/27945073/how-to-read-properties-file-in-python
properties_path = '/home/cliff/.secret/properties'
my_file = Path(properties_path)
if not my_file.is_file():
    properties_path = '/Users/Cliff/.secret/properties'

with open(properties_path) as f:
    for line in f:
        if separator in line:
            name, value = line.split(separator, 1)
            properties[name.strip()] = value.strip()
travel_url = properties.get('travel_url')
travel_number = properties.get('travel_number')
travel_answer = properties.get('travel_answer')
webhook_url = properties.get('webhook_url')
env = properties.get('env')

print ("to start browser")
driver = webdriver.Chrome('/usr/local/bin/chromedriver')
driver.get(travel_url)

# 登陆
print ("to login")
driver.find_element_by_link_text("继续未完成的申请预约").click()
driver.find_element_by_id("recordNumberHuifu").send_keys(travel_number)
select = Select(driver.find_element_by_id('questionIDHuifu'))
# select by visible text
select.select_by_visible_text('您的第一份工作在哪个城市或城镇？')

driver.find_element_by_id("answerHuifu").send_keys(travel_answer)
elements = driver.find_elements_by_class_name("ui-button-text")
elements[1].click()  # 提交

# click 进入预约
print ("to enter to reservation")
try:
    enter_reservation = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='myButton']"))
    )
    enter_reservation.click()
except:
    print("fail to enter reservation")


available_dates = set()


# need to wait it to show

try:
    cur_month = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, "fc-header-title"))
    )
    if cur_month.text == "四月 2017":
        print("it is april now")
except:
    print("fail to get cur_month")

# in 三月
# take screenshot
# cur_time = strftime("%H-%M-%S_%Y-%m-%d ", localtime())
# driver.get_screenshot_as_file('march_' + cur_time + '.png')

# march_page = ['4/3', '4/4', '4/5', '4/6', '4/7']
# reservation_dates = driver.find_elements_by_xpath("//div[@class='fc-event-inner']/span")
# for idx, reservation_date in enumerate(reservation_dates):
#     try:
#         if int(reservation_date.text[0:-3]) < 85:
#             print ("find one day!: " + march_page[idx])
#             available_dates.add(march_page[idx])
#     except:
#         print ("march reservation_date failure: ", march_page[idx])
#
# # go to next page(April)
#
# driver.find_element_by_class_name("ui-icon-circle-triangle-e").click()
# try:
#     cur_month = WebDriverWait(driver, 60).until(
#         EC.presence_of_element_located((By.CLASS_NAME, "fc-header-title"))
#     )
#     if cur_month.text == "四月 2017":
#         print("it is April now")
# except:
#     print("fail to get cur_month")

# take screenshot
cur_time = strftime("%H-%M-%S_%Y-%m-%d ", localtime())
driver.get_screenshot_as_file('april_' + cur_time + '.png')
april_slots = []
last_to_check = 15  # 20 at the most 24
my_date = 12  # 24 at the most 28
april_page = ['4/10', '4/17', '4/24', '4/4', '4/11', '4/18', '4/25',
              '4/5', '4/12', '4/19', '4/26', '4/6', '4/13', '4/20', '4/27', '4/7', '4/14', '4/21', '4/28']

# driver.implicitly_wait(2)

reservation_dates = driver.find_elements_by_xpath("//div[@class='fc-event-inner']/span")

april_info = []
for rd in reservation_dates:
    try:
        april_info.append(rd.text)
    except:
        pass
print ('april_info: ', april_info)

reservation_dates = driver.find_elements_by_xpath("//div[@class='fc-event-inner']/span")
count = 0
for idx, reservation_date in enumerate(reservation_dates):
    if idx > last_to_check:  # my date is 24 -_-|||
        break
    try:
        count += 1
        if int(reservation_date.text[:-3]) < 85:
            if int(april_page[idx][2:]) < my_date: # or int(april_page[idx][:1] == 3):  # my date is 24 -_-|||
                print ("find one day!: " + april_page[idx])
                available_dates.add(april_page[idx])
            # else:
            #     print('(not applicable for us though)on ', april_page[idx], 'there are ', str(85 - int(reservation_date.text[0:-3])), 'slot(s) left.')
    except:
        print ("april reservation_date failure: ", april_page[idx])

print ("checked count: ", count)
# date_boxes = driver.find_elements_by_class_name("ui-widget-content")
# for idx, date_box in enumerate(date_boxes):
#     # if idx < 5: # dup
#     #     continue
#     if idx > last_to_check: # my number is 20 -_-|||
#         break
#     if idx in april_slots:
#         available_date.append('4/' + str(date_box.text).strip())

if available_dates:
    print ("all available dates: ", available_dates)
else:
    print ("No available slot at all!")

# print ('rule out Thursdays')
# thursdays = ['3/30', '4/6', '4/13', '4/20', '4/27']
# for thursday in thursdays:
#     if thursday in available_dates:
#         available_dates.remove(thursday)
#         print ('remove: ', thursday)

print ('rule out date after mine')
later_days = ['4/24', '4/25', '4/26', '4/27', '4/28']
for later_day in later_days:
    if later_day in available_dates:
        available_dates.remove(later_day)
        print ('remove: ', later_day)

# mbp does not support slack bot
if available_dates and env != 'mbp':
    message = "available date(s) found: " + str(available_dates)
    # post to slack
    #param = "-t 'Found available date!' -b '" + message + "' -c 'ccjenkins' -u '" + webhook_url + "' -r 'good'"
    param = "-t '" + message + "' -b 'congrates!' -c 'ccjenkins' -u '" + webhook_url + "' -r 'good'"
    call("/home/cliff/repo/script/bash/post_to_slack.sh " + param, shell=True)
    print ("Found slot!")
    print ("post to slack: ", message)

    # send email
    # #email_path = '/home/cliff/tmp/email.txt'
    # email_path = '/Users/Cliff/tmp/email.txt'
    #
    # f = open(email_path, 'w')
    # f.write('Subject: ' + message + '\n')  # python will convert \n to os.linesep
    # f.close()
    # recipients = "lixiang.cliff@gmail.com, lixiang.cliff@outlook.com"
    # call("sendmail " + recipients + " < " + email_path, shell=True)
    # print ("send mail to: " + recipients)
else:
    print ('No available slot at all!')
driver.close()


