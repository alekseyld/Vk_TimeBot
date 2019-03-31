# -*- coding: utf-8 -*-
import MySQLdb

class DataBase:
    def __init__(self):
        self.db = MySQLdb.connect(host="localhost", user="{db_user}", passwd="{db_password}", db="timetable", charset='utf8')
        self.cursor = self.db.cursor()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close();

    #refactor заменить на userId
    #Возвращает строку с id пользователей вк через запятую
    def getUsersByGroup(self, group):
        sql = u"SELECT vk_userid FROM `users` WHERE UPPER(tt_group) = UPPER('%(tt_group)s')"%{u'tt_group':group}

        self.cursor.execute(sql)
        data = self.cursor.fetchall()

        s = ''
        for r in data:
            s+= str(r[0]) + ','
        return s[0:len(s)-1]
        
    def getGroupIdByVkid(self, userid):
        sql = u"SELECT tt_group FROM `users` WHERE vk_userid = '%(vk_userid)s'"%{u'vk_userid':userid}
        
        self.cursor.execute(sql)

        data = self.cursor.fetchall()
    
        if len(data):
            return data[0][0]
        else:
            return ''
    
    def getUserIdByVkid(self, userid):
        sql = u"SELECT id FROM `users` WHERE vk_userid = '%(vk_userid)s'"%{u'vk_userid':userid}

        self.cursor.execute(sql)

        data = self.cursor.fetchall()
        
        if len(data):
            return int(data[0][0])
        else:
            return 0
    
    def getExistGroups(self):
        sql = u"""SELECT CONVERT(tt_group USING utf8) FROM users GROUP BY tt_group"""

        self.cursor.execute(sql)
    
        data =  self.cursor.fetchall()
        groups = []
    
        for rec in data:
            groups.append(rec[0])
        
        return groups
        
    def insertUserGroup(self, userid, group):
        sql = ''
    
        if self.getUserIdByVkid(userid):
            sql = u"""UPDATE users SET tt_group = '%(tt_group)s' WHERE vk_userid = %(vk_userid)s
            """%{u"tt_group":group, u"vk_userid":userid}
            
        else:
            sql = u"""INSERT INTO users(vk_userid, tt_group)
                VALUES ('%(vk_userid)s', UPPER('%(tt_group)s'))
                """%{u"vk_userid":userid, u"tt_group":group}
    
        self.cursor.execute(sql)
        self.db.commit()
        
    def deleteUserGroup(self, userid):
        if not self.getUserIdByVkid(userid):
            return
        sql = u'DELETE FROM `users` WHERE vk_userid = %(vk_userid)s' %{u"vk_userid":userid}
        
        self.cursor.execute(sql)
        self.db.commit()
