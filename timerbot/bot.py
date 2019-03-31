# -*- coding: utf-8 -*-

import requests
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from threading import Thread, Event
from javainteg import TimeTableUtils
from database import DataBase
from datetime import datetime
import logging
import time

#Токен группы ВК
token = '{API_KEY}'

#logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = u'timebot.log')

class TimeTableRefreshThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(10*60):#20*60
            try:
                groups = getExistGroups()
                for group in groups:
                    logging.debug(u'refresh group=' + group)
                    change = refreshGroupTimeTable(group)
                    logging.debug(u'change=' + change)
                    if change:
                        userids = getUsersByGroup(group)
                        logging.debug(u'send refresh message to ' + userids + u' from ' + group + u' - change=' + change)
                        c = getTimeTableByIds(group, change)
                        if (c.lower().find(u'error') != -1 or c.lower().find(u'exception') != -1 or c.isspace() or c.lower().find(u'java') != -1):
                            logging.error(u'ERROR UPDATE THREAD ' + c)
                            continue
                            
                        sendVkMessageSafe(u'Появились изменения в расписании: \n\n' + c, False, userids)
                        
            except Exception as e:
                logging.error(e, exc_info=True)
                    
def getTimeTableByIds(group, ids):
    javaUtils = TimeTableUtils()
    javaUtils.setArguments(group, fromSite=False, dayName_date_index=ids)
    
    return javaUtils.execute()

def refreshGroupTimeTable(group):
    javaUtils = TimeTableUtils()
    javaUtils.setArguments(group, json=True, save=True)
    
    return javaUtils.execute()

def getTimeTableFromSite(group, arg):
    javaUtils = TimeTableUtils()
    javaUtils.setArguments(group, dayName_date_index=arg.title())
    
    return javaUtils.execute()

def getTimeTableFromCache(group):
    javaUtils = TimeTableUtils()
    javaUtils.setArguments(group, countDay=1, fromSite=False)
    
    return javaUtils.execute()

def getTimeTablZavtra(group):
    javaUtils = TimeTableUtils()
    javaUtils.setArguments(group, nextDay=True)
    
    return javaUtils.execute()

def getUsersByGroup(group):
    with DataBase() as db:
        return db.getUsersByGroup(group)

def getGroupIdByVkid(userid):
    with DataBase() as db:
        return db.getGroupIdByVkid(userid)

def getUserIdByVkid(userid):
    with DataBase() as db:
        return db.getUserIdByVkid(userid)
    
def getExistGroups():
    with DataBase() as db:
        return db.getExistGroups()

def insertUserGroup(userid, group):
    with DataBase() as db:
        return db.insertUserGroup(userid, group)

def deleteUserGroup(userid):
    with DataBase() as db:
        db.deleteUserGroup(userid)

def sendVkMessageSafe(mes, sendError, *userds):
    if mes == u'' or mes.isspace() or mes.find(u'Exception') != -1:
        logging.error(u'ERROR SEND MES=' + mes)
        mes = u'Ответ не определен. Проверьте правильность ввода команды'
        if not sendError:
            return
    
    vk.messages.send(
            user_ids=','.join(map(str, userds)),
            message=mes
    )

def sendVkMessage(mes, *userds):
    sendVkMessageSafe(mes, True, *userds)
    
def normalizeGroup(s):
    if s[0].isdigit() and s[len(s) - 1].isdigit():
        s = s.strip()
        
        course = s[0]
        num = s[len(s) - 1]
        
        s = s[1:len(s) - 1].strip().replace(u'-', u'')
        
        return course + u' ' + s.upper() + u'-' + num
    
    elif s[0].isdigit() and len(s) < 6:
        s = s.strip()
        course = s[0]
        s = s[1:len(s)].strip()
        
        return course + u' ' + s.upper()
            
    else: 
        return s
    
def parseMessage(mes):
    s = mes.strip()
    res = []
    course = u''
    
    while s.find(u' ') != -1:
        i = s.find(u' ')
        cut = s[0:i]

        if course:
            cut = normalizeGroup(course + u' ' + cut)
            course = u'' 
        
        if len(cut) == 1 and cut.isdigit():
            course = cut
        else:
            if cut != u'на':
                res.append(cut)
                
        s = s[i:len(s)].lstrip()
    
    if course:
        s = normalizeGroup(course + u' ' + s)
        course = u''
    
    res.append(s)
    
    if len(res) > 0:
        res[0] = res[0].lower()
        
        if len(res) > 1:
            res[1] = normalizeGroup(res[1])
    
    return res

def toNominativeCase(day):
    if day.isdigit():
        return day
    
    if day.lower().find(u'ред') != -1:
        day = u'Среда'
    elif day.lower().find(u'пятниц') != -1:
        day = u'Пятница'
    elif day.lower().find(u'суббот') != -1:
        day = u'Суббота'
    
    return day
    
