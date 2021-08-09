# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import csv
import json
import os
import time

import aiohttp
import pymysql
import requests

from logger import logger

global_config = {
    'cookie': '',  # cookie，从 https://m.weibo.cn 获取
    'start_page': 1,  # 起始页数（包含）
    'end_page': 500,  # 终止页数（包含）
    'start_date': '2000-01-01',  # 起始日期，小日期（包含）
    'end_date': '2099-12-31',  # 终止日期，大日期（包含）
    'enable_delete': False,  # 是否启用删除功能
    'enable_out_excel': False,  # 是否导出excel
    'enable_out_database': False,  # 是否保存到数据库
    'database_host': '127.0.0.1',
    'database_port': 3306,
    'database_user': 'user',
    'database_password': 'password',
    'database_db': 'weibo',
    'semaphore': 30,  # 并发数
}


def get_config():
    config_path = os.path.join(os.getcwd(), 'config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError('No such file: config.json')
    config_str = open(config_path).read().replace('\n', '')
    config = json.loads(config_str)
    global global_config
    for key, value in config.items():
        if value is not None:
            global_config[key] = value


get_config()

start_date_ts = time.mktime(time.strptime(global_config['start_date'], '%Y-%m-%d'))
end_date_ts = time.mktime(time.strptime(global_config['end_date'] + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

xsrf_token = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in global_config['cookie'].split('; ')}.get('XSRF-TOKEN')


def get_common_headers():
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'mweibo-pwa': '1',
        'pragma': 'no-cache',
        'referer': 'https://m.weibo.cn',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'cookie': global_config['cookie'],
        'x-xsrf-token': xsrf_token
    }


async def query_with_aiohttp(page: int, client, sem) -> list:
    """
    查询已发送评论
    :param page: 页数
    :param client: client
    :param sem: sem
    :return: 评论list
    """
    sent_comments_list = []
    logger.info(f'query for page: {page}')
    url = 'https://m.weibo.cn/message/myCmt?page={page}'.format(page=page)
    async with sem:
        async with client.get(url=url) as response:
            if response.status != requests.codes.OK:
                logger.error(f'page：{page}，msg：{response.status}')
            else:
                result = await response.json()
                ok = result['ok']
                if ok != 1:
                    logger.error(f'token可能已失效，page：{page}，ok：{ok}')
                else:
                    data = result['data']
                    if data is False:
                        return sent_comments_list
                    for item in data:
                        created_at = time.strptime(item['created_at'], '%a %b %d %H:%M:%S %z %Y')
                        created_at_ts = time.mktime(created_at)
                        if start_date_ts < created_at_ts < end_date_ts:
                            sent_comments_list.append({
                                'page': str(page).zfill(4),
                                'id': str(item['id']),
                                'mid': str(item['mid']),
                                'reply_text': item['text'],
                                'reply_original_text': item.get('reply_original_text'),
                                'created_date': time.strftime('%Y-%m-%d', created_at),
                                'created_time': time.strftime('%Y-%m-%d %H:%M:%S', created_at),
                                'target_text': item['status']['text'],
                                'data_json': json.dumps(item)
                            })
    return sent_comments_list


async def query_main():
    sem = asyncio.Semaphore(global_config['semaphore'])
    async with aiohttp.ClientSession(headers=get_common_headers()) as client:
        tasks = [query_with_aiohttp(i, client, sem) for i in range(global_config['start_page'], global_config['end_page'] + 1)]
        return await asyncio.gather(*tasks)


def do_query():
    sent_comments_list = []
    t = time.time()
    all_list = asyncio.run(query_main())
    for temp in all_list:
        sent_comments_list.extend(temp)
    start_date = global_config['start_date']
    end_date = global_config['end_date']
    logger.info(f'{start_date}至{end_date}内共发出评论数量：{len(sent_comments_list)}，耗时：{time.time() - t}秒')
    return sent_comments_list


def del_with_requests(mid, headers):
    """
    删除评论
    :param mid: 评论id
    :param headers: headers
    """
    url = 'https://m.weibo.cn/comments/destroy'
    response = requests.post(url=url, headers=headers, data={
        'cid': mid,
        'st': xsrf_token,
        '_spr': 'screen:1920x1080'
    })
    result = response.json()
    result_msg = result['msg']
    if response.status_code == requests.codes.OK and result['ok'] == 1:
        logger.info(f'mid：{mid}，msg：{result_msg}')
        return
    logger.error(f'mid：{mid}，msg：{result_msg}')
    raise Exception(result_msg)


def do_del(mid_list):
    logger.info(f'待删除评论数量为{len(mid_list)}')
    print('\n')
    flag = input('是否确认删除(y/n)：')
    print('\n')
    if flag == 'y':
        headers = {
            **get_common_headers(),
            'origin': 'https://m.weibo.cn',
            'content-type': 'application/x-www-form-urlencoded',
        }
        refresh_token_and_headers(headers)
        count = 0
        for mid in mid_list:
            try:
                del_with_requests(mid, headers)
            except Exception:
                break
            count = count + 1
            if count == 59:
                sec = 5 + 60 * 10
                # 每10分钟内只能删60个回复
                logger.info(f'暂停删除，休眠{sec}秒')
                time.sleep(sec)
                refresh_token_and_headers(headers)
                logger.info('继续删除')
                count = 0


def refresh_token_and_headers(headers):
    global xsrf_token
    global global_config
    old_xsrf_token = xsrf_token
    logger.info(f'刷新token，原xsrf_token为{xsrf_token}')
    url = 'https://m.weibo.cn/api/config'
    response = requests.get(url=url, headers=get_common_headers())
    result = response.json()
    if response.status_code == requests.codes.OK and result['ok'] == 1:
        xsrf_token = result['data']['st']
        global_config['cookie'] = headers['cookie'].replace(old_xsrf_token, xsrf_token)
        headers['x-xsrf-token'] = xsrf_token
        headers['cookie'] = global_config['cookie']
        logger.info(f'刷新token成功，新xsrf_token为{xsrf_token}')
        return
    logger.error('刷新token失败')


def save_to_csv(sent_comments_list, file_name='sent_comments_out.csv'):
    headers = ['page', 'id', 'mid', 'reply_text', 'reply_original_text',
               'created_date', 'created_time', 'target_text', 'data_json']
    with open(file_name, 'w', encoding='utf-8-sig')as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows([[item['page'], item['id'], item['mid'], item['reply_text'], item['reply_original_text'],
                          item['created_date'], item['created_time'], item['target_text'], item['data_json']] for item in sent_comments_list])


def save_to_database(sent_comments_list):
    conn = pymysql.connect(host=global_config['database_host'],
                           port=global_config['database_port'],
                           user=global_config['database_user'],
                           passwd=global_config['database_password'],
                           db=global_config['database_db'])
    cursor = conn.cursor()
    sql = 'INSERT INTO weibo_sent_comments (page, id, mid, reply_text, reply_original_text, created_date, created_time, target_text, data_json) ' \
          'values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    data = [(item['page'], item['id'], item['mid'], item['reply_text'], item['reply_original_text'],
             item['created_date'], item['created_time'], item['target_text'], item['data_json']) for item in sent_comments_list]
    insert_count = cursor.executemany(sql, data)
    logger.info(f'插入数据行数：{insert_count}')
    cursor.close()
    conn.commit()
    conn.close()


def main():
    sent_comments_list = do_query()

    if global_config['enable_out_excel']:
        current_time = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
        save_to_csv(sent_comments_list, f'sent_comments_out_{current_time}.csv')

    if global_config['enable_out_database']:
        save_to_database(sent_comments_list)

    if global_config['enable_delete']:
        mid_list = [item['mid'] for item in sent_comments_list]
        do_del(mid_list)


if __name__ == '__main__':
    main()
