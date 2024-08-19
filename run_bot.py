import telebot
from telebot import types
import sqlite3
from threading import Thread, Timer
import time
from requests.exceptions import ProxyError, ConnectionError
import requests
import json
import logging
from flask import Flask
import multiprocessing

API_TOKEN = '7500067001:AAESKhQXLxhm2GsWVzQMEhKhPYhulHE1EhY'
BOT = telebot.TeleBot(API_TOKEN)
# إعداد URL وAPI Key
japApiUrl = 'https://justanotherpanel.com/api/v2'
japApiKey = '828466267231ce04a7dd374a969dff26'

def run_flask():
    app = Flask(__name__)
    @app.route('/')
    def home():
        return "البوت يعمل!"
    app.run(host='0.0.0.0', port=4321)

def check_order_status(order_id):
    postData = {
        'key': japApiKey,
        'action': 'status',
        'order': order_id,
    }

    # تسجيل البيانات المرسلة
    # logging.info(f'Sending data to JAP: {json.dumps(postData)}')
    print(f"Sending data to JAP: {json.dumps(postData)}")

    try:
        response = requests.post(japApiUrl, data=postData)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f'Error while sending request: {e}')
        return None

    # تسجيل الاستجابة
    # logging.info(f'JAP response: {response.text}')
    print(f"JAP response: {response.text}")

    try:
        return response.json()
    except json.JSONDecodeError as e:
        logging.error(f'Error parsing JSON response: {e}')
        return None


@BOT.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    with_link = types.InlineKeyboardButton(" عن طريق الرابط", callback_data='with_link') # callback_data=f'show_client_{client_id}'
    with_orderno = types.InlineKeyboardButton("عن طريق رقم الاوردر في سلة", callback_data='with_order_id')
    markup.row(with_link)
    markup.row(with_orderno)
    BOT.send_message(message.chat.id,"مرحباً عبدالعزيز ، كيف تريد معرف حالة الطلب", reply_markup=markup)

@BOT.callback_query_handler(func=lambda call: call.data.startswith("with_link"))
def find_with_link(call):
    BOT.answer_callback_query(call.id)
    print('ask with link')
    msg = BOT.send_message(call.message.chat.id,'أرسل الرابط الذي كان في الطلب :')
    BOT.register_next_step_handler(msg,process_order )

@BOT.callback_query_handler(func=lambda call: call.data.startswith("with_order_id"))
def find_with_order_id(call):
    BOT.answer_callback_query(call.id)
    print('find with link')
    msg = BOT.send_message(call.message.chat.id,'أرسل رقم اوردر سلة الذي كان في الطلب :')
    BOT.register_next_step_handler(msg,process_order )

def process_order(message):
    link = message.text
    print(f"this is link : {link}")
    db_url = 'https://king-of-marketing.com/all_orders.db'
    local_db_path = 'all_orders.db'
    # تنزيل قاعدة البيانات وحفظها محليًا
    # response = requests.get(db_url)
    response = requests.get(db_url, proxies={"http": None, "https": None})

    # تحقق من نجاح التنزيل قبل حفظ الملف
    if response.status_code == 200:
        with open(local_db_path, 'wb') as f:
            f.write(response.content)
        print(f"Database downloaded and saved as {local_db_path}")
    else:
        print(f"Failed to download the database. Status code: {response.status_code}")
    conn = sqlite3.connect('all_orders.db')
    cursor = conn.cursor()
    print('dad')
    cursor.execute('SELECT * FROM orders WHERE link = ? OR salla_order_id = ?', (link,link))
    print('wxlam')
    orders = cursor.fetchall()
    if orders:
        for order in orders:
            print(order)
            order_customer = order[1]
            order_salla_id = order[2]
            order_jap_id = order[3]
            # order_jap_service_id = order[5]
            order_quantity = order[6]
            order_date = order[7]
            msg = BOT.send_message(message.chat.id,f"إسم العميل : {order_customer}\nرقم الطلب في سلة : {order_salla_id}\nرقم الطلب في JAP : {order_jap_id}\nالكمية : {order_quantity}\nتاريخ الطلب : {order_date}")
            # BOT.send_message(message.chat.id,"جاري التأكد من حالة الطلب")
            order_status = check_order_status(order_jap_id)
            try:
                print('order status')
                print(order_status)
                print(len(order_status))
                if len(order_status) >= 2:
                    status = order_status['status']
                    remains = order_status['remains']
                    start_count = order_status['start_count']
                    print(f"order status : {order_status}")
                    BOT.send_message(message.chat.id,f"حالة الطلب : {status}\nالمتبقي : {remains}\نقطة البدء : {start_count}")
                else:
                    print(order_status['error'])
                    BOT.send_message(message.chat.id,"لم يتم إيجاد الطلب في JAP")
            except Exception as e:
                BOT.send_message(message.chat.id,f"حدث خطأ ما {e}")

    else:
        BOT.send_message(message.chat.id,'لم يتم العثور على طلب')
    print(orders)
    conn.close()


while True:
        try:
            multiprocessing.Process(target=run_flask).start()
            multiprocessing.Process(target=BOT.polling(none_stop=True, interval=1)).start()


        except ProxyError as e:
            print(f"Proxy error occurred: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
        except ConnectionError as e:
            print(f"Connection error occurred: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
