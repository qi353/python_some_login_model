#coding=utf-8

import asyncio
import json
import requests
from datetime import datetime
from pyppeteer import launch
import time
import aiohttp
import re
from lxml import etree

wuxia = 'https://www.huya.com/wuxia'
login_url = 'https://www.huya.com/xxx'
js_func = '''() =>{ Object.defineProperties(navigator,{ 
        webdriver:{ get: () => undefined },
        userAgent:{ get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3840.0 Safari/537.36'},
        appVersion:{ get: () => '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3840.0 Safari/537.36'},
        languages:{ get: () => ["zh-CN", "zh", "ja", "zh-TW", "en"]},
        plugins:{ get: () => [1,2,3,5]}
     }) }'''


async def huya_login_by_phone(phone):
    try:
        retry_count = 2
        browser = await launch({'executablePath': chrome_path, 'headless': False, 'args': ['--no-sandbox'], 'dumpio': True})
        page = await browser.newPage()
        await page.setViewport({'width': 1800, 'height': 800})
        await page.goto(login_url,timeout=0)
        await page.evaluate(js_func)
        # await page.setRequestInterception(True)
        # page.on('request', intercept_request)
        while not await page.querySelector('#nav-login'):
            await asyncio.sleep(1)
        await page.click('#nav-login')

        while not page.mainFrame.childFrames:
            await asyncio.sleep(2)
        sub = page.mainFrame.childFrames[0]
        while not await sub.xpath("//div[@id='login-head-nav']/ul/li[2]"):
            await asyncio.sleep(2)

        t = await sub.xpath("//div[@id='login-head-nav']/ul/li[2]")
        await t[0].click()
        # await sub.click('#phone-login-form > div.udb-input-item.udb-input-item-sel.hy-cf > div > span')
        # await sub.click('#phone-login-form > div.udb-input-item.udb-input-item-sel.hy-cf > ul > li:nth-child(2)')
        await sub.type('#phone-login-form > div.udb-input-item.udb-input-item-sel.hy-cf > input', phone)
        await asyncio.sleep(1)
        await sub.click('#phone-login-form > div:nth-child(2) > span')
        await asyncio.sleep(1)
        await page.screenshot(path=f'./data/png/{phone}.png')
        while True:
            if not retry_count or await sub.querySelectorEval('#phone-login-form > div.input-error-tips',
                                                              'node => node.style'):
                print(f'账号不可用:{phone}')
                await page.close()
                await browser.close()
                return
            await asyncio.sleep(30)
            code = await get_code(phone)
            if code:
                break
            await sub.click('#phone-login-form > div:nth-child(2) > span')
            retry_count -= 1

        await sub.type('#phone-login-form > div:nth-child(2) > input', str(code))
        await sub.click('#phone-login-btn')
        await asyncio.sleep(1)
        # if await sub.querySelectorEval('#phone-login-form > div.input-error-tips', 'node => node.style'):
        #     print(f'账号不可用:{phone}')
        #     await page.close()
        # print('跳转主页...')
        cookie_pre = await page.cookies()
        await page.goto(wuxia,timeout=0)
        cookie = await page.cookies()
        str_cookie = await format_cookie(page)
        res = {'phone':phone,'cookie_pre':cookie_pre,'cookie':cookie,'str_cookie':str_cookie}
        c = await count_huliang(str_cookie, phone)
        res['hl'] = c
        num = c['silverBean']
        c = 1 if len(res['hl']) > 2 else 0
        with open(f"./data/test/{phone}_{c}_{num}",'wt') as f:
            f.write(json.dumps(res))

        await page.close()
        await browser.close()
        return
    except Exception as e:
        print(e)
        await page.close()
        await browser.close()
        return



async def intercept_request(req):
    '''过滤请求'''
    # if not req.resourceType in ['document', 'xhr','script','image', 'media', 'eventsource', 'websocket']:
    if not req.resourceType in ['document', 'xhr', 'script', 'image', 'stylesheet']:
        # if req.resourceType in ['websocket']:
        await req.abort()
    else:
        await req.continue_()


