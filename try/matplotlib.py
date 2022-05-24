# coding: utf-8
# source_url: https://matplotlib.org/3.5.1/gallery/index.html

import requests
from bs4 import BeautifulSoup
from time import sleep
import pymysql

URL = 'https://matplotlib.org/3.5.1/gallery/'
PATH = './img/'
KV = {'user-agent': 'Mozilla/5.0'}

def get_all_url():
    target_list = []
    main_page = requests.get(URL+'index.html/', headers=KV)
    main_soup = BeautifulSoup(main_page.text, 'html.parser')
    source_list = main_soup.find_all('div', attrs={'class': 'sphx-glr-thumbcontainer'})
    for i in source_list:
        name = i.find('span').text
        url = i.find('a', attrs={'class': 'reference internal'}).get('href')
        tool_tip = i.get('tooltip')
        target_list.append((name, url, tool_tip))
    
    return target_list    # img_name, source_url, tool_tip


def get_img_url(target_tuple):
    source_page = requests.get(URL+target_tuple[1], headers=KV)
    soup = BeautifulSoup(source_page.text, 'html.parser')
    url_list = []
    temp = soup.find('main')
    temp_list = temp.find_all('img')
    if temp_list != None:
        for i in range(len(temp_list)):
            temp_url = temp_list[i].get('src')
            url = 'https://matplotlib.org/3.5.1/_images/' + temp_url.split('/')[-1]
            url_list.append(url)
    sleep(0.2)

    return url_list    # amount


def img_storage(url):
    img = requests.get(url, headers=KV)
    save_path = PATH + url.split('/')[-1]
    with open(save_path, 'wb') as f:
        size = f.write(img.content)
    sleep(0.3)

    return (save_path, size)    # save_path, size


def info_storage(info, db):
    cursor = db.cursor()
    sql = """INSERT INTO matplotlib 
            (img_name, source_url, save_path, size, amount, tool_tip) 
            values('{}','{}','{}','{}','{}','{}')
            ;""".format(info[0], info[1], info[2], info[3], info[4], info[5])
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()


def main():
    db = pymysql.connect(host='localhost', user='root', password='@js974363', database='try_1')

    count = 0
    fail_list = []
    target_list = get_all_url()

    for target_tuple in target_list[100:]:
        try:
            url_list = get_img_url(target_tuple)
            save_path, size = '', 0
            if url_list != []:
                for url in url_list:
                    img_info = img_storage(url)
                    save_path += img_info[0] + ', '
                    size += img_info[1]
                
            info = (target_tuple[0], target_tuple[1], save_path, size, len(url_list), target_tuple[2])
            info_storage(info, db)
            count += 1
        
        except:
            fail_list.append(target_tuple)

        if count % 50 == 0:
            print('Present Target Catched: ' + str(count) + '\n')

    print(fail_list)
    while len(fail_list) != 0:
        for target_tuple in fail_list:
            try:
                url_list = get_img_url(target_tuple)
                save_path, size = '', 0
                if url_list != []:
                    for url in url_list:
                        img_info = img_storage(url)
                        save_path += img_info[0] + ', '
                        size += img_info[1]

                info = (target_tuple[0], target_tuple[1],
                        save_path, size, len(url_list), target_tuple[2])
                info_storage(info, db)
                count += 1
                fail_list.remove(target_tuple)

            except:
                pass

            if count % 50 == 0:
                print('Present Target Catched: ' + str(count) + '\n')

    db.close()


if __name__ == '__main__':
    main()
