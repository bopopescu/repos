"""
This python library aims to do two things.
1. Offer general wrapper classes around SNPs datasets.
2. Offer basic functions which can aid analysis of the SNPs.

Bjarni Vilhjalmsson, bvilhjal@usc.edu
"""

#from sets import Set
#from sets import Set as set
import sys

class _SnpsData_(object):
	"""
	05/11/2008 yh. add chromosome
	An abstract superclass.
	"""
	alphabet = None
	missingVal = None
	def __init__(self,snps,positions,baseScale=None,accessions=None,arrayIds=None, chromosome=None):
		self.snps = snps #list[position_index][accession_index]
		self.positions = positions #list[position_index]
		if accessions: 
			self.accessions=accessions #list[accession_index]
		if arrayIds: 
			self.arrayIds=arrayIds #list[accession_index]
		self.chromosome = chromosome

	def scalePositions(self,baseScale):
		for i in range(0,len(self.positions)):
			self.positions[i] = int(self.positions[i]*baseScale)
		self.baseScale = baseScale

	def addSnp(self,snp):
		self.snps.append(snp)
	
	def addPos(self,position):
		self.positions.append(position)


	def filterMonoMorphicSnps(self):
		"""
		05/12/08 yh. add no_of_monomorphic_snps_removed
		Removes SNPs from the data which are monomorphic.
		"""
		newPositions = []
		newSnps = []
		for i in range(0,len(self.positions)):
			count = 0
			for nt in self.alphabet:
				if nt in self.snps[i]:
					count += 1
			if count>1:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])
		numRemoved = len(self.positions)-len(newPositions)
		self.no_of_monomorphic_snps_removed = numRemoved
		self.snps = newSnps
		self.positions = newPositions
		return numRemoved

	def onlyBinarySnps(self):
		"""
		Removes all but binary SNPs.  (I.e. monomorphic, tertiary and quaternary alleles SNPs are removed.)
		"""
		newPositions = []
		newSnps = []
		for i in range(0,len(self.positions)):
			count = 0
			for nt in self.alphabet:
				if nt in self.snps[i]:
					count += 1
			if count==2:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])
		numRemoved = len(self.positions)-len(newPositions)
		self.no_of_nonbinary_snps_removed = numRemoved
		self.snps = newSnps
		self.positions = newPositions
		return numRemoved
	
	
	
	def orderAccessions(self,accessionMapping):
		newAccessions = [None for i in range(0,len(accessionMapping))]
		for (i,j) in accessionMapping:
			newAccessions[j]=self.accessions[i]

		newSnps = []
		for pos in self.positions:
			newSnps.append([self.missingVal for i in range(0,len(accessionMapping))])
		
		for (i,j) in accessionMapping:
			for posIndex in range(0,len(self.positions)):
				newSnps[posIndex][j] = self.snps[posIndex][i]	

		self.accessions = newAccessions
		self.snps = newSnps

		if self.arrayIds:
			newArrayIds = [None for i in range(0,len(self.arrayIds))]
			for (i,j) in accessionMapping:
				newArrayIds[j]=self.arrayIds[i]
			self.arrayIds = newArrayIds

	

	
	def filterRegion(self,startPos,endPos):
		"""
		Filter all SNPs but those in region.
		"""
		i = 0
		while i < len(self.snps) and self.positions[i]<startPos:
			i += 1
		
		newSnps = []
		newPositions = []
		while i < len(self.snps) and self.positions[i]<endPos:
			newSnps.append(self.snps[i])
			newPositions.append(self.positions[i])
			i +=1
		self.snps = newSnps
		self.positions = newPositions




class RawDecoder(dict):
	def __missing__(self, key):
		return 'NA'
	def __init__(self,initdict={}):
		for letter in ['A','C','G','T']:
			self[letter]=letter
		for letter in initdict:
			self[letter]=initdict[letter]
	
	

