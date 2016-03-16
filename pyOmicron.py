import numpy as np
import matplotlib.pyplot as plt
import struct
import os, sys
import re

class Matrix:
	def __init__(self,Path): # Give the Path of the folder containing all the mtrx files
		self.Path=Path
		self.fp=None # file variable
		for x in os.listdir(Path): # List the folder and look for the _0001.mtrx file
			if x[-10:]=="_0001.mtrx":
				self.fp=open(self.Path+"/"+x,"rb")
		if self.fp==None:
			print("Matrix file not found!")
			sys.exit(1)
		if self.fp.read(8)!="ONTMATRX": # header of the file
			print("Unknown header! Wrong Matrix file format")
			sys.exit(2)
		self.version=self.fp.read(4) # should be 0101
		self.params={} # dictionary to list all the parameters
		self.images={} # images[x] are the parameters used during the record for file named x
		while True: # While not EOF scan files and read block
			r=self.read_block()
			if r==False: break
	def read_string(self): # Strings are stored as UTF-16
		N = struct.unpack("<L",self.fp.read(4))[0] # string length
		if N==0: return ""
		s=self.fp.read(N*2).decode('utf-16').encode('utf-8')
		return s
	def plotSTS(self, ID, num=1): # plot STS file called xxx--ID_num.I(V)_mtrx
		x,y=self.getSTS(ID,num)
		plt.plot(x,y)
		plt.show()
	def getDIDV(self, ID, num=1):
		return self.getSTS(ID,num,ext='Aux2')
	def getSTS(self,ID,num=1,ext='I'): # Get a spectroscopy file xxxx-ID_num.I(V)_mtrx
		I=None # Will store the filename
		for x in self.images: # Scan through all image saved and find the one with correct ID and num
			if re.match(r'.*--%i_%i\.%s\(V\)_mtrx$'%(ID,num,ext),x):
				I=x
				break
		if I==None: return
		v1=self.images[I]['Spectroscopy']['Device_1_Start']['value'] # Get the start voltage used for the scan
		v2=self.images[I]['Spectroscopy']['Device_1_End']['value'] # Get the end voltage for the scan
		ff=open(self.Path+"/"+I,"rb") # read the STS file
		if ff.read(8)!="ONTMATRX":
			print("ERROR: Invalid STS format")
			sys.exit(1)
		if ff.read(4)!="0101":
			print("ERROR: Invalid STS version")
			sys.exit(2)
		t=ff.read(4) # TLKB header
		ff.read(8) # timestamp
		ff.read(8) # ???
		t=ff.read(4) # CSED header
		ss=struct.unpack('<15L',ff.read(60)) # 15 uint32. ss[6] and ss[7] store the size of the points. ([6] is what was planned and [7] what was actually recorded)
		# ss[6] should be used to reconstruct the X-axis and ss[7] to read the binary data
		if ff.read(4)!='ATAD':
			print("ERROR: Data should be here, but aren't. Please debug script")
			sys.exit(3)
		ff.read(4)
		data=np.array(struct.unpack("<%il"%(ss[7]),ff.read(ss[7]*4))) # The data are stored as unsignes LONG
		X=np.linspace(v1,v2,ss[6]) # reconstruct the X-axis from the start & end value + number of points
		if len(data)<len(X): data=np.concatenate((data,[np.nan]*(len(X)-len(data))))
		return X,data
	def read_value(self): # Values are stored with a specific header for each data type
		t=self.fp.read(4)
		if t=="BUOD":
			# double
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
	def getUI(self): # Read an unsigned int from the file
		return struct.unpack("<L",self.fp.read(4))[0]
	def read_block(self,sub=False):
		indent=self.fp.read(4) # 4bytes forming the header. Those are capital letters between A-Z
		if len(indent)<4: # EOF reached?
			return False
		bs=struct.unpack("<L",self.fp.read(4))[0]+[8,0][sub] # Size of the block
		r={"ID":indent,"bs":bs} # Store the parameters found in the block
		p=self.fp.tell() # store the file position of the block
		if indent=="DOMP": # Block storing parameters changed during an experiment
			self.fp.read(12)
			inst=self.read_string()
			prop=self.read_string()
			unit=self.read_string()
			self.fp.read(4)
			value=self.read_value()
			r.update({'inst':inst,'prop':prop,'unit':unit,'value':value})
			self.params[inst][prop].update({'unit':unit,'value':value}) # Update theparameters information stored in self.params
		elif indent=="CORP": # Processor of scanning window. Useless in this script for the moment
			self.fp.read(12)
			a=self.read_string()
			b=self.read_string()
			r.update({'a':a,'b':b})
		elif indent=="FERB": # A file was stored
			self.fp.read(12)
			a=self.read_string() # Filename
			r['filename']=a
			self.images[a]=self.params # Store the parameters used to record the file a
		elif indent=="SPXE": # Initial configuration
			self.fp.read(12) # ??? useless 12 bytes
			r['LNEG']=self.read_block(True)  # read subblock
			r['TSNI']=self.read_block(True)  # read subblock
			r['SXNC']=self.read_block(True)  # read subblock
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
		elif indent=="APEE": # Store the configurations
			self.fp.read(12) # ??? useless 12bytes
			num=self.getUI() # Number of parameters class
			r['num']=num
			for i in range(num):
				inst = self.read_string() # Parameter class name
				grp = self.getUI() # Number of parameters in this class
				kk={}
				for j in range(grp): # Scan for each parameter, value and unit
					prop = self.read_string() # parameter name
					unit = self.read_string() # parameter unit
					self.fp.read(4) # ???
					value = self.read_value() # parameter value
					kk[prop]={"unit":unit,"value":value}
				r[inst]=kk
			self.params=r # Store this information as initial values for the parmeters
		   # print(self.params['Spectroscopy'])
		self.fp.seek(p) # go back to the beginning of the block
		self.fp.read(bs) # go to the next block by skiping the block-size bytes
		return r # return the informations collected
