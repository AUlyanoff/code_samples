#!/usr/bin/env python
# -*- coding: utf-8 -*-
from textwrap import wrap       # разрезает строку на части с переносом целых слов, и складывает эти части в список
import cchardet as chardet      # пытается определить кодировку заранее неизвестной последовательности байт


def trunc_str(s, len_str=140, amount=16, delimiter='\n\t'):
    """ Разбиение длинной строки на короткие для удобства отображения
        s - строка,
        которая разбивается разделителем delimiter
        на части длиной len_str,
        но не более amount раз,
        если пришлось обрезать, пишем сколько символов обрезано """

    if s is not None:       # а есть с чем работать?
        res = str(s) if not isinstance(s, str) else s   # всё что к нам приходит, становится строкой
        lns = len(res)
        if lns > len_str:   # а не слишком короткая?
            chars_left = lns - len_str * amount
            if 0 < chars_left < len_str // 2:   # если не влезло меньше чем пол-строки,
                amount += 1                     # то добавим строчку
            lst = wrap(res, len_str)[:amount]   # режем на куски длиной по len_str, а потом отбрасываем лишнее
            if len_str * amount < lns:          # если не влезли в amount строк, в последней допишем, сколько обрезано
                res = delimiter.join(lst)[:-len(delimiter)]     # от конца строки-результата отрезаем разделители
                res = f'{res}{delimiter}... cut off, {chars_left} characters left!'
            else:
                res = delimiter.join(lst)   # [:-len(delimiter)]
    else:
        res = s
    return res


def convert_to_short(args):
    """ Сделаем лог ХП более читаемым, убрав синтаксический мусор и нечитаемые строки.
        Оставим только тип, имя и значение переменной базы.
    """
    if args:
        short_args = list()
        for arg in args:
            _arg_value = arg.value
            if arg.value is not None:   # если значения не установлено, ничего делать не надо
                # сначала подавление нечитаемых символов ---------------------------------------------------------
                # известны имена некоторых нечитаемых параметров
                if arg.name.upper() in ["CERT_FILE", "CERT_FINGERPRINT", ]:         # это сертификаты
                    _arg_value = trunc_str(arg.value, 64, 1, ' ')                   # укоротим их до 64 символов
                # "эвристический" блок
                elif arg.type.db_type.upper() in ["BYTEA", "BYTEARRAY"]:            # там подозрительное
                    if not isinstance(arg.value, bytes):                            # это не байты ?
                        _arg_value = f"в поле {arg.name} ({arg.type.db_type}) данные неправильного типа {arg.value}"
                    elif chardet.detect(bytes(arg.value))['encoding'] not in ["ASCII", "UTF-8"]:  # это нечитаемо?
                        _arg_value = trunc_str(arg.value, 128, 1, ' ')              # укоротим его до 128 символов
                    else:                                                           # хоть и байты, но внутри ASCII
                        _arg_value = arg.value
                # ------------------------------------------------------------------------------------------------
                elif arg.type.db_type == 'VARCHAR' and arg.value is not None:
                    _arg_value = f"'{arg.value}'"

            short_args.append(f"{arg.type.db_type.lower()} {arg.name}={_arg_value}")
        s = trunc_str(", ".join(short_args), delimiter='\n\t\t\t')
    else:
        s = ''
    return s