class RawSnpsData(_SnpsData_):
	"""
	05/11/2008 yh. give default values to all initial arguments so that it could be called without any arguments.
	Similar to the SnpsData class, except it deals with bases (A,C,G,T), instead of allele numbers (0s and 1s).
	
	Alphabet: A,C,G,T, and NA

	"""
	#alphabet = ['A','C','G','T']
	alphabet = ['A','C','G','T','-']
	missingVal = 'NA'

	callProbabilities = []  #list[position_index][accession_index]

	def __init__(self,snps=None,positions=None,baseScale=None,accessions=None,arrayIds=None, callProbabilities=None):
		self.snps = snps
		self.positions = positions
		self.accessions=accessions
		self.arrayIds=arrayIds
		if callProbabilities:
			self.callProbabilities = callProbabilities


	
	def writeToFile(self,filename,chromosome, withArrayId=False):
		"""
		Writes data to a file.  1 file for each chromosome.

		WARNING OLD, outdated!
		"""
		outStr = ""
		fieldStrings = ["Chromosome", "Positions"]
		for acc in self.accessions:
			fieldStrings.append(str(acc))
		outStr += ", ".join(fieldStrings)+"\n"
		for i in range(0,len(self.positions)):
			outStr +=str(chromosome)+", "+str(self.positions[i])+", "+", ".join(self.snps[i])+"\n"
		f = open(filename,"w")
		f.write(outStr)
		f.close()


	def mergeDataUnion(self, snpsd, priority=1, unionType=2):
		"""
		Merges two data, where the resulting data has the union of the SNPs or/and accessions

		unionType=
		1: All SNPs are included in the dataset  
		2: All accessions are included in the merged dataset 
		3: Both all SNPs and accessions are included in the merged dataset 
		
		It doesn't deal with multiple identical ecotypes/accession
		"""
		
		print "Merging datas"
		print "Number of snps:",len(self.snps),"and",len(snpsd.snps)
		
		#Find new accession indices
		newAccessions = []
		accessionsIndices = []
		commonAccessions = list(set(self.accessions).intersection(set(snpsd.accessions)))
		commonPositions = list(set(self.positions).intersection(set(snpsd.positions)))
		allAccessions = list(set(self.accessions).union(set(snpsd.accessions)))
		
		if unionType==2 or unionType==3:
			newAccessions = allAccessions
		elif unionType==1:
			newAccessions = self.accessions

		for acc in newAccessions:
			index1=-1
			index2=-1
			if self.accessions.count(acc):
				index1=self.accessions.index(acc)
			if snpsd.accessions.count(acc):
				index2=snpsd.accessions.index(acc)
			accessionsIndices.append([index1, index2])
			
			
		print "Number of common accessions:", len(commonAccessions)
		print "Total number of accessions:",len(allAccessions)
		print "Number of common Snps:",len(commonPositions)
		#print "Only in 1st data set", list(set(self.accessions).difference(set(commonAccessions)))
		#print "Only in 2st data set", list(set(snpsd.accessions).difference(set(commonAccessions)))
			
		snpErrorRate = []
		newSnps = []
		newPositions = []
		i = 0
		j = 0 
		while i <= len(self.positions) and j <= len(snpsd.positions):
			if i < len(self.positions):
				pos1 = self.positions[i]
			if j < len(snpsd.positions):
				pos2 = snpsd.positions[j] 
			if i < len(self.positions) and pos1 < pos2:
				newPositions.append(pos1)
				newSnp = []
				oldSnp = self.snps[i]
				for index in accessionsIndices:
					if index[0]!=-1:
						newSnp.append(oldSnp[index[0]])				   
					else:
						newSnp.append(self.missingVal)
				newSnps.append(newSnp)
				i = i+1
			elif j < len(snpsd.positions) and pos2 < pos1:
				if unionType==1 or unionType==3:
					newPositions.append(pos2)
					newSnp = []
					oldSnp = snpsd.snps[j]
					for index in accessionsIndices:
						if index[1]!=-1:
							newSnp.append(oldSnp[index[1]])				   
						else:
							newSnp.append(self.missingVal)
					newSnps.append(newSnp)
				j = j+1
			elif i < len(self.positions) and j < len(snpsd.positions) and pos1==pos2:
				counts = 0
				fails = 0
				for index in accessionsIndices:
					if index[0]!=-1 and index[1]!=-1:
						snp1 = self.snps[i][index[0]]
						snp2 = snpsd.snps[j][index[1]]
						if snp1!=self.missingVal and snp2!=self.missingVal:
							counts += 1
							if snp1!=snp2:
								fails = fails+1
				error = 0
				if counts>0:
					error = float(fails)/float(counts)
				snpErrorRate.append(error)										

				newPositions.append(pos1)
				newSnp = []
				oldSnp1 = self.snps[i]
				oldSnp2 = snpsd.snps[j]
				for index in accessionsIndices:
					if index[0] != -1 and oldSnp1[index[0]]!=self.missingVal and priority==1:
						newSnp.append(oldSnp1[index[0]])
					elif index[0] != -1 and oldSnp1[index[0]]!=self.missingVal and priority==2:
						if index[1] != -1:
							if oldSnp2[index[1]]==self.missingVal:
								newSnp.append(oldSnp1[index[0]])
							else:
								newSnp.append(oldSnp2[index[1]])
						else:
							newSnp.append(oldSnp1[index[0]])
					elif index[1] != -1:
						newSnp.append(oldSnp2[index[1]])
					else:
						newSnp.append(self.missingVal)
				newSnps.append(newSnp)
				i = i+1
				j = j+1

			else: 
				# One pointer has reached the end and the end and the other surpassed it, i.e. we only need to copy the remaining one..
				while i<len(self.positions):
					newPositions.append(self.positions[i])
					newSnp = []
					oldSnp = self.snps[i]
					for index in accessionsIndices:
						if index[0]!=-1:
							newSnp.append(oldSnp[index[0]])				   
						else:
							newSnp.append(self.missingVal)
					newSnps.append(newSnp)
					i = i+1

				while j<len(snpsd.positions):
					if unionType==1 or unionType==3:
						newPositions.append(snpsd.positions[j])
						newSnp = []
						oldSnp = snpsd.snps[j]
						for index in accessionsIndices:
							if index[1]!=-1:
								newSnp.append(oldSnp[index[1]])				   
							else:
								newSnp.append(self.missingVal)
						newSnps.append(newSnp)
					j = j+1
				 
				break
		
		
		if snpErrorRate :
			print "Mean Snp Error:",sum(snpErrorRate)/float(len(snpErrorRate))
		print "Number of SNPs in merged data:",len(newPositions)
		print "Number of SNPs in merged data:",len(newSnps)
		print "Number of accessions in merged data:",len(newAccessions)

		self.snps = newSnps
		self.positions = newPositions
		self.accessions = newAccessions
		self.arrayIds = None

	def mergeDataIntersection(self, snpsd, priority=1, intersectionType=2):
		"""
		Merges two data, where the resulting data has the intersection of the SNPs or/and accessions

		intersectionType=
		1: Only common SNPs are included in the dataset  (not implemented)
		2: Only common accessions are included in the merged dataset 
		3: Only common SNPs and accessions are included in the merged dataset (not implemented)
		
		It doesn't deal with multiple identical ecotypes/accession
		"""
		
		print "Merging datas"
		print "Number of snps:",len(self.snps),"and",len(snpsd.snps)
		
		#Find new accession indices
		newAccessions = []
		accessionsIndices = []
		commonAccessions = list(set(self.accessions).intersection(set(snpsd.accessions)))
		commonPositions = list(set(self.positions).intersection(set(snpsd.positions)))
		allAccessions = list(set(self.accessions).union(set(snpsd.accessions)))
		
		if intersectionType==2 or intersectionType==3:
			newAccessions = commonAccessions
		elif intersectionType==1:
			newAccessions = self.accessions

		for acc in newAccessions:
			index1=-1
			index2=-1
			if self.accessions.count(acc):
				index1=self.accessions.index(acc)
			if snpsd.accessions.count(acc):
				index2=snpsd.accessions.index(acc)
			accessionsIndices.append([index1, index2])
			
			
		print "Number of common accessions:", len(commonAccessions)
		print "Total number of accessions:",len(allAccessions)
		print "Number of common Snps:",len(commonPositions)
		#print "Only in 1st data set", list(set(self.accessions).difference(set(commonAccessions)))
		#print "Only in 2st data set", list(set(snpsd.accessions).difference(set(commonAccessions)))
			
		snpErrorRate = []
		newSnps = []
		newPositions = []
		i = 0
		j = 0 
		while i <= len(self.positions) and j <= len(snpsd.positions):
			if i < len(self.positions):
				pos1 = self.positions[i]
			if j < len(snpsd.positions):
				pos2 = snpsd.positions[j] 
			if i < len(self.positions) and pos1 < pos2:
				if intersectionType == 2:
					newPositions.append(pos1)
					newSnp = []
					oldSnp = self.snps[i]
					for index in accessionsIndices:
						if index[0]!=-1:
							newSnp.append(oldSnp[index[0]])				   
						else:
							newSnp.append(self.missingVal)
					newSnps.append(newSnp)
				i = i+1
			elif j < len(snpsd.positions) and pos2 < pos1:
				j = j+1
			elif i < len(self.positions) and j < len(snpsd.positions) and pos1==pos2:
				counts = 0
				fails = 0
				for index in accessionsIndices:
					if index[0]!=-1 and index[1]!=-1:
						snp1 = self.snps[i][index[0]]
						snp2 = snpsd.snps[j][index[1]]
						if snp1!=self.missingVal and snp2!=self.missingVal:
							counts += 1
							if snp1!=snp2:
								fails = fails+1
				error = 0
				if counts>0:
					error = float(fails)/float(counts)
				snpErrorRate.append(error)										

				newPositions.append(pos1)
				newSnp = []
				oldSnp1 = self.snps[i]
				oldSnp2 = snpsd.snps[j]
				for index in accessionsIndices:
					if index[0] != -1 and oldSnp1[index[0]]!=self.missingVal and priority==1:
						newSnp.append(oldSnp1[index[0]])
					elif index[0] != -1 and oldSnp1[index[0]]!=self.missingVal and priority==2:
						if index[1] != -1:
							if oldSnp2[index[1]]==self.missingVal:
								newSnp.append(oldSnp1[index[0]])
							else:
								newSnp.append(oldSnp2[index[1]])
						else:
							newSnp.append(oldSnp1[index[0]])
					elif index[1] != -1:
						newSnp.append(oldSnp2[index[1]])
					else:
						newSnp.append(self.missingVal)
				newSnps.append(newSnp)
				i = i+1
				j = j+1

			else: 
				# One pointer has reached the end and the end and the other surpassed it, i.e. we only need to copy the remaining one..
				while i<len(self.positions):
					if intersectionType == 2:
						newPositions.append(self.positions[i])
						newSnp = []
						oldSnp = self.snps[i]
						for index in accessionsIndices:
							if index[0]!=-1:
								newSnp.append(oldSnp[index[0]])				   
							else:
								newSnp.append(self.missingVal)
						newSnps.append(newSnp)
					i = i+1

				while j<len(snpsd.positions):
					j = j+1
				 
				break
		
		
		if len(snpErrorRate):
			print "Mean Snp Error:",sum(snpErrorRate)/float(len(snpErrorRate))
		print "Number of SNPs in merged data:",len(newPositions)
		print "Number of SNPs in merged data:",len(newSnps)
		print "Number of accessions in merged data:",len(newAccessions)

		self.snps = newSnps
		self.positions = newPositions
		self.accessions = newAccessions
		self.arrayIds = None


	def mergeData(self,snpsd, priority=1, debug=0):
		"""

		Merges two RawSnpsData objects.

		If snps disagree, then the snps from the object called from is used.		
		"""
		sys.stderr.write("Merging datas Number of snps: %s vs %s ..."%(len(self.snps),len(snpsd.snps)))
		# Find common accession indices
		accessionsIndices = []
		commonAccessions = list(set(self.accessions).intersection(set(snpsd.accessions)))
		allAccessions = list(set(self.accessions).union(set(snpsd.accessions)))

		for i in range(0,len(self.accessions)):
			acc1 = self.accessions[i]
			for k in range(0,len(snpsd.accessions)):
				acc2 = snpsd.accessions[k]
				if acc1==acc2:
					accessionsIndices.append([i,k])
   
		if debug:
			sys.stderr.write("Common accessions: %s\n"% len(commonAccessions))
			sys.stderr.write("All accessions: %s\n"%len(allAccessions))
			#print "Only in 1st data set", list(set(self.accessions).difference(set(commonAccessions)))
			#print "Only in 2st data set", list(set(snpsd.accessions).difference(set(commonAccessions)))
			print snpsd.accessions
			print len(snpsd.accessions), len(list(set(snpsd.accessions)))
			
		commonSnpsPos = []
		snpErrorRate = []
		goodSnpsCounts = []
		i = 0
		j = 0 
		while i <= len(self.positions) and j <= len(snpsd.positions):
			if i < len(self.positions):
				pos1 = self.positions[i]
			if j < len(snpsd.positions):
				pos2 = snpsd.positions[j] 
			if i < len(self.positions) and pos1 < pos2: #Do nothing
				i = i+1
			elif j < len(snpsd.positions) and pos2 < pos1:  #Do nothing
				j = j+1
			elif i < len(self.positions) and j < len(snpsd.positions) and pos1==pos2:
				commonSnpsPos.append(pos1)
				counts = 0
				fails = 0
				for index in accessionsIndices:
					snp1 = self.snps[i][index[0]]
					snp2 = snpsd.snps[j][index[1]]
					if snp1!=self.missingVal and snp2!=self.missingVal:
						counts += 1
						if snp1!=snp2:
							fails = fails+1

					if self.snps[i][index[0]] == self.missingVal or priority==2 and snpsd.snps[j][index[1]] != self.missingVal:
						self.snps[i][index[0]]=snpsd.snps[j][index[1]]		   

				goodSnpsCounts.append(counts)
				error = 0
				if counts>0:
					error = float(fails)/float(counts)
				snpErrorRate.append(error)										
				i = i+1
				j = j+1
				action ="pos2=pos1"
			else: 
				# One pointer has reached the end so we're done...
				break
		sys.stderr.write("In all %s common snps found.\n"%len(commonSnpsPos))
		sys.stderr.write("In all %s common accessions found.\n"%len(commonAccessions))
		sys.stderr.write("Mean Snp Error: %s.\n"%(sum(snpErrorRate)/float(len(snpErrorRate))) )



	def compareWith(self,snpsd, withArrayIds=0, verbose=True, heterozygous2NA=False):
		"""
		05/10/2008 len(commonSnpsPos) could be zero
		This function performs QC on two datasets.

		Requires accessions to be defined.

		withArrayIds = 0 (no array IDs), =1 the object called from has array IDs, =2 both objects have array IDs 
		"""
		basicAlphabet = ['-','A','C','G','T']

		if verbose:
			print "Comparing datas"
			print "Number of snps:",len(self.snps),"and",len(snpsd.snps)
		# Find common accession indices
		accessionsIndices = []
		accessionErrorRate = []
		accessionCallRates = [[],[]]
		accessionCounts = []
		commonAccessions = []
		arrayIds = []
		for i in range(0,len(self.accessions)):
			acc = self.accessions[i]
			if snpsd.accessions.count(acc):
				j = snpsd.accessions.index(acc)
				accessionsIndices.append([i,j])
				accessionErrorRate.append(0)
				accessionCounts.append(0)
				accessionCallRates[0].append(0)
				accessionCallRates[1].append(0)
				commonAccessions.append(acc)
				if withArrayIds>0:
					if withArrayIds==1:
						aId = self.arrayIds[i]
					elif withArrayIds==2:
						aId = (self.arrayIds[i], snpsd.arrayIds[j])
					arrayIds.append(aId)
		commonSnpsPos = []
		snpErrorRate = []
		snpCallRate = [[],[]]
		goodSnpsCounts = []
		totalCounts = 0
		totalFails = 0
		i = 0
		j = 0
		while i <= len(self.positions) and j <= len(snpsd.positions):
			if i < len(self.positions):
				pos1 = self.positions[i]
			if j < len(snpsd.positions):
				pos2 = snpsd.positions[j] 
			if i < len(self.positions) and pos1 < pos2:
				i = i+1
			elif j < len(snpsd.positions) and pos2 < pos1:
				j = j+1
			elif i < len(self.positions) and j < len(snpsd.positions) and pos1==pos2:
				commonSnpsPos.append(pos1)
				fails = 0
				counts = 0
				missing1 = 0
				missing2 = 0
				for k in range(0,len(accessionsIndices)):
					accIndices = accessionsIndices[k]
					snp1 = self.snps[i][accIndices[0]]
					snp2 = snpsd.snps[j][accIndices[1]]
					
					if heterozygous2NA:
						if snp1 in basicAlphabet and snp2 in basicAlphabet:
							accessionCounts[k] += 1
							counts += 1
							if snp1!=snp2:
								fails = fails+1
								accessionErrorRate[k] += 1
						else:
							if snp1==self.missingVal:
								accessionCallRates[0][k]+=1
								missing1 += 1
							if snp2==self.missingVal:
								accessionCallRates[1][k]+=1
								missing2 += 1
					else:
						if snp1!=self.missingVal and snp2!=self.missingVal:
							accessionCounts[k] += 1
							counts += 1
							if snp1!=snp2:
								fails = fails+1
								accessionErrorRate[k] += 1
						else:
							if snp1==self.missingVal:
								accessionCallRates[0][k]+=1
								missing1 += 1
							if snp2==self.missingVal:
								accessionCallRates[1][k]+=1
								missing2 += 1
				goodSnpsCounts.append(counts)
				error = 0
				totalCounts += counts
				totalFails += fails
				if counts>0:
					error = float(fails)/float(counts)
					snpErrorRate.append(error) 
				snpCallRate[0].append(missing1/float(len(accessionsIndices)))									   
				snpCallRate[1].append(missing2/float(len(accessionsIndices)))									   
				i = i+1
				j = j+1
			else: 
				# One pointer has reached and the end and the other surpassed it.
				break
		
		for i in range(0,len(accessionErrorRate)):
			if accessionCounts[i]>0:
				accessionErrorRate[i] = accessionErrorRate[i]/float(accessionCounts[i])
			no_of_common_snps_pos = len(commonSnpsPos)
			if no_of_common_snps_pos>0:	#05/08/10 yh
				accessionCallRates[0][i] = accessionCallRates[0][i]/float(no_of_common_snps_pos)
				accessionCallRates[1][i] = accessionCallRates[1][i]/float(no_of_common_snps_pos)
			else:
				accessionCallRates[0][i] = 0
				accessionCallRates[1][i] = 1
		"""
		print "In all",len(snpErrorRate),"common snps found"
		print "In all",len(commonAccessions),"common accessions found"
		print "Common accessions IDs :",commonAccessions
		print "Common SNPs positions :", commonSnpsPos
		print "Accessions error rates",accessionErrorRate 
		print "Average Accession SNP Error:",sum(accessionErrorRate)/float(len(accessionErrorRate))
		print "SNP error rates",snpErrorRate
		print "Average Snp Error:",sum(snpErrorRate)/float(len(snpErrorRate))
		"""

		naCounts1 = [0]*len(accessionsIndices)
		for i in range(0,len(self.positions)):
			for k in range(0,len(accessionsIndices)):
				accIndices = accessionsIndices[k]
				snp = self.snps[i][accIndices[0]]
				if snp==self.missingVal:
					naCounts1[k] += 1
		
		naCounts2 = [0]*len(accessionsIndices)
		for i in range(0,len(snpsd.positions)):
			for k in range(0,len(accessionsIndices)):
				accIndices = accessionsIndices[k]
				snp = snpsd.snps[i][accIndices[1]]
				if snp==self.missingVal:
					naCounts2[k] += 1
		
		
		return [commonSnpsPos, snpErrorRate, commonAccessions, accessionErrorRate, accessionCallRates, arrayIds, accessionCounts, snpCallRate, [naCounts1,naCounts2], [totalCounts,totalFails]]

	def getSnpsData(self, missingVal=-1):
		"""
		Returns a SnpsData object correspoding to this RawSnpsData object.

		Note that some of the SnpsData attributes are a shallow copy of the RawSnpsData obj.

		Note that 
		"""
		decoder = {self.missingVal:missingVal} #Might cause errors somewhere???!!!
		
		snps = []
		for i in range(0,len(self.snps)):
			k = 0
			for nt in self.alphabet:
				if nt in self.snps[i]:
					decoder[nt]=k
					k = k+1
			snp = []
			if k > 2:
				max1 = 0
				maxnt1 = ''
				max2 = 0
				maxnt2 = ''
				for nt in self.alphabet:
					c = self.snps[i].count(nt)
					if c>max1:
						max1 = c
						maxnt1 = nt
					elif c>max2:
						max2 = c
						maxnt2 = nt
					decoder[nt]=missingVal
				decoder[maxnt1]=0
				decoder[maxnt2]=1
			for nt in self.snps[i]:
				snp.append(decoder[nt])
			snps.append(snp)

		accessions = self.accessions
		positions = self.positions
		return SnpsData(snps,positions,accessions=accessions)


	def filterBadSnps(self,snpsd,maxNumError=0):
		"""
		05/12/08 add no_of_snps_filtered_by_mismatch
		Filters snps with high rate mismatches, when compared against another snpsd.
		"""

		newSnps = []
		newPositions = []
		sys.stderr.write( "Comparing datas. Number of snps: %s vs %s. \n"%(len(self.snps), len(snpsd.snps)))
		# Find common accession indices
		accessionsIndices = []
		commonAccessions = []
		for i in range(0,len(self.accessions)):
			acc = self.accessions[i]
			if snpsd.accessions.count(acc):
				j = snpsd.accessions.index(acc)
				accessionsIndices.append([i,j])
				commonAccessions.append(acc)		 


		commonSnpsPos = []
		i = 0
		j = 0
		while i <= len(self.positions) and j <= len(snpsd.positions):
			if i < len(self.positions):
				pos1 = self.positions[i]
			if j < len(snpsd.positions):
				pos2 = snpsd.positions[j] 
			if i < len(self.positions) and pos1 < pos2:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])
				i = i+1
			elif j < len(snpsd.positions) and pos2 < pos1:
				j = j+1
			elif i < len(self.positions) and j < len(snpsd.positions) and pos1==pos2:
				commonSnpsPos.append(pos1)
				fails = 0
				counts = 0
				for k in range(0,len(accessionsIndices)):
					accIndices = accessionsIndices[k]
					snp1 = self.snps[i][accIndices[0]]
					snp2 = snpsd.snps[j][accIndices[1]]
					if snp1!=self.missingVal and snp2!=self.missingVal:
						counts += 1
						if snp1!=snp2:
							fails = fails+1
				error = 0
				if counts>0:
					error = float(fails)/float(counts)
				if error<=maxNumError:
					newSnps.append(self.snps[i])
					newPositions.append(self.positions[i])				
				i = i+1
				j = j+1
			else: 
				# One pointer has reached and the end and the other surpassed it.
				break
		self.no_of_snps_filtered_by_mismatch = len(self.snps)-len(newSnps)
		sys.stderr.write('%s SNPs were filtered\n'%(self.no_of_snps_filtered_by_mismatch))
		self.snps = newSnps
		self.positions = newPositions
		

	def convertBadCallsToNA(self,minCallProb=0):
		"""
		Converts all base calls with call prob. lower than the given one to NAs.
		"""
		totalCount = len(self.positions)*len(self.snps[0])
		count = 0
		for i in range(0,len(self.positions)):
			for j in range(0,len(self.snps[i])):
				if self.callProbabilities[i][j]<minCallProb:
					self.snps[i][j] = self.missingVal
					count += 1
		fractionConverted = count/float(totalCount)
		return fractionConverted
		



	def countMissingSnps(self):
		"""
		Returns a list of accessions and their missing value rates.
		"""
		missingCounts = 0
		totalCounts = 0
		for i in range(0,len(self.positions)):
			for j in range(0,len(self.accessions)):
				totalCounts +=1
				if self.snps[i][j]==self.missingVal:
					missingCounts += 1
		
		return missingCounts/float(totalCounts)
	
	def getSnpsNArates(self):
		"""
		Returns a list of accessions and their missing value rates.
		"""
		naRates = []
		for i in range(0,len(self.positions)):
			missingCounts = 0
			totalCounts = 0
			for j in range(0,len(self.accessions)):
				totalCounts +=1
				if self.snps[i][j]==self.missingVal:
					missingCounts += 1
			naRates.append(missingCounts/float(totalCounts))
					
		return naRates


	def filterMissingSnps(self, maxNumMissing=0):
		"""
		05/12/2008 add no_of_snps_filtered_by_na
		Removes SNPs from the data which have more than maxNumMissing missing values.
		"""
		newPositions = []
		newSnps = []
		for i in range(0,len(self.positions)):
			missingCount = 0
			for nt in self.snps[i]:
				if nt ==self.missingVal:
					missingCount += 1
			if missingCount<=maxNumMissing:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])
		numRemoved = len(self.positions)-len(newPositions)
		self.no_of_snps_filtered_by_na = numRemoved
		self.snps = newSnps
		self.positions = newPositions
		return numRemoved


	def filterMinMAF(self, minMAF=0):
		"""
		Removes SNPs from the data which have a minor allele count less than the given one.
		"""
		newPositions = []
		newSnps = []
		ntCounts = [0.0]*len(self.alphabet)
		ntl = self.alphabet
		for i in range(0,len(self.positions)):
			snp = self.snps[i]
			totalCount = 0
			for j in range(0,len(self.alphabet)):
				nt = ntl[j]
				c = snp.count(nt)
				ntCounts[j] = c
				totalCount += c
			if totalCount==0 :
				print "snp:",snp
				print "self.alphabet:",self.alphabet
			maxAF = max(ntCounts)
			maf = 0
			if ntCounts.count(maxAF)<2:
				for j in range(0,len(self.alphabet)):
					if ntCounts[j]<maxAF and ntCounts[j] > 0:
						if ntCounts[j]>maf:
							maf = ntCounts[j]
			else:
				maf = maxAF
								
			if minMAF<=maf:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])

		numRemoved = len(self.positions)-len(newPositions)
		self.snps = newSnps
		self.positions = newPositions
		return numRemoved



	def filterMinRMAF(self, minMAF=0):
		"""
		Removes SNPs from the data which have a Relative MAF less than the given one.
		"""
		newPositions = []
		newSnps = []
		ntCounts = [0.0]*len(self.alphabet)
		ntl = self.alphabet
		for i in range(0,len(self.positions)):
			snp = self.snps[i]
			totalCount = 0
			for j in range(0,len(self.alphabet)):
				nt = ntl[j]
				c = snp.count(nt)
				ntCounts[j] = c
				totalCount += c
			if totalCount==0 :
				print "snp:",snp
				print "self.alphabet:",self.alphabet
			for j in range(0,len(self.alphabet)):
				ntCounts[j] = ntCounts[j]/float(totalCount)
			maxAF = max(ntCounts)
			maf = 0
			if ntCounts.count(maxAF)<2:
				for j in range(0,len(self.alphabet)):
					if ntCounts[j]<maxAF and ntCounts[j] > 0.0:
						if ntCounts[j]>maf:
							maf = ntCounts[j]
			else:
				maf = maxAF
								
			if minMAF<=maf:
				newSnps.append(self.snps[i])
				newPositions.append(self.positions[i])

		numRemoved = len(self.positions)-len(newPositions)
		self.snps = newSnps
		self.positions = newPositions
		return numRemoved




	
	def removeAccessions(self,accessions,arrayIds=None):
		"""
		Removes accessions from the data.
		"""
		accPair = set()
		for i in range(0,len(accessions)):
			if arrayIds:
				key = (accessions[i],arrayIds[i])
			else:
				key = accessions[i]
			accPair.add(key)
		newAccessions = []
		newArrayIds = []
		for i in range(0, len(self.snps)):
			snp = self.snps[i]
			newSnp = []
			for j in range(0,len(self.accessions)):
				if arrayIds:
					key = (self.accessions[j], self.arrayIds[j])
				else:
					key = self.accessions[j]
				if not key in accPair:
					newSnp.append(snp[j])
					if i==0:
						newAccessions.append(self.accessions[j])
						if arrayIds:
							newArrayIds.append(self.arrayIds[j])
			self.snps[i] = newSnp
		self.accessions = newAccessions
		if arrayIds:
			self.arrayIds = newArrayIds
		

	def removeAccessionIndices(self,indicesToKeep):
		"""
		Removes accessions from the data.
		"""
		newAccessions = []
		newArrayIds = []
		for i in indicesToKeep:
			newAccessions.append(self.accessions[i])
			if self.arrayIds:
				newArrayIds.append(self.arrayIds[i])
		for i in range(0, len(self.snps)):
			snp = self.snps[i]
			newSnp = []
			for j in indicesToKeep:
				newSnp.append(snp[j])
			self.snps[i] = newSnp
		self.accessions = newAccessions
		if self.arrayIds:
			#print "removeAccessionIndices: has array IDs: self.arrayIds =",self.arrayIds
			self.arrayIds = newArrayIds
			#print "len(self.arrayIds):",len(self.arrayIds)
		#print "len(self.accessions):",len(self.accessions)
			
		
	def mergeIdenticalAccessions(self,accessionIndexList, priority):
		"""
		The priority argument gives particular accessions in the list priority
		if priority is set to 0, then majority (if any) rules.
		"""
		pass


	def accessionsMissingCounts(self):
		"""
		Returns a list of accessions and their missing value rates.
		"""
		missingCounts = [0]*len(self.accessions)

		for i in range(0,len(self.positions)):
			for j in range(0,len(self.accessions)):
				if self.snps[i][j]==self.missingVal:
					missingCounts[j] += 1
		
		return missingCounts

	def getStatString(self):
		st = "Number of accessions: "+str(len(self.accessions))+"\n"
		st += "Number of SNPs: "+str(len(self.snps))+"\n"
		uniqueAccessions = list(set(self.accessions))
		if len(uniqueAccessions)<len(self.accessions):
			st += "Not all accessions are unique. \n"+"Number of unique accessions: "+str(len(uniqueAccessions))+"\n"
			for acc in uniqueAccessions:
				count = self.accessions.count(acc)
				if count>1:
					st += acc+" has "+str(count)+" occurrences.\n\n"
		return st

 		
 
 
