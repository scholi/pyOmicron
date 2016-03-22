import numpy as np

class STS:
	def __init__(self, V, I , dI, DV=1, ADJUST=1e-9):
		if len(V)<2: raise(ValueError)
		if V[-1]<V[0]:
			self.V=np.array(V[::-1])
			self.I=np.array(I[::-1])
			self.dI=np.array(dI[::-1])
		else:
			self.I=np.array(I)
			self.V=np.array(V)
			self.dI=np.array(dI)

		Vstep=float(self.V[-1]-self.V[0])/len(self.V)
		DVstep=Vstep*np.ceil(DV/Vstep)
		skip=int(DVstep/Vstep)
		nVb=np.linspace(min(self.V)-DVstep,min(self.V),skip,endpoint=False)
		nVe=np.linspace(max(self.V)+Vstep,max(self.V)+DVstep,skip)
		self.nV=np.concatenate((nVb,self.V,nVe))
		self.W=np.exp(-np.abs(self.nV)/DV)
		self.IV=np.pad(self.I/self.V,(skip,skip),'edge')
		self.IV[np.abs(self.nV)<ADJUST]=0
		BIV=np.convolve(self.IV,self.W,mode='same')/sum(self.W)
		self.BIV=BIV[skip:-skip]

	def getIV(self):
		return self.IV
	def getBIV(self):
		return self.BIV
	def getW(self):
		return self.W
	def getnV(self):
		return self.nV