async def fetch(session, url, proxy=None):
    async with session.get(url, proxy=proxy) as response:
        print(f'{response.status}:正在下载页面:{url}')
        return await response.text()


async def get_code(phone):

    url = f'https://sms.bilulanlv.com/message/{phone}.html'
    async with aiohttp.ClientSession(headers={'User-Agent': ua}) as sess:
        html_ = await fetch(sess, url)
        doc = etree.HTML(html_)

        tr_list = doc.xpath("//tbody/tr[position()<4]")
        print(f'{phone}:正在检索验证码:{doc.xpath("//title/text()")[0]}:{len(tr_list)}', end=' --->')
        for tr in tr_list:
            content = tr.xpath("./td[2]/text()")[0]
            if not content:
                break
            # t = tr.xpath("./td[3]/text()")[0]
            # t = datetime.strptime(t,'%Y-%m-%d %H:%M:%S').timestamp()
            # cha = datetime.now().timestamp() - t
            # code = num_rex.findall(content)
            cha = 1
            code = re.match(r'.*?(\d{6}).*?', content)
            if '虎牙' in content and code and cha < 180:
                print(f'{phone}:成功检索到:{code}')
                return code.group(1)
    print('没有收到验证码')
    return None


async def format_cookie(page):
    '''
     获取登录后cookie
    :param page:
    :return:
    '''
    print('正在获取format cookie...')
    cookies_list = await page.cookies()
    print(cookies_list)
    cookies = ''
    for cookie in cookies_list:
        str_cookie = '{0}={1};'
        str_cookie = str_cookie.format(cookie.get('name'), cookie.get('value'))
        cookies += str_cookie
        # print('{}:{}'.format(cookie.get('name'), cookie.get('value')))
    print(cookies)
    return cookies


async def count_huliang(cookie, phone):
    # stime = str(int(time.time()))
    print(f'{phone}查询剩余虎粮')
    sign_url = f'https://q.huya.com/index.php?m=PackageApi&do=getTimeSign&_={str(int(time.time()))}'
    list_total = 'https://q.huya.com/index.php?m=PackageApi&do=listTotal&time={}&sign={}'
    referer = 'https://hd.huya.com/pay/index.html?source=web'
    headers = {
        'User-Agent': ua,
        'Referer': referer,
        'cookie': cookie
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as sess:
            res = {}
            html_ = await fetch(sess, sign_url)
            # print(html_)

            sign_json = json.loads(html_)

            if sign_json['status'] != 200:
                return ''
            html_ = await fetch(sess, list_total.format(sign_json['data']['time'], sign_json['data']['sign']))
            # print(html_)
            json_total = json.loads(html_)

            if sign_json['status'] != 200:
                return ''
            for i in json_total['data']['package']:
                res['type'] = i['type']
                res['cName'] = i['cName']
                res['num'] = i['num']
            res['silverBean'] = json_total['data']['silverBean']['num']
            res['phone'] = phone
            return res
    except Exception as e:
        print(f'Count 虎粮报错:{e}')
        return ''


async def main():
    for i in get_free_phone():
        await huya_login_by_phone(i)

def get_free_phone():
    for i in range(1, 6):
        url = f'https://sms.bilulanlv.com/dl/{i}.html'
        # url = f'https://sms.bilulanlv.com/gat/{i}.html'
        resp = requests.get(url, headers={'User-Agent': ua})
        if resp.status_code != 200:
            break
        doc = etree.HTML(resp.text)
        phone_list = doc.xpath("//div[@class='main']/div/div")
        for pd in phone_list:
            state = pd.xpath(".//div[@class='layui-card-header']/span[2]/text()")[0]
            if state == '接收中':
                num = pd.xpath(".//div[@class='layui-card-body layuiadmin-card-list']/p/@id")[0]
                yield num

if __name__ == '__main__':
    json_rex = re.compile(r'.*?\(({.*?})\).*?')
    chrome_path = 'C:\\Users\\user\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        print(f'程序退出:{e}')
