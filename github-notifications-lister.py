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
import base64
import argparse
import constants
import json

headers = {'Authorization': 'token %s' % constants.GITHUB_API_TOKEN}

def get_notifications():
	with open('repo-notifications-list.csv', 'w') as f:
		try:
			url = "https://api.github.com/notifications" #users/ishandutta2007/repos?page="
			time.sleep(1)
			r = requests.get(url, headers=headers)
			if r.ok:
				repo_items = json.loads(r.text or r.content)
				for ctr, repo_item in enumerate(repo_items):
					if repo_item['reason']=='security_alert' or repo_item['subject']['type']=='RepositoryVulnerabilityAlert':
						alerts_url = repo_item['repository']['html_url'] + '/network/alerts'
						print(ctr, repo_item['subject']['title'], alerts_url)
						f.write("%s\n" % alerts_url)
			else:
				print(r)
		except Exception:
			traceback.print_exc()

def main():
	get_notifications()

if __name__ == '__main__':
  main()