class SnpsData(_SnpsData_):
	"""
	A class for SNPs data.  It uses 0, 1 (and 2, 3 if there are more than 2 alleles) to represent SNPs.  
	-1 is used if the allele data is missing.

	Contains various functions that aid the analysis of the data.
	"""
	#freqs = [] #list[position_index1][position_index2-position_index1+1] Linkage frequencies. 
	#baseScale = 1 #Scaling for positions
	alphabet = [0,1,2,3]
	missingVal = -1
	def __init__(self,snps,positions,baseScale=None,accessions=None,arrayIds=None,chromosome=None):
		self.snps = snps 
		self.positions = positions
		if baseScale:
			self.scalePositions(baseScale)
		self.accessions=accessions
		self.arrayIds = arrayIds
		self.chromosome=chromosome


	def clone(self):
		"""
		Filter all SNPs but those in region.
		"""
		newSNPs = []
		newPositions = []
		newAccessions = []
		for acc in self.accessions:
			newAccessions.append(acc)
		
		
		for i in range(0,len(self.positions)):
			new_snp = []
			for j in range(0,len(self.accessions)):
				new_snp.append(self.snps[i][j])
			newSNPs.append(new_snp)
			newPositions.append(self.positions[i])
				
		return SnpsData(newSNPs, newPositions, accessions=newAccessions,arrayIds=self.arrayIds,chromosome=self.chromosome)

		

	def calcFreqs(self,windowSize, innerWindowSize = 0): # Returns a list of two loci comparison frequencies with in a window.
		freqs =	[]
		delta =0
		if len(self.snps)>0:
			delta = 1.0/float(len(self.snps[0]))
		for i in xrange(0,len(self.snps)-1):
			l = []
			j = i+1
			while j<len(self.snps) and (self.positions[j] - self.positions[i]) < innerWindowSize :
				j = j+1
			while j<len(self.snps) and (self.positions[j] - self.positions[i]) <= windowSize:
				jfreqs = [0.0]*4
				snp1 = self.snps[i]
				snp2 = self.snps[j]
				count =	0
				for k in xrange(0,len(snp1)):
					val = snp1[k]*2+snp2[k]
					jfreqs[val] = jfreqs[val]+delta
				l.append(jfreqs)
				j = j+1
			freqs.append(l)
		self.freqs = freqs
		return self.freqs

	def calcFreqsUnbiased(self,windowSize, innerWindowSize = 0): # Returns a list of two loci comparison frequencies with in a window.
		""" 
		Uses a distribution of frequencies that is not dependent on the lenght of the sequence.  (Alot of data is disregarded.)
		"""
		numPairs = 0  #Counts the number of pairs
		freqs =	[]
		delta =0
		if len(self.snps)>0:
			delta = 1.0/float(len(self.snps[0]))
		for i in xrange(0,len(self.snps)-1):
			if (self.positions[len(self.snps)-1] - self.positions[i]) >= windowSize:
				j = i+1
				l = []
				while j<len(self.snps) and (self.positions[j] - self.positions[i]) < innerWindowSize :
					j = j+1
				while  j<len(self.snps) and (self.positions[j] - self.positions[i]) <= windowSize:
					jfreqs = [0.0]*4
					snp1 = self.snps[i]
					snp2 = self.snps[j]
					count =	0
					for k in xrange(0,len(snp1)):
						val = snp1[k]*2+snp2[k]
						jfreqs[val] = jfreqs[val]+delta
					l.append(jfreqs)
					j = j+1
					numPairs = numPairs+1
				freqs.append(l)
			else:
				break
		self.freqs = freqs
		return self.freqs
		#return numPairs
		

	def calcFreqsSimple(self):
		freqs =	[]
		delta =0
		if len(self.snps)>0:
			delta = 1.0/float(len(self.snps[0]))
		for i in xrange(0,len(self.snps)-1):
			l = []
			for j in xrange(i+1,len(self.snps)):
				jfreqs = [0.0]*4
				snp1 = self.snps[i]
				snp2 = self.snps[j]
				count =	0
				for k in xrange(0,len(snp1)):
					val = snp1[k]*2+snp2[k]
					jfreqs[val] = jfreqs[val]+delta
				l.append(jfreqs)
			freqs.append(l)
		self.freqs = freqs
		return self.freqs
	

	def snpsFilter(self):
		"""
		Splits the SNPs up after their allele frequency ..
		"""
		snpsDatas = [SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[]), SnpsData([],[])]

		l = len(self.snps[0])
		for j in xrange(0,len(self.snps)):
			snp = self.snps[j]
			c = snp.count(0)/float(l)
			"""
			if c>0.5:
			c = 1-c
			if c ==	0.5:
			c =0.499
			"""
			if c ==	1:
				c =0.99999
			i = int(c*10)
			snpsDatas[i].addSnp(snp)
			snpsDatas[i].addPos(self.positions[j])
		return snpsDatas
		
	def snpsFilterMAF(self,mafs):
		"""
		Filters all snps with MAF not in the interval out of dataset.
		"""
		newsnps = []
		newpos = []
		#print self.snps
		l = len(self.snps[0])
		if l == 0:
			print self.snps
		for j in xrange(0,len(self.snps)):
			snp = self.snps[j]
			c = snp.count(0)/float(l)
			if c>0.5:
				c = 1-c
			if c >mafs[0] and c<=mafs[1]:
				newsnps.append(snp)
				newpos.append(self.positions[j])
		if len(newsnps)==0:  
			print "Filtered out all snps from",len(self.snps)," what to do what to do?"
		del self.snps
		self.snps = newsnps
		del self.positions
		self.positions = newpos


	def snpsFilterRare(self,threshold=0.1):
		"""Filters all snps with MAF of less than threshold out of dataset."""
		newsnps = []
		newpos = []
		#print self.snps
		l = len(self.snps[0])
		if l == 0:
			print self.snps
		for j in xrange(0,len(self.snps)):
			snp = self.snps[j]
			c = snp.count(0)/float(l)
			if c>0.5:
				c = 1-c
			if c >threshold:
				newsnps.append(snp)
				newpos.append(self.positions[j])
		#if len(newsnps)==0:  
			#print "Filtered out all snps from",len(self.snps)," what to do what to do?"
		del self.snps
		self.snps = newsnps
		del self.positions
		self.positions = newpos


	def _genRecombFile(self,filename,windowSize,maxNumPairs):
		n = len(self.snps[0]) #number of individuals/accessions
		numPairs = self.calcFreqsUnbiased(windowSize)
		if numPairs!= 0:
			filterProb = float(maxNumPairs)/numPairs
		else:
			return numPairs
		f = open(filename, 'w')
		numPairs = 0
		for i in range(0,len(self.freqs)):
			for j in range(0,len(self.freqs[i])):
				if random.random()<=filterProb:
					numPairs = numPairs +1
					st = str(i+1)+" "+str(j+i+2)+" "+str(self.positions[j+i+1]-self.positions[i])+" u "  # u denotes unknown as opposed to ad ancestral derived
					st = st+str(int(self.freqs[i][j][0]*n+0.5))+" "+str(int(self.freqs[i][j][1]*n+0.5))+" "
					st = st+str(int(self.freqs[i][j][2]*n+0.5))+" "+str(int(self.freqs[i][j][3]*n+0.5))+" 0 0 0 0 "+str(100-n)+"\n"
					f.write(st)
		f.close()
		return numPairs

	def estimateRecomb(self, windowSize, maxNumPairs = 10000,  tempfile1 = "tmp1", tempfile2="tmp2", meanTract=200, numPoints=50):
		num = self._genRecombFile(tempfile1,windowSize,maxNumPairs)
		if num < 1:
			return [0,0,0]
		os.system(homedir+"Projects/programs/Maxhap/maxhap 1 "+homedir+"Projects/programs/Maxhap/h100rho  .0008 10 .1 0.01 500 "+str(numPoints)+" "+str(meanTract)+" < "+tempfile1+" > "+tempfile2)
		f = open(tempfile2,'r')
		lines = f.readlines()
		npairs = float(lines[1].split()[2])
		i = 2
		while(lines[i].split()[0]=="Warning:"):
			i = i+1
		rho = float(lines[i].split()[1])
		ratio = float(lines[i].split()[2])
		f.close()
		return [rho,ratio,npairs]


	def meanAF(self):
		""" Mean allele frequency. """
		if len(self.snps):
			l = float(len(self.snps[0]))
			c = 0
			for j in xrange(0,len(self.snps)):
				snp = self.snps[j]
				snpsc = snp.count(0)
				if snpsc<(l/2.0):
					c = c+snpsc/l
				else:
					c = c+abs((l/2.0)-snpsc)/l
			return c/len(self.snps)
		else: 
			return 0
		
	def EHH(self,snp1,snp2):
		""" Calculates the EHH between two SNPs"""
		data = self.snps[snp1:snp2]
		haplotypes = []
		haplotypecount = []
		for i in range(0,len(self.snps[0])):
			haplotype = []
			for j in range(snp1,snp2+1):
				haplotype.append(self.snps[j][i])
			if not haplotype in haplotypes:
				haplotypes.append(haplotype)
				haplotypecount.append(1.0)
			else:
				k = haplotypes.index(haplotype)
				haplotypecount[k] = haplotypecount[k] + 1.0
		s = 0.0
		for i in range(0,len(haplotypes)):
			if haplotypecount[i]>1:
				s = s+haplotypecount[i]*(haplotypecount[i]-1)
		s = s/(len(self.snps[0])*(len(self.snps[0])-1))
		return s

	def totalEHH(self,windowSize,innerWindowSize):
		""" 
		Lenght indep mean EHH statistics.. (Note: no data filtering!)
		"""
		ehhcount = 0
		ehh = 0.0
		for i in xrange(0,len(self.snps)-1):
			if (self.positions[len(self.snps)-1] - self.positions[i]) >= windowSize:
				j = i+1
				l = []
				while j<len(self.snps) and (self.positions[j] - self.positions[i]) < innerWindowSize :
					j = j+1
				while  j<len(self.snps) and (self.positions[j] - self.positions[i]) <= windowSize:
					ehh = ehh+self.EHH(i,j)
					ehhcount = ehhcount + 1
					j = j+1
			else:
				break
		return [ehh,ehhcount]




