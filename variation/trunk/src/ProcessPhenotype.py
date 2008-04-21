#!/usr/bin/env python
"""
2008-02-13
	class to process phenotype data from at.phenotype and at.experiment to get flowering time.
	Flowering time is "time of first flower open" - "date counted as germination"
	
Argument list:
	-z ..., --hostname=...	the hostname, papaya.usc.edu(default)*
	-d ..., --dbname=...	the database name, stock_250k(default)*
	-k ..., --schema=...	which schema in the database, dbsnp(default)
	-o ..., output_fname (if wanna output)
	-a ..., raw_phenotype_table=argument1, at.phenotype(default)*
	-e ..., experiment_table=argument2, at.experiment_table(default)*
	-f ...,	phenotype_table to store results=argument3, stock_250k.phenotype(default)*
	-g ...,	phenotype_avg_table=argument4, stock_250k.phenotype_avg(default)*
	-j ...,	method_table=argument5, stock_250k.phenotype_method(default)*
	-c,	commit db transaction
	-b,	toggle debug
	-r, toggle report
Examples:
	main.py -y 2 -o /tmp/phenotype.tsv
	# dump all data into db
	main.py -y 2 -c
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import time, csv, numpy
import warnings, traceback
from pymodule import process_function_arguments

class ProcessPhenotype:
	__doc__ = __doc__
	def __init__(self,  **keywords):
		"""
		2008-02-28
		"""
		argument_default_dict = {('hostname',1, ):'papaya.usc.edu',\
								('dbname',1, ):'stock_250k',\
								('schema',0, ):'',\
								('user',1, ):None,\
								('passwd',1, ):None,\
								('output_fname',0, ):None,\
								('raw_phenotype_table',1, ):'at.phenotype',\
								('experiment_table',1, ):'at.experiment',\
								('phenotype_table',1, ):'stock_250k.phenotype',\
								('phenotype_avg_table',1, ):'stock_250k.phenotype_avg',\
								('method_table',1, ):'stock_250k.phenotype_method',\
								('commit',0, int):0,\
								('debug',0, int):0,\
								('report',0, int):0}
		"""
		2008-02-28
			argument_default_dict is a dictionary of default arguments, the key is a tuple, ('argument_name', is_argument_required, argument_type)
			argument_type is optional
		"""
		#argument dictionary
		self.ad = process_function_arguments(keywords, argument_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		self.debug = self.ad['debug']
		self.report = self.ad['report']
	
	def get_experiment_id2data(self, curs, experiment_table='at.experiment'):
		"""
		2008-02-20
			
		"""
		sys.stderr.write("Getting experiment_id2data ...\n")
		curs.execute("select id, description, day_counted_as_germination from %s"%experiment_table)
		experiment_id2data = {}
		rows = curs.fetchall()
		for row in rows:
			experiment_id, description, day_counted_as_germination = row
			day_counted_as_germination = str(day_counted_as_germination)	#transform the datetime.date type into string
			time_germination = time.strptime(day_counted_as_germination, '%Y-%m-%d')
			experiment_id2data[experiment_id] = [description, time_germination]
		sys.stderr.write("Done.\n")
		return experiment_id2data
	
	def get_experiment_id2accession_id2reading_ls(self, curs, raw_phenotype_table):
		"""
		2008-04-16
			also get germination date from the same table. glenda added germination date for each strain.
			glenda fixed lots of errors in the phenotype table. but the automatic fix for the old errors in this function
			shouldn't be affected.
		2008-02-29
			replicate gets converted to arabic and included in the returning results
		2008-02-23
			'long ago' now mapped to 'NA'
			the reading_error_dict applied before testing whether it's NA or not
		2008-02-20
		"""
		sys.stderr.write("Getting experiment_id2accession_id2reading_ls ...\n")
		curs.execute("select experiment, accession, replicate, reading, measure from %s where measure='first flower open' or measure='germination date'"%raw_phenotype_table)
		rows = curs.fetchall()
		experiment_id2accession_id2reading_ls = {}
		reading_error_dict = {'1/14/2003+C41':'1/14/03',
							'110/20/03':'11/20/03',
							'1/12003':'1/12/03',	#could also be 1/1/03 but after discussing with glenda and look around the table, 1/12/03 is more likely.
							'10//24/03':'10/24/03',
							'long ago':'NA'}
		from pymodule.roman import fromRoman
		for row in rows:
			experiment_id, accession_id, replicate, reading, measure = row
			if reading in reading_error_dict:	#correct the typo
				reading = reading_error_dict[reading]
			if reading!='NA' and reading!='N' and reading!='' and reading!=None:
				if experiment_id not in experiment_id2accession_id2reading_ls:
					experiment_id2accession_id2reading_ls[experiment_id] = {}
				if accession_id not in experiment_id2accession_id2reading_ls[experiment_id]:
					experiment_id2accession_id2reading_ls[experiment_id][accession_id] = {}
				try:
					if experiment_id==3 and reading[-2:]=='99':	#wrong year input
						reading = reading[:-2]+'03'
					if experiment_id==4 and reading[-2:]=='00':	#wrong year input
						reading = reading[:-2]+'02'
					if reading!='DNF':
						time_tuple = time.strptime(reading, '%m/%d/%y')	#transform it into a time tuple
					else:
						time_tuple = 'DNF'
				except:
					print "reading:",reading
					traceback.print_exc()
					print sys.exc_info()
					sys.exit(2)
				replicate = fromRoman(replicate)
				if replicate not in experiment_id2accession_id2reading_ls[experiment_id][accession_id]:
					experiment_id2accession_id2reading_ls[experiment_id][accession_id][replicate] = [None, None]	#1st is germination date, 2nd is first flower open
				if measure=='first flower open':
					experiment_id2accession_id2reading_ls[experiment_id][accession_id][replicate][1] = time_tuple
				elif measure=='germination date':
					experiment_id2accession_id2reading_ls[experiment_id][accession_id][replicate][0] = time_tuple
		sys.stderr.write("Done.\n")
		return experiment_id2accession_id2reading_ls
	
	def get_experiment_id2accession_id2FT(self, experiment_id2data, experiment_id2accession_id2reading_ls):
		"""
		2008-04-16
			germination date from experiment_id2data is not used anymore. experiment_id2accession_id2reading_ls contains germination date as well.
		2008-03-01
			move the average/stdev operation to output_experiment_id2accession_id2FT()
		2008-02-20
		"""
		sys.stderr.write("Getting experiment_id2accession_id2FT ...\n")
		experiment_id2accession_id2FT = {}
		for experiment_id, accession_id2reading_ls in experiment_id2accession_id2reading_ls.iteritems():
			description, time_germination = experiment_id2data[experiment_id]
			experiment_id2accession_id2FT[experiment_id] = {}
			for accession_id, replicate2reading_ls in accession_id2reading_ls.iteritems():
				FT_rep_ls = []
				for replicate, reading in replicate2reading_ls.iteritems():
					if reading[1]!=None and reading[0]!=None and reading[1]!='DNF':
						FT = (time.mktime(reading[1])-time.mktime(reading[0]))/(3600.0*24)	#counted as days
					elif reading[1]=='DNF':
						FT = 200
					else:
						continue
					if FT<0:
						warnings.warn("Warning: experiment_id=%s, accession_id=%s, FT is negative: %s, reading is %s, time_germination is %s.\n"%\
										(experiment_id, accession_id, FT, reading, time_germination))
					FT_rep_ls.append((FT, replicate))
				if len(FT_rep_ls)>0:
					experiment_id2accession_id2FT[experiment_id][accession_id] = FT_rep_ls
		sys.stderr.write("Done.\n")
		return experiment_id2accession_id2FT
	
	def submit2db(self, curs, experiment_id2accession_id2FT, experiment_id2data, method_table, phenotype_table, phenotype_avg_table):
		"""
		2008-04-20
			check if a method is already in method_table before insertion.
		2008-03-01
			submit to method_table and phenotype_table
			... need the accession_id2ecotype_id ...
		"""
		sys.stderr.write("Submitting experiment_id2data to %s ... "%method_table)
		no_of_methods_submitted = 0
		for experiment_id, data in experiment_id2data.iteritems():
			curs.execute("select id, short_name from %s where id=%s and short_name='%s'"%(method_table, experiment_id, data[0]))
			rows = curs.fetchall()
			if not rows:	#only insert if the method_table doesn't have these data.
				curs.execute("insert into %s(id, short_name) values (%s, '%s')"%(method_table, experiment_id, data[0]))
				no_of_methods_submitted += 1
		sys.stderr.write("%s methods inserted. Done.\n"%(no_of_methods_submitted))
		
		sys.stderr.write("Submitting experiment_id2accession_id2FT to %s and %s ... "%(phenotype_table, phenotype_avg_table))
		from variation.src.common import map_accession_id2ecotype_id
		accession_id2ecotype_id = map_accession_id2ecotype_id(curs)
		for expt_id in experiment_id2accession_id2FT:
			for accession_id in experiment_id2accession_id2FT[expt_id]:
				FT_rep_ls = experiment_id2accession_id2FT[expt_id][accession_id]
				ecotype_id = accession_id2ecotype_id[accession_id]
				for FT, replicate in FT_rep_ls:
					curs.execute("insert into %s(ecotype_id, value, replicate, method_id) values (%s, %s, %s, %s)"%\
								(phenotype_table, ecotype_id, FT, replicate, expt_id))
				
				FT_ls = [row[0] for row in experiment_id2accession_id2FT[expt_id][accession_id]]
				avg_FT = numpy.average(FT_ls)
				if len(FT_ls)>1:
					std_FT = numpy.std(FT_ls)
				else:
					std_FT = 'NULL'	#for mySQL db submission
				curs.execute("insert into %s(ecotype_id, value, stdev, sample_size, method_id) values (%s, %s, %s, %s, %s)"%\
							(phenotype_avg_table, ecotype_id, avg_FT, std_FT, len(FT_ls), expt_id))
		sys.stderr.write("Done.\n")
	
	def output_experiment_id2accession_id2FT(self, experiment_id2accession_id2FT, experiment_id2data, output_fname):
		"""
		2008-03-01
			do the average/stdev operation here.
		2008-02-20
		2008-02-25
			stdev and sample size become standalone columns
		"""
		sys.stderr.write("outputting experiment_id2accession_id2FT ...")
		writer = csv.writer(open(output_fname, 'w'), delimiter='\t')
		expt_id_ls = experiment_id2data.keys()
		expt_id_ls.sort()
		accession_id_ls = experiment_id2accession_id2FT[expt_id_ls[0]].keys()
		accession_id_ls.sort()
		header = ['accession id']
		for expt_id in expt_id_ls:
			header.append('%s %s'%(expt_id, experiment_id2data[expt_id][0]))
			header.append('%s %s (stdev)'%(expt_id, experiment_id2data[expt_id][0]))
			header.append('%s %s (sample size)'%(expt_id, experiment_id2data[expt_id][0]))
		writer.writerow(header)
		matrix = []
		for accession_id in accession_id_ls:
			data_row = [accession_id]
			for expt_id in expt_id_ls:
				if accession_id in experiment_id2accession_id2FT[expt_id]:
					FT_ls = [row[0] for row in experiment_id2accession_id2FT[expt_id][accession_id]]
					avg_FT = numpy.average(FT_ls)
					if len(FT_ls)>1:
						std_FT = numpy.std(FT_ls)
					else:
						std_FT = 'NA'
					data_row += [avg_FT, std_FT, len(FT_ls)]
				else:
					data_row += ['NA']*3
			matrix.append(data_row)
		for data_row in matrix:
			writer.writerow(data_row)
		del writer
		sys.stderr.write("Done.\n")
	
	def run(self):
		if self.debug:
			import pdb
			pdb.set_trace()
		import MySQLdb
		conn = MySQLdb.connect(db=self.dbname, host=self.hostname, user = self.user, passwd = self.passwd)
		curs = conn.cursor()
		experiment_id2data = self.get_experiment_id2data(curs, self.experiment_table)
		experiment_id2accession_id2reading_ls = self.get_experiment_id2accession_id2reading_ls(curs, self.raw_phenotype_table)
		experiment_id2accession_id2FT = self.get_experiment_id2accession_id2FT(experiment_id2data, experiment_id2accession_id2reading_ls)
		if self.output_fname:
			self.output_experiment_id2accession_id2FT(experiment_id2accession_id2FT, experiment_id2data, self.output_fname)
		if self.commit:
			self.submit2db(curs, experiment_id2accession_id2FT, experiment_id2data, self.method_table, \
						self.phenotype_table, self.phenotype_avg_table)
			curs.execute("commit")