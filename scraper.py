# https://github.com/teal33t/captcha_bypass
# Dont use this code for spy and 

import unittest
import sys, time, os
from pathlib import Path
import requests
import numpy as np
import scipy.interpolate as si

from datetime import datetime
from time import sleep, time
from random import uniform, randint

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import NoSuchElementException
import threading
import sqlalchemy as db
import json
import warnings
from random import choice
import settings

# Randomization Related
MIN_RAND        = 1.24
MAX_RAND        = 2.27
LONG_MIN_RAND   = 4.78
LONG_MAX_RAND 	= 9.1
thread_limit = settings.THREADS_COUNT
user_agents = []
# Update this list with proxybroker http://proxybroker.readthedocs.io
PROXY_LIST = []

thread_count = 0

class SyncMe():

	number = None
	headless = True
	options = None
	profile = None
	capabilities = None

	def create_connection(self):
		host = settings.MYSQL_HOSTNAME
		user = settings.MYSQL_USERNAME
		password = settings.MYSQL_PASSWORD
		dbname = settings.MYSQL_DATABASE
		self.engine = db.create_engine('mysql+mysqldb://%s:%s@%s/%s?charset=utf8' % (user, password, host, dbname))
		self.conn = self.engine.connect()
		self.metadata = db.MetaData()


	def create_table(self):
		self.create_connection()
		self.land = db.Table('land_info', self.metadata,
			# db.Column('id', db.Integer(), primary_key = True),
			db.Column('search', db.String(200)),
			db.Column('reg_number', db.String(200)),
			db.Column('reg_type', db.String(200)),
			db.Column('designation', db.String(50)),
			db.Column('reg_date', db.String(50)),
			db.Column('close_date', db.String(50)),
			db.Column('position', db.String(500)),
			db.Column('owner', db.String(500)),
			db.Column('created_at', db.DateTime(timezone=True))
		)
		self.metadata.create_all(self.engine)
		self.close_connection()

	def store_db(self, item):
		self.create_connection()
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print(item)
		ins = self.land.insert().values(
			search=item[0],
			reg_number=item[1],
			reg_type=item[2],
			designation=item[3],
			reg_date=item[4],
			close_date=item[5],
			position=item[6],
			owner=item[7],
			created_at=timestamp)
		self.conn.execute(ins)
		self.close_connection()

	def check_duplicate(self, value):
		self.create_connection()
		query = db.select([db.func.count()]).select_from(self.land).where(self.land.columns.search == value)
		result = self.conn.execute(query)
		ResultSet = result.fetchone()
		self.close_connection()
		if ResultSet and ResultSet[0] and ResultSet[0] > 0:
			print("===========================")
			print("Duplicated - %s" % (value))
			print("===========================")
			return True
		else:
			return False

	def close_connection(self):
		try:
			self.conn.close()
			self.engine.dispose()
		except Exception:
			pass
	# Setup options for webdriver
	def setUpOptions(self):
		user_agent = choice(user_agents)['ua']
		# user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'
		self.options = webdriver.FirefoxOptions()
		# self.options.add_option('useAutomationExtension', False)
		self.options.headless = self.headless
		self.options.add_argument(f'user-agent={user_agent}')
		

	# Setup profile with buster captcha solver
	def setUpProfile(self):
		self.profile = webdriver.FirefoxProfile()
		self.profile._install_extension("buster_captcha_solver_for_humans-0.7.2-an+fx.xpi", unpack=False)
		self.profile.set_preference("security.fileuri.strict_origin_policy", False)
		self.profile.set_preference('permissions.default.stylesheet', 2)
		self.profile.set_preference("dom.webdriver.enabled", False)
		self.profile.set_preference('useAutomationExtension', False)
		self.profile.set_preference('devtools.jsonview.enabled', False)
		self.profile.update_preferences()
		

	# Enable Marionette, An automation driver for Mozilla's Gecko engine
	def setUpCapabilities(self):
		self.capabilities = webdriver.DesiredCapabilities.FIREFOX
		self.capabilities['marionette'] = True

	# Setup proxy
	def setUpProxy(self):
		global PROXY_LIST
		print(PROXY_LIST)
		PROXY = choice(PROXY_LIST)
		print(PROXY)
		self.capabilities['proxy'] = {
			"proxyType": "MANUAL",
			"httpProxy": PROXY,
			"ftpProxy": PROXY,
			"sslProxy": PROXY
		}

	# Setup settings
	def setUpAlt(self):
		self.setUpProfile()
		self.setUpOptions()
		self.setUpCapabilities()
		if settings.PROXY_FLAG:
			self.setUpProxy() # comment this line for ignore proxy
		self.driver = webdriver.Firefox(options=self.options, capabilities=self.capabilities, firefox_profile=self.profile)
		
	# Simple logging method
	def log(s,t=None):
			now = datetime.now()
			if t == None :
					t = "Main"
			print ("%s :: %s -> %s " % (str(now), t, s))

	# Use time.sleep for waiting and uniform for randomizing
	def wait_between(self, a, b):
		rand=uniform(a, b) 
		sleep(rand)

	# Using B-spline for simulate humane like mouse movments
	def human_like_mouse_move(self, action, start_element):
		points = [[6, 2], [3, 2],[0, 0], [0, 2]];
		points = np.array(points)
		x = points[:,0]
		y = points[:,1]

		t = range(len(points))
		ipl_t = np.linspace(0.0, len(points) - 1, 100)

		x_tup = si.splrep(t, x, k=1)
		y_tup = si.splrep(t, y, k=1)

		x_list = list(x_tup)
		xl = x.tolist()
		x_list[1] = xl + [0.0, 0.0, 0.0, 0.0]

		y_list = list(y_tup)
		yl = y.tolist()
		y_list[1] = yl + [0.0, 0.0, 0.0, 0.0]

		x_i = si.splev(ipl_t, x_list)
		y_i = si.splev(ipl_t, y_list)

		startElement = start_element

		action.move_to_element(startElement)
		action.perform()

		c = 5 # change it for more move
		i = 0
		for mouse_x, mouse_y in zip(x_i, y_i):
			action.move_by_offset(mouse_x,mouse_y)
			action.perform()
			# self.log("Move mouse to, %s ,%s" % (mouse_x, mouse_y))   
			i += 1    
			if i == c:
				break

	def do_api_captcha(self,driver):
		driver.switch_to.default_content()

		self.log("Get site key")
		site_key_dom = driver.find_element(By.XPATH, '//div[@class="g-recaptcha2"]')
		site_key = site_key_dom.get_attribute("data-sitekey")
		# site_key = '6LdrkCITAAAAANNzQ4LmMMEPcqOpvDnYizGrBOed'
		url = 'https://2captcha.com/in.php?key=%s&method=userrecaptcha&googlekey=%s&pageurl=%s' % (settings.CAPTCHA_API, site_key, driver.current_url)
		print(url)
		apirequest = requests.get(url)
		print(apirequest.content)
		apiresponse = str(apirequest.content.decode("unicode_escape")).split('|')
		print(apiresponse)
		if apiresponse[0]!='OK':
			return False
		
		res_flag = False
		while not res_flag:
			res_url = "https://2captcha.com/res.php?key=%s&action=get&id=%s" % (settings.CAPTCHA_API, apiresponse[1])
			resrequest = requests.get(res_url)
			token = str(resrequest.content.decode("unicode_escape"))
			print(token)
			if token != 'CAPCHA_NOT_READY':
				res_flag = True
			sleep(5)

		if token=='ERROR_CAPTCHA_UNSOLVABLE':
			return False

		token_arr = token.split('|')
		if token_arr[0]!='OK':
			return False

		driver.execute_script('document.getElementById("captchaBean.reCaptcha2Bean.recaptchaResponse").value="%s";' % (token_arr[1]))
		driver.execute_script('document.getElementById("g-recaptcha-response").innerHTML="%s";' % (token_arr[1]))
		# resrequest = requests.get(res_url)
		# print(resrequest)
		# captcha_res = driver.find_element_by_id('g-recaptcha-response')
		# captcha_res.send_keys(token_arr[1])
		print(token_arr[1])
		return True
		# iframes = driver.find_elements_by_tag_name("iframe")

	def do_captcha(self,driver):

		driver.switch_to.default_content()
		self.log("Switch to new frame")
		iframes = driver.find_elements_by_tag_name("iframe")
		driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])

		self.log("Wait for recaptcha-anchor")
		check_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID ,"recaptcha-anchor")))

		self.log("Wait")
		self.wait_between(MIN_RAND, MAX_RAND)  

		action =  ActionChains(driver)
		self.human_like_mouse_move(action, check_box)

		self.log("Click")
		check_box.click() 
	
		self.log("Wait")
		self.wait_between(MIN_RAND, MAX_RAND)  

		self.log("Mouse movements")
		action =  ActionChains(driver)
		self.human_like_mouse_move(action, check_box)

		self.log("Switch Frame")
		driver.switch_to.default_content()
		iframes = driver.find_elements_by_tag_name("iframe")
		driver.switch_to.frame(iframes[2])
		
		self.log("Wait")
		self.wait_between(LONG_MIN_RAND, LONG_MAX_RAND)  

		self.log("Find solver button")
		capt_btn = WebDriverWait(driver, 50).until(
				EC.element_to_be_clickable((By.XPATH ,'//button[@id="solver-button"]'))
				) 

		self.log("Wait")
		self.wait_between(LONG_MIN_RAND, LONG_MAX_RAND)  

		self.log("Click")
		capt_btn.click()

		self.log("Wait")
		self.wait_between(LONG_MIN_RAND, LONG_MAX_RAND)  

		try:
			self.log("Alert exists")
			alert_handler = WebDriverWait(driver, 20).until(
					EC.alert_is_present()
					) 
			alert = driver.switch_to.alert
			self.log("Wait before accept alert")
			self.wait_between(MIN_RAND, MAX_RAND)  

			alert.accept()

			self.wait_between(MIN_RAND, MAX_RAND)  
			self.log("Alert accepted, retry captcha solver")

			self.do_captcha(driver)
		except:
			self.log("No alert")
			
		self.log("Switch")
		driver.switch_to.default_content()

	def thread_process(self, search:str):
		global thread_count
		self.setUpAlt()
		driver = self.driver
		self.log("Start get")
		try:
			driver.get('https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW')
			input1 = driver.find_element_by_id("kodWydzialuInput")
			input2 = driver.find_element_by_id("numerKsiegiWieczystej")
			input3 = driver.find_element_by_id("cyfraKontrolna")
			searchVal = search.split(",")
			# for index in range(len(searchVal[0])):
			# 	input1.send_keys(searchVal[0][index])
			# 	sleep
			input1.send_keys(searchVal[0])
			input2.send_keys(searchVal[1])
			input3.send_keys(searchVal[2])

		except:
			driver.quit()
			thread_count -= 1
			print("connection failed, proxy error")
			filename = 'failed/list.txt'
			with open(filename, 'a') as f:
				f.write(search+'\n')
			return

		
		
		self.log("Wait")
		self.wait_between(MIN_RAND, MAX_RAND)
		try:
			inner_cookie = driver.find_element_by_css_selector('.inner-cookies span.button')
			if inner_cookie:
				inner_cookie.click()
				sleep(2)
		except Exception as err:
			print(err)
			print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
			pass
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
		result = self.do_api_captcha(driver)
		if not result:
			driver.quit()
			thread_count -= 1
			print("Recaptcha failed")
			filename = 'failed/list.txt'
			with open(filename, 'a') as f:
				f.write(search+'\n')
			return
		# exit()
		# self.do_captcha(driver)
		driver.switch_to.default_content()
		self.log("Done")
		
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		firstpage = True
		whileCnt = 0

		try:
			submit = driver.find_element_by_id("wyszukaj")
			# action =  ActionChains(driver)
			# self.human_like_mouse_move(action, submit)
			# print(search)
			# print("network busy")
			submit.click()
			sleep(2)
		except:
			driver.execute_script("document.getElementById('wyszukaj').click();")
			# print('send enter key')
			# input3 = driver.find_element_by_id("cyfraKontrolna")
			# input3.send_keys(searchVal[2])
			# input3.send_keys(Keys.ENTER)
			# print(search)
			sleep(2)
			errResponse = 'failed/responses/' + search + '.html'
			with open(errResponse, 'w') as f:
				f.write(driver.page_source)
		# while firstpage:
		# 	try:
		# 		# enterType = choice([1,2])
		# 		# if enterType==1:
		# 		submit = driver.find_element_by_id("wyszukaj")
		# 		action =  ActionChains(driver)
		# 		self.human_like_mouse_move(action, submit)
		# 		print(search)
		# 		print("network busy")
		# 		submit.click()
		# 		sleep(2)
		# 		# else:
		# 		# 	print('send enter key')
		# 		# 	input3 = driver.find_element_by_id("cyfraKontrolna")
		# 		# 	input3.send_keys(searchVal[2])
		# 		# 	input3.send_keys(Keys.ENTER)
		# 		# 	print(search)
		# 		# 	sleep(3)

		# 		whileCnt += 1
		# 		if whileCnt>20:
		# 			firstpage = False
					
		# 			filename = 'failed/list.txt'
		# 			with open(filename, 'a') as f:
		# 				f.write(search+'\n')
		# 			errResponse = 'failed/responses/' + search + '.html'
		# 			with open(errResponse, 'w') as f:
		# 				f.write(driver.page_source)

		# 			driver.quit()
		# 			thread_count -= 1
		# 			self.getProxies()
		# 			return
		# 		# self.wait_between(LONG_MIN_RAND, LONG_MAX_RAND) 
		# 	except:
		# 		firstpage = False
		# 		pass

		try:
			alerts = driver.find_elements_by_css_selector('p.h7')
			if alerts:
				infos = driver.find_elements_by_css_selector('.section .form-row .left')
				index = 0
				item = [search]
				for info in infos:
					index += 1
					item.append(info.text)
					if index >=7:
						break
				self.store_db(item)
			else:
				nextPageElement = driver.find_elements_by_css_selector('.form-row')
				if nextPageElement and len(nextPageElement)==2:
					self.store_db([search, '','','','','','',''])
				else:
					filename = 'failed/list.txt'
					with open(filename, 'a') as f:
						f.write(search+'\n')
					errResponse = 'failed/responses/' + search + '.html'
					with open(errResponse, 'w') as f:
						f.write(driver.page_source)

		except:
			filename = 'failed/list.txt'
			with open(filename, 'a') as f:
				f.write(search+'\n')
			errResponse = 'failed/responses/' + search + '.html'
			with open(errResponse, 'w') as f:
				f.write(driver.page_source)
			pass
		
		try:
			nextpagebtn = driver.find_element_by_id("przyciskWydrukZupelny")
			nextpagebtn.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData = content
			nexttab = driver.find_element(By.XPATH, '//table[@id="nawigacja"]/tbody/tr/td[2]/form/input[@type="submit"]')
			nexttab.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData += content
			nexttab = driver.find_element(By.XPATH, '//table[@id="nawigacja"]/tbody/tr/td[3]/form/input[@type="submit"]')
			nexttab.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData += content
			nexttab = driver.find_element(By.XPATH, '//table[@id="nawigacja"]/tbody/tr/td[4]/form/input[@type="submit"]')
			nexttab.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData += content
			nexttab = driver.find_element(By.XPATH, '//table[@id="nawigacja"]/tbody/tr/td[5]/form/input[@type="submit"]')
			nexttab.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData += content
			nexttab = driver.find_element(By.XPATH, '//table[@id="nawigacja"]/tbody/tr/td[6]/form/input[@type="submit"]')
			nexttab.click()
			sleep(1)
			content = driver.find_element_by_id("contentDzialu").get_attribute('innerHTML')
			htmlData += content
			filename = 'results/' + search + '.html'
			with open(filename, 'w') as f:
				f.write(htmlData)

		except:
			pass
		driver.quit()
		thread_count -= 1

	def getProxies(self):
		global PROXY_LIST

		with open('proxies.txt', 'r') as f:
			for line in f:
				PROXY_LIST.append(line.strip())
		# proxy_content = requests.get("http://pubproxy.com/api/proxy?format=txt&limit=10")
		# proxy_txt = proxy_content.content.decode("unicode_escape")
		# PROXY_LIST = proxy_txt.split("\n")

	# Main function  
	def test_run(self):
		self.create_table()
		global thread_count
		global user_agents
		self.getProxies()

		ua_file = 'uas.json'
		logpath = "results"
		Path(logpath).mkdir(parents=True, exist_ok=True)
		failedpath = "failed"
		Path(failedpath).mkdir(parents=True, exist_ok=True)
		failedResppath = "failed/responses"
		Path(failedResppath).mkdir(parents=True, exist_ok=True)

		with open(ua_file, 'r') as f:
			user_agents = json.load(f)

		searchList = []
		with open('list.txt', 'r') as clist:
			for x in clist:
				searchList.append(x.strip())
		index = 0
		while index < len(searchList):
			if thread_count < thread_limit:
				search = searchList[index]
				print(search)
				if self.check_duplicate(search):
					index += 1
					continue
				x = threading.Thread(target=self.thread_process, args=(str(search), ))
				x.start()
				thread_count += 1
				index += 1


	def tearDown(self):
		self.wait_between(21.13, 31.05) 

if __name__ == "__main__":
	# warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
	service = SyncMe()
	service.test_run()