class SNPsDataSet:
	#Log 110708 - bjarni: old name was SnpsDataSet
	
	"""
	A class that encompasses multiple _SnpsData_ chromosomes objects (chromosomes), and can deal with them as a whole.

	This object should eventually replace the snpsdata lists.. 
	"""
	snpsDataList = None
	chromosomes = None
	accessions = None

	def __init__(self,snpsds,chromosomes):
		self.snpsDataList = snpsds
		self.chromosomes = chromosomes
		self.accessions = self.snpsDataList[0].accessions
		for i in range(1,len(self.chromosomes)):
			if self.accessions != self.snpsDataList[i].accessions:
				raise Exception("Accessions (or order) are different between SNPs datas")

	def writeToFile(self, filename, deliminator=", ", missingVal = "NA", accDecoder=None, withArrayIds = False, decoder=None, callProbFile=None):
		"""
		Writes data to a file. 
		
		Note that there is no decoder dictionary option here..
		"""
	
		print "Writing data to file:",filename
		numSnps = 0
		for i in range(0,len(self.chromosomes)):
			numSnps += len(self.snpsDataList[i].positions)
		
	   
		#outStr = "NumSnps: "+str(numSnps)+", NumAcc: "+str(len(accessions))+"\n"
		if withArrayIds:
			outStr = ", ".join(["-", "-"]+self.snpsDataList[0].arrayIds)+"\n"
		else:
			outStr = ""
		fieldStrings = ["Chromosome", "Positions"]
		if accDecoder:
			for acc in self.snpsDataList[i].accessions:
				fieldStrings.append(str(accDecoder[acc]))
		else:
			for acc in self.snpsDataList[i].accessions:
				fieldStrings.append(str(acc))
		outStr += deliminator.join(fieldStrings)+"\n"
		f = open(filename,"w")
		f.write(outStr)
		if decoder:
			for i in range(0,len(self.chromosomes)):
				sys.stdout.write(".")
				sys.stdout.flush()
				for j in range(0,len(self.snpsDataList[i].positions)):
					outStr =""
					outStr += str(self.chromosomes[i])+deliminator+str(self.snpsDataList[i].positions[j])
					for k in range(0, len(self.snpsDataList[0].accessions)):
						outStr += deliminator+str(decoder[self.snpsDataList[i].snps[j][k]])
					outStr +="\n"
					f.write(outStr)
		else:
			for i in range(0,len(self.chromosomes)):
				sys.stdout.write(".")
				sys.stdout.flush()
				for j in range(0,len(self.snpsDataList[i].positions)):
					outStr =""
					outStr += str(self.chromosomes[i])+deliminator+str(self.snpsDataList[i].positions[j])
					snp = self.snpsDataList[i].snps[j]
					if len(snp) != len(self.snpsDataList[0].accessions):
						print "len(snp):",len(snp),", vs. len(self.snpsDataList[0].accessions):",len(self.snpsDataList[0].accessions)
						raise Exception("The length didn't match")
					for nt in snp:
						outStr += deliminator+str(nt)
					outStr +="\n"
					f.write(outStr)
		f.close()
		print ""

		if callProbFile:
			if withArrayIds:
				outStr = "-, -, "+", ".join(self.snpsDataList[0].arrayIds)+"\n"
			else:
				outStr = ""
			f = open(callProbFile,"w")
			outStr += deliminator.join(fieldStrings)+"\n"
			f.write(outStr)
			f.flush()
			for i in range(0,len(self.chromosomes)):
				outStr = ""
				snpsd = self.snpsDataList[i]
				self.snpsDataList[i] = []
				for j in range(0,len(snpsd.positions)):
					outStr += str(self.chromosomes[i])+deliminator+str(snpsd.positions[j])
					for k in range(0, len(snpsd.accessions)):
						outStr += deliminator+str(snpsd.callProbabilities[j][k])
					outStr +="\n"
				del snpsd
				f.write(outStr)
				f.flush()
			f.close()


	def getSnps(self):
		snplist = []
		for snpsd in self.snpsDataList:
			for snp in snpsd.snps:
				snplist.append(snp)
		return snplist
		
	def getPositions(self):
		poslist = []
		for snpsd in self.snpsDataList:
			for pos in snpsd.positions:
				poslist.append(pos)
		return poslist
		
	def getChrPosList(self):
		chr_pos_list = []
		for i in range(0,len(self.snpsDataList)):
			snpsd = self.snpsDataList[i]
			chr = i+1
			for pos in snpsd.positions:
				chr_pos_list.append((chr,pos))
		return chr_pos_list
		
	def getChrPosSNPList(self):
		chr_pos_snp_list = []
		for i in range(0,len(self.snpsDataList)):
			snpsd = self.snpsDataList[i]
			chr = i+1
			for j in range(0,len(snpsd.positions)):
				pos = snpsd.positions[j]
				snp = snpsd.snps[j]
				chr_pos_snp_list.append((chr,pos,snp))
		return chr_pos_snp_list


	def updateRegions(self,regionList):
		"""
		Deprecated 11/11/08 - Bjarni
		"""
		c_i=0
		i=0
		rl_i=0 #region list index
		while c_i<len(self.chromosomes) and rl_i<len(regionList):
			region = regionList[rl_i]
			snpsd = self.snpsDataList[c_i]
			cp1=(c_i+1,snpsd.positions[i])
			cp_start=(region.chromosome,region.startPos)
			while cp1 < cp_start:
				if i < len(snpsd.positions):
					i += 1
				else:
					c_i += 1
					snpsd = self.snpsDataList[c_i]
					i = 0
				cp1=(c_i+1,snpsd.positions[i])
			cp_end=(region.chromosome,region.endPos)
			while cp1<=cp_end:
				"""Update current region!"""
				region.snps.append(snpsd.snps[i])
				region.snps_indices.append((c_i,i))
				
				i += 1
				if i < len(snpsd.positions):
					cp1=(c_i+1,snpsd.positions[i])
				else:
					c_i += 1
					i = 0
					break
						
			rl_i += 1

