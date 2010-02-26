#!/usr/bin/env python
"""

Examples:
	PutPhenotypeIntoDB.py -i /Network/Data/250k/anthocyanin.csv -u yh -c
	
	PutPhenotypeIntoDB.py -i /Network/Data/250k/hyaloperonaspora2.csv -u yh -c
	
	#2009-5-29 put raw lesioning phenotype into db.
	PutPhenotypeIntoDB.py -i ./acc2lesioning.csv -u yh -c
	
	#2009-7-31 put individual (not-averaged) values of phenotypes into db
	~/script/variation/src/PutPhenotypeIntoDB.py -i /tmp/batch4_swedishlines_FT_LN.txt -u yh -y 2 -c
	
	#2009-7-31 put average values of phenotypes into db
	~/script/variation/src/PutPhenotypeIntoDB.py -i /tmp/batch_3_phenotypes.txt -u yh -y 1 -c -r
	
Description:
	2009-9-23
		Put phenotype data into table phenotype_avg, phenotype_method.
		Input file is matrix format with either tab or coma.:
			First line is the phenotype name for each column (except 1st two cols), which matches the short_name in db or is to be created if it's new.
			First two columns are used to identify the accession. accession ID and name (not used).
			
			If accession ID is comprised of all numbers, it's assumed to be ecotype id.
			Otherwise, if it (turned into upper case) cannot be uniquely linked to an ecotype id by using nativename2tg_ecotypeid_set (key is uppercase)
				& ecotype_id_set_250k_in_pipeline, program would stop and ask user.
		In the individual-datapoint mode, the replicate value is calculated based on the max (phenotype_method_id, ecotype_id) "replicate".
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
import warnings, traceback, re

from Stock_250kDB import Stock_250kDB, PhenotypeAvg, PhenotypeMethod, ArrayInfo, Phenotype
from pymodule import figureOutDelimiter, SNPData, read_data
from pymodule.utils import getGeneIDSetGivenAccVer
from common import getNativename2TgEcotypeIDSet, get_ecotype_id_set_250k_in_pipeline, get_ecotypeid2tg_ecotypeid
import numpy

class PutPhenotypeIntoDB(object):
	__doc__ = __doc__
	option_default_dict = {('drivername', 1,):['mysql', 'v', 1, 'which type of database? mysql or postgres', ],\
							('hostname', 1, ): ['papaya.usc.edu', 'z', 1, 'hostname of the db server', ],\
							('dbname', 1, ): ['stock_250k', 'd', 1, 'database name', ],\
							('schema', 0, ): [None, 'k', 1, 'database schema name', ],\
							('db_user', 1, ): [None, 'u', 1, 'database username', ],\
							('db_passwd', 1, ): [None, 'p', 1, 'database password', ],\
							("input_fname", 1, ): [None, 'i', 1, ''],\
							("run_type", 1, int): [1, 'y', 1, '1: submit to phenotype_avg (phenotypes from which only average value is available), 2: submit to phenotype (individual data points are available)'],\
							('commit', 0, int):[0, 'c', 0, 'commit db transaction'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	
	def __init__(self,  **keywords):
		"""
		2009-5-28
		"""
		from pymodule import ProcessOptions
		self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		
		"""
		if self.phenotype_id==-1 and self.phenotype_name is None:
			sys.stderr.write("Error: None of phenotype_id and phenotype_name is specified.\n")
			sys.exit(3)
		"""
		
	allNumberPattern = re.compile(r'^\d+$')
	def straightenEcotypeID(self, accID_ls, nativename2tg_ecotypeid_set, ecotypeid2tg_ecotypeid, ecotype_id_set_250k_in_pipeline=None):
		"""
		2009-8-11
			use accID2ecotype_id to store a map from accID to ecotype_id to ease linking
		2009-7-30
			find all correct ecotype IDs for entries in accID_ls
		"""
		sys.stderr.write("Straightening ecotype id out ...")
		counter = 0
		accID2ecotype_id = {}
		ecotype_id_ls = []
		for original_name in accID_ls:
			counter += 1
			original_name = original_name.strip()
			original_name = original_name.upper() #2009-7-23 turn into uppercase since nativename2tg_ecotypeid_set has its key all upper-cased.
			if original_name in accID2ecotype_id:
				ecotype_id = accID2ecotype_id[original_name]
			elif self.allNumberPattern.match(original_name):	#2009-7-23 the original_name is all number. assume it's ecotypeid.
				ecotype_id = original_name
			elif original_name in nativename2tg_ecotypeid_set:
				tg_ecotypeid_set = nativename2tg_ecotypeid_set.get(original_name)
				if len(tg_ecotypeid_set)>1:
					if ecotype_id_set_250k_in_pipeline is not None:	#2009-7-22 solve the redundancy problem
						candidate_ecotyepid_ls = []
						for ecotype_id in tg_ecotypeid_set:
							if ecotype_id in ecotype_id_set_250k_in_pipeline:
								candidate_ecotyepid_ls.append(ecotype_id)
						if len(candidate_ecotyepid_ls)==1:
							ecotype_id = candidate_ecotyepid_ls[0]
						else:
							ecotype_id = None
					if ecotype_id is None:	#2009-7-22 only do this if the procedure above fails 
						while 1:
							ecotype_id = raw_input("No %s. Pick one ecotype id from "%counter +repr(list(tg_ecotypeid_set)) + " for %s: "%original_name)
							yes_or_no = raw_input("Sure about ecotype id %s?(Y/n)"%ecotype_id)
							if yes_or_no =='n' or yes_or_no=='N' or yes_or_no == 'No' or yes_or_no =='no':
								pass
							else:
								break
						
				else:
					ecotype_id = list(tg_ecotypeid_set)[0]
			else:
				choice_instructions = "No %s. Enter ecotypeid for accession %s: "%(counter, original_name)
				while 1:
					ecotype_id = raw_input(choice_instructions)
					yes_or_no = raw_input("Sure about ecotype id %s?(Y/n)"%ecotype_id)
					if yes_or_no =='n' or yes_or_no=='N' or yes_or_no == 'No' or yes_or_no =='no':
						pass
					else:
						break
			ecotype_id = int(ecotype_id)
			if original_name not in accID2ecotype_id:
				accID2ecotype_id[original_name] = ecotype_id
			tg_ecotypeid = ecotypeid2tg_ecotypeid[ecotype_id]
			ecotype_id_ls.append(tg_ecotypeid)
		sys.stderr.write("Done.\n")
		return ecotype_id_ls
	
	#2009-8-18
	phenotype_name2pm = {}
	def findPhenotypeMethodGivenName(self, phenotype_name, db):
		"""
		2009-7-30
			find/create the db phenotype entry given phenotype_name
		"""
		session = db.session
		if phenotype_name:	#if the short name is given, forget about phenotype_id
			if phenotype_name in self.phenotype_name2pm:
				return self.phenotype_name2pm.get(phenotype_name)
			
			pm = PhenotypeMethod.query.filter_by(short_name=phenotype_name).first()	#try search the db first.
			if not pm:
				pm = PhenotypeMethod(short_name=phenotype_name)
				session.save(pm)
				session.flush()
			if self.report:
				sys.stderr.write("phenotype ID for %s is %s."%(phenotype_name, pm.id))
			self.phenotype_name2pm[phenotype_name] = pm
		return pm
	
	def putPhenotypeIntoDB(self, db, phenData, ecotype_id_ls):
		"""
		2010-2-25
			add functionality to check db whether an ecotype has a phenotype in db already to avoid redundancy.
		2009-7-30
			overhauled to deal with multiple phenotypes from phenData to table phenotype_avg
		2009-7-22
			use ecotype_id_set_250k_in_pipeline to solve the ecotypeid redundancy problem (more than one ecotype ids for one accession name) 
		2009-5-28
		"""
		session = db.session
		no_of_rows, no_of_cols = phenData.data_matrix.shape
		if no_of_rows!=len(ecotype_id_ls):
			sys.stderr.write("Error: No of rows in phenotype matrix (%s) != no of ecotypes from 1st column (%s).\n"%(no_of_rows, len(ecotype_id_ls)))
			sys.exit(3)

		for j in range(len(phenData.col_id_ls)):
			phenotype_name = phenData.col_id_ls[j]
			pm = self.findPhenotypeMethodGivenName(phenotype_name, db)
			sys.stderr.write("Submitting phenotype %s ..."%phenotype_name)
			counter = 0
			success_counter = 0
			no_of_NAs = 0
			no_of_existed = 0
			for i in range(len(phenData.row_id_ls)):
				ecotype_id = ecotype_id_ls[i]
				phenotype_value = phenData.data_matrix[i][j]
				counter += 1
				if numpy.isnan(phenotype_value):
					no_of_NAs += 1
					continue
				if pm.id:	# 2010-2-25 check whether it's in db already
					rows = PhenotypeAvg.query.filter_by(method_id=pm.id).filter_by(ecotype_id=ecotype_id)
					if rows.count()>0:
						no_of_existed += 1
						continue
				pa = PhenotypeAvg(ecotype_id=ecotype_id, value=phenotype_value)
				pa.phenotype_method = pm
				session.save(pa)
				session.flush()
				success_counter += 1
			sys.stderr.write("%s/%s put into db. Ignored: %s NA, %s existed in db.\n"%(success_counter, counter, no_of_NAs, no_of_existed))
	
	def findInitialReplicateCount(self, db, phenotype_method_id, ecotype_id):
		"""
		2009-8-24
			get the maximum replicate out of the db, rather than how many. The two sometimes don't agree.
		2009-8-11
			query table Phenotype to get how many replicates exist in db
		"""
		rows = Phenotype.query.filter_by(method_id=phenotype_method_id).filter_by(ecotype_id=ecotype_id)
		replicate_ls = [row.replicate for row in rows]
		if len(replicate_ls)==0:
			return 0
		else:
			return max(replicate_ls)
	
	def putReplicatePhenotypeIntoDB(self, db, phenData, ecotype_id_ls):
		"""
		2009-8-11
			start the replicate counter based on the db
		2009-7-30
			similar to putPhenotypeIntoDB() but submit data to phenotype
		"""
		session = db.session
		no_of_rows, no_of_cols = phenData.data_matrix.shape
		if no_of_rows!=len(ecotype_id_ls):
			sys.stderr.write("Error: No of rows in phenotype matrix (%s) != no of ecotypes from 1st column (%s).\n"%(no_of_rows, len(ecotype_id_ls)))
			sys.exit(3)
		
		method_id_ecotype_id2count = {}
		
		total_count = 0
		effective_total_count = 0
		for i in range(len(phenData.row_id_ls)):
			replicate_counter = 0
			counter = 0
			for j in range(len(phenData.col_id_ls)):
				phenotype_name = phenData.col_id_ls[j]
				pm = self.findPhenotypeMethodGivenName(phenotype_name, db)
				ecotype_id = ecotype_id_ls[i]
				replicate_key = (pm.id, ecotype_id)
				if replicate_key not in method_id_ecotype_id2count:	#get the replicate count from db
					method_id_ecotype_id2count[replicate_key] = self.findInitialReplicateCount(db, pm.id, ecotype_id)
				
				method_id_ecotype_id2count[replicate_key] += 1
				
				phenotype_value = phenData.data_matrix[i][j]
				counter += 1
				if numpy.isnan(phenotype_value):
					continue
				replicate_counter += 1
				pa = Phenotype(ecotype_id=ecotype_id, value=phenotype_value, replicate=method_id_ecotype_id2count[replicate_key])
				pa.phenotype_method = pm
				session.save(pa)
				session.flush()	#not necessary, but do it in case
			sys.stderr.write("%s/%s put into db.\n"%(replicate_counter, counter))
			total_count += counter
			effective_total_count += replicate_counter
		sys.stderr.write("In total, %s/%s put into db.\n"%(effective_total_count, total_count))
	
	def run(self):
		"""
		2009-5-28
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		db = Stock_250kDB(drivername=self.drivername, username=self.db_user,
				   password=self.db_passwd, hostname=self.hostname, database=self.dbname, schema=self.schema)
		db.setup(create_tables=False)
		
		nativename2tg_ecotypeid_set = getNativename2TgEcotypeIDSet(db.metadata.bind, turnUpperCase=True)
		ecotype_id_set_250k_in_pipeline = get_ecotype_id_set_250k_in_pipeline(ArrayInfo)
		ecotypeid2tg_ecotypeid = get_ecotypeid2tg_ecotypeid(db.metadata.bind)
		
		#turn_into_integer=2 because it's not nucleotides
		header_phen, strain_acc_list_phen, category_list_phen, data_matrix_phen = read_data(self.input_fname, turn_into_integer=2, matrix_data_type=float)
		data_matrix_phen = numpy.array(data_matrix_phen)
		
		#2009-8-19 bug here. strain_acc_list_phen is not unique for each row. causing replicates to have the same value
		#from Association import Association
		#data_matrix_phen = Association.get_phenotype_matrix_in_data_matrix_order(strain_acc_list_phen, strain_acc_list_phen, data_matrix_phen)
		
		phenData = SNPData(header=header_phen, strain_acc_list=strain_acc_list_phen, data_matrix=data_matrix_phen)
		
		ecotype_id_ls = self.straightenEcotypeID(phenData.row_id_ls, nativename2tg_ecotypeid_set, ecotypeid2tg_ecotypeid, \
												ecotype_id_set_250k_in_pipeline)
		
		session = db.session
		session.begin()
		if self.run_type==1:
			self.putPhenotypeIntoDB(db, phenData, ecotype_id_ls)
		elif self.run_type==2:
			self.putReplicatePhenotypeIntoDB(db, phenData, ecotype_id_ls)
		else:
			sys.stderr.write("Unsupported run type: %s.\n"%(self.run_type))
		if self.commit:
			session.commit()

if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = PutPhenotypeIntoDB
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()