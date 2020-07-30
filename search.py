# https://github.com/teal33t/captcha_bypass
# Dont use this code for spy and 
import os
from os import listdir
from os.path import isfile, join
from pathlib import Path
import cgi
from datetime import datetime
from time import sleep, time
from random import uniform, randint

import sqlalchemy as db
import settings

arguments = cgi.FieldStorage()
keyword = arguments.getvalue('keyword')
if keyword is None or keyword=='':
	print('Please give a keyword.')
	exit()

logpath = "results"
result_path = 'search_results'
Path(result_path).mkdir(parents=True, exist_ok=True)

host = settings.MYSQL_HOSTNAME
user = settings.MYSQL_USERNAME
password = settings.MYSQL_PASSWORD
dbname = settings.MYSQL_DATABASE
engine = db.create_engine('mysql+mysqldb://%s:%s@%s/%s?charset=utf8' % (user, password, host, dbname))
dbconnection = engine.connect()
metadata = db.MetaData()

table = db.Table('land_info', metadata, autoload=True, autoload_with=engine)
query = db.select([table.columns.search]).where(db.or_(table.columns.reg_type.ilike('%'+keyword+'%'), table.columns.designation.ilike('%'+keyword+'%'), table.columns.position.ilike('%'+keyword+'%'), table.columns.owner.ilike('%'+keyword+'%')))
ResultProxy = dbconnection.execute(query)
ResultSet = ResultProxy.fetchall()

file_result = []
logfiles = [f for f in listdir(logpath) if isfile(join(logpath, f))]
for logfile in logfiles:
	filename = join(logpath, logfile)
	with open(filename, 'r') as f:
		content = f.read()
		if content.find(keyword) > -1:
			file_result.append(os.path.splitext(logfile)[0])

if len(ResultSet) > 0 or len(file_result)>0:
	filename = join(result_path, keyword)
	if os.path.exists(filename):
		os.remove(filename)
	with open(filename, 'w') as f:
		if len(ResultSet) > 0:
			f.write('----------- From Database -------------\n')
			for dbrow in ResultSet:
				f.write(dbrow[0] +'\n')

		if len(file_result) > 0:
			f.write('----------- From files -------------\n')
			for keyword in file_result:
				f.write(keyword +'\n')