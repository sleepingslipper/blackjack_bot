# -*- coding: utf-8 -*-

import config
from main import Bot

try:
    Bot(phone=config.number, qiwiApi=config.tokenQiwi, token=config.token, admin_id=config.admin_id)
except Exception as e:
    print(f'Произошла ошибка: {e}')
    input('Нажми Enter')