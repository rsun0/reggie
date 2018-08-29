# -*- coding: utf-8 -*-

import time
import json
import argparse
from bs4 import BeautifulSoup
import urllib3
import certifi

parser = argparse.ArgumentParser()
parser.add_argument('-t', dest='test', action='store_true', default=False)
parser.add_argument('-w', dest='winlocal', action='store_true', default=False)
parser.add_argument('-l', dest='linlocal', action='store_true', default=False)
parser.add_argument('-s', dest='sms', action='store_true', default=False)
parser.add_argument('-b', dest='brief', action='store_true', default=False)
args = parser.parse_args()

if args.winlocal:
    import win32api
if args.linlocal:
    import tkinter as tk
    from tkinter import messagebox
if args.sms:
    from twilio.rest import Client

class CourseScraper:
    URL_ROOT = 'https://courses.illinois.edu/schedule'
    HTTP = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    if args.linlocal:
        ALERT_ROOT = tk.Tk()
        ALERT_ROOT.withdraw()
    if args.sms:
        TWILIO_CLIENT = Client('AC494daf76b092345792ef2a93a4414f2c', '6cd7dfd1c98cbe02c77b1a5cce8f5cb0')
        FROM = '+12244073342'
    loop_iteration = 0

    @staticmethod
    def loop(scrapers):
        if args.brief:
            successes = 0
            fails = 0
        while True:
            CourseScraper.loop_iteration += 1
            if not args.brief:
                print('Checking #' + str(CourseScraper.loop_iteration) + '...')
            for s in scrapers:
                try:
                    s.check_avail()
                    if args.brief:
                        successes += 1
                except Exception as e:
                    if args.brief:
                        fails += 1
                    try:
                        CourseScraper.send_error(e)
                    except Exception:
                        pass
            if not args.brief:
                print('Done.')
            elif (CourseScraper.loop_iteration) % (12 * 60) == 0:
                print("Iterations: " + str(CourseScraper.loop_iteration))
                print('Successes: ' + str(successes))
                print('Fails: ' + str(fails))
            time.sleep(60)

    def __init__(self, year, season, major, num, crns=[]):
        self.url = '/'.join([self.URL_ROOT, str(year), str(season), str(major), str(num)])
        self.name = str(major) + ' ' + str(num)
        self.crns = {c:0 for c in crns}

    def send_alert(self, crn, avail):
        self.crns[crn] = CourseScraper.loop_iteration
        alert = self.name + ' (' + str(crn) + ') is ' + avail
        print(alert)
        if args.winlocal:
            win32api.MessageBox(0, alert, 'Reggie', 0x00001030)
        if args.linlocal:
            messagebox.showwarning('Reggie', alert)
        if args.sms:
            self.TWILIO_CLIENT.api.account.messages.create(to='+16304482388', from_=CourseScraper.FROM, body=alert)
            # self.TWILIO_CLIENT.api.account.messages.create(to='+19135446871', from_='+12242316794', body=alert)

    @staticmethod
    def send_error(e):
        print(e)
        if args.sms:
            CourseScraper.TWILIO_CLIENT.api.account.messages.create(to='+16304482388', from_=CourseScraper.FROM, body=str(e))

    def is_avail(self, crn, avail):
        if crn in self.crns and avail != 'Closed' and avail != 'UNKNOWN':
            return self.crns[crn] == 0 or self.crns[crn] <= CourseScraper.loop_iteration - 10
        return False

    def check_avail(self):
        page = self.retrieve_page()
        data = self.process_page(page)
        for crn, avail in data.items():
            if self.is_avail(crn, avail):
                self.send_alert(crn, avail)

    def retrieve_page(self):
        while True:
            response = self.HTTP.request('GET', self.url)
            if response.status == 200:
                break
            time.sleep(1)
        return response.data.decode('utf-8')

    def process_page(self, data):
        soup = BeautifulSoup(data, 'lxml')
        js = soup.find(type='text/javascript')
        fields = self.parse_js(js.string)
        statuses = self.extract_status(fields)
        return statuses

    def parse_js(self, js):
        dataline = js.split('\n', 2)[1]
        openbracket = dataline.find('[')
        assert(dataline[:openbracket] == '    var sectionDataObj = ')
        closebracket = len(dataline) - 1
        jsonblock = dataline[openbracket:closebracket]
        return json.loads(jsonblock)

    def extract_status(self, jsonlist):
        statuses = {int(o['crn']):o['availability'] for o in jsonlist}
        return statuses

if __name__ == '__main__':
    if args.test:
        # cs374 = CourseScraper(2018, 'spring', 'CS', 374, [65088, 67005, 65089])
        engl = CourseScraper(2018, 'fall', 'ENGL', 251, [40995])
    else:
        # cs374 = CourseScraper(2018, 'spring', 'CS', 374, [65088, 67005])
        # atms120 = CourseScraper(2018, 'spring', 'ATMS', 120, [39412])
        # anth103 = CourseScraper(2018, 'spring', 'ANTH', 103, [54206])
        engl = CourseScraper(2018, 'fall', 'ENGL', 266, [61869, 61905])
    CourseScraper.loop([engl])