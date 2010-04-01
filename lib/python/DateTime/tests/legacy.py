##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from DateTime.DateTimeZone import _data
from time import time

class _timezone:
    def __init__(self,data):
        self.name,self.timect,self.typect, \
        self.ttrans,self.tindex,self.tinfo,self.az=data

    def default_index(self):
        if self.timect == 0: return 0
        for i in range(self.typect):
            if self.tinfo[i][1] == 0: return i
        return 0

    def index(self,t=None):
        t=t or time()
        if self.timect==0: idx=(0, 0, 0)
        elif t < self.ttrans[0]:
            i=self.default_index()
            idx=(i, ord(self.tindex[0]),i)
        elif t >= self.ttrans[-1]:
            if self.timect > 1:
                idx=(ord(self.tindex[-1]),ord(self.tindex[-1]),
                     ord(self.tindex[-2]))
            else:
                idx=(ord(self.tindex[-1]),ord(self.tindex[-1]),
                     self.default_index())
        else:
            for i in range(self.timect-1):
                if t < self.ttrans[i+1]:
                    if i==0: idx=(ord(self.tindex[0]),ord(self.tindex[1]),
                                  self.default_index())
                    else:    idx=(ord(self.tindex[i]),ord(self.tindex[i+1]),
                                  ord(self.tindex[i-1]))
                    break
        return idx

    def info(self,t=None):
        idx=self.index(t)[0]
        zs =self.az[self.tinfo[idx][2]:]
        return self.tinfo[idx][0],self.tinfo[idx][1],zs[:zs.find('\000')]


_zlst =   ['Brazil/Acre','Brazil/DeNoronha','Brazil/East',
           'Brazil/West','Canada/Atlantic','Canada/Central',
           'Canada/Eastern','Canada/East-Saskatchewan',
           'Canada/Mountain','Canada/Newfoundland',
           'Canada/Pacific','Canada/Yukon',
           'Chile/Continental','Chile/EasterIsland','CST','Cuba',
           'Egypt','EST','GB-Eire','Greenwich','Hongkong','Iceland',
           'Iran','Israel','Jamaica','Japan','Mexico/BajaNorte',
           'Mexico/BajaSur','Mexico/General','MST','Poland','PST',
           'Singapore','Turkey','Universal','US/Alaska','US/Aleutian',
           'US/Arizona','US/Central','US/Eastern','US/East-Indiana',
           'US/Hawaii','US/Indiana-Starke','US/Michigan',
           'US/Mountain','US/Pacific','US/Samoa','UTC','UCT','GMT',

           'GMT+0100','GMT+0200','GMT+0300','GMT+0400','GMT+0500',
           'GMT+0600','GMT+0700','GMT+0800','GMT+0900','GMT+1000',
           'GMT+1100','GMT+1200','GMT+1300','GMT-0100','GMT-0200',
           'GMT-0300','GMT-0400','GMT-0500','GMT-0600','GMT-0700',
           'GMT-0800','GMT-0900','GMT-1000','GMT-1100','GMT-1200',
           'GMT+1',

           'GMT+0130', 'GMT+0230', 'GMT+0330', 'GMT+0430', 'GMT+0530',
           'GMT+0630', 'GMT+0730', 'GMT+0830', 'GMT+0930', 'GMT+1030',
           'GMT+1130', 'GMT+1230',

           'GMT-0130', 'GMT-0230', 'GMT-0330', 'GMT-0430', 'GMT-0530',
           'GMT-0630', 'GMT-0730', 'GMT-0830', 'GMT-0930', 'GMT-1030',
           'GMT-1130', 'GMT-1230',

           'UT','BST','MEST','SST','FST','WADT','EADT','NZDT',
           'WET','WAT','AT','AST','NT','IDLW','CET','MET',
           'MEWT','SWT','FWT','EET','EEST','BT','ZP4','ZP5','ZP6',
           'WAST','CCT','JST','EAST','GST','NZT','NZST','IDLE']

