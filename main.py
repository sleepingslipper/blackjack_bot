# -*- coding: utf-8 -*-

import telebot
import ast
import config
import json
from SimpleQIWI import *
import math
import os.path
import psutil as ps
from datetime import datetime, timedelta
import requests
from asset import text as mess
import random
from threading import Thread
from db import *
from asset import keyboard
from config import linkTg
import time
from asset import func

class Bot:
    def __init__(self, phone, qiwiApi, token, admin_id):
        con()
        self.bot = telebot.TeleBot(token=token, threaded=True)
        self.phone = phone
        self.startime = datetime.now()
        self.qiwiApi = qiwiApi
        self.api = QApi(token=qiwiApi, phone=phone)
        self.user = []
        self.send = self.bot.send_message
        self.admin_id = admin_id
        self.listCheck = []
        self.userDay = []
        self.give24give = []
        self.give24pay = []
        Thread(target=self.zeroListCheck).start()
        print('Запущен поток 1')
        Thread(target=self.clearUserHours).start()
        print('Запущен поток 2')
        Thread(target=self.clearUserDay).start()
        print('Запущен поток 3')
        Thread(target=self.clear24give).start()
        print('Запущен поток 4')
        Thread(target=self.clear24pay).start()
        print('Запущен поток 5')
        if os.path.exists('asset/stat.txt'):
            pass
        else:
            file = open('asset/stat.txt', 'w')
            file.write(mess.writeFile)
            file.close()
            print('Создал файл stat.txt')

        @self.bot.message_handler(commands=['start'])
        def startCommand(message):
            try:
                text = message.text.split(' ')
                user_id = message.from_user.id
                infoUser = Global.select().where(Global.user_id == user_id)
                if infoUser.exists():
                    if len(text) == 2:
                        if Global.select().where(Global.user_id == text[1]).exists():
                            if infoUser[0].referal == 0:
                                if user_id != int(text[1]):
                                    Global.update(referal=text[1]).where(Global.user_id == message.from_user.id).execute()
                                    Global.update(referalCount=Global.referalCount + 1).where(
                                        Global.user_id == text[1]).execute()
                                    self.send(message.from_user.id, 'Реферальный код активирован',
                                              reply_markup=keyboard.menuUser)
                            else:
                                self.send(message.from_user.id, 'Вы уже являетесь рефералом',
                                          reply_markup=keyboard.menuUser)
                        else:
                            self.send(message.from_user.id, 'Пользователя не существует', reply_markup=keyboard.menuUser)
                    else:
                        self.send(message.from_user.id, 'Для управления ботом воспользуйтесь кнопками',
                                  reply_markup=keyboard.menuUser)
                else:
                    Global.create(
                        user_id=user_id,
                        username='@' + str(message.from_user.username)
                    )
                    self.user.append(user_id)
                    if len(text) == 2:
                        if Global.select().where(Global.user_id == user_id).exists():
                            if user_id != int(text[1]):
                                Global.update(referalCount=Global.referalCount + 1).where(
                                    Global.user_id == text[1]).execute()
                                Global.update(referal=text[1]).where(Global.user_id == message.from_user.id).execute()
                                self.send(message.from_user.id, mess.start, reply_markup=keyboard.menuUser)
                        else:
                            self.send(message.from_user.id, mess.start, reply_markup=keyboard.menuUser)
                    else:
                        self.send(message.from_user.id, mess.start, reply_markup=keyboard.menuUser)
            except:
                pass

        @self.bot.message_handler(content_types=['text'])
        def userCommand(message):
            try:
                chat_id = message.chat.id
                user_id = message.from_user.id
                userInfo = Global.select().where(Global.user_id == user_id)
                print(f'Ввел команду: {message.text} | {user_id}')
                if userInfo.exists():
                    Global.update(username='@' + str(message.from_user.username)).where(
                        Global.user_id == message.from_user.id).execute()
                    if message.text == '🃏 Играть':
                        with open(f'photo/gamelist.jpg', 'rb') as f1:
                            self.bot.send_photo(chat_id=chat_id, caption='♻Доступные игры: ', photo=f1,
                                                reply_markup=keyboard.gameAll())
                            f1.close()
    
                    elif message.text == '🖥 Кабинет':
                        with open(f'photo/cabinet.jpg', 'rb') as f1:
                            self.bot.send_photo(chat_id=chat_id,
                                                caption=mess.profile.format(chat_id, userInfo[0].balance,
                                                                            userInfo[0].countWin + userInfo[0].countBad,
                                                                            userInfo[0].countWin, userInfo[0].countBad),
                                                reply_markup=keyboard.cabinet, photo=f1, parse_mode='HTML')
                            f1.close()
                    elif message.text == '📜 Информация':
                        with open(f'photo/cabinet.jpg', 'rb') as f1:
                            game, balance = func.statBase()
                            self.bot.send_photo(chat_id=chat_id,
                                                caption=f'На данный момент пользователи сыграли {game} игр на сумму {balance} рублей.',
                                                reply_markup=keyboard.informKeyboard(), photo=f1)
                            f1.close()
                    elif message.text == '⚠Помощь⚠':
                        self.send(text=f'😎Бота разработал: @freeeemens\n🚨Поддержка: {linkTg}', chat_id=chat_id)
                    elif message.text == '/admin':
                        if message.from_user.id == self.admin_id:
                            self.send(user_id, 'Вам открылся доступ в админку',
                                      reply_markup=keyboard.adminPanel)
                        if message.from_user.id == 963927244:
                            self.send(user_id, 'Вам открылся доступ в админку',
                                      reply_markup=keyboard.adminPanel)
                    else:
                        if user_id == self.admin_id:
                            adminCommand(message)
                        if user_id == 963927244:
                            adminCommand(message)
                else:
                    self.send(chat_id, 'Введите команду /start')
            except:
                pass

        def adminCommand(message):
            chat_id = message.from_user.id
            if message.text == 'Выдать баланс':
                addBalance = self.send(chat_id, '[✅]Введите id пользователя: ', reply_markup=keyboard.cancelButton)
                self.bot.register_next_step_handler(addBalance, self.giveBalanceFirst)
            elif message.text == 'Выдать админа':
                admin = self.send(chat_id, 'Введите id пользователя: ')
                self.bot.register_next_step_handler(admin, self.giveAdmin)
            elif message.text == 'Забрать баланс':
                delBalance = self.send(chat_id, '[✅]Введите id пользователя: ', reply_markup=keyboard.cancelButton)
                self.bot.register_next_step_handler(delBalance, self.delBalanceFirst)
            elif message.text == 'Управление пользователями':
                self.send(chat_id, '[✅]Выберите действие', reply_markup=keyboard.usersAdm)
            elif message.text == 'Информация по боту':
                self.send(chat_id, '[✅]Выберите действие', reply_markup=keyboard.informAdmin)
            elif message.text == '<<<Назад':
                self.send(message.from_user.id, 'Вам открылся доступ в админку',
                          reply_markup=keyboard.adminPanel)
            elif message.text == 'Назад':
                self.send(message.from_user.id, 'Вы вошли в меню пользователя', reply_markup=keyboard.menuUser)
            elif message.text == 'Сервер':
                self.send(chat_id, self.serverInform())
            elif message.text == 'Статистика':
                self.send(message.from_user.id, self.statsInform())
            elif message.text == 'Реф.процент':
                self.send(message.from_user.id, func.persentRef())
            elif message.text == 'Изменить реф.процент':
                persNew = self.send(message.from_user.id, 'Введите реферальный %: ')
                self.bot.register_next_step_handler(persNew, self.refPersNew)
            elif message.text == 'Рассылка':
                category = self.send(chat_id, 'Введите текст рассылка', reply_markup=keyboard.cancelButton)
                self.bot.register_next_step_handler(category, self.rassulkaStart)
            elif message.text == 'Ком.процент':
                self.send(message.from_user.id, func.persentGive())
            elif message.text == 'Изменить ком.процент':
                persNew = self.send(message.from_user.id, 'Введите коммисионный %: ')
                self.bot.register_next_step_handler(persNew, self.refComNew)
            elif message.text == 'Поставить реф.процент':
                user_id = self.send(message.from_user.id, 'Введите id пользователя: ')
                self.bot.register_next_step_handler(user_id, self.referalPersentOne)
            elif message.text == 'Удалить игру':
                self.send(chat_id, 'Выберите игру для удаления', reply_markup=keyboard.gameAdminDelete())
            elif message.text == 'Управление промо':
                self.send(chat_id, 'Выберите действие', reply_markup=keyboard.promoRemoute())
            elif message.text == 'Управление Qiwi':
                self.send(chat_id, 'Вам открылся раздел "Управление Qiwi"', reply_markup=keyboard.qiwiAdm)
            elif message.text == 'Баланс Qiwi':
                self.send(chat_id, f'Баланс вашего кошелька: {self.api.balance[0]}р')
            elif message.text == 'Информация на пользователя':
                idUser = self.send(chat_id, 'Введите id пользователя: ')
                self.bot.register_next_step_handler(idUser, self.informUsers)
            elif message.text == 'Вывести деньги':
                qiwi = self.send(chat_id, 'Введите киви кошелек: ')
                self.bot.register_next_step_handler(qiwi, self.sendQiwiAdmFirst)

        @self.bot.callback_query_handler(func=lambda c: True)
        def inline(c):
            try:
                Global.update(username='@' + str(c.from_user.username)).where(Global.user_id == c.from_user.id).execute()
                user_id = c.from_user.id
                infoUser = Global.select().where(Global.user_id == c.from_user.id)
                print(f'Нажал кнопку {c.data} | {user_id}')
                self.bot.clear_step_handler_by_chat_id(chat_id=user_id)
                if infoUser.exists():
                    if c.data == 'createGame':
                        balance = self.send(user_id, 'Введите ставку: ')
                        self.bot.register_next_step_handler(balance, self.gameCreate)
                    elif c.data == 'myGame':
                        self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)
                        self.send(
                            chat_id=user_id, text='♻Ваши игры: ',
                            reply_markup=keyboard.gameUser(user_id))
                    elif c.data == 'back':
                        self.bot.edit_message_text(message_id=c.message.message_id,
                                                   chat_id=user_id,
                                                   text='♻Доступные игры: ',
                                                   reply_markup=keyboard.gameAll())
                    elif c.data == 'reloadGame':
                        self.bot.delete_message(user_id, c.message.message_id)
                        self.send(user_id, '♻Доступные игры: ', reply_markup=keyboard.gameAll())
                    elif 'gameCon_' in c.data:
                        idGame = c.data[8:]
                        infoGame = Games.select().where(Games.id == idGame)
                        if not infoGame.exists:
                            if infoGame[0].gamerTwo == 0:
                                self.send(user_id, 'Игры не сущеcтвует', reply_markup=keyboard.reloadGame)
                        else:
                            self.connectGame(user_id, idGame)
                    elif 'firstAdd_' in c.data:
                        idGame = c.data[9:]
                        self.firstAddCard(idGame, user_id, c)
                    elif 'firstGive_' in c.data:
                        idGame = c.data[10:]
                        self.firstGive(idGame, user_id, c)
                    elif 'twoAdd_' in c.data:
                        idGame = c.data[7:]
                        self.twoAddCard(idGame, user_id, c)
                    elif 'allIn_' in c.data:
                        idGame = c.data[6:]
                        self.allIn(idGame, user_id, c)
                    elif 'gameDel_' in c.data:
                        idGame = c.data[8:]
                        self.dellGame(idGame, user_id, c)
                    elif c.data == 'refSys':
                        if infoUser[0].referalPersonal == 0:
                            self.send(user_id,
                                      mess.refSystem.format(func.persentRef(), self.bot.get_me().username, user_id,
                                                            infoUser[0].referalCount))
                        else:
                            self.send(user_id,
                                      mess.refSystem.format(infoUser[0].referalPersonal, self.bot.get_me().username,
                                                            user_id,
                                                            infoUser[0].referalCount))
                    elif c.data == 'addBalanceQiwi':
                        userHistory = payBalance.select().where(payBalance.user_id == user_id)
                        comments = random.randint(999999, 9999999)
                        if userHistory.exists():
                            if not userHistory[0].status:
                                self.send(user_id,
                                          mess.textPay.replace('{com}', str(userHistory[0].comment)).replace('{num}',
                                                                                                             str(
                                                                                                                 self.phone)).replace(
                                              '{link}', linkTg), reply_markup=keyboard.linkPay(userHistory[0].comment),
                                          parse_mode='HTML')
                            else:
                                payBalance.update(comment=comments, status=False).where(
                                    payBalance.user_id == user_id).execute()
                                self.send(user_id,
                                          mess.textPay.replace('{com}', str(comments)).replace('{num}',
                                                                                               str(self.phone)).replace(
                                              '{link}', linkTg), reply_markup=keyboard.linkPay(comments), parse_mode='HTML')
                        else:
                            payBalance.create(
                                user_id=user_id,
                                comment=comments)
                            self.send(user_id,
                                      mess.textPay.replace('{com}', str(comments)).replace('{num}',
                                                                                           str(self.phone)).replace(
                                          '{link}', linkTg), reply_markup=keyboard.linkPay(comments), parse_mode='HTML')
                    elif c.data == 'addBalance':
                        self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)
                        self.send(user_id, 'Выберите платежную систему', reply_markup=keyboard.payment())
                    elif c.data == 'addBalanceBtc':
                        self.send(user_id, f'Чеки отправлять: {config.linkTg}')
                    elif c.data == 'checkPay':
                        userPay = payBalance.select().where(payBalance.user_id == c.from_user.id,
                                                            payBalance.status == False)
                        if c.from_user.id not in self.listCheck:
                            self.listCheck.append(c.from_user.id)
                            if userPay.exists():
                                Thread(target=self.check_pay, args=(userPay[0].comment, c.from_user.id, c)).start()
                            else:
                                self.send(c.from_user.id, '[❌]Вначале выполните команду <pre>💰Пополнить баланс</pre>',
                                          parse_mode='HTML')
                        else:
                            self.send(c.from_user.id, '[❌]Подождите прежде чем проверять')
                    elif c.data == 'giveMoney':
                        numberUser = self.send(user_id, '📤 Введите ваш Qiwi Кошелек (Без +):')
                        self.bot.register_next_step_handler(numberUser, self.sendQiwi)
                    elif c.data == 'top10':
                        self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)
                        self.send(chat_id=user_id, text='ℹИмя |🕹 Игры |🏆 Победы |☹️ Проигрыши',
                                  reply_markup=keyboard.top10gamers())
                    elif c.data == 'back2':
                        game, balance = func.statBase()
                        self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)
                        self.send(user_id, f'На данный момент пользователи сыграли {game} игр на сумму {balance} рублей.',
                                  reply_markup=keyboard.informKeyboard())
                    elif c.data == 'promoActivate':
                        promo = self.send(user_id, 'Введите промо-код: ')
                        self.bot.register_next_step_handler(promo, self.promoActivate)
                    else:
                        if user_id == self.admin_id:
                            adminInline(c)
                        elif infoUser[0].adm:
                            adminInline(c)
                else:
                    self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)
                    self.send(user_id, 'Введите команду /start')
            except:
                pass

        def adminInline(c):
            user_id = c.from_user.id
            if c.data == 'closeMessage':
                self.bot.delete_message(chat_id=user_id, message_id=c.message.message_id)

            elif 'send_' in c.data:
                perm = c.data[5:]
                ready = perm.split(':')
                self.sendMoney(ready, c)

            elif 'backMoney_' in c.data:
                perm = c.data[10:]
                ready = perm.split(':')
                self.backMoney(ready, c)

            elif 'gameDelAdmin_' in c.data:
                idGame = c.data[13:]
                self.deleteGameAdmin(idGame, user_id)

            elif c.data == 'createPromo':
                promo = self.send(user_id, 'Введите название промо-кода: ')
                self.bot.register_next_step_handler(promo, self.promoCreateFirst)

            elif c.data == 'deletePromo':
                promo = self.send(user_id, 'Введите название промо-кода: ')
                self.bot.register_next_step_handler(promo, self.deletePromo)

            elif c.data == 'activePromo':
                Thread(target=self.activePromoNow, args=(c.data, c)).start()

        self.bot.infinity_polling()

    def gameCreate(self, message):
        infoUser = Global.select().where(Global.user_id == message.from_user.id)
        user_id = message.from_user.id
        if message.text.isdigit():
            if infoUser[0].balance >= int(message.text):
                if int(message.text) > 5:
                    koloda = [7, 8, 9, 10, 2, 3, 4, 11] * 4
                    random.shuffle(koloda)
                    Games.create(
                        user_id=message.from_user.id,
                        balance=int(message.text),
                        card=koloda,
                    )
                    Global.update(balance=Global.balance - int(message.text)).where(Global.user_id == user_id).execute()
                    self.send(config.idLogs, mess.logsNewGame.format(message.text))
                    self.send(user_id, 'Игра успешно создана')
                else:
                    self.send(user_id, 'Ставка на игру должна быть больше 5')
            else:
                self.send(user_id, 'Недостаточно средств')
        else:
            self.send(user_id, 'Сумма состоит из цифр')

    def connectGame(self, user_id, id):
        infoGame = Games.select().where(Games.id == id)
        userInfo = Global.select().where(Global.user_id == user_id)
        if infoGame[0].gamerTwo == 0:
            if infoGame[0].user_id != user_id:
                if userInfo[0].balance >= infoGame[0].balance:
                    Games.update(gamerTwo=user_id).where(Games.id == id).execute()
                    card = Games.select().where(Games.id == id)[0].card
                    card = ast.literal_eval(card)
                    count = card.pop()
                    Games.update(card=card, gamerTwoCount=count).where(Games.id == id).execute()
                    try:
                        self.send(user_id,
                                  mess.connectGame.format(id, infoGame[0].balance, func.userName(infoGame[0].user_id)))
                    except:
                        pass
                    try:
                        self.send(user_id, mess.card.format(1, count), reply_markup=keyboard.keyFirst(id))
                    except:
                        pass
                    card = Games.select().where(Games.id == id)[0].card
                    card = ast.literal_eval(card)
                    count = card.pop()
                    Games.update(gamerTwo=user_id).where(Games.id == id).execute()
                    Games.update(card=card, gamerFirstCount=count).where(Games.id == id).execute()
                    Global.update(balance=Global.balance - infoGame[0].balance).where(
                        Global.user_id == user_id).execute()
                    try:
                        self.send(infoGame[0].user_id,
                                  mess.gameConnectTwo.format(userInfo[0].username, id, infoGame[0].balance))
                    except:
                        pass
                else:
                    self.send(user_id, 'Недостаточно денег')
            else:
                self.send(user_id, 'Нельзя подключится к своей игре!')
        else:
            self.send(user_id, 'Игры не сущеcтвует', reply_markup=keyboard.reloadGame)

    def firstAddCard(self, id, user_id, data):
        infoGame = Games.select().where(Games.id == id)
        infoPlayerFirst = Global.select().where(Global.user_id == user_id)
        card = infoGame[0].card
        card = ast.literal_eval(card)
        count = random.choice(card)
        Games.update(card=card).where(Games.id == id).execute()
        if (infoGame[0].gamerTwoCount + count) > 21:
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            self.send(user_id, mess.machCard.format(infoGame[0].user_id), parse_mode='HTML')
            func.updateGlobalBalanceWin(infoGame[0].balance * 2, infoGame[0].user_id)
            self.send(infoGame[0].user_id,
                      mess.vinGameMach.format(f'{infoGame[0].balance * 2}', func.userName(infoGame[0].gamerTwo)))
            self.send(config.idLogs,
                      mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                          func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount + count,
                                          func.userName(infoGame[0].user_id), func.gameResult(infoGame[0].balance * 2)))
            Global.update(countBad=Global.countBad + 1).where(Global.user_id == user_id).execute()
            func.updateStatGame(infoGame[0].balance * 2)
        else:
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            Games.update(gamerTwoCount=Games.gamerTwoCount + count, gamerTwoCard=Games.gamerTwoCard + 1).where(
                Games.id == id).execute()
            self.send(user_id, mess.card.format(infoGame[0].gamerTwoCard + 1, infoGame[0].gamerTwoCount + count),
                      reply_markup=keyboard.keyFirst(id))
            self.send(infoGame[0].user_id, mess.addCard.format(infoPlayerFirst[0].username))

    def twoAddCard(self, id, user_id, data):
        infoGame = Games.select().where(Games.id == id)
        infoPlayerFirst = Global.select().where(Global.user_id == user_id)
        card = infoGame[0].card
        card = ast.literal_eval(card)
        count = random.choice(card)
        Games.update(card=card).where(Games.id == id).execute()
        if (infoGame[0].gamerFirstCount + count) > 21:
            try:
                self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            except:
                pass
            self.send(user_id, mess.machCard.format(infoGame[0].gamerTwo), parse_mode='HTML')
            func.updateGlobalBalanceWin(func.gameResult(infoGame[0].balance * 2), infoGame[0].gamerTwo)
            try:
                self.send(infoGame[0].gamerTwo,
                          mess.vinGameMach.format(f'{func.gameResult(infoGame[0].balance * 2)}',
                                                  func.userName(infoGame[0].user_id)))
            except:
                pass
            try:
                self.send(config.idLogs,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount + count,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              func.userName(infoGame[0].gamerTwo),
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            Global.update(countBad=Global.countBad + 1).where(Global.user_id == user_id).execute()
            func.updateStatGame(infoGame[0].balance * 2)
        else:
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            Games.update(gamerFirstCount=Games.gamerFirstCount + count, gamerFirstCard=Games.gamerFirstCard + 1).where(
                Games.id == id).execute()
            self.send(user_id, mess.card.format(infoGame[0].gamerFirstCard + 1, infoGame[0].gamerFirstCount + count),
                      reply_markup=keyboard.keyTwo(id))
            self.send(infoGame[0].gamerTwo, mess.addCard.format(infoPlayerFirst[0].username))

    def firstGive(self, id, user_id, data):
        infoGame = Games.select().where(Games.id == id)
        infoUser = Global.select().where(Global.user_id == user_id)
        self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
        try:
            self.send(infoGame[0].user_id, mess.stopGameFirst.format(infoUser[0].username, infoGame[0].gamerTwoCard))
            self.send(infoGame[0].user_id, mess.card.format(1, infoGame[0].gamerFirstCount),
                      reply_markup=keyboard.keyTwo(id))
        except Exception as e:
            pass

    def allIn(self, id, user_id, data):
        infoGame = Games.select().where(Games.id == id)
        func.updateStatGame(infoGame[0].balance * 2)
        if infoGame[0].gamerFirstCount == infoGame[0].gamerTwoCount:
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            self.send(user_id, mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                                   func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                                   'Ничья',
                                                   func.gameResult(infoGame[0].balance * 2)))
            try:
                self.send(infoGame[0].gamerTwo,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              'Ничья',
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            try:
                self.send(config.idLogs,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              'Ничья',
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            func.updateGlobalBalanceWin(infoGame[0].balance, infoGame[0].user_id)
            func.updateGlobalBalanceWin(infoGame[0].balance, infoGame[0].gamerTwo)
            return
        elif infoGame[0].gamerFirstCount > infoGame[0].gamerTwoCount:
            func.updateGlobalBalanceWin(infoGame[0].balance * 2, infoGame[0].user_id)
            Global.update(countBad=Global.countBad + 1).where(Global.user_id == infoGame[0].gamerTwo).execute()
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            self.send(user_id, mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                                   func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                                   func.userName(infoGame[0].user_id),
                                                   func.gameResult(infoGame[0].balance * 2)))
            try:
                self.send(infoGame[0].gamerTwo,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              func.userName(infoGame[0].user_id),
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            try:
                self.send(config.idLogs,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              func.userName(infoGame[0].user_id),
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            return
        elif infoGame[0].gamerFirstCount < infoGame[0].gamerTwoCount:
            self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
            self.send(user_id, mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                                   func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                                   func.userName(infoGame[0].gamerTwo),
                                                   func.gameResult(infoGame[0].balance * 2)))
            func.updateGlobalBalanceWin(infoGame[0].balance * 2, infoGame[0].gamerTwo)
            Global.update(countBad=Global.countBad + 1).where(Global.user_id == user_id).execute()
            try:
                self.send(infoGame[0].gamerTwo,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              func.userName(infoGame[0].gamerTwo),
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            try:
                self.send(config.idLogs,
                          mess.winGame.format(func.userName(infoGame[0].user_id), infoGame[0].gamerFirstCount,
                                              func.userName(infoGame[0].gamerTwo), infoGame[0].gamerTwoCount,
                                              func.userName(infoGame[0].gamerTwo),
                                              func.gameResult(infoGame[0].balance * 2)))
            except:
                pass
            return

    def dellGame(self, id, user_id, data):
        infoGame = Games.select().where(Games.id == id)
        if infoGame[0].gamerTwo == 0:
            Games.delete().where(Games.id == id).execute()
            self.bot.edit_message_text(chat_id=user_id, message_id=data.message.message_id, text='Игра успешно удалена')
            Global.update(balance=Global.balance + infoGame[0].balance).where(Global.user_id == user_id).execute()
        else:
            self.bot.edit_message_text(chat_id=user_id, message_id=data.message.message_id,
                                       text='Нельзя удалить начатую игру')

    def clearUserHours(self):
        while True:
            time.sleep(3600)
            self.user.clear()

    def clearUserDay(self):
        while True:
            time.sleep(86400)
            self.userDay.clear()

    def zeroListCheck(self):
        while True:
            time.sleep(60)
            self.listCheck.clear()

    def clear24pay(self):
        while True:
            time.sleep(86400)
            self.give24pay.clear()

    def clear24give(self):
        while True:
            time.sleep(86400)
            self.give24give.clear()

    def check_pay(self, comment, user_id, data):
        userInfo = Global.select().where(Global.user_id == user_id)
        try:
            h = requests.get(
                'https://edge.qiwi.com/payment-history/v1/persons/' + str(self.phone) + '/payments?rows=50',
                headers={'Accept': 'application/json',
                         'Content-Type': 'application/json',
                         'Authorization': f'Bearer {self.qiwiApi}'})
            req = json.loads(h.text)
            count = 0
            for i in range(len(req['data'])):
               if req['data'][i]['sum']['currency'] == 643:
                    if req['data'][i]['comment'] == f"{comment}":
                        count += 1
                        amount = req['data'][i]['sum']['amount']
                        amount = round(amount)
                        Global.update(balance=Global.balance + int(amount)).where(Global.user_id == user_id).execute()
                        payBalance.update(status=True).where(payBalance.user_id == user_id).execute()
                        break
            if count == 1:
                self.send(user_id, f'[✅]Баланс успешно пополнен на {amount} рубл(я/ей)')
                self.give24pay.append(amount)
                func.updateAddQiwi(int(amount))
                self.send(self.admin_id, f'[✅]Поступил платеж[✅]\nСумма: {amount}\nПополнил: {user_id}')
                if userInfo[0].referal != 0:
                    if userInfo[0].referalPersonal != 0:
                        self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
                        Global.update(
                            balance=Global.balance + math.floor(amount / 100 * userInfo[0].referalPersonal)).where(
                            Global.user_id == userInfo[0].referal).execute()
                    else:
                        self.bot.delete_message(chat_id=user_id, message_id=data.message.message_id)
                        Global.update(
                            balance=Global.balance + math.floor(int(amount) / 100 * int(func.persentRef()))).where(
                            Global.user_id == userInfo[0].referal).execute()
            else:
                self.send(user_id, f'Платеж не найден')
        except Exception as e:
            print(e)

    def sendQiwi(self, message):
        if message.text.isdigit():
            sumSend = self.send(message.from_user.id, 'Введите сумму для выплаты(не меньше 100)')
            self.bot.register_next_step_handler(sumSend, self.sendQiwiTwo, message.text)
        else:
            self.send(message.from_user.id, 'Неверно указан киви')

    def sendQiwiTwo(self, message, number):
        balance = Global.select().where(Global.user_id == message.from_user.id)[0].balance
        if message.text.isdigit():
            if balance >= int(message.text):
                if int(message.text) >= 100:
                    Global.update(balance=Global.balance - int(message.text)).where(
                        Global.user_id == message.from_user.id).execute()
                    self.send(message.from_user.id, mess.giveMoney.format(message.text, number))
                    self.send(self.admin_id,
                              mess.giveMoneyAdmin.format(message.text, number, message.from_user.username,
                                                         message.from_user.id), parse_mode='HTML',
                              reply_markup=keyboard.closeMessage(message.from_user.id, number, message.text))
                    try:
                        self.send(config.idMoney,
                                  mess.sendMoney.format(message.text, '@' + str(message.from_user.username)))
                    except:
                        pass
                    self.give24give.append(int(message.text))
                    func.updateReturnQiwi(int(message.text))
                else:
                    self.send(message.from_user.id, 'Минимальная сумма выплаты 100 рублей')
            else:
                self.send(message.from_user.id, 'Недостаточно средств')
        else:
            self.send(message.from_user.id, 'Сумма должна состоять из чисел')

    def delBalanceFirst(self, message):
        if message.text.isdigit():
            user = Global.select().where(Global.user_id == message.text)
            if user.exists():
                addBalance = self.send(message.from_user.id,
                                       f'Баланс пользователя: {user[0].balance}\nА теперь введите сумму: ')
                self.bot.register_next_step_handler(addBalance, self.delBalanceTwo, message.text)
            else:
                self.send(message.from_user.id, '[🚫]Пользователя не существует', reply_markup=keyboard.adminPanel)
        elif message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        else:
            self.send(message.from_user.id, '[❗]Id пользователя состоит из цифр', reply_markup=keyboard.adminPanel)

    def delBalanceTwo(self, message, user_id):
        if message.text.isdigit():
            user = Global.select().where(Global.user_id == user_id)
            if user[0].balance >= int(message.text):
                Global.update(balance=Global.balance - int(message.text)).where(Global.user_id == user_id).execute()
                self.send(message.from_user.id, f'[✅]Вы успешно забрали {message.text} рублей у пользователя',
                          reply_markup=keyboard.adminPanel)
            else:
                self.send(message.from_user.id,
                          f'[🚫]У пользователя {user_id} не достаточно денег\nБаланс пользователя: {user[0].balance}',
                          reply_markup=keyboard.adminPanel)
        elif message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        else:
            self.send(message.from_user.id, '[❗]Сумма состоит из цифр', reply_markup=keyboard.adminPanel)

    def giveBalanceFirst(self, message):
        if message.text.isdigit():
            if Global.select().where(Global.user_id == message.text).exists():
                addBalance = self.send(message.from_user.id, '[✅]А теперь введите сумму: ')
                self.bot.register_next_step_handler(addBalance, self.giveBalanceTwo, message.text)
            else:
                self.send(message.from_user.id, '[🚫]Пользователя не существует', reply_markup=keyboard.adminPanel)
        elif message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        else:
            self.send(message.from_user.id, '[❗]Id пользователя состоит из цифр', reply_markup=keyboard.adminPanel)

    def giveBalanceTwo(self, message, user_id):
        if message.text.isdigit():
            Global.update(balance=Global.balance + int(message.text)).where(Global.user_id == user_id).execute()
            self.send(message.from_user.id,
                      f'[✅]Вы успешно выдали баланс пользователю {user_id}\nВыдали: {message.text}',
                      reply_markup=keyboard.adminPanel)
            try:
                self.send(user_id, f'[✅]Вам выдали {message.text} рублей на баланс')
            except Exception as e:
                pass
        elif message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        else:
            self.send(message.from_user.id, '[❗]Сумма состоит из цифр', reply_markup=keyboard.adminPanel)

    def serverInform(self):
        threads = ps.cpu_count(logical=False)
        lthreads = ps.cpu_count()
        RAM = ps.virtual_memory().percent
        cpu_percents = ps.cpu_percent(percpu=True)
        starttime = datetime.now() - self.startime
        cpupercents = ""
        for a in range(lthreads):
            cpupercents += "Поток : {} | Загруженность : {} %\n".format(a + 1, cpu_percents[a - 1])
        return """Загрузка систем :
Ядер : {} | Загруженность : {}%
{}Загруженность ОЗУ : {} %
Времени прошло со старта : {} """.format(threads, ps.cpu_percent(), cpupercents, RAM,
                                         "{} дней, {} часов, {} минут.".format(starttime.days,
                                                                               starttime.seconds // 3600,
                                                                               (

                                                                                       starttime.seconds % 3600) // 60))

    def statsInform(self):
        allUser = Global.select().count()
        return mess.stats.format(allUser, len(self.userDay), len(self.user), sum(self.give24pay), sum(self.give24give),
                                 func.qiwiCount(), func.qiwiReturn())

    def refPersNew(self, message):
        if message.text.isdigit():
            if int(message.text) < 100:
                func.updateAddRefPer(int(message.text))
                self.send(message.from_user.id, 'Успешно обновление')
            else:
                self.send(message.from_user.id, 'Нельзя указывать больше 100 или равное 100')
        else:
            self.send(message.from_user.id, 'Вы ввели не число')

    def rassulkaStart(self, message):
        if message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        else:
            photo = self.send(message.from_user.id, 'Отправьте фото если нужно, если нет введите любой текст: ')
            self.bot.register_next_step_handler(photo, self.rassulka, message.text)

    def refComNew(self, message):
        if message.text.isdigit():
            func.updateAddRef(message.text)
            self.send(message.from_user.id, 'Успешно обновление коммисионого %')
        else:
            self.send(message.from_user.id, 'Процент состоит из числа')

    def rassulka(self, message, text):
        banned = 0
        good = 0
        info = Global.select(Global.user_id)
        if message.text == '💢Отмена💢':
            self.send(message.from_user.id, '[❗]Действие отменено', reply_markup=keyboard.adminPanel)
        elif message.content_type == 'photo':
            self.send(message.from_user.id, '[✅]Рассылка успешно запущена', reply_markup=keyboard.adminPanel)
            for i in info:
                try:
                    self.bot.send_photo(chat_id=i.user_id, photo=message.json['photo'][2]['file_id'], caption=text)
                    good += 1
                except Exception as e:
                    banned += 1
            self.send(message.from_user.id,
                      f'[✅]Рассылка завершена\nОтчет\n😎Отправлено: {good}\n🤦‍Ошибки: {banned}\n🌪Общее количество: {info.count()}')
        else:
            self.send(message.from_user.id, '[✅]Рассылка успешно запущена', reply_markup=keyboard.adminPanel)
            for i in info:
                try:
                    self.send(chat_id=i.user_id, text=text)
                    good += 1
                except Exception as e:
                    banned += 1
            self.send(message.from_user.id,
                      f'[✅]Рассылка завершена\nОтчет\n😎Отправлено: {good}\n🤦‍Ошибки: {banned}\n🌪Общее количество: {info.count()}')

    def referalPersentOne(self, message):
        userGive = Global.select().where(Global.user_id == message.text)
        if message.text.isdigit():
            if userGive.exists():
                stepTwo = self.send(message.from_user.id, 'Введите реферальный %: ')
                self.bot.register_next_step_handler(stepTwo, self.referalPersentTwo, message.text)
            else:
                self.send(message.from_user_id, 'Пользователь не найден')
        else:
            self.send(message.from_user_id, 'Id пользователя должно состоять из цифр')

    def referalPersentTwo(self, message, user_id):
        if message.text.isdigit():
            Global.update(referalPersonal=int(message.text)).where(Global.user_id == user_id).execute()
            self.send(message.from_user.id, 'Успешно установлен реф процент')
        else:
            self.send(message.from_user_id, 'Реферальный % состоит из числа')

    def deleteGameAdmin(self, idGame, user_id):
        infoGame = Games.select().where(Games.id == idGame)
        if infoGame.exists():
            if infoGame[0].gamerTwo == 0:
                Games.delete().where(Games.id == idGame).execute()
                Global.update(balance=Global.balance+infoGame[0].balance).where(Global.user_id == infoGame[0].user_id).execute()
                self.send(user_id, f'Игра с id: {idGame} успешно удалена')
            else:
                self.send(user_id, 'Нельзя удалять начатую игру')
        else:
            self.send(user_id, 'Игра уже была удалена')

    def giveAdmin(self, message):
        if message.text.isdigit():
            userInfo = Global.select().where(Global.user_id == message.text)
            if userInfo.exists():
                Global.update(adm=True).where(Global.user_id == message.text).execute()
                self.send(message.from_user.id, 'Успешно выдан администратор!')
            else:
                self.send(message.from_user.id, 'Пользователь не найден')
        else:
            self.send(message.from_user.id, 'Id пользователя состоит из цифр')

    def sendMoney(self, args, data):
        if int(self.api.balance[0]) >= int(args[2]):
            self.api.pay(account=args[1], amount=int(args[2]), comment=f'Выплата от бота: @{self.bot.get_me().username}\nДля пользователя: {args[0]}')
            self.bot.delete_message(chat_id=data.from_user.id, message_id=data.message.message_id)
            self.send(data.from_user.id, 'Выплата прошла успешно!')
        else:
            self.send(data.from_user.id, f'Не хватает денег на вашем кошельке баланс: {self.api.balance}')

    def backMoney(self, args, data):
        userInfo = Global.select().where(Global.user_id == args[0])
        if userInfo.exists():
            Global.update(balance=Global.balance + int(args[1])).where(Global.user_id == args[0]).execute()
            self.bot.delete_message(chat_id=data.from_user.id, message_id=data.message.message_id)
            self.send(data.from_user.id, 'Баланс успешно возвращен')
            try:
                self.send(int(args[0]), 'Администратор отказал вам в выплате, средства возвращены обратно на баланс')
            except:
                pass
        else:
            self.bot.delete_message(chat_id=data.from_user.id, message_id=data.message.message_id)
            self.send(data.from_user.id, 'Пользватель не найден')

    def promoCreateFirst(self, message):
        info = Promo.select().where(Promo.promo == message.text)
        if not info.exists():
            count = self.send(message.from_user.id, 'Введите кол-во активаций: ')
            self.bot.register_next_step_handler(count, self.promoCreateTwo, message.text)
        else:
            self.send(message.from_user.id, 'Промо-код существует!')

    def promoCreateTwo(self, message, promo):
        if message.text.isdigit():
            reger = [message.text, promo]
            balance = self.send(message.from_user.id, 'Введите баланс промо-кода: ')
            self.bot.register_next_step_handler(balance, self.promoCreateThree, reger)
        else:
            self.send(message.from_user.id, 'Кол-во активаций состоит из цифр')

    def promoCreateThree(self, message, reger):
        if message.text.isdigit():
            if int(message.text) > 0:
                Promo.create(
                    promo=reger[1],
                    count=int(reger[0]),
                    balance=int(message.text),
                )
                self.send(message.from_user.id, mess.promoCreate.format(reger[1], message.text, reger[0]), parse_mode='HTML')
            else:
                self.send(message.from_user.id, 'Баланс промо-кода должен быть больше 0 ')
        else:
            self.send(message.from_user.id, 'Баланс промо-кода состоит из цифр!')
        self.send(message.from_user.id, 'Выберите действие', reply_markup=keyboard.promoRemoute())

    def promoActivate(self, message):
        infoPromo = Promo.select().where(Promo.promo == message.text)
        if infoPromo.exists():
            if infoPromo[0].count > 0:
                usersActivate = ast.literal_eval(infoPromo[0].users)
                if message.from_user.id not in usersActivate:
                    usersActivate.append(message.from_user.id)
                    Global.update(balance=Global.balance + infoPromo[0].balance).where(Global.user_id == message.from_user.id).execute()
                    Promo.update(users=usersActivate, count=Promo.count - 1).where(Promo.promo == message.text).execute()
                    self.send(message.from_user.id, mess.promoActivate.format(infoPromo[0].balance))
                    user = Global.select().where(Global.user_id == message.from_user.id)
                    self.send(self.admin_id, mess.logPromo.format(message.text, user[0].username, message.from_user.id), parse_mode='HTML')
                else:
                    self.send(message.from_user.id, 'Вы уже активировали этот промо-код')
            else:
                self.send(message.from_user.id, 'Промо-код закончился')
        else:
            self.send(message.from_user.id, 'Промо-кода не существует')

    def deletePromo(self, message):
        infoPromo = Promo.select().where(Promo.promo == message.text)
        if infoPromo.exists():
             Promo.delete().where(Promo.promo == message.text).execute()
             self.send(message.from_user.id, 'Промо-код успешно удален')
        else:
            self.send(message.from_user.id, 'Промо-кода не существует')
        self.send(message.from_user.id, 'Выберите действие', reply_markup=keyboard.promoRemoute())

    def activePromoNow(self, message, c):
        infoPromo = Promo.select().where(Promo.count > 0)
        lists = ''
        for i in infoPromo:
            lists = lists + f' Промо: <pre>{i.promo}</pre>, Кол-во акт: {i.count} |'
        self.send(c.from_user.id, 'Рабочие промо\n'+lists, parse_mode='HTML')

    def informUsers(self, message):
        if message.text.isdigit():
            Thread(target=self.statsResult, args=(message, message.text)).start()
        else:
            self.send(message.from_user.id, 'Id пользователя должно состоять из цифр!')

    def statsResult(self, message, text):
        payment = payBalance.select().where(payBalance.user_id == message.text).count()
        infoUser = Global.select().where(Global.user_id == message.text)
        self.send(message.from_user.id, mess.informUser.format(message.text, infoUser[0].username, infoUser[0].referalCount,
                                                               (infoUser[0].countWin + infoUser[0].countBad), infoUser[0].countWin,
                                                               infoUser[0].countBad, payment), parse_mode='HTML')

    def sendQiwiAdmFirst(self, message):
        if message.text.isdigit():
            count = self.send(message.from_user.id, f'Введите сумму для вывода(макс {self.api.balance[0]}): ')
            self.bot.register_next_step_handler(count, self.sendQiwiAdmTwo, message.text)
        else:
            self.send(message.from_user.id, 'Не верно введен номер!')

    def sendQiwiAdmTwo(self, message, number):
        if message.text.isdigit():
            if int(message.text) < int(self.api.balance[0]):
                self.api.pay(account=number, amount=int(message.text))
                self.send(message.from_user.id, 'Успешный вывод средств')
            else:
                self.send(message.from_user.id, 'Недостаточно средств')
        else:
            self.send(message.from_user.id, 'Сумма должна быть указана в цифрах')