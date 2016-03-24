import numpy as np

class STS:
	"""
	The STS class can calculate the (dI/dV)/(I/V) function out of spectroscopy
	measurement performed with as STM. The calculation uses an exponential
	broadening function.
	"""
	def __init__(self, V, I , DV=1, ADJUST=1e-9):
		"""
		V: the voltage array or list
		I: the current array or list
		dI: the dI/dV array or list
		DV: (Delta V), the bandbroadening term
		ADJUST: a value which discard I/V values for V<ADJUST (as it would diverge)
		"""
		if len(V)<2: raise(ValueError)
		if V[-1]<V[0]: # Decreasing voltage? Inverse the data
			self.V=np.array(V[::-1])
			self.I=np.array(I[::-1])
		else: # Increasing Voltage data
			self.I=np.array(I)
			self.V=np.array(V)

		Vstep=float(self.V[-1]-self.V[0])/len(self.V) # Voltage step
		DVstep=Vstep*np.ceil(DV/Vstep) # Round DV to multiple of Vstep
		skip=int(DVstep/Vstep) # The number of Vstep to reach DVstep

		## The voltage vector will be extended to min(V)-DV and max(V)+DV and stored as nV
		nVb=np.linspace(min(self.V)-DVstep,min(self.V),skip,endpoint=False)
		nVe=np.linspace(max(self.V)+Vstep,max(self.V)+DVstep,skip)
		self.nV=np.concatenate((nVb,self.V,nVe))

		## The window function W is the exponentiel used in the convolution
		self.W=np.exp(-np.abs(self.nV)/DV)

		## IV stores I/V, discard values for |V|<ADJUST and pad the vector to match the size of nV
		self.IV=np.pad(self.I/self.V,(skip,skip),'edge')
		self.IV[np.abs(self.nV)<ADJUST]=0

		## BIV: broadened I/V : calculated by the convolution
		BIV=np.convolve(self.IV,self.W,mode='same')/sum(self.W)
		self.BIV=BIV[skip:-skip]

	## Various functions to retrieve the usefull values
	def getIV(self):
		return self.IV
	def getBIV(self):
		return self.BIV
	def getW(self):
		return self.W
	def getnV(self):
		return self.nV