def readSNPsDataSetFile(delim=","):
	"""
	Read data file and return a SNPsDataSet object.
	"""
	pass
	
def readSNPsDataSetAccessions(datafile,delim=","):
	f = open(datafile, 'r')
	line = f.readline().split(delim)
	arrayIDs = []
	if line[0]!="Chromosome":
		for aID in line[2:]:
			arrayIDs.append(aID.strip())		
		line = f.readline().split(delim)
	f.close()
	accessions = []
	for acc in line[2:]:
		accessions.append(acc.strip())
	return (accessions,arrayIDs)




def coordinateSnpsAndPhenotypeData(phed,p_i,snpsds,onlyBinarySNPs=True):
	"""
	1. Remove accessions which are not in either of the two datasets
	2. Order the data in same way.
	3. Remove monomorphic SNPs
	"""
	
	numAcc = len(snpsds[0].accessions)
	phenotype = phed.getPhenIndex(p_i)
	accIndicesToKeep = []			
	phenAccIndicesToKeep = []
	#Checking which accessions to keep and which to remove .
	for i in range(0,len(snpsds[0].accessions)):
		acc1 = snpsds[0].accessions[i]
		for j in range(0,len(phed.accessions)):
			acc2 = phed.accessions[j]
			if acc1==acc2 and phed.phenotypeValues[j][phenotype]!='NA':
				accIndicesToKeep.append(i)
				phenAccIndicesToKeep.append(j)
				break	


	#Filter accessions which do not have the phenotype value (from the genotype data).
	for snpsd in snpsds:
		sys.stdout.write(".")
		sys.stdout.flush()
		snpsd.removeAccessionIndices(accIndicesToKeep)
	print ""
	print numAcc-len(accIndicesToKeep),"accessions removed from genotype data, leaving",len(accIndicesToKeep),"accessions in all."
		

	print "Filtering phenotype data."
	phed.removeAccessions(phenAccIndicesToKeep) #Removing accessions that don't have genotypes or phenotype values

	#Ordering accessions according to the order of accessions in the genotype file
	accessionMapping = []
	i = 0
	for acc in snpsds[0].accessions:
		if acc in phed.accessions:
			accessionMapping.append((phed.accessions.index(acc),i))
			i += 1
	phed.orderAccessions(accessionMapping)
	

	for snpsd in snpsds:
		snpsd.onlyBinarySnps()
			


