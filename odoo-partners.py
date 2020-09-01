#!/usr/bin/env python3

from bs4 import BeautifulSoup  # HTML data structure
from urllib.request import urlopen as uReq  # Web client
from multiprocessing.dummy import Pool
from requests import get as http_get
from requests import post as http_post
import csv, time
import threading
import logging
import urllib3

try:
    to_unicode = unicode
except NameError:
    to_unicode = str
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from configs import headers, TIMEOUT, base_url, print_info

logging.basicConfig(
	handlers=[logging.FileHandler('app.log', 'w', 'utf-8')],
	format='%(name)s - %(levelname)s - %(message)s', 
	datefmt='%Y-%m-%d-%H:%M',
	level=logging.INFO # CRITICAL ERROR WARNING  INFO    DEBUG    NOTSET 
)

fn_odoo_partners_csv = "output/odoo-partners.csv"
fn_odoo_partners_gold_csv = "output/odoo-partners-gold.csv"
fn_odoo_partners_silver_csv = "output/odoo-partners-silver.csv"
fn_odoo_partners_ready_csv = "output/odoo-partners-ready.csv"

class Partner:
	def __init__(self):
		self.ttype = " "
		self.name = " "
		self.address = " "
		self.telephone = " "
		self.website = " "
		self.email = " "

def grab_partner(partner_link):
	partner = Partner()
	response = http_get(partner_link, headers=headers(), timeout=TIMEOUT)
	partner_soup = BeautifulSoup(response.text, 'html.parser')
	try:
		partner_type = partner_soup.find('h3', {"class": "col-lg-12 text-center text-muted"}).getText()
		partner.ttype = partner_type[1:] # remove first item
	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))

	try:
		partner.name = partner_soup.find('h1', {"id": "partner_name"}).getText()
		partner.name = partner.name.replace(';', ' - ')
	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))
	#logging.info("[+]Type: {}, Partner Name: {}".format(partner.ttype, partner.name))

	try:
		partner.address = partner_soup.find('span', {"itemprop": "streetAddress"}).getText()
		partner.address = partner.address.replace(';', ' - ')

	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))

	try:
		partner.telephone = partner_soup.find('span', {"itemprop": "telephone"}).getText()
		partner.telephone = partner.telephone.replace(';', ' - ')
	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))
	
	try:
		partner.website = partner_soup.find('span', {"itemprop": "website"}).getText()
		partner.website = partner.website.replace(';', ' - ')
	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))
	
	try:
		partner.email = partner_soup.find('span', {"itemprop": "email"}).getText()
		partner.email = partner.email.replace(';', ' - ').replace('\"', '')
	except Exception as e:
		logging.warning("[-] {}: {}".format(partner.name, e))
	
	with open(fn_odoo_partners_csv, 'a+', newline='', encoding='utf-8') as g:
		file_writer = csv.writer(g, delimiter=';', dialect='excel')
		file_writer.writerow([partner.ttype, partner.name, partner.address, partner.telephone, partner.website, partner.email,])
		g.close()

class GrabPartnerThread(threading.Thread):
	def __init__(self, partner_link):
		threading.Thread.__init__(self)
		self.partner_link = partner_link
	def run(self):
		grab_partner(self.partner_link)
 
def init_files():
	with open(fn_odoo_partners_csv, 'a+', newline='', encoding='utf-8') as o:
		file_writer = csv.writer(o, delimiter=';', dialect='excel')
		file_writer.writerow(['Type', 'Name', 'Address', 'Telephone', 'Website', 'Email',])
		o.close()

def get_partner_links():
	page_nos = [ x for x in range(1, 36)]
	partners = []
	partner_links = []
	for page_no in page_nos:
		# https://www.odoo.com/partners/page/1?country_all=True
		main_url = "%(base_url)s/partners/page/%(page_no)s?&country_all=True" % dict(base_url=base_url, page_no=page_no)
		response = http_get(main_url, headers=headers(), timeout=TIMEOUT)
		site_soup = BeautifulSoup(response.text, 'html.parser')

		for all_sites in site_soup.findAll('div', {"class": "media-body o_partner_body"}):
			site = all_sites.find('a')
			partner_links.append("%(base_url)s%(href)s" % dict(base_url=base_url, href=site.get('href')))
	return partner_links
if __name__ == '__main__':
	init_files()
	logging.info("[+] Starts gathering Partner Links")
	partner_links = get_partner_links()
	logging.info("[+] Odoo Partners Link Grabbed: {}".format(len(partner_links)))
	# for partner_link in partner_links:
	# 	thread1 = GrabPartnerThread(partner_link=partner_link)
	# 	thread1.start()
	threads = Pool(5)
	thread = threads.map(grab_partner, partner_links)
	logging.info("[+] Threading Done")