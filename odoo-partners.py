#!/usr/bin/env python3

from bs4 import BeautifulSoup  # HTML data structure
from urllib.request import urlopen as uReq  # Web client
import csv, time
import threading
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

fn_odoo_partners_csv = "output/odoo-partners.csv"
fn_odoo_partners_gold_csv = "output/odoo-partners-gold.csv"
fn_odoo_partners_silver_csv = "output/odoo-partners-silver.csv"
fn_odoo_partners_ready_csv = "output/odoo-partners-ready.csv"

base_url = "https://www.odoo.com"

class Partner:
	def __init__(self):
		self.ttype = ""
		self.name = ""
		self.address = ""
		self.telephone = ""
		self.website = ""
		self.email = ""


class GrabPartnerThread(threading.Thread):
	def __init__(self, partner_link):
		threading.Thread.__init__(self)
		self.partner_link = partner_link
	def run(self):
		partner = Partner()
		partner_page = uReq(self.partner_link)
		partner_soup = BeautifulSoup(partner_page, 'html.parser')
		partner_page.close()

		partner_type = partner_soup.find('h3', {"class": "col-lg-12 text-center text-muted"}).getText()
		partner.ttype = partner_type[1:] # remove first item
		
		partner.name = partner_soup.find('h1', {"id": "partner_name"}).getText().replace(';', ', ')
		
		try:
			address = partner_soup.find('span', {"itemprop": "streetAddress"}).getText()
			partner.address = address.replace(';', ', ')
		except Exception as e:
			logging.warning("{}: {}".format(partner.name, e))

		try:
			partner.telephone = partner_soup.find('span', {"itemprop": "telephone"}).getText()
		except Exception as e:
			logging.warning("{}: {}".format(partner.name, e))
		
		try:
			partner.website = partner_soup.find('span', {"itemprop": "website"}).getText()
		except Exception as e:
			logging.warning("{}: {}".format(partner.name, e))
		
		try:
			partner.email = partner_soup.find('span', {"itemprop": "email"}).getText()
		except Exception as e:
			logging.warning("{}: {}".format(partner.name, e))
		
		with open(fn_odoo_partners_csv, 'a+') as g:
			file_writer = csv.writer(g, delimiter=';')
			file_writer.writerow((partner.ttype, partner.name, partner.address, partner.telephone, partner.website, partner.email,))
			g.close()
 
def init_files():
	with open(fn_odoo_partners_csv, 'a+') as o:
		file_writer = csv.writer(o, delimiter=';')
		file_writer.writerow(('Type', 'Name', 'Address', 'Telephone', 'Website', 'Email',))
		o.close()

if __name__ == '__main__':
	init_files()
	page_nos = [ x for x in range(1, 36)]
	partners = []
	partner_links = []
	for page_no in page_nos:
		# https://www.odoo.com/partners/page/1?country_all=True
		temp = "%(base_url)s/partners/page/%(page_no)s?&country_all=True" % dict(base_url=base_url, page_no=page_no)
		url = uReq(temp)
		site_soup = BeautifulSoup(url.read(), 'html.parser')
		url.close()

		for all_sites in site_soup.findAll('div', {"class": "media-body o_partner_body"}):
			site = all_sites.find('a')
			partner_link = base_url + site.get('href')
			partner_links.append(partner_link)
			thread1 = GrabPartnerThread(partner_link)
			thread1.start()
		time.sleep(3)