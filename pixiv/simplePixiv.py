# coding: UTF-8
# This is a simple spider for pixiv.net which crawling by artist.
# Only catches img, img_name, and simple label.
# source_url: www.pixiv.net, pixiv.re

import os
import pymysql
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from imghdr import what
from time import sleep, perf_counter

SAVE_PATH = '/Volumes/Elements SE/SpiderDataBase/Pixiv/'
#SAVE_PATH = './pix_img/'
#PD = input('Enter MySQL password: ')
PD = '@js974363'
UID = '1753843107@qq.com'

class PixivSession:
    def __init__(self) -> None:
        self.save_path = SAVE_PATH
        self.db = pymysql.connect(host='localhost', user='root', passwd=PD, database='Pixiv')
        self.cursor = self.db.cursor()
        self.browser = webdriver.Safari()
        self.browser.maximize_window()
        self.kv = {'user-agent': 'Mozilla/5.0'}

    def __end(self) -> None:
        self.cursor.close()


    # 模拟登录
    def log_in(self) -> None:
        log_in_url = 'https://accounts.pixiv.net/login'
        self.browser.get(log_in_url)
        element = self.browser.find_element(By.ID, 'LoginComponent')
        element_list = element.find_elements(By.TAG_NAME, 'input')
        element_list[0].send_keys(UID)
        element_list[1].send_keys(PD[1:]+'\n')
        self.browser.implicitly_wait(5)
        sleep(10)
        print('Account access success.\n')


    # 检查作者数据库状态, 方法待修改
    def check_table(self, uid: str) -> None:
        try:
            sql = 'DESC `uid:' + uid + '`;'
            self.cursor.execute(sql)
            print('Database uid:{} state Normal.\n'.format(uid))
        except:
            form = """ id int unsigned primary key auto_increment,
                        name varchar(36),
                        pid int unsigned not null,
                        age varchar(8),
                        img_num tinyint unsigned,
                        dynamic enum('Yes', 'No') """
            sql = 'CREATE TABLE `uid:' + uid +'`(' + form + ');'
            self.cursor.execute(sql)
            print('Database uid:{} does not exist.'.format(uid))
            print('New database uid:' + uid + ', creating success.\n')

    
    # 检查作者文件夹状态
    def check_dir(self, artist: str, uid: str) -> None:
        path = SAVE_PATH + artist + '#' + uid
        if os.path.isdir(path):
            print('Artist\'s dir exits.\n')
        else:
            os.makedirs(path)
            print('Artist\'s dir {}#{} does not exist.'.format(artist, uid))
            print('New dir {}#{}, creating success\n'.format(artist, uid))


    # 数据库中查询图片
    def check_sql_img(self, uid: str, pid: int) -> bool:
        sql = 'SELECT id FROM `uid:{}` WHERE pid={};'.format(uid, pid)
        if self.cursor.execute(sql) == 1:
            return True
        elif self.cursor.execute(sql) == 0:
            return False


    # 查询数据库中最大的PID
    def get_max_pid(self, uid: str) -> int:
        sql = 'SELECT MAX(pid) FROM `uid:{}`;'.format(uid)
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    # 查询数据库中最小的PID
    def get_min_pid(self, uid: str) -> int:
        sql = 'SELECT MIN(pid) FROM `uid:{}`;'.format(uid)
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    
    # 获取所有作品信息
    def get_imgs_url(self, uid: str) -> list:
        page = 1
        basic_url = 'https://www.pixiv.net/users/' + uid + '/artworks?p='
        info_list = []
        while True:
            judge, c = 0, 0
            try:
                self.browser.get(basic_url + str(page))
                self.browser.implicitly_wait(5)
                sleep(8)
                html = self.browser.page_source
                part_info_list = self.artwork_analyze(html)
            except:
                judge, c = 1, c + 1
                print('Raising exception: artworks page: {}'.format(basic_url + str(page)))
            if judge and c < 5:
                continue
            else:
                if len(part_info_list) != 0:
                    info_list = info_list + part_info_list
                    page += 1
                else:
                    break
        return info_list
    

    # 作品页分析
    def artwork_analyze(self, html: str) -> list:
        part_info_list = []
        soup = BeautifulSoup(html, 'html.parser')
        label = soup.find('div', attrs={'class': 'sc-1xvpjbu-0 gXGuur'})
        img_list = label.find_all('li')

        for img_label in img_list:
            pid = img_label.find('a').get('data-gtm-value')
            age = img_label.find('div', attrs={'class': 'sc-rp5asc-13 liXhix'}).text
            temp = img_label.find('div', attrs={'class': 'sc-rp5asc-5 hHNegy'})
            if temp == None:
                num = '1'
            else:
                num = temp.text
            temp = img_label.find('svg', attrs={'class': 'sc-192k5ld-0 etaMpt sc-rp5asc-8 kSDUsv'})
            if temp == None:
                dym = 'No'
            else:
                dym = 'Yes'
            name = img_label.find('div', attrs={'class': 'sc-iasfms-0 jtpclu'}).text
            name = name.replace('/', '-')
            name = name.replace('\'', ' ')
            if name == '.':
                name = '。'

            info = (pid, age, num, dym, name)   # (PID, 年龄, 图片数, 判断动图, 图片名)
            part_info_list.append(info)
        
        return part_info_list
    

    # 单张图片存取 来源: pixiv.re
    def get_img(self, artist: str, uid: str, info: tuple) -> None:
        path = self.save_path + artist + '#' + uid + '/'
        basic_url = 'https://pixiv.re/'
        num = int(info[2])
        if num == 1:
            url = basic_url + info[0] + '.png'
            name = info[-1] + '#' + info[0] + '.png'
            img = requests.get(url, headers=self.kv)
            self.save_img(path, name, img)
            self.save_info(uid, info)
            sleep(1.04)
        else:
            for i in range(1, num+1):
                name = info[-1] + '#' + info[0] + '-' + str(i) + '.png'
                url = basic_url + info[0] + '-' + str(i)  + '.png'
                img = requests.get(url, headers=self.kv)
                self.save_img(path, name, img)
                sleep(1.05)
            self.save_info(uid, info)


    # 图片存储
    def save_img(self, path: str, name: str, img) -> None:
        save_path = path + name
        with open(save_path, 'wb') as f:
            f.write(img.content)


    # 数据库存储
    def save_info(self, uid: str, info: tuple) -> None:
        sql = 'SELECT id FROM `uid:{}` WHERE pid={};'.format(uid, info[0])
        if self.cursor.execute(sql) != 0:
            return 0
        name, pid, img_num, dynamic = info[4], info[0], info[2], info[3]
        if info[1] == '':
            age = 'All'
        else:
            age = info[1]
        form = '(name, pid, age, img_num, dynamic) VALUES (\'' + name +'\','+ pid +',\''+ age +'\','+ img_num +',\''+ dynamic + '\');'
        sql = 'INSERT INTO `uid:' + uid + '`' + form
        self.cursor.execute(sql)
        self.db.commit()


    # 根据uid查找作者名称
    def get_artist_name(self, uid: str) -> str:
        kv2 = {'user-agent': 'Mozilla/5.0', 'Referer': 'https://www.pixiv.net'}
        home = requests.get('https://www.pixiv.net/users/' + uid, headers=kv2)
        soup = BeautifulSoup(home.text, 'html.parser')
        text = soup.find('title').text
        name = text.split(' ')[0]
        name = name.replace('/', '-')
        return name

    ##################################### 以下为用户方法 #####################################

    # 爬取作者全部作品
    def get_by_artist(self, uid: str) -> None:
        start = perf_counter()
        artist = self.get_artist_name(uid)
        self.check_table(uid)
        self.check_dir(artist, uid)
        info_list2 = self.get_imgs_url(uid)
        info_list = []
        for info in info_list2:
            ans = self.check_sql_img(uid, info[0])
            if not ans:
                info_list.append(info)

        print('Find {} imgs, saving process starts.'.format(len(info_list)))
        fail_list = []
        count = 0
        for info in info_list[::-1]:
            try:
                self.get_img(artist, uid, info)
                count += 1
            except:
                fail_list.append(info)
                print('Rasing exception: {}.'.format(info))
            if count % 10 == 0:
                print('  Already saved: {}, remaining: {}.'.format(count, len(info_list)-count))
            sleep(0.5)

        count = 0
        while len(fail_list) != 0 and count < 5:
            temp = []
            print('Fail_list not empty, error amount: {}.'.format(len(fail_list)))
            count += 1
            for i in fail_list:
                try:
                    self.get_img(artist, uid, info)
                except:
                    temp.append(i)
            fail_list = temp
        print('Final fail_list length: {}\n.'.format(len(fail_list)))
        print('Artist\'s (uid: {}) all artworks have already saved, amount: {}.'.format(uid, len(info_list)))
        print('Saving process accomplish.\n')

        end = perf_counter()
        print('Scanning mission accomplish.\nArtist: {}#{}\nTime(second): {:.4f}\n'.format(artist, uid, end-start))


    # 更新作者作品
    def update_artist(self):
        pass


    # 修复已损坏的图片
    def fix_img(self, uid: str) -> None:
        artist = self.get_artist_name(uid)
        dir = SAVE_PATH + artist + '#' + uid + '/'
        broken_list = []
        for i in os.walk(dir):
            for img in i[2]:
                try:
                    if what(dir+img) == None and img[0] != '.':
                        broken_list.append(img)
                except:
                    print('Strange img name: {}.'.format(img))
        print('Find {} broken imgs, fixing process starts.'.format(len(broken_list)))

        for i in range(5):
            temp = []
            for img in broken_list:
                url = 'https://pixiv.re/' + img.split('#')[-1]
                self.save_img(dir, img, requests.get(url, headers=self.kv))
                sleep(1.05)
                if what(dir+img) == None:
                    temp.append(img)
            print('Troop {} has finish, broken img remain: {}'.format(i+1, len(temp)))
            broken_list = temp
            if len(broken_list) == 0:
                break

        print('Fixing process accomplish.\n')
            



    

def main():
    #uid = input('Input uid: ')
    alist = []
    session = PixivSession()
    session.log_in()
    for uid in alist:  
        session.get_by_artist(uid)
        session.fix_img(uid)
        print('-----------------------------------------------------\n')



if __name__ == '__main__':
    main()


