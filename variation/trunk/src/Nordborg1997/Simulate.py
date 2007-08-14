#!/usr/bin/env python
"""
Usage: Simulate.py [OPTIONS] -o OUTPUT_FILE

Option:
	-o ...,	output file
	-t ...,	theta, 5 (default)
	-s ...,	selfing rate, 0.8(default)
	-k ...,	no_of_diploids, 20(default)
	-n ...,	no_of_alleles_in_total, 200(default)
	-b, --debug	enable debug
	-r, --report	enable more progress-related output
	-h, --help	show this help

Examples:
	./Simulate.py -o /tmp/output  -b
	
Description:
	program to simulate data according to Nordborg1997
	
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64/annot/bin')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script/annot/bin')))
import getopt, csv, math, random
import Numeric, pylab
from sets import Set

class Simulate:
	def __init__(self, output_fname=None, theta=5, selfing_rate=0.8, no_of_diploids=20,\
		no_of_alleles_in_total=200, debug=0, report=0):
		"""
		2007-08-03
		"""
		self.output_fname = output_fname
		self.theta = float(theta)
		self.selfing_rate = float(selfing_rate)
		self.no_of_diploids = int(no_of_diploids)
		self.no_of_alleles_in_total = int(no_of_alleles_in_total)
		self.debug = int(debug)
		self.report = int(report)
	
	def simulate_binomial(self, n, p):
		x = 0
		for i in range(n):
			u = random.random()
			if u<=p:
				x += 1
		return x
	
	def forward_simulate_alleles(self, no_of_alleles_to_be_simulated, theta, selfing_rate):
		"""
		2007-08-05
			forward simulation based on Donnelly1995
		2007-08-08
			the algorithm starts with 2 same alleles (not 1 allele)
			now the copy_prob makes sense. (otherwise it's always impossible to reach 2 alleles.)
		"""
		sys.stderr.write("Forward Simulating alleles ...")
		allele_ls = [1,1]
		sigma_sqd = 2/(2-selfing_rate)
		allele_type2counts = {1:2}
		while (len(allele_ls)<=no_of_alleles_to_be_simulated+1):
			no_of_extant_alleles = len(allele_ls)
			chosen_allele_index = random.randint(0, no_of_extant_alleles-1)
			chosen_allele = allele_ls[chosen_allele_index]
			copy_prob = (no_of_extant_alleles-1)*sigma_sqd/(theta+(no_of_extant_alleles-1)*sigma_sqd)
			u = random.random()
			if u<=copy_prob:
				if no_of_extant_alleles==no_of_alleles_to_be_simulated:
					#watch, algorithm stopped when it just exceeds the quota by 1
					break
				else:
					allele_ls.append(chosen_allele)
					allele_type2counts[chosen_allele] += 1
			else:
				if allele_type2counts[chosen_allele]==1:
					new_allele = chosen_allele	#the old allele is singleton, use old label. no of distinctive alleles stay same.
				else:
					new_allele = len(allele_type2counts) + 1
					allele_type2counts[new_allele] = 1
					allele_type2counts[chosen_allele] -= 1
				allele_ls[chosen_allele_index] = new_allele
		sys.stderr.write("Done.\n")
		return allele_ls, allele_type2counts
	
	def partition_alleles_into_individuals(self, allele_ls, X, no_of_diploids):
		"""
		2007-08-05
			algorithm according to simulation step 3 in Nordborg1997
		"""
		sys.stderr.write("Partitioning alleles into individuals...")
		random.shuffle(allele_ls)
		individual_ls = []
		i = -1
		for i in range(X):
			individual_ls.append((allele_ls[i], allele_ls[i]))
		if i==-1:	#X=0
			i=0
		else:
			i += 1	#start from next position
		while len(individual_ls)<no_of_diploids:
			individual_ls.append((allele_ls[i], allele_ls[i+1]))
			i += 2
		individual_ls += allele_ls[i:]
		sys.stderr.write("Done.\n")
		return individual_ls
	
	def run(self):
		"""
		2007-08-05
		"""
		X = self.simulate_binomial(self.no_of_diploids, self.selfing_rate/(2-self.selfing_rate))
		if self.debug:
			import pdb
			pdb.set_trace()
		allele_ls, allele_type2counts = self.forward_simulate_alleles(self.no_of_alleles_in_total-X, self.theta, self.selfing_rate)
		print allele_ls
		print allele_type2counts
		individual_ls = self.partition_alleles_into_individuals(allele_ls, X, self.no_of_diploids)
		print individual_ls
		
		Estimate_instance = Estimate()
		Hw = Estimate_instance.estimate_Hw(individual_ls)
		Hb = Estimate_instance.estimate_Hb(individual_ls)
		print 'Hw:', Hw
		print "Hb:", Hb
		s = Estimate_instance.estimate_s(Hw, Hb)
		theta = Estimate_instance.estimate_theta(Hw, Hb)
		print 's:', s
		print 'theta:', theta
		s_M = Estimate_instance.estimate_s_Milligan1996(Hw, Hb)
		theta_M = Estimate_instance.estimate_theta_Milligan1996(Hw, Hb)
		print "s_M:", s_M
		print "theta_M:", theta_M
		return s, theta

class Estimate:
	def __init__(self, input_fname=None, debug=0, report=0):
		"""
		2007-08-06
		"""
		self.input_fname = input_fname
		self.debug = int(debug)
		self.report = int(report)
	
	def get_no_of_diploids(self, individual_ls):
		"""
		2007-08-06
			the tuples are in the front part of allele_ls
		"""
		no_of_diploids = 0
		for i in range(len(individual_ls)):
			if type(individual_ls[i])==tuple:
				no_of_diploids += 1
			else:	#after all diploids, it's all singletons
				break
		return no_of_diploids
	
	def estimate_Hw(self, individual_ls):
		no_of_homozygous_pairs = 0
		no_of_pairs = 0.0
		no_of_individuals = len(individual_ls)
		for i in range(no_of_individuals):
			if type(individual_ls[i])==tuple:
				no_of_pairs += 1
				if individual_ls[i][0] == individual_ls[i][1]:
					no_of_homozygous_pairs += 1
			else:	#after all diploids, it's all singletons
				break
		return no_of_homozygous_pairs/no_of_pairs
	
	def estimate_Hb(self, individual_ls):
		no_of_homozygous_pairs = 0
		no_of_pairs = 0.0
		no_of_individuals = len(individual_ls)
		for i in range(no_of_individuals):
			for j in range(i+1, no_of_individuals):
				if type(individual_ls[i])==tuple:
					if type(individual_ls[j])==tuple:
						no_of_pairs += 4
						no_of_homozygous_pairs += int(individual_ls[i][0]==individual_ls[j][0])
						no_of_homozygous_pairs += int(individual_ls[i][0]==individual_ls[j][1])
						no_of_homozygous_pairs += int(individual_ls[i][1]==individual_ls[j][0])
						no_of_homozygous_pairs += int(individual_ls[i][1]==individual_ls[j][1])
					else:
						no_of_pairs += 2
						no_of_homozygous_pairs += int(individual_ls[i][0]==individual_ls[j])
						no_of_homozygous_pairs += int(individual_ls[i][1]==individual_ls[j])
				else:
					if type(individual_ls[j])==tuple:	#not supposed to happen as diploids only appear in the beginning part of individual_ls
						no_of_pairs += 2
						no_of_homozygous_pairs += int(individual_ls[i]==individual_ls[j][0])
						no_of_homozygous_pairs += int(individual_ls[i]==individual_ls[j][1])
					else:
						no_of_pairs += 1
						no_of_homozygous_pairs += int(individual_ls[i]==individual_ls[j])
		return no_of_homozygous_pairs/no_of_pairs
	
	def estimate_s(self, Hw, Hb):
		return 2*(Hw-Hb)/(1+Hw-2*Hb)
	
	def estimate_theta(self, Hw, Hb):
		return (Hw-2*Hb+1)/Hb
	
	def estimate_s_Milligan1996(self, Hw, Hb):
		"""
		2007-08-08
			use the estimate from Milligan1996
		"""
		Sw = 1-Hw
		Sb = 1-Hb
		return 2*(Sb-Sw)/(2*Sb-Sw)
	
	def estimate_theta_Milligan1996(self, Hw, Hb):
		"""
		2007-08-08
			use the estimate from Milligan1996
		"""
		Sw = 1-Hw
		Sb = 1-Hb
		return 2*Sb-Sw
	
	def run(self):
		pass
	
	
		
	
if __name__ == '__main__':
	if len(sys.argv) == 1:
		print __doc__
		sys.exit(2)
		
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:t:s:k:n:br", ["help"])
	except:
		print __doc__
		sys.exit(2)
	output_fname = None
	theta = 5
	selfing_rate = 0.8
	no_of_diploids = 20
	no_of_alleles_in_total = 200
	debug = 0
	report = 0
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print __doc__
			sys.exit(2)
		elif opt in ("-o",):
			output_fname = arg
		elif opt in ("-t",):
			theta = float(arg)
		elif opt in ("-s",):
			selfing_rate = float(arg)
		elif opt in ("-k",):
			no_of_diploids = int(arg)
		elif opt in ("-n",):
			no_of_alleles_in_total = int(arg)
		elif opt in ("-b",):
			debug = 1
		elif opt in ("-r",):
			report = 1
	if output_fname:
		"""
		s_ls = []
		theta_ls = []
		for i in range(10000):
			try:
				random.jumpahead(100)
		"""
		instance = Simulate(output_fname, theta, selfing_rate, no_of_diploids, no_of_alleles_in_total, debug, report)
		s, theta = instance.run()
		"""
				s_ls.append(s)
				theta_ls.append(theta)
			except:
				pass
		import rpy
		print "mean of s:", rpy.r.mean(s_ls)
		print "std of s:", rpy.r.sd(s_ls)
		print "mean of theta:", rpy.r.mean(theta_ls)
		print "std of theta:", rpy.r.sd(theta_ls)
		"""
	else:
		print __doc__
		sys.exit(2)