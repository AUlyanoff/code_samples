#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
import time
import platform

from paths import CACHE_DIR

import config
import log

logger = logging.getLogger(__name__)


def cache_cleaner():
    """Очистка кэша передачи файлов инженерного сервера nginx"""
    """
        cleaning_period - период очистки, в секундах
        shelf_life - срок годности файла, в секундах
        1. Просмотреть файлы, и для которых
           (текущее_время - время последнего_доступа) > shelf_life, то удалить этот файл
        2. Запуститься через cleaning_period
    """

    config.objects.prefix_loggers = "c_c_"
    logger.fatal(f"CACHE CLEANER started at {datetime.now().strftime('%d-%m-%Y %H:%M:%S, %A')}...")
    os_pl = platform.system()
    logger.debug(f"OS {os_pl}, fcntl{'_win' if os_pl == 'Windows' else ''} used (files descriptor control system)")

    cache_dir = CACHE_DIR                                       # путь к кэшу
    logger.fatal(f"Cache directory `{cache_dir}`")
    cleaning_period = config.objects.find_cleaning_period()     # период очистки
    shelf_life = config.objects.find_shelf_life()               # разрешённое время жизни файла

    while True:
        now = time.time()
        logger.warning(f"Shelf life = {shelf_life} sec., period = {cleaning_period} sec. - "
                       f"cache check started at {time.ctime(now)}")

        erased = 0  # счётчик удалённых файлов
        for folder, subfolders, files in os.walk(cache_dir):    # обход кэша с подкаталогами
            for file in files:
                full_name = os.path.join(folder, file)
                atime = os.stat(full_name).st_atime             # время последнего доступа
                if now - atime > shelf_life:
                    os.unlink(full_name)                        # удаление устаревшего файла
                    erased += 1
                    logger.debug(f"{time.ctime(atime)} - erased {full_name}")
                else:
                    logger.debug(f"{time.ctime(atime)} - cached {full_name}")
        logger.warning(f"{erased:003} files erased - cache check ended")
        time.sleep(cleaning_period)


if __name__ == '__main__':
    cache_cleaner()
