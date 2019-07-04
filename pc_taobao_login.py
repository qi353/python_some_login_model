# -*- coding: utf-8 -*-
import asyncio
import json
from pyppeteer import launch


async def taobao_login(username, password, url):
    browser = await launch({'headless': False, 'args': ['--no-sandbox'], 'dumpio': True})
    page = await browser.newPage()
    response = await page.goto(url)
    await page.evaluate('''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => undefined } }) }''')
    # await page.setRequestInterception(True)
    await page.click('a.J_Quick2Static')

    await page.type('input#TPL_username_1', username)
    await asyncio.sleep(1)
    await page.type('input#TPL_password_1', password)
    await asyncio.sleep(1)
    await_count = 5
    while await_count:
        print("循环等待。。。")
        await asyncio.sleep(1)
        if await page.querySelectorEval('#nocaptcha', 'node => node.style'):
            print('滑块验证出现。。。')
            await asyncio.sleep(12)
            await page.hover('#nc_1_n1z')
            await asyncio.sleep(1)
            await page.mouse.down()
            await asyncio.sleep(0.7)
            await page.mouse.move(2000, 0, {'delay': random.randint(1000, 2000)})
            await page.mouse.up()
            break
        await_count -= 1
    else:
        print('验证失败。。。')
        return None

    await_count = 5
    while await_count:
        print('正在判断验证是否成功。。。')
        await asyncio.sleep(2)
        if await page.querySelectorEval('.nc-lang-cnt', 'node => node.textContent') == '验证通过':
            print('验证通过。。。')
            await page.click('button#J_SubmitStatic')
            break
        await_count -= 1
    else:
        print('验证失败。。。')
        return None
    await page.goto('https://chaoshi.tmall.com/')
    cookie_str = await format_cookie(page)
    # save_cookie('./tmall_session_cache', cookie_str)
    # await asyncio.sleep(5)
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
    return cookies


if __name__ == '__main__':
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
    username = 'test'
    password = 'test'
    url = 'https://login.taobao.com/member/login.jhtml'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(taobao_login(username, password, url))
