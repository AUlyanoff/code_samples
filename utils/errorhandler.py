#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
import traceback
from flask import jsonify, request
from werkzeug.exceptions import NotFound, MethodNotAllowed
from threading import Thread

import config

from database.entities import exceptions
from database.addons import ResultCheckError
from utils.exceptions_utils import (BadCertException, BadKeyException,
                                    KeyCertNotMatchException, DocumentPermissionException,
                                    DocumentNotFoundException)

logger = logging.getLogger(__name__)


def all_error(err):
    """Базовый обработчик исключений"""
    """ Получает управление от flask-а, зарегистрирован при старте MDM-сервера в src/app/mdm_app.py """
    ex_type, ex, tb = sys.exc_info()    # запросим стек вызовов

    # Если режим логирования это DEBUG или не установлен, или стек пустой,
    if logger.getEffectiveLevel() <= logging.DEBUG or not sys.exc_info():
        raise err                              # то стандартная обработка.

    req_uri = request.environ['REQUEST_URI'][1:] if request else "(Error occurred outside request)"  # имя API
    my_doc = all_error.__doc__

    if isinstance(err, NotFound):
        response, stat = {"error": f"url {req_uri} resource not found {err}"}, 404
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\turl or resource {req_uri} not found\n\t\t{err}\n{NotFound.description}\n")

    elif isinstance(err, FileNotFoundError):
        response, stat = {"error": f"{req_uri}, file not found - {err}"}, 404
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tfor {req_uri} file no found\n\t\t{err}\n")

    elif isinstance(err, ValueError):
        response, stat = {"error": f"{req_uri}, value error - {err}"}, 400
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tfor {req_uri} value error\n\t\t{err}\n")

    elif isinstance(err, TypeError):
        response, stat = {"error": f"{req_uri}, type error - {err}"}, 400
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tfor {req_uri} type error\n\t\t{err}\n")

    elif isinstance(err, AssertionError):
        if ResultCheckError.rc in (-3301, -3303):
            response, stat = {"error": f"{req_uri}, Kit not found - {ResultCheckError}"}, 401
            logger.error(f"({my_doc})"
                         f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                         f"ended HTTP={stat}\n\t\tfor {req_uri} Kit not found"
                         f"\n\t\trc={ResultCheckError.rc} error={ResultCheckError.err} proc={ResultCheckError.proc}\n")
        else:
            logger.exception('Неожиданная ошибка ', err, sys.exc_info())
            raise err

    elif isinstance(err, MethodNotAllowed):
        response, stat = {"error": f"for {req_uri} method '{request.method}' not allowed"}, 405
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tfor {req_uri} method '{request.method}' not allowed\n")

    elif isinstance(err, BadCertException):             # Файл сертификата есть, но внутри не сертификат
        cert_path = config.objects.config_find_ios_signature_files_crt()
        response, stat = {"error": f"Bad or corrupted certificate, path {cert_path} ({err}) API {req_uri}"}, 500
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tBad or corrupted certificate, path {cert_path} "
                     f"({err})\n\t\tAPI {req_uri}\n")

    elif isinstance(err, BadKeyException):              # Файл ключа есть, но внутри не ключ
        key_path = config.objects.config_find_ios_signature_files_key()
        response, stat = {"error": f"Bad or corrupted private key, path {key_path} ({err}) API {req_uri}"}, 500
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tBad or corrupted certificate, path {key_path} "
                     f"({err})\n\t\tAPI {req_uri}\n")

    elif isinstance(err, KeyCertNotMatchException):    # Несоответствие ключа и сертификату, это ключ от др. сертификата
        key_path = config.objects.config_find_ios_signature_files_key()
        response, stat = {"error": f"Certificate and key do not match, path {key_path} ({err}) API {req_uri}"}, 500
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tCertificate and key do not match, path {key_path} "
                     f"({err})\n\t\tAPI {req_uri}\n")

    elif isinstance(err, DocumentPermissionException):  # Нет доступа к файлу сертификата или ключа
        response, stat = {"error": f"Certificate permission error ({err}) API {req_uri}"}, 500
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tCertificate permission error ({err}) "
                     f"\n\t\tAPI {req_uri}\n")

    elif isinstance(err, DocumentNotFoundException):    # Не найден файл сертификата
        response, stat = {"error": f"Certificate file not found ({err}) API {req_uri}"}, 500
        logger.error(f"({my_doc})"
                     f"\n\t<~\t{str(traceback.extract_tb(tb)[-1][0])}: {str(traceback.extract_tb(tb)[-1][2])} "
                     f"ended HTTP={stat}\n\t\tCertificate file not found ({err}) "
                     f"\n\t\tAPI {req_uri}\n")

    elif isinstance(err, exceptions.DatabaseError):
        response, stat = f"Database error or database connection error", 500
        if 'closed the connection unexpectedly' not in str(err):
            ll = list()
            ll.append(f'({my_doc})\n<~\t{req_uri} ended with Database or database connection error, HTTP={stat}'
                      f'\n\t\tSet debug level for details iosmdm.yml/log D')
            for obj in traceback.extract_tb(tb):            # накапливаем traceback для логирования
                ll.append(f'\t\t{obj[0]}, called: {obj[2]}')
                ll.append(f'\t\t\tLine: {obj[1]}: {obj[3]}')
            ll.append(f'\t\tError: {err}.')
            logger.error("\n".join(ll)+"\n")

        def handle_exit():
            """Функция задерживает останов сервера на .sleep(<секунд>)"""
            """Импортируем цинично внутри функции, потому что эти библиотеки нужно только для останова сервера"""
            import time
            from os import devnull
            import _thread
            time.sleep(2)             # чтобы обработчик успел завершиться и вернуть response
            logger.critical("Server forcibly stopped for restart...\n")
            sys.stderr = open(devnull, "w")     # sys.stdout = open(os.devnull, "w")  # подавление вывода в консоль
            _thread.interrupt_main()  # уроним сервер как будто от клавиатуры, а его контейнер перезапустит
            # sys.stdout = sys.__stdout__       # sys.stderr = sys.__stderr__         # восстановление вывода в консоль

        thread = Thread(target=handle_exit)
        thread.start()

    else:
        response, stat = {"error": f"{err.__class__.__name__}: {err}"}, 500
        ll = list()
        ll.append(f'\t<~\tError occurred in request processing: {req_uri} ended with HTTP={stat}')
        for obj in traceback.extract_tb(tb):            # накапливаем traceback для логирования
            ll.append(f'\t\t{obj[0]}, called: {obj[2]}')
            ll.append(f'\t\t\tLine: {obj[1]}: {obj[3]}')
        ll.append(f'\t\tError: {err}.')
        logger.error(f"({my_doc})\n"+"\n".join(ll)+"\n")

    return jsonify(response), stat
