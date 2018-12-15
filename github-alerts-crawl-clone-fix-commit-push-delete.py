import os, sys, unittest, time, re, requests
from bs4 import BeautifulSoup
import traceback

import json
import hashlib
import urllib.error
from urllib.request import Request, urlopen, build_opener, install_opener, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm
from lxml import etree
import csv
import time
import logging
from datetime import date, timedelta
import subprocess
from requests import session
import pprint as pp
import re

import argparse
import constants

USER = constants.GITHUB_ID
PASSWORD = constants.GITHUB_PASS
GITHUB_SESSION_URL = 'https://github.com/session'

def clone(notification_url):
	url = notification_url.replace('/network/alerts','')
	time.sleep(2)
	subprocess.call(["git", "clone", url, "mypyrepos/" + url.split('/')[-1]])

def get_alert_urls(s, notification_url):
	alert_urls = []
	get_noti_page_resp = s.get(notification_url)
	html_source = get_noti_page_resp.text
	try:
		parsed_html = BeautifulSoup(html_source, 'html.parser')
		alerts_links = parsed_html.select("li div.d-table div.float-left a.v-align-middle")
		for alerts_link in alerts_links:
			alert_urls.append("https://github.com" + alerts_link['href'])
	except urllib.error.URLError as e:
		print("Seems URL changed for: " + notification_url)
		print(e)
	except Exception as e:
		print("Unknown Error: " + notification_url)
		print(e)
	return alert_urls

def get_alert_message(s, alert_url):
	get_noti_page_resp = s.get(alert_url)
	html_source = get_noti_page_resp.text
	try:
		parsed_html = BeautifulSoup(html_source, 'html.parser')
		message_p = parsed_html.find_all("p")
		return ' '.join(message_p[0].text.split()).replace('\n','').strip()
	except urllib.error.URLError as e:
		print("Seems URL changed for: " + alert_url)
		print(e)
	except Exception as e:
		print("Unknown Error: " + alert_url)
		print(e)

def review(url):
	with open('review_cmds.sh', 'a') as f:
		f.write("cd $(echo $PWD'/mypyrepos/" + url.split('/')[-1] + "')\n")
		f.write("git status\n")
		f.write("git add requirements.txt\n")
		f.write("git status\n")
		f.write("git diff --cached\n")
		f.write("echo '===" + url.split('/')[-1] + " done==='\n")
		f.write("cd ../..\n")

def commit_push(url):
	with open('commit_push_cmds.sh', 'a') as f:
		f.write("cd $(echo $PWD'/mypyrepos/" + url.split('/')[-1] + "')\n")
		f.write("git status\n")
		f.write("git add requirements.txt\n")
		f.write("git status\n")
		f.write("git commit -m \"addressing security vulnerabilities\"\n")
		f.write("git status\n")
		f.write("git push\n")
		f.write("git status\n")
		f.write("echo '===" + url.split('/')[-1] + " done==='\n")
		f.write("cd ../..\n")

def delete_clones(url):
	with open('delete_clones_cmds.sh', 'a') as f:
		f.write("rm -rf $(echo $PWD'/mypyrepos/" + url.split('/')[-1] + "')\n")

def delete_shell_scripts():
	for f in os.listdir('.'):
		if os.path.splitext(f)[1] == '.sh':
			os.unlink(f)

def main():
	delete_shell_scripts()
	time.sleep(5)
	notification_urls = []
	with open('repo-notifications-list.csv','r') as f:
		notification_urls = f.readlines()

	with session() as s:
		req = s.get(GITHUB_SESSION_URL).text
		html = BeautifulSoup(req, 'html.parser')
		token = html.find("input", {"name": "authenticity_token"}).attrs['value']
		com_val = html.find("input", {"name": "commit"}).attrs['value']

		login_data = {
			'login': USER,
			'password': PASSWORD,
			'commit' : com_val,
			'authenticity_token' : token
		}

		login_resp = s.post(GITHUB_SESSION_URL, data = login_data)
		print('login success = ', login_resp)

		for notification_url in notification_urls:
			notification_url = notification_url.replace('\n','').strip()
			clone(notification_url)

		time.sleep(10)
		for notification_url in notification_urls:
			try:
				notification_url = notification_url.replace('\n','').strip()
				repo_url = notification_url.replace('/network/alerts','')
				repo_name = repo_url.split('/')[-1]
				alert_urls = get_alert_urls(s, notification_url.strip())
				for alert_url in alert_urls:
					print(notification_url, "==>", get_alert_message(s, alert_url.strip()))
					alert_msg = get_alert_message(s, alert_url.strip())
					parts = alert_msg.split(' ')
					pkg, ver = parts[1], parts[4]
					print("FULL PASS SEARCH REPLACE FOR:", pkg)

					with open( "mypyrepos/" + repo_name + '/requirements.txt','r') as f:
						with open( "mypyrepos/" + repo_name + '/requirements2.txt','w') as f2:
							lines = f.readlines()
							for line in lines:
								if line.find(pkg) >= 0:
									f2.write(re.sub(r'== .*', r'== ' + ver, line.rstrip())+'\n')
								else:
									f2.write(line.replace('\n','').strip()+'\n')
							print()
						print()

					os.unlink("mypyrepos/" + repo_name + '/requirements.txt')
					os.rename("mypyrepos/" + repo_name + '/requirements2.txt', "mypyrepos/" + repo_name + '/requirements.txt')

				review(repo_url)
				commit_push(repo_url)
				delete_clones(repo_url)
			except Exception as e:
				traceback.print_exc()
				print("Probably not a python repo", e)

if __name__ == '__main__':
	main()