def writeRawSnpsDatasToFile(filename,snpsds,chromosomes=[1,2,3,4,5], deliminator=", ", missingVal = "NA", accDecoder=None, withArrayIds = False, callProbFile=None):
	"""
	2008-05-17
		for callProbFile, modify it to output a row immediately. no memory hoarding, untested.
	2008-05-17
		modify it to output a row immediately. no memory hoarding
		fix a slight bug. arrayIds is outputted always using ', ' as delimiter
	Writes data to a file. 
	"""
	import sys,csv
	sys.stderr.write("Writing data to file: %s ..."%filename)
	numSnps = 0
	for i in range(0,len(chromosomes)):
		numSnps += len(snpsds[i].positions)
		
	accessions = snpsds[0].accessions
	for i in range(1,len(chromosomes)):
		if accessions != snpsds[i].accessions:
			raise Exception("Accessions are different between SNPs datas")


	decoder = RawDecoder()
	decoder[RawSnpsData.missingVal]=missingVal

	print "NumSnps: "+str(numSnps)+", NumAcc: "+str(len(accessions))+"\n"
	#writer = csv.writer(open(filename, 'w'), delimiter=deliminator)
	if withArrayIds:
		#writer.writerow(['-', '-']+snpsds[0].arrayIds)
		outStr = deliminator.join(['-', '-'])+deliminator+deliminator.join(snpsds[0].arrayIds)+"\n"
	else:
		outStr = ""
	fieldStrings = ["Chromosome", "Positions"]
	if accDecoder:
		for acc in snpsds[i].accessions:
			fieldStrings.append(str(accDecoder[acc]))
	else:
		for acc in snpsds[i].accessions:
			fieldStrings.append(str(acc))
	#writer.writerow(fieldStrings)
	f = open(filename, 'w')
	outStr += deliminator.join(fieldStrings)+"\n"
	f.write(outStr)
	import util  #Used to convert val list to stringlist.
	for i in range(0,len(chromosomes)):
		for j in range(0,len(snpsds[i].positions)):
			outStr = str(chromosomes[i])+deliminator+str(snpsds[i].positions[j])+deliminator
			snp = util.valListToStrList(snpsds[i].snps[j])
			outStr += deliminator.join(snp)+"\n"
			f.write(outStr)
			f.flush()
	f.close()

	if callProbFile:
		outStr = ""
		if withArrayIds:
			outStr = deliminator.join(["-", "-"]+snpsds[0].arrayIds)+"\n"
		f = open(callProbFile,"w")
		outStr += deliminator.join(fieldStrings)+"\n"
		f.write(outStr)
		f.flush()
		for i in range(0,len(chromosomes)):
			snpsd = snpsds[i]
			for j in range(0,len(snpsd.positions)):
				outStr = str(chromosomes[i])+deliminator+str(snpsd.positions[j])
				for k in range(0, len(snpsd.accessions)):
					outStr += deliminator+str(snpsd.callProbabilities[j][k])
				outStr +="\n"
				f.write(outStr)
				f.flush()
			del snpsd
			
		f.close()
		
	sys.stderr.write("Done.\n")

