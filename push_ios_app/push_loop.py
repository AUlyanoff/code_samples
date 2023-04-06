"""
Это пуш-сервер наших (несистемных) Мониторов iOS
================================================
"""
import logging
import os
import sys
import threading

import hyper
import json
import time
from datetime import datetime
from hyper import tls
from ssl import SSLError
from threading import Thread

import log

import database
import config
import paths

from monitor_push_http2.exceptions import MonitorsUidMismatchException

logger = logging.getLogger("commands")


def send_notification(uid, token, cert_path, address, port, push=None):
    """Посылаем пуш нашему монитору iOS"""
    push = {"aps": {"content-available": 1, "sound": ""}} if push is None else push
    ssl_context = tls.init_context(cert=cert_path)
    conn = hyper.HTTP20Connection(host=address, port=port, secure=True, ssl_context=ssl_context,
                                  timeout=60, force_proto='h2')
    json_str = json.dumps(push, ensure_ascii=False, separators=(',', ':'))
    json_payload = json_str.encode('utf-8')
    headers = {'apns-topic': uid, 'apns-expiration': '0', 'apns-priority': '5'}
    url = f'/3/device/{token}'

    try:
        logger.warning("Trying to send notification address={}, url={}".format(address, url))
        conn.request('POST', url, json_payload, headers)
    except SSLError as err:
        logger.error(f"Cannot send notification to monitor. SSL error: {err}")
    except Exception as err:
        logger.error(f"Cannot send notification to monitor. Unexpected error: {err}")
    else:
        logger.debug("APNS response: {}".format(str(conn.get_response().read().decode('utf-8'))))
    finally:
        conn.close()


def thread_permission_check() -> bool:
    """Проверяет, работают ли потоки в системе"""
    def test_thread():
        fname = open(os.devnull, 'w+')
        sys.stdout = fname
        print(f'\tTest threads: threading.active_count() = {threading.active_count()}, '
              f'names = {", ".join([t.name for t in threading.enumerate()])}', file=fname)
        sys.stdout = sys.__stdout__
        fname.close()
    success = 0
    for i in range(1, 6):
        try:
            t = Thread(target=test_thread(), name='Test_Tread-'+str(i))
            t.start()
        except RuntimeError:
            success -= 1
        else:
            success += 1
    if success > 0:
        res = True
        logger.debug("Threads are allowed, the server is running in multi-threaded mode.")
    else:
        res = False
        logger.warning("Attention! Threads are disabled in system, the server is running in single-threaded mode.")
    return res


def wait_terminate_threads(max_threads, terminate_timeout, terminate_threads):
    """если потоков слишком много, приостановить выполнение, пока не завершится terminate_threads пушей"""
    if threading.active_count() > max_threads + 4:  # Питон, ввод, вывод и main
        ttc = 0  # счётчик завершённых потоков, т.е. отосланных пушей
        for t in threading.enumerate():
            if '(apns_notice)' in t.name:   # ищем потоки, которые отправляли пуши
                if t.is_alive():            # если поток работает
                    try:
                        t.join(timeout=terminate_timeout)  # ждём завершения потока, не более timeout секунд
                    except RuntimeError:  # поток умудрился помереть раньше, мы чем начали этого ждать
                        pass
                    ttc += 1  # ещё один поток завершился
                else:
                    ttc += 1  # ещё один поток завершился
            if ttc >= terminate_threads:
                break  # можно снова посылать пуши


def infinity_loop():
    """Собственно сервер - бесконечный цикл опроса базы и посылки пушей
       асинхронный многопоточный
    """
    # инициализация логирования и БД
    config.objects.prefix_loggers = "mon_push_"
    logger.fatal(f"\niOS Monitor push-server started at {datetime.now().strftime('%d-%m-%Y %H:%M:%S, %A')}...")
    log.setup_log(config.objects.iosmdm.get("log"), config.objects.iosmdm.get("log_ext"))
    database.init(paths.SRC_DIR, config.objects.db)

    # если не задано в конфиге, то проверить, можно ли порождать потоки
    if config.objects.find_push_monitor_threads_allowed() is None:
        threads_allowed = thread_permission_check()
    else:
        threads_allowed = config.objects.find_push_monitor_threads_allowed()
    # макс количество потоков для одновременной посылки пушей (1 поток = 1 пуш)
    max_threads = config.objects.find_push_monitor_max_treads()
    # если потоков слишком много, ждём завершения terminate_threads числа потоков
    terminate_threads = config.objects.find_push_monitor_terminate_threads()
    # ждём завершения потока не более terminate_timeout времени
    terminate_timeout = config.objects.find_push_monitor_terminate_timeout()
    # какой пуш посылаем (alert, silent - указываем в конфиге в виде словаря текст пуш-уведомления)
    push = config.objects.find_push_monitor_push()
    nc, nn = 0, 0           # счётчики циклов и уведомлений

    uuid = config.objects.config_find_monitor_uid_ios()                             # получение имени монитора
    monitor_address_and_port = config.objects.get_monitor_address_and_port(uuid)    # и адреса куда пушить
    if monitor_address_and_port is None:
        logger.error(
            f"\n\tIt is not possible to continue loading due to problems with the monitor's push server."
            f"\n\tMonitor '{uuid}' not found in iosmdm.yml monitors section.\n\tServer loading stopped.")
        raise MonitorsUidMismatchException
    (address, port) = monitor_address_and_port
    cert_path = config.objects.get_monitor_cert_path(uuid)
    logger.fatal(f"APNs address = {address}, port = {port}, cert_path = {cert_path}")
    logger.fatal(f"APNs push = {push}")
    logger.fatal(f"threads_allowed = {threads_allowed}, max_threads = {max_threads},"
                 f"terminate_threads = {terminate_threads}, terminate_timeout = {terminate_timeout}")

    while True:
        nc = nc + 1 if nc < 1000 else 1             # просто порядковый номер цикла для удобства чтения логов
        with database.get_connection() as dbo:      # Получение токенов для Монитора устройства
            _out, rs = database.objects.push_clients.sp_imdm_poll(
                dbo, "APNS", "ru.niisokb.mdm_server.iosMonitor", uuid,
                3000,  # предотвратить переполнение памяти
                check_rc_handler=database.check_rc_handler_any_data)
            dbo.commit()
            logger.info('rs.push_clients_list_task = {}'.format(str(rs.push_clients_list_task)))

        nn = 0
        for push_client in rs.push_clients_list_task:
            nn = nn + 1 if nn < 1000 else 1     # просто порядковый номер уведомления для удобства чтения логов
            logger.info("Sending notification, sequence number={} started...".format(str(nn)))

            if threads_allowed:                 # разрешено ли порождать потоки
                # если потоков слишком много, приостановить выполнение, пока не завершится terminate_threads пушей
                wait_terminate_threads(max_threads, terminate_timeout, terminate_threads)
                next_thread = Thread(target=send_notification,
                                     args=(uuid, push_client['pcli_token'], cert_path, address, port),
                                     kwargs={'push': push},
                                     name=f'Thread_{nc:003}_{nn:003}_(apns_notice)')
                next_thread.start()
            else:
                send_notification(uuid, push_client['pcli_token'], cert_path, address, port, push=push)

        logger.info("Sleep for 10 seconds, sequence cycle number={} ended...".format(str(nc)))
        time.sleep(10)

if __name__ == '__main__':
    infinity_loop()
