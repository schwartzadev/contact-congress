import requests
import logging
from bs4 import BeautifulSoup
import re
import sys
import os
from lxml import etree

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    # level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_via_clerk():
    URL = 'http://clerk.house.gov/member_info/ttd.aspx'
    html_doc = requests.get(URL).text

    soup = BeautifulSoup(html_doc, 'html.parser')

    table = soup.find("table")
    yml_data = ''
    for row in table.findAll("tr"):
        # logger.debug(row)
        tds = row.findAll("td")
        if len(tds) != 0:
            if len(row.findAll("strong")) == 1 and len(row.findAll("em")) == 1:
                party = 'Commissioner/Delegate'
            elif len(row.findAll("em")) == 1:
                party = 'D'
            else:
                party = 'R'
            name = tds[0].text
            state = tds[1].text
            district = tds[2].text

            # logger.debug(district)
            if district not in ['At Large', 'Delegate', 'Resident Commissioner']:
                district = re.sub('[^0-9]','', tds[2].text)

            phone = '(202)' + tds[3].text
            room_num = tds[4].text
            if len(room_num) == 3:
                room = '{} Cannon'.format(room_num)
            elif len(room_num) == 4 and room_num[0] == '1':
                room = '{} Longworth'.format(room_num)
            elif len(room_num) == 4 and room_num[0] == '2':
                room = '{} Rayburn'.format(room_num)
            else:
                room = 'NO ROOM'

            info = """
      - name: {}
        state: {}
        district: {}
        party: {}
        room: {}
        phone: {}
        committee: 
            """.format(name, state, district, party, room, phone)
            yml_data += info
            # logger.debug('{} ems = {}'.format(name, len(ems)))
            # logger.debug('{}\t{}\t{}\t{}'.format(name, state, district, phone))
    # logger.debug(yml_data)
    with open(os.path.join(sys.path[0], "hor.yml"), 'w', encoding='utf-8') as f:
        print(yml_data, file=f)

    # with open('house.yml', 'w') as f:
    #     f.write('Hello\n')
    logger.info("saved!")

def get_via_house_gov():
    URL = 'https://www.house.gov/representatives'
    html_doc = requests.get(URL).text

    soup = BeautifulSoup(html_doc, 'html.parser')
    tables = soup.findAll("table")

    rows = []
    for table in tables[56:81]:
        for row in table.findAll("tr"):
            # logger.debug(row.prettify())
            tds = row.findAll("td")
            if len(tds) != 0:
                rows.append(row)
    # logger.debug(rows)
    yml_data = '---\n'
    for row in rows:
        tds = row.findAll("td")
        name = tds[0].text

        state_district = tds[1].text.split(' ')
        state_district = list(filter(None, state_district))
        if state_district[-2] == 'At' and state_district[-1] == 'Large':
            district = 'At Large'
            state_district.pop()
            state_district.pop()
        elif state_district[-2] == 'Resident' and state_district[-1] == 'Commissioner':
            district = 'Resident Commissioner'
            state_district.pop()
            state_district.pop()        	
        else:
            district = state_district[-1]
            state_district.pop()
        state = ' '.join(state_district)
        # logger.debug('{}     {}'.format(district, state))
        if district not in ['At Large', 'Delegate', 'Resident Commissioner']:
            district = re.sub('[^0-9]','', district)

        party = tds[2].text

        room = tds[3].text
        room_num = re.sub('[^0-9]','', room)
        if len(room_num) == 3:
            room = '{} Cannon'.format(room_num)
        elif len(room_num) == 4 and room_num[0] == '1':
            room = '{} Longworth'.format(room_num)
        elif len(room_num) == 4 and room_num[0] == '2':
            room = '{} Rayburn'.format(room_num)
        else:
            room = 'NO ROOM'

        phone = tds[4].text

        committee = tds[5].findAll('li')
        committee_list = [c.text for c in committee]
        committee_info = ', '.join(committee_list)
        # logger.debug(committee_info)

        info = """
  - name: {}
    state: {}
    district: {}
    party: {}
    room: {}
    phone: {}
    committee: {}
            """.format(name, state, district, party, room, phone, committee_info)
        yml_data += info
    logger.debug(yml_data)
    file_name = "hor.yml"
    with open(os.path.join(sys.path[0], file_name), 'w', encoding='utf-8') as f:
        print(yml_data, file=f)
    logger.info('saved to {}'.format(file_name))

def get_senate_info():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36',
    }

    xml_doc = requests.get('https://www.senate.gov/general/contact_information/senators_cfm.xml', headers=headers)
    # logger.debug(xml_doc.text)
    root = etree.fromstring(xml_doc.text.replace('<?xml version="1.0" encoding="UTF-8"?>', ''))

    yml_info = '---\n'
    for s in root.findall('member'):
        full = s.find('member_full').text
        last = s.find('last_name').text
        first = s.find('first_name').text
        party = s.find('party').text
        state = s.find('state').text
        address = s.find('address').text
        phone = s.find('phone').text
        email = s.find('email').text
        website = s.find('website').text

        info = """
  - name: {}
    last: {}
    firstname: {}
    party: {}
    location: {}
    address: {}
    phone: {}
    contact: {}
    website: {}   
        """.format(full, last, first, party, state, address, phone, email, website)
        yml_info += info

    # logger.debug(yml_info)
    file_name = 'senators.yml'
    with open(os.path.join(sys.path[0], file_name), 'w', encoding='utf-8') as f:
        print(yml_info, file=f)
    logger.info('saved to {}'.format(file_name))
        

get_via_house_gov()
get_senate_info()
