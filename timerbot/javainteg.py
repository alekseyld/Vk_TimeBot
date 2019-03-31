# -*- coding: utf-8 -*-
from subprocess import *
import platform
import logging

class TimeTableUtils:
    def __init__(self):
        self.arg = ''
        self.jarName = 'collegetimetableutils.jar'

    #default toi
    def setArguments(self, group, json = False, countDay = 0, save = False,  nextDay = False, fromSite = True, dayName_date_index = ''):
        
        self.arg = []
        
        if platform.system() == 'Linux':
            self.arg.append(group)
        else:
            self.arg.append(group.encode("cp1251"))
        
        s = ''
        
        if json:
            s += 'j'
        else:
            s += 't'
            
        if countDay != 0:
            s += 'd' + str(countDay)
        
        if nextDay:
            s += 'n'
            
        if save:
            s += 's'
        else:
            s += 'o'
        
        if fromSite:
            s += 'i'
        else:
            s += 'c'
        
        if dayName_date_index:
            if dayName_date_index.isdigit() or dayName_date_index.find(',') != -1:
                s += 'bg'
            elif dayName_date_index.find('.') == -1:
                s += 'bx'
            elif dayName_date_index.find('.') != -1:
                s += 'ba'
        
        self.arg.append(s)
           
        if dayName_date_index:
            if platform.system() == 'Linux':
                self.arg.append(dayName_date_index)
            else:
                self.arg.append(dayName_date_index.encode("cp1251"))
            
    
    def getArguments(self):
        return ['-Dfile.encoding=UTF-8', self.jarName] + self.arg

    def jarWrapper(self, args):
        process = Popen(['java', '-jar'] + args, stdout=PIPE, stderr=PIPE)
        ret = []
        while process.poll() is None:
            line = process.stdout.readline()
            if line != '' and line.endswith('\n'):
                ret.append(line[:-1].decode('utf-8').replace('\r', ''))
        stdout, stderr = process.communicate()
        ret += stdout.split('\n')
        if stderr != '':
            ret += stderr.split('\n')
        #ret.remove('')
        return ret
    
    def execute(self):
        logging.debug(u'JAR PARAMS=' + str(self.getArguments()))
        
        result = self.jarWrapper(self.getArguments())
        s1 = u''

        if len(result) == 2 and result[1] == '':
            return s1 + result[0]
        
        for r in result:
            if len(result) > 1:
                s1 += r + u'\n'
        return s1
        