def getMAF(snp,alphabet=[0,1]): 
	counts = []
	for letter in alphabet:
		counts.append(snp.count(letter))
	maf = min(counts) 
	marf = maf/float(sum(counts))
	return (marf,maf)

def estimateRecomb(snpsdList,baseNum,filterProb,id):
	rho = 0
	npairs = 0
	for i in range(0,len(snpsdList)):
		snpsd = snpsdList[i]
		tmp1 = "tmp"+id+"1"
		tmp2 = "tmp"+id+"2"
		(rho2,npairs2) = snpsd.estimateRecomb(baseNum,filterProb,tmp1,tmp2)
		rho = rho + rho2*npairs2
		npairs = npairs + npairs2
	rho = rho/float(npairs)
	print "rho: "+str(rho)+", npairs: "+str(npairs)
	return rho
		
def D(freqs):
	""" Returns the D' LD measure """
	p1 = freqs[1]+freqs[3]  #Always positive (if no trivial SNPs are allowed).
	p2 = freqs[2]+freqs[3]
	Dmax = min(p1*(1-p2),p2*(1-p1))
	Dmin = -min(p1*p2,(1-p2)*(1-p1))
	D = freqs[3]-p1*p2
	if D >=0.0:
		return D/Dmax
	else:
		return D/Dmin
		
def r2(freqs):
	f1 = freqs[1]+freqs[3]
	f2 = freqs[2]+freqs[3]
	D = freqs[3]-f1*f2
	divisor = f1*f2*(1-f1)*(1-f2)
	if divisor != 0:
		return D*D/divisor
	else:
		return -1


	
