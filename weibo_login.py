import rsa
import binascii
import time
import re
import json
import requests
from urllib import parse
import base64
import pickle


user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
referer = 'https://weibo.com/login.php'
username = 'test'
password = 'test'
session_cache_path = './data/weibo/session_cache'


def encrypt_passwd(passwd, pubkey, servertime, nonce):
    key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
    passwd = rsa.encrypt(message.encode('utf-8'), key)
    print(passwd)
    return binascii.b2a_hex(passwd)


def get_prelt(pre_login):
    prelt = int(time.time() * 1000) - pre_login['preloginTimeStart'] - pre_login['exectime']
    return prelt


def prelogin(session):
    preloginTimeStart = int(time.time() * 1000)
    url = f'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_={preloginTimeStart}'
    resp = session.get(url)
    pre_login_str = re.match(r'[^{]+({.+?})', resp.text).group(1)
    pre_login = json.loads(pre_login_str)
    pre_login['preloginTimeStart'] = preloginTimeStart
    return pre_login


def login(session, pre_login, sp):
    url = f'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)&_={int(time.time() * 1000)}'
    data = {
        'entry': 'weibo',
        'gateway': 1,
        'from': '',
        'savestate': 7,
        'qrcode_flag': 'false',
        'userticket': 1,
        'pagerefer': 'https://my.sina.com.cn/profile/logined',
        'vsnf': 1,
        'su': base64.b64encode(parse.quote(username).encode()),
        'service': 'miniblog',
        'servertime': pre_login['servertime'],
        'nonce': pre_login['nonce'],
        'pwencode': 'rsa2',
        'sp': sp,
        'rsakv': pre_login['rsakv'],
        'encoding': 'UTF-8',
        'cdult': 2,
        'prelt': 279,
        'sr': "1920*1080",
        'domain': 'weibo.com',
        'returntype': 'TYPE'
    }
    resp = session.post(url, data=data)
    print(resp.status_code)
    redirect_url = re.findall(r'location\.replace\("(.*?)"', resp.text)[0]
    resp = session.get(redirect_url)
    print(resp.status_code)
    arrURL = re.findall(r'"arrURL":(.*?)\}', resp.text)[0]
    arrURL = json.loads(arrURL)
    for url in arrURL:
        r = session.get(url)
    redirect_url = re.findall(r'location\.replace\(\'(.*?)\'', resp.text)[0]
    resp = session.get(redirect_url)
    print(resp.status_code)


def weibo_login():
    sess = requests.session()
    sess.headers['User-Agent'] = user_agent
    sess.headers['Referer'] = referer
    pre_login = prelogin(sess)
    print(pre_login)
    sp = encrypt_passwd(password, pre_login['pubkey'], pre_login['servertime'], pre_login['nonce'])
    login(sess, pre_login, sp)
    with open(session_cache_path, 'wb') as f:
        pickle.dump(sess.cookies, f)



def main(sess=None):
    weibo_login()


if __name__ == '__main__':
    # with open(session_cache_path, 'rb') as f:
    #     if f:
    #         session_cache = pickle.load(f)
    #     else:
    #         weibo_login()

    main()
