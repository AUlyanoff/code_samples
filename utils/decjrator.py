# -*- coding: utf-8 -*-
import json
import logging
import re
from functools import wraps

import jsonschema
from flask import request, jsonify
from xmlschema import XMLSchema
from xmlschema.validators.exceptions import XMLSchemaValidatorError

import config
import settings
from utils.json_utils import it_is_json as is_json
from utils.string import trunc_str
from utils.repository.kit_service import kit_id_exist  # для декоратора проверки check_kit_id

logger = logging.getLogger(__name__)



def check_kit_id(func):
    """Декоратор проверки номера КИТ в X-MCC-ID"""
    """
    :param  func: API-функция, X-MCC-ID
    :return: проверенный kit_id, ранее принятая func
    Если kit_id неверен, то API не вызывается.
    """
    @wraps(func)  # для исключения перезаписи конечной точки flask
    def wrap(*args, **kwargs):
        kit_id = request.headers.get("X-MCC-ID", None)
        api_path = request.base_url[request.base_url.find('api', 1):]  # путь вызова API
        logger.debug(f"\n\t~>\t\tcheck_kit_id ({check_kit_id.__doc__}) for API {api_path} kit_id={kit_id} started")
        status, err = None, None  # текст ошибки и код HTTP ответа

        if kit_id is None:
            status, err = 400, "HTTP header 'X-MCC-ID' not found in request"
        elif kit_id == '':
            status, err = 412, "HTTP header 'X-MCC-ID' contains an empty string"
        elif not kit_id.isdigit():
            status, err = 412, f"kit_id='{kit_id}' is not a positive integer"
        elif int(kit_id) == 0:
            status, err = 412, "kit_id is zero"
        elif not kit_id_exist(kit_id=kit_id):
            status, err = 475, f"kit_id={kit_id} not found in database"

        if status is not None:
            logger.error(f"\n\t<~\t\tcheck_kit_id, error for API {api_path}, HTTP={status}, ended"
                         f"\n\t\t\tfor {func.__name__} ({str(func.__doc__).strip()}), {err}")
            return jsonify({"error": err}), status
        else:
            logger.debug(f"\n\t<~\t\tcheck_kit_id for API {api_path}, kit_id={kit_id} ok, ended")
            return func(*args, **kwargs, kit_id=int(kit_id))    # вызов API

    return wrap