def r2listAll(data,windowSize,nbins=10):
	sums = {1:[0.0]*nbins,2:[0.0]*nbins,3:[0.0]*nbins,4:[0.0]*nbins,5:[0.0]*nbins,6:[0.0]*nbins,7:[0.0]*nbins,8:[0.0]*nbins,"mean":[0.0]*nbins}		
	counts = {1:[0]*nbins,2:[0]*nbins,3:[0]*nbins,4:[0]*nbins,5:[0]*nbins,6:[0]*nbins,7:[0]*nbins,8:[0]*nbins,"tot":[0]*nbins}
	for snpsd in data:
		fsnpd = snpsd.snpsFilter()
		for k in [1,2,3,4,5,6,7,8]:
			freqs =	fsnpd[k].calcFreqs(windowSize)
			for i in xrange(0,len(freqs)):
				for j in xrange(0,len(freqs[i])):
					r = r2(freqs[i][j])
					if r !=	-1:
						bin = int((fsnpd[k].positions[j+i+1]-fsnpd[k].positions[i])*nbins/(windowSize+0.01))
						#print fsnpd[k].positions[j+i+1], fsnpd[k].positions[i]
						#print bin						
						counts[k][bin] = counts[k][bin]+1
						sums[k][bin] = sums[k][bin] +	r
						
	for k in [1,2,3,4,5,6,7,8]:
		for i in xrange(0,nbins):
			if counts[k][i] != 0:
				sums["mean"][i]	= sums["mean"][i]+sums[k][i] 
				sums[k][i] = float(sums[k][i])/float(counts[k][i])
				counts["tot"][i] = counts["tot"][i]+counts[k][i]
	for i in xrange(0,nbins):
		if counts["tot"][i] != 0:
			sums["mean"][i] = float(sums["mean"][i])/float(counts["tot"][i])
			
	return (sums)



def DlistAll(snpsdlist,windowSize,nbins=10):
	sums = {1:[0.0]*nbins,2:[0.0]*nbins,3:[0.0]*nbins,4:[0.0]*nbins,5:[0.0]*nbins,6:[0.0]*nbins,7:[0.0]*nbins,8:[0.0]*nbins,"mean":[0.0]*nbins}		
	counts = {1:[0]*nbins,2:[0]*nbins,3:[0]*nbins,4:[0]*nbins,5:[0]*nbins,6:[0]*nbins,7:[0]*nbins,8:[0]*nbins,"tot":[0]*nbins}
	for snpsd in snpsdlist:
		fsnpd = snpsd.snpsFilter()
		for k in [1,2,3,4,5,6,7,8]:
			freqs =	fsnpd[k].calcFreqs(windowSize)
			for i in xrange(0,len(freqs)):
				for j in xrange(0,len(freqs[i])):
					r = D(freqs[i][j])
					if r !=	-1:
						bin = int((fsnpd[k].positions[j+i+1]-fsnpd[k].positions[i])*nbins/(windowSize+0.01))
						counts[k][bin] = counts[k][bin]+1
						sums[k][bin] = sums[k][bin] + r
						
	for k in [1,2,3,4,5,6,7,8]:
		for i in xrange(0,nbins):
			if counts[k][i]	!= 0:
				sums["mean"][i]	= sums["mean"][i]+sums[k][i] 
				sums[k][i] = float(sums[k][i])/float(counts[k][i])
				counts["tot"][i] = counts["tot"][i]+counts[k][i]
	for i in xrange(0,nbins):
		if counts["tot"][i] != 0:
			sums["mean"][i]	= float(sums["mean"][i])/float(counts["tot"][i])
	
	return (sums)


def DlistAll2(snpsdlist,windowSize,nbins=10):
	sums = {0:[0.0]*nbins,1:[0.0]*nbins,2:[0.0]*nbins,3:[0.0]*nbins,4:[0.0]*nbins,"mean":[0.0]*nbins}		
	counts = {0:[0]*nbins,1:[0]*nbins,2:[0]*nbins,3:[0]*nbins,4:[0]*nbins,"tot":[0]*nbins}
	for snpsd in snpsdlist:
		fsnpdata = snpsd.snpsFilter()
		for k in [0,1,2,3,4]:
			fsnpsd1 = fsnpdata[k]
			fsnpsd2 = fsnpdata[9-k]
			for fsnpd in [fsnpsd1,fsnpsd2]:
				freqs =	fsnpd.calcFreqs(windowSize)
				for i in xrange(0,len(freqs)):
					for j in xrange(0,len(freqs[i])):
						r = D(freqs[i][j])
						if r !=	-1:
							bin = int((fsnpd.positions[j+i+1]-fsnpd.positions[i])*nbins/(windowSize+0.01))
							counts[k][bin] = counts[k][bin]+1
							sums[k][bin] = sums[k][bin] + r
			
						
	for k in [0,1,2,3,4]:
		for i in xrange(0,nbins):
			if counts[k][i] != 0:
				sums["mean"][i]	= sums["mean"][i]+sums[k][i] 
				sums[k][i] = float(sums[k][i])/float(counts[k][i])
				counts["tot"][i] = counts["tot"][i]+counts[k][i]
	for i in xrange(0,nbins):
		if counts["tot"][i] != 0:
			sums["mean"][i]	= float(sums["mean"][i])/float(counts["tot"][i])
	
	return (sums)

def r2listAll2(snpsdlist,windowSize,nbins=10):
	sums = {0:[0.0]*nbins,1:[0.0]*nbins,2:[0.0]*nbins,3:[0.0]*nbins,4:[0.0]*nbins,"mean":[0.0]*nbins}		
	counts = {0:[0]*nbins,1:[0]*nbins,2:[0]*nbins,3:[0]*nbins,4:[0]*nbins,"tot":[0]*nbins}
	for snpsd in snpsdlist:
		fsnpdata = snpsd.snpsFilter()
		for k in [0,1,2,3,4]:
			fsnpsd1 = fsnpdata[k]
			fsnpsd2 = fsnpdata[9-k]
			for fsnpd in [fsnpsd1,fsnpsd2]:
				freqs =	fsnpd.calcFreqs(windowSize)
				for i in xrange(0,len(freqs)):
					for j in xrange(0,len(freqs[i])):
						r = r2(freqs[i][j])
						if r !=	-1:
							bin = int((fsnpd.positions[j+i+1]-fsnpd.positions[i])*nbins/(windowSize+0.01))
							counts[k][bin] = counts[k][bin]+1
							sums[k][bin] = sums[k][bin] + r
			
						
	for k in [0,1,2,3,4]:
		for i in xrange(0,nbins):
			if counts[k][i] != 0:
				sums["mean"][i]	= sums["mean"][i]+sums[k][i] 
				sums[k][i] = float(sums[k][i])/float(counts[k][i])
				counts["tot"][i] = counts["tot"][i]+counts[k][i]
	for i in xrange(0,nbins):
		if counts["tot"][i] != 0:
			sums["mean"][i]	= float(sums["mean"][i])/float(counts["tot"][i])
	
	return (sums)


def writeRFormat(plotData, list = [0,1,2,3,4,"mean"],windowSize=20000,ylab="",lab=""):
	delta = float(windowSize)/float(len(plotData[list[0]]))
	st = "xv <- seq("+str(delta/2.0)+","+str(windowSize)+","+str(delta)+")\n"
	maxlim = 0.0
	minlim = 1.0
	for k in list:
		data = plotData[k]
		st = st+"d"+str(k)+" <- c("
		for i in range(0,len(data)-1):
			st = st + str(data[i])+", "
			maxlim = max(maxlim,data[i])
			minlim = min(minlim,data[i])
		st = st+str(data[len(data)-1])+")\n"
		maxlim = max(maxlim,data[len(data)-1])
		minlim = min(minlim,data[len(data)-1])
	i = 1
	for k in list[0:len(list)-1]:
		st = st+"plot(y=d"+str(k)+", x=xv, ylim = c("+str(minlim)+","+str(maxlim)+"), col = "+str(i)+', type = "b",ylab="",xlab="")\npar(new=T)\n'
		i = i + 1	
	st = st+"plot(y=d"+str(list[len(list)-1])+", x=xv, ylim = c("+str(minlim)+","+str(maxlim)+'), type = "b",ylab="'+ylab+'",xlab="Bases", col = '+str(i)+', main="'+lab+'")\n'
	return st


if __name__ == "__main__":
	pass 
