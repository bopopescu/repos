#!/usr/bin/env python
"""

Examples:
	./src/Kruskal_Wallis.py -i /tmp/250K_method_5_after_imputation_noRedundant_051908.tsv -p /Network/Data/250k/finalData_051808/phenotypes.tsv -e -r -o /tmp/250K_method_5_after_imputation_noRedundant_051908.LD.pvalue

Description:
	class to do kruskal wallis test on SNP data.
	
	Input genotype file format is Strain X SNP format (Yu's format, Output by DB_250k2data.py Or Output250KSNPs.py + ConvertBjarniSNPFormat2Yu.py).
	Input phenotype file format is Strain X phenotype format (Output by OutputPhenotype.py). "NA" or empty is regarded as missing value.
	
	It requires a minimum number of ecotypes for either alleles of a single SNP to be eligible for kruskal wallis test.
	
	It will automatically match strains in two files. NO worry for missing/extra data in either input file.
	
	2009-1-7
		0 is no longer regarded as NA in genotype_ls. -2 or numpy.nan is regarded as NA.
		please run this program on binary (0/1) SNPs. or run Association.py to invoke this KW instead.
"""

import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))
import csv, numpy
from pymodule import read_data, ProcessOptions, PassingData

def returnTop2Allele(snp_allele2count):
	"""
	2008-08-06 copied from misc.py
	2008-08-06 remove redundant argument snp_allele_ls
	2008-08-05 in the descending order of count for each allele, assign index ascending
	"""
	snp_allele_count_ls = []
	snp_allele_ls = snp_allele2count.keys()
	for snp_allele in snp_allele_ls:
		snp_allele_count_ls.append(snp_allele2count[snp_allele])
	import numpy
	argsort_ls = numpy.argsort(snp_allele_count_ls)
	new_snp_allele2index = {}
	for i in [-1, -2]:
		snp_index = argsort_ls[i]	#-1 is index for biggest, -2 is next biggest
		new_snp_allele2index[snp_allele_ls[snp_index]] = -i-1
	return new_snp_allele2index


