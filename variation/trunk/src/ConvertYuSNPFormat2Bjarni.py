#!/usr/bin/env python
"""

Examples:
	./src/ConvertYuSNPFormat2Bjarni.py -i data/2010/data_2010_ecotype_id_y0002_n1c1d110_mergedup.tsv -o  data/2010/data_2010_ecotype_id_y0002_n1c1d110_mergedup_bjarni.csv -r
	
	./src/ConvertYuSNPFormat2Bjarni.py -i genotyping/149snp/stock_149SNP_y0000110101_mergedup.csv -o genotyping/149snp/stock_149SNP_y0000110101_mergedup_bjarni.csv  -r
	
	./src/ConvertYuSNPFormat2Bjarni.py  -i genotyping/384-illumina_y0000110101_mergedup.csv -o genotyping/384-illumina_y0000110101_mergedup_bjarni.csv -r
	
	./src/ConvertYuSNPFormat2Bjarni.py -i /mnt/nfs/NPUTE_data/input/250k_l3_y0.85.tsv -o /mnt/nfs/NPUTE_data/input/250k_l3_y0.85_bjarni.tsv -a -b

Description:
	Convert Yu's SNP format (input) to Bjarni's.

	Input format is strain X snp. 2nd column ignored by default (change by array_id_2nd_column).
		delimiter (either tab or comma) is automatically detected. 	header is 'chromosome_position'.
	
	Output format is snp X strain, bjarni's format. The addition of an extra first row for array id depends
		on the array_id_2nd_column option. If it's toggled, yes.
	
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64/')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script/')))
from pymodule import process_function_arguments, write_data_matrix, figureOutDelimiter, read_data
from variation.src.QC_250k import SNPData
from common import SNPData2RawSnpsData_ls
import snpsdata

class ConvertYuSNPFormat2Bjarni(object):
	__doc__ = __doc__
	option_default_dict = {('input_fname', 1, ): [None, 'i', 1, ],\
						('output_fname', 1, ): [None, 'o', 1, 'Output Filename'],\
						('ecotype_table', 1, ): ['stock.ecotype', 'e', 1, 'ecotype Table to get ecotypeid2nativename'],\
						('array_id_2nd_column', 0, int): [0, 'a', 0, 'whether 2nd column in input_fname is array id or not'],\
						('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
						('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	def __init__(self, **keywords):
		"""
		2008-05-18
			add argument array_id_2nd_column
		2008-5-12
		"""
		from pymodule import ProcessOptions
		self.ad=ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
	
	def run(self):
		"""
		2008-5-12
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		
		delimiter = figureOutDelimiter(self.input_fname, report=self.report)
		header, strain_acc_list, category_list, data_matrix = read_data(self.input_fname, delimiter=delimiter)
		
		if self.array_id_2nd_column:
			snpData = SNPData(header=header, strain_acc_list=strain_acc_list, category_list=category_list,\
							data_matrix=data_matrix)
		else:
			snpData = SNPData(header=header, strain_acc_list=strain_acc_list,\
							data_matrix=data_matrix)	#ignore category_list
		
		rawSnpsData_ls = SNPData2RawSnpsData_ls(snpData, need_transposeSNPData=1, report=self.report)
		chromosomes = [rawSnpsData.chromosome for rawSnpsData in rawSnpsData_ls]
		snpsdata.writeRawSnpsDatasToFile(self.output_fname, rawSnpsData_ls, chromosomes=chromosomes, deliminator=',', withArrayIds=self.array_id_2nd_column)
		
if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = ConvertYuSNPFormat2Bjarni
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()
