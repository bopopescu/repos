#!/usr/bin/env python
"""

Examples:
	#cross match for call_info_id=1449,1452,1455 to 1457, from call_method_id=3, use 0.85 as oligo cutoff. Table QC_cross_match is new.
	QC_250k_cross_match.py -l 3 -m 9 -c -a -s 1449,1452,1455-1457 -w -y 0.85
	
	QC_250k_cross_match.py  -l 3 -m 9 -c -a -s 9864-10186 -y 0.85
	
	#cross-match all call info entries from call method 3 with the mismatch rate above 0.08, no_of_non_NA_pairs>=5
	QC_250k_cross_match.py  -l 3 -m13 -c -a -s 512-10584 -y 0.85 -t 0.08 -f 5
	
	
Description:
	cross-match 250k call data (whose maternal_ecotype_id and paternal_ecotype_id must be same and non-null)
		from call_info_table against 2010, perlegen, 149SNP data given a list of call_info_ids.
	
	The output (including QC_method_id) is in QC_cross_match table (no output to output_fname even if it's given.)
	
	Some options are inherited from QC_250k, don't make sense here.
		The max_call_info_mismatch_rate option is ignored.
		min_no_of_non_NA_pairs filters cross-matching results by allowing only ones with no_of_non_NA_pairs above it to be stored into db.
		
	
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import time, csv, getopt
import warnings, traceback
from pymodule import process_function_arguments, turn_option_default_dict2argument_default_dict, SNPData, TwoSNPData, getListOutOfStr, read_data
from variation.src.QualityControl import QualityControl
from variation.src.common import number2nt, nt2number
from QC_250k import QC_250k
import Stock_250kDB
from Stock_250kDB import Results, ResultsMethod, PhenotypeMethod, QCMethod, CallQC, CallInfo, README

class QC_250k_cross_match(QC_250k):
	__doc__ = __doc__
	option_default_dict = QC_250k.option_default_dict
	option_default_dict.update({('call_info_id_ls', 1, ): [None, 's', 1, 'list of call_info_ids to be cross-matched, coma or dash-separated'],\
							('new_QC_cross_match_table', 0, int):[0, 'w', 0, 'whether the QC_cross_match table is new or not' ],\
							('min_call_info_mismatch_rate', 0, float):[0.1, 't', 1, 'restrict entries in call_info_id_ls to those whose mismatch_rate >=this rate.' ],\
							('max_mismatch_rate', 0, float):[0.25, '', 1, 'cross-matching results with mismatch_rate <=max_mismatch_rate are to be stored into db.' ]})
	
	
	def __init__(self,  **keywords):
		"""
		2008-07-01 chop off most functions, inherit from QC_250k
		2008-04-20
		"""
		from pymodule import ProcessOptions
		self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		if self.call_info_id_ls:
			self.call_info_id_ls = getListOutOfStr(self.call_info_id_ls, data_type=int)
		self.QCMethod_class = QCMethod
	
	def plone_run(self, min_call_info_mismatch_rate=0.1):
		"""
		2009-6-9
			pass self.max_mismatch_rate, self.min_no_of_non_NA_pairs to TwoSNPData to filter entries stored in db.
		2009-4-13
			add min_call_info_mismatch_rate
		2009-2-5
			add "create_tables=False" to db.setup()
		2008-07-02
			fix a bug which causes the program to continue read data even while call_info_id2fname is empty and input_dir is null.
		2008-07-01
			adjust to the newest functions in QC_250k.py
		2008-04-25
			return None if QC_method_id==0
		2008-04-20
			for plone to call it just to get row_id2NA_mismatch_rate
		"""
		
		import MySQLdb
		conn = MySQLdb.connect(db=self.dbname, host=self.hostname, user = self.user, passwd = self.passwd)
		curs = conn.cursor()
		self.curs = curs
		
		#database connection and etc
		db = Stock_250kDB.Stock_250kDB(username=self.user,
				   password=self.passwd, hostname=self.hostname, database=self.dbname)
		db.setup(create_tables=False)
		session = db.session
		session.begin()
		#transaction = session.create_transaction()
		# if cmp_data_filename not specified, try to find in the data_description column in table QC_method.
		qm = QCMethod.query.get(self.QC_method_id)
		if not self.cmp_data_filename and self.QC_method_id!=0:
			if qm.data_description:
				data_description_ls = qm.data_description.split('=')
				if len(data_description_ls)>1:
					self.cmp_data_filename = qm.data_description.split('=')[1].strip()
		
		#after db query, cmp_data_filename is still nothing, exit program.
		if not self.cmp_data_filename and self.QC_method_id!=0:
			sys.stderr.write("cmp_data_filename is still nothing even after db query. please specify it on the commandline.\n")
			sys.exit(3)
		
		
		#from variation.src.FilterStrainSNPMatrix import FilterStrainSNPMatrix
		header, strain_acc_list, category_list, data_matrix = read_data(self.cmp_data_filename)
		strain_acc_list = map(int, strain_acc_list)	#it's ecotypeid, cast it to integer to be compatible to the later ecotype_id_ls from db
		snpData2 = SNPData(header=header, strain_acc_list=strain_acc_list, \
						data_matrix=data_matrix, snps_table=self.QC_method_id2snps_table.get(self.QC_method_id), ignore_het=qm.ignore_het)
						#category_list is not used.
		
		if self.input_dir:
			#04/22/08 Watch: call_info_id2fname here is fake, it's actually keyed by (array_id, ecotypeid)
			#no submission to db
			call_info_id2fname = self.get_array_id2fname(curs, self.input_dir)
		else:
			#call_info_id2fname = self.get_call_info_id2fname(curs, self.call_info_table, self.call_QC_table, self.QC_method_id)
			call_data = self.get_call_info_id2fname(db, self.QC_method_id, self.call_method_id, \
				filter_calls_QCed=0, max_call_info_mismatch_rate=1, min_call_info_mismatch_rate=min_call_info_mismatch_rate,\
				debug=self.debug)
			call_info_id2fname = call_data.call_info_id2fname
			call_info_ls_to_return = call_data.call_info_ls_to_return
		
		#2008-07-01 pick the call_info_ids to be handled
		new_call_info_id2fname = {}
		for call_info_id_wanted in self.call_info_id_ls:
			if call_info_id_wanted in call_info_id2fname:
				new_call_info_id2fname[call_info_id_wanted] = call_info_id2fname[call_info_id_wanted]
			elif self.report:
				sys.stderr.write("%s not in call_info_id2fname.\n"%(call_info_id_wanted))
		call_info_id2fname = new_call_info_id2fname
		
		if call_info_id2fname:
			pdata = self.read_call_matrix(call_info_id2fname, self.min_probability)
			header = pdata.header
			call_info_id_ls = pdata.call_info_id_ls
			array_id_ls = pdata.array_id_ls
			ecotype_id_ls = pdata.ecotype_id_ls
			data_matrix = pdata.data_matrix
		elif self.input_dir:	#2008-07-02
			#input file is SNP by strain format. double header (1st two lines)
			header, snps_name_ls, category_list, data_matrix = FilterStrainSNPMatrix.read_data(self.input_dir, double_header=1)
			ecotype_id_ls = header[0][2:]
			call_info_id_ls = header[1][2:]
			data_matrix = numpy.array(data_matrix)
			data_matrix = data_matrix.transpose()
			header = ['', ''] + snps_name_ls	#fake a header for SNPData
		else:	#2008-07-02
			sys.stderr.write("No good arrays.\n")
			return None
		
		snps_name2snps_id = None
		
		#swap the ecotype_id_ls and call_info_id_ls when passing them to SNPData. now strain_acc_list=ecotype_id_ls
		snpData1 = SNPData(header=header, strain_acc_list=ecotype_id_ls, category_list= call_info_id_ls, data_matrix=data_matrix, \
						min_probability=self.min_probability, call_method_id=self.call_method_id, col_id2id=snps_name2snps_id,\
						max_call_info_mismatch_rate=self.max_call_info_mismatch_rate, snps_table='stock_250k.snps')	#snps_table is set to the stock_250k snps_table
		
		twoSNPData = TwoSNPData(SNPData1=snpData1, SNPData2=snpData2, curs=curs, \
							QC_method_id=self.QC_method_id, user=self.user, row_matching_by_which_value=0, debug=self.debug,\
							max_mismatch_rate=self.max_mismatch_rate, min_no_of_non_NA_pairs=self.min_no_of_non_NA_pairs)
							#2009-6-9 cross-matching results whose mismatch_rates are below max_mismatch_rate would be put into db. 
		
		row_id2NA_mismatch_rate = None
		
		#2008-05-01 create a cross match table temporarily
		twoSNPData.qc_cross_match_table = 'qc_cross_match'
		twoSNPData.new_QC_cross_match_table = self.new_QC_cross_match_table
		twoSNPData.cal_row_id2pairwise_dist()	#database submission is done along.
		return row_id2NA_mismatch_rate
	
	def run(self):
		if self.debug:
			import pdb
			pdb.set_trace()
		row_id2NA_mismatch_rate = self.plone_run(self.min_call_info_mismatch_rate)
			
		if self.output_fname and row_id2NA_mismatch_rate:
			self.output_row_id2NA_mismatch_rate(row_id2NA_mismatch_rate, self.output_fname)
		
		#WATCH: self.curs rather than curs
		if row_id2NA_mismatch_rate and self.commit and not self.input_dir:
			#if self.input_dir is given, no db submission. call_info_id2fname here is fake, it's actually keyed by (array_id, ecotypeid)
			#row_id2NA_mismatch_rate might be None if it's method 0.
			#self.submit_to_call_QC(self.curs, row_id2NA_mismatch_rate, self.call_QC_table, self.QC_method_id, self.user)
			pass
		
		if self.commit:
			self.curs.execute("commit")


if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = QC_250k_cross_match
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()