_zmap =   {'aest':'GMT+1000', 'aedt':'GMT+1100',
           'aus eastern standard time':'GMT+1000',
           'sydney standard time':'GMT+1000',
           'tasmania standard time':'GMT+1000',
           'e. australia standard time':'GMT+1000',
           'aus central standard time':'GMT+0930',
           'cen. australia standard time':'GMT+0930',
           'w. australia standard time':'GMT+0800',

           'brazil/acre':'Brazil/Acre',
           'brazil/denoronha':'Brazil/DeNoronha',
           'brazil/east':'Brazil/East','brazil/west':'Brazil/West',
           'canada/atlantic':'Canada/Atlantic',
           'canada/central':'Canada/Central',
           'canada/eastern':'Canada/Eastern',
           'canada/east-saskatchewan':'Canada/East-Saskatchewan',
           'canada/mountain':'Canada/Mountain',
           'canada/newfoundland':'Canada/Newfoundland',
           'canada/pacific':'Canada/Pacific','canada/yukon':'Canada/Yukon',
           'central europe standard time':'GMT+0100',
           'chile/continental':'Chile/Continental',
           'chile/easterisland':'Chile/EasterIsland',
           'cst':'US/Central','cuba':'Cuba','est':'US/Eastern','egypt':'Egypt',
           'eastern standard time':'US/Eastern',
           'us eastern standard time':'US/Eastern',
           'central standard time':'US/Central',
           'mountain standard time':'US/Mountain',
           'pacific standard time':'US/Pacific',
           'gb-eire':'GB-Eire','gmt':'GMT',

           'gmt+0000':'GMT+0', 'gmt+0':'GMT+0',

           'gmt+0100':'GMT+1', 'gmt+0200':'GMT+2', 'gmt+0300':'GMT+3',
           'gmt+0400':'GMT+4', 'gmt+0500':'GMT+5', 'gmt+0600':'GMT+6',
           'gmt+0700':'GMT+7', 'gmt+0800':'GMT+8', 'gmt+0900':'GMT+9',
           'gmt+1000':'GMT+10','gmt+1100':'GMT+11','gmt+1200':'GMT+12',
           'gmt+1300':'GMT+13',
           'gmt-0100':'GMT-1', 'gmt-0200':'GMT-2', 'gmt-0300':'GMT-3',
           'gmt-0400':'GMT-4', 'gmt-0500':'GMT-5', 'gmt-0600':'GMT-6',
           'gmt-0700':'GMT-7', 'gmt-0800':'GMT-8', 'gmt-0900':'GMT-9',
           'gmt-1000':'GMT-10','gmt-1100':'GMT-11','gmt-1200':'GMT-12',

           'gmt+1': 'GMT+1', 'gmt+2': 'GMT+2', 'gmt+3': 'GMT+3',
           'gmt+4': 'GMT+4', 'gmt+5': 'GMT+5', 'gmt+6': 'GMT+6',
           'gmt+7': 'GMT+7', 'gmt+8': 'GMT+8', 'gmt+9': 'GMT+9',
           'gmt+10':'GMT+10','gmt+11':'GMT+11','gmt+12':'GMT+12',
           'gmt+13':'GMT+13',
           'gmt-1': 'GMT-1', 'gmt-2': 'GMT-2', 'gmt-3': 'GMT-3',
           'gmt-4': 'GMT-4', 'gmt-5': 'GMT-5', 'gmt-6': 'GMT-6',
           'gmt-7': 'GMT-7', 'gmt-8': 'GMT-8', 'gmt-9': 'GMT-9',
           'gmt-10':'GMT-10','gmt-11':'GMT-11','gmt-12':'GMT-12',

           'gmt+130':'GMT+0130',  'gmt+0130':'GMT+0130',
           'gmt+230':'GMT+0230',  'gmt+0230':'GMT+0230',
           'gmt+330':'GMT+0330',  'gmt+0330':'GMT+0330',
           'gmt+430':'GMT+0430',  'gmt+0430':'GMT+0430',
           'gmt+530':'GMT+0530',  'gmt+0530':'GMT+0530',
           'gmt+630':'GMT+0630',  'gmt+0630':'GMT+0630',
           'gmt+730':'GMT+0730',  'gmt+0730':'GMT+0730',
           'gmt+830':'GMT+0830',  'gmt+0830':'GMT+0830',
           'gmt+930':'GMT+0930',  'gmt+0930':'GMT+0930',
           'gmt+1030':'GMT+1030',
           'gmt+1130':'GMT+1130',
           'gmt+1230':'GMT+1230',

           'gmt-130':'GMT-0130',  'gmt-0130':'GMT-0130',
           'gmt-230':'GMT-0230',  'gmt-0230':'GMT-0230',
           'gmt-330':'GMT-0330',  'gmt-0330':'GMT-0330',
           'gmt-430':'GMT-0430',  'gmt-0430':'GMT-0430',
           'gmt-530':'GMT-0530',  'gmt-0530':'GMT-0530',
           'gmt-630':'GMT-0630',  'gmt-0630':'GMT-0630',
           'gmt-730':'GMT-0730',  'gmt-0730':'GMT-0730',
           'gmt-830':'GMT-0830',  'gmt-0830':'GMT-0830',
           'gmt-930':'GMT-0930',  'gmt-0930':'GMT-0930',
           'gmt-1030':'GMT-1030',
           'gmt-1130':'GMT-1130',
           'gmt-1230':'GMT-1230',

           'greenwich':'Greenwich','hongkong':'Hongkong',
           'iceland':'Iceland','iran':'Iran','israel':'Israel',
           'jamaica':'Jamaica','japan':'Japan',
           'mexico/bajanorte':'Mexico/BajaNorte',
           'mexico/bajasur':'Mexico/BajaSur','mexico/general':'Mexico/General',
           'mst':'US/Mountain','pst':'US/Pacific','poland':'Poland',
           'singapore':'Singapore','turkey':'Turkey','universal':'Universal',
           'utc':'Universal','uct':'Universal','us/alaska':'US/Alaska',
           'us/aleutian':'US/Aleutian','us/arizona':'US/Arizona',
           'us/central':'US/Central','us/eastern':'US/Eastern',
           'us/east-indiana':'US/East-Indiana','us/hawaii':'US/Hawaii',
           'us/indiana-starke':'US/Indiana-Starke','us/michigan':'US/Michigan',
           'us/mountain':'US/Mountain','us/pacific':'US/Pacific',
           'us/samoa':'US/Samoa',

           'ut':'Universal',
           'bst':'GMT+1', 'mest':'GMT+2', 'sst':'GMT+2',
           'fst':'GMT+2', 'wadt':'GMT+8', 'eadt':'GMT+11', 'nzdt':'GMT+13',
           'wet':'GMT', 'wat':'GMT-1', 'at':'GMT-2', 'ast':'GMT-4',
           'nt':'GMT-11', 'idlw':'GMT-12', 'cet':'GMT+1', 'cest':'GMT+2',
           'met':'GMT+1',
           'mewt':'GMT+1', 'swt':'GMT+1', 'fwt':'GMT+1', 'eet':'GMT+2',
           'eest':'GMT+3',
           'bt':'GMT+3', 'zp4':'GMT+4', 'zp5':'GMT+5', 'zp6':'GMT+6',
           'wast':'GMT+7', 'cct':'GMT+8', 'jst':'GMT+9', 'east':'GMT+10',
           'gst':'GMT+10', 'nzt':'GMT+12', 'nzst':'GMT+12', 'idle':'GMT+12',
           'ret':'GMT+4', 'ist': 'GMT+0530'
           }

timezones = dict((name, _timezone(data)) for name, data in _data.iteritems())