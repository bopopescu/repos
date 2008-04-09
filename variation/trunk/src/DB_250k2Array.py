"""
2008-02-26
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import csv, numpy, rpy
import traceback, gc
from pymodule import process_function_arguments

class probe:
	def __init__(self, probes_id, snps_id, xpos, ypos, allele, strand):
		self.xpos = int(xpos)
		self.ypos = int(ypos)
		self.probes_id = probes_id
		self.snps_id = snps_id
		self.allele = allele
		self.strand = strand

class probes_class:
	def __init__(self):
		self.probes_id2probes_info = {}
	
	def add_one_probe(self, probes_id, snps_id, xpos, ypos, allele, strand):
		if probes_id in self.probes_id2probes_info:
			sys.stderr.write("Error: probes_id %s already in probes_id2probes_info.\n"%(probes_id))
			sys.exit(3)
		probe_ins = probe(probes_id, snps_id, xpos, ypos, allele, strand)
		self.probes_id2probes_info[probes_id] = probe_ins
	
	def get_one_probe(self, probes_id):
		return self.probes_id2probes_info[probes_id]

class snp:
	def __init__(self, snps_id, snpid):
		self.snps_id = snps_id
		self.snpid = snpid
		self.probes_id_ls = [-1]*4	#probes_id of [sense1, sense2, antisense1, antisense2]
		self.allele2index = {}

class snps_class:
	def __init__(self):
		self.snps_id2snps_info = {}
		self.snps_id_ls = []
	
	def add_one_snp(self, snps_id, snpid):
		if snps_id in self.snps_id2snps_info:
			sys.stderr.write("Error: snps_id %s already in snps_id2snps_info.\n"%(snps_id))
			sys.exit(3)
		snp_ins = snp(snps_id, snpid)
		self.snps_id2snps_info[snps_id] = snp_ins
		self.snps_id_ls.append(snps_id)
	
	def add_one_allele2snp(self, snps_id, allele):
		if snps_id not in self.snps_id2snps_info:
			sys.stderr.write("snps_id: %s not in snps_id2snps_info yet. no allele added."%snps_id)
			return
		allele2index = self.snps_id2snps_info[snps_id].allele2index
		self.snps_id2snps_info[snps_id].allele2index[allele] = len(allele2index)

	def add_one_probes_id2snp(self, snps_id, probes_id, allele, strand):
		allele_index = self.snps_id2snps_info[snps_id].allele2index[allele]
		if strand=='sense':
			self.snps_id2snps_info[snps_id].probes_id_ls[allele_index] = probes_id
		elif strand=='antisense':
			self.snps_id2snps_info[snps_id].probes_id_ls[allele_index+2] = probes_id
	
	def get_one_snp(self, snps_id):
		return self.snps_id2snps_info[snps_id]

class DB_250k2Array:
	"""
	2008-02-26
		
	Argument list:
		-z ..., --hostname=...	the hostname, localhost(default)
		-d ..., --dbname=...	the database name, stock20071008(default)
		-k ..., --schema=...	which schema in the database, (IGNORE)
		-o ...,	output_dir*
		-a ...,	snps_table, 'stock_250k.snps'(default)
		-e ...,	probes_table, 'stock_250k.probes'(default)
		-g ...,	array_info_table, 'stock_250k.array_info'(default)
		-b,	toggle debug
		-r, toggle report
	Examples:
		main.py -y 3 -o /tmp/arrays/
	Description:
		output all .cel array files (according to array_info_table) as intensity matrices in output_dir
	
	"""
	def __init__(self, **keywords):
		"""
		2008-02-28
		"""
		argument_default_dict = {('hostname',1, ):'localhost',\
								('dbname',1, ):'stock20071008',\
								('schema',0, ):'',\
								('output_dir',1, ):None,\
								('snps_table',1, ):'stock_250k.snps',\
								('probes_table',1, ):'stock_250k.probes',\
								('array_info_table',1, ):'stock_250k.array_info',\
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
	
	def get_snps(self, curs, snps_table):
		"""
		"""
		sys.stderr.write("Getting snps ... ")
		snps = snps_class()
		curs.execute("select id, snpid, allele1, allele2 from %s order by chromosome, position"%snps_table)
		rows = curs.fetchall()
		for row in rows:
			snps_id, snpid, allele1, allele2 = row
			snps.add_one_snp(snps_id, snpid)
			snps.add_one_allele2snp(snps_id, allele1)
			snps.add_one_allele2snp(snps_id, allele2)
		del rows
		sys.stderr.write("Done.\n")
		return snps
	
	def get_probes(self, curs, probes_table, snps):
		"""
		"""
		sys.stderr.write("Getting probes ... ")
		probes = probes_class()
		curs.execute("select id, snps_id, xpos, ypos, allele, strand from %s where snps_id is not null"%(probes_table))
		rows = curs.fetchall()
		for row in rows:
			probes_id, snps_id, xpos, ypos, allele, strand = row
			probes.add_one_probe(probes_id, snps_id, xpos, ypos, allele, strand)
			snps.add_one_probes_id2snp(snps_id, probes_id, allele, strand)
		del rows
		sys.stderr.write("Done.\n")
		return probes
	
	def outputArray(self, curs, output_dir, array_info_table, snps, probes):
		"""
		2008-04-08
		"""
		sys.stderr.write("Outputting arrays ... \n")
		rpy.r.library('affy')
		array_size = None
		if not os.path.isdir(output_dir):
			os.makedirs(output_dir)
		curs.execute("select id, filename from %s"%(array_info_table))
		rows = curs.fetchall()
		for row in rows:
			array_id, filename = row
			sys.stderr.write("\t%s ... \n"%(filename))
			array = rpy.r.read_affybatch(filenames=filename)
			intensity_array = rpy.r.intensity(array)	#return a lengthX1 2-Dimensional array.
			intensity_array_size = len(intensity_array)
			if array_size == None:
				array_size = int(math.sqrt(intensity_array_size))	#assume it's square array
			
			output_fname = os.path.join(output_dir, '%s_array_intensity.tsv'%(array_id))
			writer = csv.writer(open(output_fname, 'w'), delimiter='\t')
			header = [ 'sense1', 'sense2', 'antisense1', 'antisense2']
			func = lambda x: '%s_%s'%(array_id, x)
			header = map(func, header)
			header = ['SNP_ID'] + header
			writer.writerow(header)
			for snps_id in snps.snps_id_ls:
				one_snp = snps.get_one_snp(snps_id)
				output_row = [one_snp.snpid]
				for probes_id in one_snp.probes_id_ls:
					one_probe = probes.get_one_probe(probes_id)
					intensity_array_index = array_size*(array_size - one_probe.xpos - 1) + one_probe.ypos
					output_row.append(intensity_array[intensity_array_index][0])
				writer.writerow(output_row)
		sys.stderr.write("Done.\n")
	
	def run(self):
		import MySQLdb
		conn = MySQLdb.connect(db=self.dbname, host=self.hostname)
		curs = conn.cursor()
		
		snps = self.get_snps(curs, self.snps_table)
		probes = self.get_probes(curs, self.probes_table, snps)
		self.outputArray(curs, self.output_dir, self.array_info_table, snps, probes)