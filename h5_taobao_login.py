# -*- coding: utf-8 -*-

import asyncio
import json
from pyppeteer import launch
import aiohttp


async def h5_taobao_login(username, password, url):
    browser = await launch({'headless': False, 'args': ['--no-sandbox'], 'dumpio': True})
    page = await browser.newPage()
    await page.setViewport(viewport={'width': 375, 'height': 667})
    response = await page.goto(url)
    await page.evaluate('''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => undefined } }) }''')
    # await page.setRequestInterception(True)
    await page.type('#username', username)
    await asyncio.sleep(1)
    await page.type('#password', password)
    await asyncio.sleep(1)

    await page.click('#submit-btn', delay=1)
    await asyncio.sleep(1)
    await page.evaluate('''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => undefined } }) }''')
    count = 5
    while count:
        if await page.querySelector('div.km-dialog-buttons'):
            print('触发验证。。。')
            await page.click('div.km-dialog-buttons', delay=1)
            await asyncio.sleep(1)
            await page.hover('#SM_BTN_1')
            await asyncio.sleep(0.5)
            await page.mouse.down()
            await asyncio.sleep(0.2)
            await page.mouse.up()
            break
        count -= 1
    else:
        print('登陆成功。。。')
        await asyncio.sleep(2)
        await format_cookie(page)
    while not await page.querySelectorEval('#SM_TXT_1', 'node => node.textContent') == '验证成功':
        pass
    await asyncio.sleep(1)
    await page.querySelectorEval('#username', 'node => node.value=""')
    await page.type('#username', username)
    await asyncio.sleep(1)
    await page.querySelectorEval('#password', 'node => node.value=""')
    await page.type('#password', password)
    await asyncio.sleep(1)
    await page.hover('#submit-btn')
    await page.mouse.down()
    await page.mouse.up()
    cookie_str = format_cookie(page)
    await browser.close()
    return cookie_str


async def format_cookie(page):
    '''
     获取登录后cookie
    :param page:
    :return:
    '''
    cookies_list = await page.cookies()
    print(cookies_list)
    cookies = ''
    for cookie in cookies_list:
        str_cookie = '{0}={1};'
        str_cookie = str_cookie.format(cookie.get('name'), cookie.get('value'))
        cookies += str_cookie
        # print('{}:{}'.format(cookie.get('name'), cookie.get('value')))
    # print(cookies)
    return cookies

if __name__ == '__main__':
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
    username = 'test'
    password = 'test'
    url = 'https://login.m.taobao.com/login.htm?loginFrom=wap_tmall&redirectURL=https://www.tmall.com/?from=m'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(h5_taobao_login(username, password, url))