def processMessage(mes, user_id):
    
    logging.debug(u'mes=%s from user_id=%d'%(mes, user_id))
    
    parse_mes = parseMessage(mes)
    
    logging.debug(u'parse_mes=' + str(parse_mes))
    
    if parse_mes[0] == u'группа':
        group = parse_mes[1]
        insertUserGroup(user_id, group);
        refreshGroupTimeTable(group)
        sendVkMessage(u'Вы добавлены в базу для оповещения', user_id)
        
    elif parse_mes[0] == u'расписание':
        group = parse_mes[1]
                                                        
        arg = u''
        if len(parse_mes) == 3:
            arg = toNominativeCase(parse_mes[2])
        sendVkMessage(getTimeTableFromSite(group, arg), user_id)
        
    elif parse_mes[0] == u'завтра':
        #делать проверку на регистрацию
        group = getGroupIdByVkid(user_id)
        sendVkMessage(getTimeTablZavtra(group), user_id)  
        
    elif parse_mes[0] == u'сегодня':
        group = getGroupIdByVkid(user_id)
        date = datetime.strftime(datetime.now(), "%d.%m.%Y")
        sendVkMessage(getTimeTableFromSite(group, date), user_id) 
    
    elif parse_mes[0] == u'неделя':
        group = getGroupIdByVkid(user_id)
        sendVkMessage(getTimeTableFromSite(group, u''), user_id) 

    elif parse_mes[0] == u'отключить':
        deleteUserGroup(user_id)
        sendVkMessage(u'Вы удалены из базы оповещений', user_id)
    
    elif parse_mes[0] == u'помощь':
        s = u'''Примеры команд \n\n1. группа 3 АПП-1 = регистрация в системе оповещений\n\n2. отключить = отключение оповещений\n\n3. завтра = расписание на завтра (при регистрации)\n\n4. расписание 3 АПП-1 = расписание группы на неделю\n\n5. расписание 3 АПП-1 Вторник = расписание на вторник\n\n6. расписание 3 АПП-1 04.06.2018 = расписание по дате\n\n7. расписание 3 АПП-1 0,1 = расписание на Понедельник и Вторник
                '''
        
        sendVkMessage(s, user_id)
        
    elif parse_mes[0] == u'test':
        sendVkMessage(u'bot online', user_id)
    
    elif parse_mes[0] == u'преподаватель':
        pass
#         vk.messages.send(
#             rawData=True,
#             user_ids=user_id,
#             message='asdadd',
#             keyboard='{"one_time":false,"buttons":[[{"action":{"type":"text","payload":"{\"button\":\"1\"}","label":"R111ed"},"color":"negative"},{"action":{"type":"text","payload":"{\"button\":\"2\"}","label":"Green"},"color":"positive"}],[{"action":{"type":"text","payload":"{\"button\":\"3\"}","label":"White"},"color":"default"},{"action":{"type":"text","payload":"{\"button\":\"4\"}","label":"Blue"},"color":"primary"}]]}'
#         
#             )
    
    elif mes.lower().find(u'нулев') != -1 and mes.lower().find(u'ты') != -1 and mes.lower().find(u'идешь') != -1:
        sendVkMessage(u'Возможно, но @asad_fanzilevich (он) точно не идет', user_id)
    elif mes.lower() == u'мне нужен сварщик':
        sendVkMessage(u'@kostik303(Костя-сварщик) - лучший сварщик на Руси', user_id)
    elif mes.lower() == u'мне нужна мировая революция':
        sendVkMessage(u'Тебе к @id408583560(нему)', user_id)
    elif mes.lower() == u'мне нужен топ игрок cs':
        sendVkMessage(u'@xxxola(Старший брат Симпла)', user_id)
    elif mes.lower() == u'где находится 48й километр':
        sendVkMessage(u'@48km_mkada (Тута)', user_id)
    elif mes.lower().find(u'зме') != -1 and mes.lower().find(u'приготов') != -1 and mes.lower().find(u'углях') != -1:
        sendVkMessage(u'@nikniggabro (Мэтр по шашлыкам из змей)', user_id)

def longpollListener(event):
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        try:
            processMessage(event.text, event.user_id)
        except Exception as e:
            logging.error(e, exc_info=True)

def initVkBot():
    session = requests.Session()

    vk_session = vk_api.VkApi(token=token)

    global vk
    vk = vk_session.get_api()

    global  upload 
    upload = VkUpload(vk_session)
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        longpollListener(event)

def initUpdateThread():
    stopFlag = Event()
    global thread 
    thread = TimeTableRefreshThread(stopFlag)
    thread.start()

def main():
    initUpdateThread()
 
    while True:
        try:
            initVkBot()
        except Exception as e:
            logging.error(e, exc_info=True)
        
        time.sleep(2)
        
        if not thread.isAlive():
            initUpdateThread()


if __name__ == '__main__':
    main()
