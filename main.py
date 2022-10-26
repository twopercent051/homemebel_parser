import logging
import json
import os
import csv
import requests
import lxml

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from transliterate import translit

file_log = logging.FileHandler("logger.log")
console_out = logging.StreamHandler()
logging.basicConfig(handlers=(file_log, console_out), level=logging.INFO)

def correct_name(name):
    forbidden_symbols = ['/', '\\', '|']
    for c in forbidden_symbols:
        if c in name:
            name = name.replace(c, '_')
    return name

def get_main_categories():
    url = 'https://mayamebel.ru/catalog/'
    useragent = UserAgent()
    headers = {
        "Accept": "*/*",
        "User-Agent": useragent.random
    }
    session = requests.Session()
    retry = Retry(connect=100, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    req = session.get(url=url, headers=headers)
    src = req.text
    soup = BeautifulSoup(src, 'lxml')

    catalog_list = soup.find(class_='wd-nav-vertical')
    items = catalog_list.find_all(class_='menu-item-object-product_cat')
    categoty_dict = {}
    for item in items:
        item_name = item.text
        trans_categories = translit(item_name, language_code='ru', reversed=True).replace(' ', '_').lower()
        item_href = item.find(class_='woodmart-nav-link').get('href')
        categoty_dict[trans_categories] = item_href
    with open('/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/main_categories.json', 'w',
              encoding='utf-8') as file:
        json.dump(categoty_dict, file, indent=4, ensure_ascii=False)

def create_directories():
    with open('/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/main_categories.json') as file:
        all_categories = json.load(file)
    for name_category, href_category in all_categories.items():
        if not os.path.exists(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}'):
            os.mkdir(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}')
        if not os.path.exists(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/images'):
            os.mkdir(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/images')

def get_photo(url, category, img_name):
    session = requests.Session()
    retry = Retry(connect=100, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    directory = f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{category}/images'
    img_data = session.get(url).content
    with open(f'{directory}/{img_name}', 'wb') as handler:
        handler.write(img_data)

def get_card_info(item_category, item_name, item_href):
    print(f'Начинаем парсить позицию {item_name}')
    url = item_href
    useragent = UserAgent()
    headers = {
        "Accept": "*/*",
        "User-Agent": useragent.random
    }
    session = requests.Session()
    retry = Retry(connect=100, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    req = session.get(url=url, headers=headers)
    src = req.text
    soup = BeautifulSoup(src, 'lxml')

    img_block = soup.find(class_='woocommerce-product-gallery__wrapper').find_all('figure')
    item_dict = {}
    photo_list = []
    photo_counter = 0
    for image in img_block:
        photo_counter += 1
        print(f'Сохраняем {photo_counter}/{len(img_block)} фото')
        img_href = image.find('a').get('href')
        img_name = '_'.join(img_href.split('/')[5:])
        img_upload_href = f'https://homemebel72.ru/wp-content/uploads/{img_name}'
        photo_list.append(img_upload_href)
        get_photo(url=img_href, category=item_category, img_name=img_name)
    try:
        description = soup.find(class_='woocommerce-product-details__short-description').text.strip()
    except:
        description = ''
    char = str(soup.find(class_='wc-tab-inner').find('div')).replace('\n', '').replace('<div class="">', '').\
        replace('</div>', '').strip()
    char1 = char.replace('</li><li>', '<br>').replace('<li>', '<br>').replace('</li>', '<br>').\
        replace('<ul>', '</b></header>').replace('</ul>', '<header><b>').replace('</b></header><br>', '</b></header>')
    char2 = f'<header><b>{char1}'
    c = char2.count('header')
    if (c % 2) == 0:
        characters = char2
    else:
        characters = f'{char2}</b></header>'

    item_dict['item_name'] = item_name
    item_dict['basic_price'] = ''
    item_dict['sale_price'] = ''
    item_dict['item_href'] = item_href
    item_dict['photo_hrefs'] = photo_list
    item_dict['description'] = description
    item_dict['category'] = 'Загрузка'
    item_dict['characters'] = characters
    return item_dict

def get_items():
    with open('/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/main_categories.json') as file:
        all_categories = json.load(file)
    counter_outside = 0
    for name_category, href_category in all_categories.items():
        print(f'Начинаем парсить категорию {name_category}')
        item_dict = []
        url = href_category
        useragent = UserAgent()
        headers = {
            "Accept": "*/*",
            "User-Agent": useragent.random
        }
        session = requests.Session()
        retry = Retry(connect=100, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        req = session.get(url=url, headers=headers)
        src = req.text
        soup = BeautifulSoup(src, 'lxml')

        try:
            pagination_block = soup.find(class_='woocommerce-pagination').find_all(class_='page-numbers')
            number_pages = len(pagination_block) - 2
        except:
            number_pages = 1

        for page in range(1, number_pages + 1):
            url_page = f'{href_category}page/{page}/'
            req = session.get(url=url_page, headers=headers)
            src = req.text
            soup = BeautifulSoup(src, 'lxml')
            names_item = soup.find_all(class_='wd-entities-title')
            for item in names_item:
                item_name = item.text
                item_href = item.find('a').get('href')
                item_info = get_card_info(item_category=name_category, item_name=item_name, item_href=item_href)
                item_dict.append(item_info)

        with open(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/item_dict.json', 'w', encoding='utf-8') as file:
            json.dump(item_dict, file, indent=4, ensure_ascii=False)

        counter_outside += 1


def convert_to_csv():
    with open('/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/main_categories.json') as file:
        all_categories = json.load(file)
    counter = 0
    for name_category, href_category in all_categories.items():
        counter += 1
        with open(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/data.csv', 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                (
                    'Имя',
                    'Базовая цена',
                    'Акционная цена',
                    'Изображения',
                    'Категории',
                    'Мета: characteristic',
                    'Описание'
                )
            )
        json_direct = f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/item_dict.json'
        with open(json_direct, 'r') as f:
            item_dict = json.loads(f.read())

        for item in item_dict:
            item_name = item['item_name']
            basic_price = item['basic_price']
            sale_price = item['sale_price']
            category = item['category']
            photo_href_list = item['photo_hrefs']
            description = item['description']
            characters = item['characters']
            photo_hrefs = ','.join(photo_href_list)

            with open(f'/home/twopercent/PycharmProjects/pythonProject/Commercial/homemebel/data/{name_category}/data.csv', \
                      'a', encoding='utf-8-sig') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(
                    (
                        item_name,
                        basic_price,
                        sale_price,
                        photo_hrefs,
                        category,
                        characters,
                        description
                    )
                )


def get_capcha():
    url = 'https://www.bundestag.de/services/formular/contactform?mdbId=860102'
    useragent = UserAgent()
    headers = {
        "Accept": "*/*",
        "User-Agent": useragent.random
    }
    session = requests.Session()
    retry = Retry(connect=100, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    req = session.get(url=url, headers=headers)
    src = req.text
    soup = BeautifulSoup(src, 'lxml')




if __name__ == '__main__':
    # get_main_categories()
    # create_directories()
    # get_items()
    convert_to_csv()