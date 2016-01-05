#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
Copyright 2015, Luis Javier Gonzalez (luis.j.glez.devel@gmail.com)

This program is licensed under the GNU GPL 3.0 license.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import requests, json, getopt, sys, os

# INITIAL CHECK AND SETUP

BASE_PATH = os.getenv("HOME", "/usr/tmp")
UTOOLS_PATH = "/.utools"
UCHECK_PATH = "/ucheck"
DB_PATH = BASE_PATH + UTOOLS_PATH + UCHECK_PATH
DB_NAME = "default"
USERS_DB = DB_PATH + "/" + DB_NAME + ".db"
try:
	f = open(USERS_DB,"a")
	f.write("\n")
	f.close()
except:
	try:
		os.makedirs(DB_PATH)
	except:
		pass
	f = open(USERS_DB,"w")
	f.write("{}")
	f.close()

# DATABASE FUNCTIONS

#db specs:
#   {"User": 
#      [last_submision_in_database, 
#      {problem1id: verdict, ...}, 
#      userid], 
#   "User2": 
#      [...], ...}

def load_db():
	try:
		DBF = open(USERS_DB)
		DB = json.load(DBF)
		DBF.close()
	except:
		DB = {}
	return DB

def update_db(DB):
	print "Updating database..."
	try:
		
		DBF = open(USERS_DB, "w")
		DBF.write(json.dumps(DB))
		DBF.close()
		print "Done"
	except:
		print "Error: writting to the database permission denied" #1
		exit(1)

# DATA RETRIEVAL AND COMPARISON FUNCTIONS

def get_user_data(username):
	try:
		d=requests.get("http://uhunt.felix-halim.net/api/uname2uid/"+str(username))
		userid = int(d.text)
		d=requests.get("http://uhunt.felix-halim.net/api/subs-user/"+str(userid)+"/")
		probs = d.json()["subs"]
	except:
		print "Error: network failure" #2
		exit(2)
	user = [0, {}, int(userid)]
	for sub in probs:
		if user[0] < sub[0]:
			user[0] = sub[0]
		if sub[1] in user[1].keys():
			if sub[2] > user[1][sub[1]]:
				user[1][sub[1]] = int(sub[2])
		else:
			user[1][sub[1]] = int(sub[2])
	return user

def check_new_ac(DB):
	changes = 0
	for u in DB.keys():
		try:
			d=requests.get("http://uhunt.felix-halim.net/api/subs-user/"+str(DB[u][2])+"/"+str(DB[u][0]))
			probs = d.json()["subs"]
		except:
			print "Error: network failure" #2
			exit(2)
		for sub in probs:
			notif = 0
			if DB[u][0] < sub[0]:
				DB[u][0] = sub[0]
			if sub[1] in DB[u][1].keys():
				if int(sub[2]) > DB[u][1][sub[1]]:
					DB[u][1][sub[1]] = int(sub[2])
					notif = 1
			else:
				DB[u][1][sub[1]] = int(sub[2])
				notif = 1
			if notif == 1:
				changes = 1
				if DB[u][1][sub[1]] == 90:
					notify_ac(u, sub[1])
	if changes:
		update_db(DB)
	return changes

# NOTIFICATION SYSTEM
# separated from previous function in order to allow easy integration with dbus for popup notifications
# actually unimplemented

def notify_ac(user, probid):
	try:
		d = requests.get("http://uhunt.felix-halim.net/api/p/id/"+str(probid))
		num = d.json()["num"]
		print "%s solved problem # %s" % (str(user), str(num))
	except:
		print "Error: network failure" #2
		exit(2)

# ARGUMENTS PARSING

opts, args = getopt.getopt(sys.argv[1:], "a:r:hd:", ["add_check=", "remove_check=", "help", "database="])
add = []
delete = []
update = 0
for o, a in opts:
	if o in ("-d","--database"):
		DB_NAME = a
		USERS_DB = DB_PATH + "/" + DB_NAME +".db"
	if o in ("-a","--add_check"):
		add.append(a)
		update = 1
	if o in ("-r","--remove_check"):
		delete.append(a)
		update = 1
	if o in ("-h","--help"):
		print "Usage: ucheck [-a username] [-r username] [-d database] [-h]" #0
		exit(0)

# DB LOAD AND MODIFICATION

DB = load_db()
print "Database: %r" % DB_NAME

if update:
	for el in add:
		print "Adding %s..." % el
		DB[el] = get_user_data(el)
	for el in delete:
		print "Removing %s..." % el
		try:
			del DB[el]
		except:
			print "Warning: %s not in database" % el
	update_db(DB)

# MAIN ACTION

print "Checking:",
first = 1
for el in DB.keys():
	if first:
		first = 0
	else:
		print "&",
	print "%s" % el,
print ""

if check_new_ac(DB) == 0:
	print "No new solved problems"