class Kruskal_Wallis:
	__doc__ = __doc__
	option_default_dict = {('input_fname', 1, ): ['', 'i', 1, 'input genotype matrix. Strain X SNP format.', ],\
							('output_fname', 1, ): ['', 'o', 1, 'store the pvalue', ],\
							('phenotype_fname', 1, ): [None, 'p', 1, 'phenotype file, "NA" or empty is regarded as missing value.', ],\
							('minus_log_pvalue', 0, ): [0, 'e', 0, 'toggle -log(pvalue)', ],\
							('which_phenotype', 1, int): [0, 'w', 1, 'which phenotype, 0=first phenotype (3rd column in phenotype_fname) and so on.',],\
							('min_data_point', 1, int): [3, 'm', 1, 'minimum number of ecotypes for either alleles of a single SNP to be eligible for kruskal wallis test'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	def __init__(self, **keywords):
		"""
		2008-02-14
		"""
		ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		"""
		if not input_fname or not phenotype_fname or not output_fname:
			print self.__doc__
			sys.exit(2)
		self.input_fname = input_fname
		self.phenotype_fname = phenotype_fname
		self.output_fname = output_fname
		self.log_pvalue = int(log_pvalue)
		self.debug = int(debug)
		self.report = int(report)
		"""
	
	def get_phenotype_matrix_in_data_matrix_order(self, strain_acc_list, strain_acc_list_phen, data_matrix_phen):
		"""
		2009-7-30
			empty string is also regarded as missing value (=numpy.nan).
		2008-09-07
			order the whole phenotype matrix, not just one column.
			convert the phenotype matrix to numpy.float, NA to numpy.nan
		2008-05-21
			strain_acc could be missing in strain_acc_phen2index
			phenotype_value could be 'NA'
		2008-02-14
		"""
		sys.stderr.write("Getting phenotype_matrix in data_matrix order ...")
		strain_acc_phen2index = dict(zip(strain_acc_list_phen, range(len(strain_acc_list_phen)) ) )
		no_of_rows = len(strain_acc_list)	#this is the number of strains in the input matrix, not the phenotype matrix
		no_of_cols = len(data_matrix_phen[0])
		new_data_matrix_phen = numpy.zeros([no_of_rows, no_of_cols], numpy.float)
		for i in range(len(strain_acc_list)):
			strain_acc = strain_acc_list[i]
			if strain_acc in strain_acc_phen2index:
				phen_index = strain_acc_phen2index[strain_acc]
				for j in range(no_of_cols):
					if data_matrix_phen[phen_index][j]=='NA' or data_matrix_phen[phen_index][j]=='':
						new_data_matrix_phen[i,j] = numpy.nan
					else:
						new_data_matrix_phen[i,j] = float(data_matrix_phen[phen_index][j])
			else:
				new_data_matrix_phen[i,:] = numpy.nan
		sys.stderr.write("Done.\n")
		return new_data_matrix_phen
	get_phenotype_matrix_in_data_matrix_order = classmethod(get_phenotype_matrix_in_data_matrix_order)
	
	def _kruskal_wallis(cls, genotype_ls, phenotype_ls, min_data_point=3, snp_index=None):
		"""
		2008-11-25
			0 is no longer regarded as NA in genotype_ls. -2 or numpy.nan is regarded as NA.
		2008-09-07
			split out of _kruskal_wallis_whole_matrix()
			input is one genotype list, one phenotype list
		"""
		import rpy
		rpy.r.as_factor.local_mode(rpy.NO_CONVERSION)
		non_NA_genotype_ls = []
		non_NA_phenotype_ls = []
		non_NA_genotype2count = {}
		#non_NA_genotype2phenotype_ls = {}	#2008-08-06 try wilcox
		for i in range(len(genotype_ls)):
			if genotype_ls[i]!=-2 and not numpy.isnan(genotype_ls[i]) and not numpy.isnan(phenotype_ls[i]):	#assume genotype_ls is either 0 or 1. -2 is NA.
				non_NA_genotype = int(genotype_ls[i])	#2008-11-25 if genotype_ls[i] is of type numpy.int8, rpy.r.as_factor() won't handle.
				non_NA_genotype_ls.append(non_NA_genotype)
				non_NA_phenotype_ls.append(phenotype_ls[i])
				if non_NA_genotype not in non_NA_genotype2count:
					non_NA_genotype2count[non_NA_genotype] = 0
					#non_NA_genotype2phenotype_ls[non_NA_genotype] = []	#2008-08-06 try wilcox
				non_NA_genotype2count[non_NA_genotype] += 1
				#non_NA_genotype2phenotype_ls[non_NA_genotype].append(phenotype_ls[i])	#2008-08-06 try wilcox
		"""
		#2008-08-06 try wilcox
		new_snp_allele2index = returnTop2Allele(non_NA_genotype2count)
		top_2_allele_ls = new_snp_allele2index.keys()
		non_NA_genotype2count = {top_2_allele_ls[0]: non_NA_genotype2count[top_2_allele_ls[0]],
								top_2_allele_ls[1]: non_NA_genotype2count[top_2_allele_ls[1]]}
		"""
		count_ls = non_NA_genotype2count.values()
		
		if len(count_ls)>=2 and min(count_ls)>=min_data_point:	#require all alleles meet the min data point requirement
			kw_result = rpy.r.kruskal_test(x=non_NA_phenotype_ls, g=rpy.r.as_factor(non_NA_genotype_ls))
			pvalue = kw_result['p.value']
			#2008-08-06 try wilcox
			#pvalue = rpy.r.wilcox_test(non_NA_genotype2phenotype_ls[top_2_allele_ls[0]], non_NA_genotype2phenotype_ls[top_2_allele_ls[1]], conf_int=rpy.r.TRUE)['p.value']
			pdata = PassingData(snp_index=snp_index, pvalue=pvalue, count_ls=count_ls)
			
		else:
			pdata = None
		return pdata
	
	_kruskal_wallis = classmethod(_kruskal_wallis)
	
	def _kruskal_wallis_whole_matrix(self, data_matrix, phenotype_ls, min_data_point=3, **keywords):
		"""
		2008-09-07
			_kruskal_wallis() spinned off.
		2008-05-21
			phenotype_ls could have None value, skip them
			each kw result is wrapped in PassingData
		2008-02-14
		"""
		sys.stderr.write("Doing kruskal wallis test ...\n")
		no_of_rows, no_of_cols = data_matrix.shape
		results = []
		counter = 0
		real_counter = 0
		for j in range(no_of_cols):
			genotype_ls = data_matrix[:,j]
			pdata = self._kruskal_wallis(genotype_ls, phenotype_ls, min_data_point, snp_index=j)
			if pdata is not None:
				results.append(pdata)
				real_counter += 1
			counter += 1
			if self.report and counter%2000==0:
				sys.stderr.write("%s\t%s\t%s"%('\x08'*40, counter, real_counter))
		if self.report:
			sys.stderr.write("%s\t%s\t%s"%('\x08'*40, counter, real_counter))
		sys.stderr.write("Done.\n")
		return results
	
	def output_kw_results(self, kw_results, SNP_header, output_fname, log_pvalue=0):
		"""
		2009-6-17
			last two columns now boast MAF, MAC instead of the counts of two alleles
		2008-05-27
			log10
		2008-05-21
			more stuff in kw_results
			each kw result is wrapped in PassingData
		2008-02-14
		"""
		sys.stderr.write("Outputting pvalue results ...")
		writer = csv.writer(open(output_fname,'w'), delimiter='\t')
		for i in range(len(kw_results)):
			pdata = kw_results[i]
			snp_index = pdata.snp_index
			pvalue = pdata.pvalue
			SNP_name = SNP_header[snp_index]
			SNP_pos_ls = SNP_name.split('_')
			if log_pvalue:
				if pvalue>0:
					pvalue = -math.log10(pvalue)
				else:
					pvalue = 'NA'
			MAC = min(pdata.count_ls)
			MAF = float(MAC)/sum(pdata.count_ls)
			writer.writerow([SNP_pos_ls[0], SNP_pos_ls[1], pvalue, MAF, MAC])
		del writer
		sys.stderr.write("Done.\n")
	
	def run(self):
		if self.debug:
			import pdb
			pdb.set_trace()
		header_phen, strain_acc_list_phen, category_list_phen, data_matrix_phen = read_data(self.phenotype_fname, turn_into_integer=0)
		header, strain_acc_list, category_list, data_matrix = read_data(self.input_fname)
		if type(data_matrix)==list:
			data_matrix = numpy.array(data_matrix)
		
		data_matrix_phen = self.get_phenotype_matrix_in_data_matrix_order(strain_acc_list, strain_acc_list_phen, data_matrix_phen)
		kw_results = self._kruskal_wallis_whole_matrix(data_matrix, data_matrix_phen[:, self.which_phenotype], self.min_data_point)
		self.output_kw_results(kw_results, header[2:], self.output_fname, self.minus_log_pvalue)

if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = Kruskal_Wallis
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()