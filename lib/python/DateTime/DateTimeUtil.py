"""Build timezone info into a compiled .pyc file"""


import os,struct


f_zones=['Brazil/Acre','Brazil/DeNoronha','Brazil/East','Brazil/West',
         'Canada/Atlantic','Canada/Central','Canada/Eastern',
         'Canada/East-Saskatchewan','Canada/Mountain','Canada/Newfoundland',
         'Canada/Pacific','Canada/Yukon',
         'Chile/Continental','Chile/EasterIsland',
         'Cuba','Egypt','GB-Eire',
         'GMT','GMT+1','GMT+2','GMT+3','GMT+4','GMT+5','GMT+6','GMT+7',
         'GMT+8','GMT+9','GMT+10','GMT+11','GMT+12','GMT+13','GMT-1',
         'GMT-2','GMT-3','GMT-4','GMT-5','GMT-6','GMT-7','GMT-8','GMT-9',
         'GMT-10','GMT-11','GMT-12','Greenwich','Hongkong','Iceland','Iran',
         'Israel','Jamaica','Japan',
         'Mexico/BajaNorte','Mexico/BajaSur','Mexico/General',
         'Poland','Singapore','Turkey','Universal',
         'US/Alaska','US/Aleutian','US/Arizona','US/Central','US/Eastern',
         'US/East-Indiana','US/Hawaii','US/Indiana-Starke','US/Michigan',
         'US/Mountain','US/Pacific','US/Samoa']


class UnpackerLite:
    # Tastes great, less filling ;)
    def __init__(self,data): self.reset(data)
    def reset(self,data):    self.__buf,self.__pos=data,0
    if (struct.pack('l',1)=='\0\0\0\1'):
        def unpack_int(self):
	    i = self.__pos
	    self.__pos = j = i+4
	    data = self.__buf[i:j]
	    d=struct.unpack('l',self.__buf[i:j])[0]
	    if d >= 0x80000000L: return int(d-0x100000000L)
	    return int(d)
    else:
	def unpack_int(self):
            i = self.__pos
	    self.__pos = j = i+4
	    d=self.__buf[i:j]
	    x=long(ord(d[0]))<<24 | ord(d[1])<<16 | ord(d[2])<<8 | ord(d[3])
	    if x >= 0x80000000L: return int(x-0x100000000L)
	    return int(x)



db_name='DateTimeZone'
zonedir='zones/'

def main():
    print 'Building timezone data...'
    zdata={}
    try:    db=open('%s.py' % db_name,'w')
    except: raise 'IOError','Could not create %s.py' % db_name
    for f in f_zones:
        name,ttrans,tindex,ttinfo,az=f,[],'',[],''
        _f=open('%s%s' % (zonedir,f),'rb')
	data=_f.read()
        _f.close()
        up=UnpackerLite(data[32:44])
        tzh_timecnt,tzh_typecnt,tzh_charcnt= \
        up.unpack_int(),up.unpack_int(),up.unpack_int()
        up.reset(data[44:44+4*tzh_timecnt])
        p=44+4*tzh_timecnt
        for i in range(tzh_timecnt): ttrans.append(up.unpack_int())
        tindex=data[p:p+tzh_timecnt]
        p=p+tzh_timecnt
        d=data[p:p+6*tzh_typecnt]
        for i in range(tzh_typecnt):
            up.reset(d[6*i:6*i+4])
            ttinfo.append(up.unpack_int(),ord(d[6*i+4]),ord(d[6*i+5]))
	p=p+6*tzh_typecnt
	az=data[p:p+tzh_charcnt]
        zdata[name]=(name,tzh_timecnt,tzh_typecnt,ttrans,tindex,ttinfo,az)
    db.write('_data=%s' % str(zdata))
    db.close()
    print 'Creating %s.pyc...' % db_name
    __import__(db_name)
    print '%s.pyc created successfully.' % db_name


if __name__=='__main__': main()
