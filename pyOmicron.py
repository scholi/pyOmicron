import numpy as np
import matplotlib.pyplot as plt
import struct
import os, sys
import re
import copy

class Matrix:
	"""
	Class to Read and Hangle Matrix files
	"""
	def __init__(self,Path,pbCallback=None,fast=False): # Give the Path of the folder containing all the mtrx files
		# Read PATH and open file
		self.Path=Path
		self.fp=None # file variable
		for x in os.listdir(Path): # List the folder and look for the _0001.mtrx file
			if x[-10:]=="_0001.mtrx":
				self.fp=open(self.Path+"/"+x,"rb")
		if self.fp==None:
			print("Matrix file not found!")
			sys.exit(1)
		if self.fp.read(8)!=b"ONTMATRX": # header of the file
			print("Unknown header! Wrong Matrix file format")
			sys.exit(2)
		self.version=self.fp.read(4) # should be 0101
		self.IDs={}
		self.params={} # dictionary to list all the parameters
		self.images={} # images[x] are the parameters used during the record for file named x

		# Parse the file and read the block
		cur = self.fp.tell()
		self.fp.seek(0,2)
		FileSize = self.fp.tell()
		self.fp.seek(cur)
		while True: # While not EOF scan files and read block
			r=self.read_block(fast=fast)
			if pbCallback is not None:
				pbCallback(100*self.fp.tell()/FileSize)
			if r==False: break

	def read_string(self):
		# Strings are stored as UTF-16. First 32-bits is the string length
		N = struct.unpack("<L",self.fp.read(4))[0] # string length
		if N==0: return ""
		s=self.fp.read(N*2).decode('utf-16')
		return s

	def plotSTS(self, ID, num=1): # plot STS file called xxx--ID_num.I(V)_mtrx
		x,y=self.getSTS(ID,num)
		plt.plot(x,y)
		plt.show()
	
	def getUpDown(self, X,Y, NPTS):
		"""
		Split data in Up and Down measurement, pad them with NaN if necessary and return them in increasing order.
		The returned value are X,Yup, Ydown
		If Up/Down data are missing an empty array will be returned
		"""
		if len(Y)<NPTS: # Missing data
			Y=np.pad(Y,NPTS,'constant',constant_values=np.nan)
		elif len(Y)>NPTS: # Forward and backward scans
			if len(Y)<2*NPTS: # Missing data
				Y=np.pad(Y,2*NPTS,'constant',constant_values=np.nan)
			if X[NPTS-1]<X[0]: return X[NPTS:],[Y[NPTS:],Y[NPTS-1::-1]]
			else: return X[:NPTS],[Y[:NPTS],Y[-1:NPTS-1:-1]]
		if X[-1]<X[0]: return X[::-1],[np.empty(NPTS),Y[::-1],np.empty(NPTS)]
		return X,[Y,np.empty(NPTS)]

		

	def getSTSData(self, ID,nums=[1]):
		if not ID in self.IDs or len(nums)<1: return None
		# retrieve the spectroscopy data (V, I and an object IM containing the parameters)
		V,I,IM=self.getSTS(ID,nums[0],params=True)
		NPTS=int(IM['Spectroscopy']['Device_1_Points']['value'])
		hasDI=self.IDs[ID]['hasDI']
		# Call the function to split and flip data if it's UP/Down measurements
		V,I=self.getUpDown(V,I,NPTS)
		for num in nums[1:]: # Skip first num as it's already parsed above
			X,Y=self.getUpDown(*self.getSTS(ID,num),NPTS=NPTS)
			if not np.array_equal(V,X): raise Exception("Bias axis differs between measurements?!?")
			for i in range(2): # i=0: Up scan, i=1: Down scan
				I[i]=np.vstack((I[i],Y[i]))
		Im=[np.nan]*2   # Store the mean of I
		Ims=[np.nan]*2  # Store StDev of I
		for i in range(2): # i=0: Up scan, i=1: Down scan
			Im[i]=I[i].mean(axis=0)
			Ims[i]=I[i].std(axis=0)
		if hasDI:
			X,dI=self.getUpDown(*self.getDIDV(ID,nums[0]),NPTS=NPTS)
			for num in nums[1:]:
				X,Y=self.getUpDown(*self.getDIDV(ID,num),NPTS=NPTS)
				if not np.array_equal(V,X): raise Exception("Bias axis differs between measurements?!?")
				for i in range(2): # i=0: Up scan, i=1: Down scan
					dI[i]=np.vstack((dI[i],Y[i]))
			dIm=[np.nan]*2   # Store the mean of dI/dV
			dIms=[np.nan]*2  # Store the StdDev of dI/dV
			for i in range(2): # i=0: Up scan, i=1: Down scan
				dIm[i]=dI[i].mean(axis=0)
				dIms[i]=dI[i].std(axis=0)
			return {'nums':nums,'V':V,'I':I,'dI':dI,'Imean':Im,'Istd':Ims,'dImean':dIm,'dIstd':dIms}

	def getDIDV(self, ID, num=1):
		"""
		The dI/dV measurements are stored the same way as the I(V), but with file extension Aux2(V).
		"""
		return self.getSTS(ID,num,ext='Aux2')

	def getSTSparams(self, ID, num=1, ext='I'):
		if not ID in self.IDs: return None,None
		I=u"%s--%i_%i.%s(V)_mtrx"%(self.IDs[ID]['root'],ID,num,ext)
		if not I in self.images: return None
		return self.images[I]

	def getSTS(self,ID,num=1,ext='I',params=False): # Get a spectroscopy file xxxx-ID_num.I(V)_mtrx
		IM=self.getSTSparams(ID,num,ext)
		if IM==None: return None
		v1=IM['Spectroscopy']['Device_1_Start']['value'] # Get the start voltage used for the scan
		v2=IM['Spectroscopy']['Device_1_End']['value'] # Get the end voltage for the scan
		I=u"%s--%i_%i.%s(V)_mtrx"%(self.IDs[ID]['root'],ID,num,ext)
		ImagePath=self.Path+"/"+I
		if not os.path.exists(ImagePath): return None
		ff=open(ImagePath,"rb") # read the STS file
		if ff.read(8)!=b"ONTMATRX":
			print("ERROR: Invalid STS format")
			sys.exit(1)
		if ff.read(4)!=b"0101":
			print("ERROR: Invalid STS version")
			sys.exit(2)
		t=ff.read(4) # TLKB header
		ff.read(8) # timestamp
		ff.read(8) # Skip 8bytes (??? unknown data. Usualy it's = 00 00 00 00 00 00 00 00)
		t=ff.read(4) # CSED header
		ss=struct.unpack('<15L',ff.read(60)) # 15 uint32. ss[6] and ss[7] store the size of the points. ([6] is what was planned and [7] what was actually recorded)
		# ss[6] should be used to reconstruct the X-axis and ss[7] to read the binary data
		if ff.read(4)!=b'ATAD':
			print("ERROR: Data should be here, but aren't. Please debug script")
			sys.exit(3)
		ff.read(4)
		data=np.array(struct.unpack("<%il"%(ss[7]),ff.read(ss[7]*4))) # The data are stored as unsigned LONG

		# Reconstruct the x-axis. Take the start and end volatege (v1,v2) with the correct number of points and pad it to the data length. Padding is in 'reflect' mode in the case of Forward/backward scans.
		X=np.linspace(v1,v2,int(IM['Spectroscopy']['Device_1_Points']['value']))
		if len(X)<ss[6]:
			X=np.concatenate((X,X[::-1]))

		if len(data)<len(X): data=np.concatenate((data,[np.nan]*(len(X)-len(data))))
		if params: return X,data,IM
		return X,data

	def read_value(self): # Values are stored with a specific header for each data type
		t=self.fp.read(4)
		if t==b"BUOD":
			# double
			v=struct.unpack("<d",self.fp.read(8))[0]
		elif t==b"GNOL":
			# uint32
			v=struct.unpack("<L",self.fp.read(4))[0]
		elif t==b"LOOB":
			# bool32
			v=struct.unpack("<L",self.fp.read(4))[0]>0
		elif t==b"GRTS":
			v=self.read_string()
		else:
			v=t
		return v

	def getUI(self): # Read an unsigned int from the file
		return struct.unpack("<L",self.fp.read(4))[0]

	def read_block(self,sub=False,fast=False):
		indent=self.fp.read(4) # 4bytes forming the header. Those are capital letters between A-Z
		if len(indent)<4: # EOF reached?
			return False
		bs=struct.unpack("<L",self.fp.read(4))[0]+[8,0][sub] # Size of the block
		r={"ID":indent,"bs":bs} # Store the parameters found in the block
		p=self.fp.tell() # store the file position of the block
		if indent==b"DOMP": # Block storing parameters changed during an experiment
			self.fp.read(12)
			inst=self.read_string()
			prop=self.read_string()
			unit=self.read_string()
			self.fp.read(4)
			value=self.read_value()
			r.update({'inst':inst,'prop':prop,'unit':unit,'value':value})
			self.params[inst][prop].update({'unit':unit,'value':value}) # Update theparameters information stored in self.params
		elif indent==b"CORP": # Processor of scanning window. Useless in this script for the moment
			self.fp.read(12)
			a=self.read_string()
			b=self.read_string()
			r.update({'a':a,'b':b})
		elif indent==b"FERB": # A file was stored
			self.fp.read(12)
			a=self.read_string() # Filename
			r['filename']=a
			if not fast:
				self.images[a]=copy.deepcopy(self.params) # Store the parameters used to record the file
			else:
				self.images[a]={'Spectroscopy':copy.deepcopy(self.params['Spectroscopy'])} # Store the parameters used to record the file
				

			# Create a catalogue to avoid to scan all images later
			res=re.search(r'^(.*?)--([0-9]*)_([0-9]*)\.([^_]+)_mtrx$',a)
			ID=int(res.group(2))
			num=int(res.group(3))
			_type=res.group(4)
			if not ID in self.IDs: self.IDs[ID]={'nums':[],'root':res.group(1)}
			if _type in ["Aux2(V)"]: self.IDs[ID]['hasDI']=True
			if _type in ["I(V)"]: self.IDs[ID]['nums'].append(num)
			
		elif indent==b"SPXE": # Initial configuration
			self.fp.read(12) # ??? useless 12 bytes
			r['LNEG']=self.read_block(True)  # read subblock
			r['TSNI']=self.read_block(True)  # read subblock
			r['SXNC']=self.read_block(True)  # read subblock
		elif indent==b"LNEG":
			r.update({'a':self.read_string(),'b':self.read_string(),'c':self.read_string()})
		elif indent==b"TSNI":
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
		elif indent==b"SXNC":
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
		elif indent==b"APEE": # Store the configurations
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
