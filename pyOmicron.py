import numpy as np
import matplotlib.pyplot as plt
import struct
import os, sys
import re
import binascii

class Matrix:
    def __init__(self,Path):
        self.Path=Path
        self.fp=None
        for x in os.listdir(Path):
            if x[-10:]=="_0001.mtrx":
                self.fp=open(self.Path+"/"+x,"rb")
        if self.fp==None:
            print("Matrix file not found!")
            sys.exit(1)
        if self.fp.read(8)!="ONTMATRX":
            print("Unknown header! Wrong Matrix file format")
            sys.exit(2)
        self.version=self.fp.read(4)
        self.params={}
        self.images={}
        while True:
            r=self.read_block()
            if r==False: break
    def read_string(self):
        N = struct.unpack("<L",self.fp.read(4))[0]
        if N==0: return ""
        s=self.fp.read(N*2).decode('utf-16').encode('utf-8')
        return s
    def getSTS(self,ID,num=1):
        I=None
        for x in self.images:
            if re.match(r'.*--%i_%i\.I\(V\)_mtrx$'%(ID,num),x):
                I=x
                break
        if I==None: return
        v1=self.images[I]['Spectroscopy']['Device_1_Start']['value']
        v2=self.images[I]['Spectroscopy']['Device_1_End']['value']
        print("Voltage: %f -> %f"%(v1,v2))
        ff=open(self.Path+"/"+I,"rb")
        if ff.read(8)!="ONTMATRX":
            print("ERROR: Invalid STS format")
            sys.exit(1)
        if ff.read(4)!="0101":
            print("ERROR: Invalid STS version")
            sys.exit(2)
        t=ff.read(4) # TLKB
        ff.read(8) # timestamp
        ff.read(8) # ???
        t=ff.read(4) # CSED
        ss=struct.unpack('<15L',ff.read(60))
        if ff.read(4)!='ATAD':
            print("ERROR: Data should be here, but aren't. Please debug script")
            sys.exit(3)
        s=struct.unpack('<L',ff.read(4))
        data=np.array(struct.unpack("<%il"%(ss[6]),ff.read(ss[6]*4)))
        X=np.linspace(v1,v2,ss[6])
        return X,data
    def read_value(self):
        t=self.fp.read(4)
        if t=="BUOD":
            # double 32bits (float)
            v=struct.unpack("<d",self.fp.read(8))[0]
        elif t=="GNOL":
            # uint32
            v=struct.unpack("<L",self.fp.read(4))[0]
        elif t=="LOOB":
            # bool32
            v=struct.unpack("<L",self.fp.read(4))[0]>0
        elif t=="GRTS":
            v=self.read_string()
        else:
            v=t
        return v
    def getUI(self):
        return struct.unpack("<L",self.fp.read(4))[0]
    def read_block(self,sub=False):
        indent=self.fp.read(4)
        if len(indent)<4:
            return False
        bs=struct.unpack("<L",self.fp.read(4))[0]+[8,0][sub]
        r={"ID":indent,"bs":bs}
        p=self.fp.tell()
        if indent=="DOMP":
            self.fp.read(12)
            inst=self.read_string()
            prop=self.read_string()
            unit=self.read_string()
            self.fp.read(4)
            value=self.read_value()
            r.update({'inst':inst,'prop':prop,'unit':unit,'value':value})
            self.params[inst][prop].update({'unit':unit,'value':value})
        elif indent=="CORP":
            self.fp.read(12)
            a=self.read_string()
            b=self.read_string()
            r.update({'a':a,'b':b})
        elif indent=="FERB":
            self.fp.read(12)
            a=self.read_string()
            r['filename']=a
            self.images[a]=self.params
        elif indent=="SPXE":
            self.fp.read(12)
            r['LNEG']=self.read_block(True)
            r['TSNI']=self.read_block(True)
            r['SXNC']=self.read_block(True)
        elif indent=="LNEG":
            r.update({'a':self.read_string(),'b':self.read_string(),'c':self.read_string()})
        elif indent=="TSNI":
            anz=self.getUI()
            rr=[]
            for ai in range(anz):
                a=self.read_string()
                b=self.read_string()
                c=self.read_string()
                count=self.getUI()
                pa=[]
                for i in range(count):
                    x=self.read_string()
                    y=self.read_string()
                    pa.append({'a':x,'b':y})
                rr.append({'a':a,'b':b,'c':c,'content':pa})
        elif indent=="SXNC":
            count=self.getUI()
            r['count']=count
            rr=[]
            for i in range(count):
                a=self.read_string()
                b=self.read_string()
                k=self.getUI()
                kk=[]
                for j in range(k):
                    x=self.read_string()
                    y=self.read_string()
                    kk.append((x,y))
                rr.append((a,b,i,kk))
            r['content']=rr
        elif indent=="APEE":
            self.fp.read(12)
            num=self.getUI()
            r['num']=num
            for i in range(num):
                inst = self.read_string()
                grp = self.getUI()
                kk={}
                for j in range(grp):
                    prop = self.read_string()
                    unit = self.read_string()
                    self.fp.read(4)
                    value = self.read_value()
                    kk[prop]={"unit":unit,"value":value}
                r[inst]=kk
            self.params=r
           # print(self.params['Spectroscopy'])
        self.fp.seek(p)
        self.fp.read(bs)
        return r

Path=r"C:/Users/scholi/Desktop/15-Oct-2015"        
M=Matrix(Path)
print(M.getSTS(66,4))
