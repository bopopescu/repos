#!/usr/bin/env python
"""
Usage: FilterStrainSNPMatrix.py [OPTIONS] -i INPUT_FILE -o OUTPUT_FILE

Option:
	-i ...,	input file
	-o ...,	output file
	-n ...,	row NA ratio cutoff, 0.4(default)
	-c ...,	column NA ratio cutoff, 0.4(default)
	-d ...,	bits to toggle filtering, '111'(default)
	-a ...,	bits to toggle input/output StrainSNP matrix format, 0 is integer.
		1 is alphabet. 1st digit is for input. 2nd is for output. 00 (default)
	-b, --debug	enable debug
	-r, --report	enable more progress-related output
	-h, --help	show this help

Examples:
	#filter out snps and strains with too many NAs but not identity strains
	FilterStrainSNPMatrix.py -i stock20071008/data.tsv -o stock20071008/data_d110.tsv -d 110
	
	#translate integer nucleotide into english letter (no filtering)
	FilterStrainSNPMatrix.py -d 110 -n 1.1 -c 1.1 -a 01 -i data/justin_data_filtered.csv -o data/justin_data_filtered_for_yan.csv
	
	#remove all-NA rows & columns
	./src/FilterStrainSNPMatrix.py -i data/2010/data_2010_ecotype_id_y0002.tsv -o data/2010/data_2010_ecotype_id_y0002_n1c1d110.tsv -n 1 -c 1 -d 110 -r

Description:
	Filtering procedures:
	 1. strains with too many NAs (-n specifies the cutoff)
	 2. SNPs with too many NAs (-c specifies the cutoff)
	 3. identity strains
	
	NA could be 0 (NA, undecided in calling) or -2 (not touched by the procedure).
	
	Input format is strain X snp. delimiter (either tab or comma) is automatically detected.
	
	Output format is strain X snp. same delimiter as input would be used.
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64/')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script/')))
import getopt, csv, math
import Numeric as num
from sets import Set
from variation.src.common import number2nt, nt2number
from pymodule import dict_map, PassingData, figureOutDelimiter, write_data_matrix, read_data

class FilterStrainSNPMatrix(object):
	def __init__(self, input_fname=None, output_fname=None, row_cutoff=0.6, col_cutoff=0.6,\
		filtering_bits='111', nt_alphabet_bits='00', debug=0, report=0):
		"""
		2007-02-27
		2007-04-27
			add need_to_filter
			add nt_alphabet
		2007-05-14
			use nt_alphabet_bits to replace nt_alphabet and input_alphabet
		2007-09-13
			change need_to_filter to filtering_bits
		"""
		self.input_fname = input_fname
		self.output_fname = output_fname
		self.row_cutoff = float(row_cutoff)
		self.col_cutoff = float(col_cutoff)
		self.filtering_bits = filtering_bits
		self.nt_alphabet_bits = nt_alphabet_bits
		self.debug = int(debug)
		self.report = int(report)
	
	def remove_rows_with_too_many_NAs(cls, data_matrix, row_cutoff, cols_with_too_many_NAs_set=None, NA_set=Set([0, -2]), debug=0, is_cutoff_max=0):
		"""
		2008-05-19
			if is_cutoff_max=1, anything > row_cutoff is deemed as having too many NAs
			if is_cutoff_max=0 (cutoff is minimum), anything >= row_cutoff is deemed as having too many NAs
		2008-05-12
			made more robust
			add cols_with_too_many_NAs_set
			add NA_set
		2008-05-08
			become classmethod
		"""
		sys.stderr.write("Removing rows with NA rate >= %s ..."%(row_cutoff))
		no_of_rows, no_of_cols = data_matrix.shape
		rows_with_too_many_NAs_set = Set()
		total_cols_set = Set(range(no_of_cols))
		if cols_with_too_many_NAs_set:
			cols_to_be_checked = total_cols_set - cols_with_too_many_NAs_set
		else:
			cols_to_be_checked = total_cols_set
		row_index2no_of_NAs = {}
		for i in range(no_of_rows):
			no_of_NAs = 0.0
			for j in cols_to_be_checked:
				if data_matrix[i][j] in NA_set:
					no_of_NAs += 1
			if no_of_cols!=0:
				NA_ratio = no_of_NAs/no_of_cols
			else:
				NA_ratio = 0.0
			row_index2no_of_NAs[i] = NA_ratio
			if is_cutoff_max:
				if NA_ratio > row_cutoff:
					rows_with_too_many_NAs_set.add(i)
			else:
				if NA_ratio >= row_cutoff:
					rows_with_too_many_NAs_set.add(i)
		if debug:
			print
			print 'rows_with_too_many_NAs_set'
			print rows_with_too_many_NAs_set
		passingdata = PassingData(rows_with_too_many_NAs_set=rows_with_too_many_NAs_set)
		passingdata.row_index2no_of_NAs = row_index2no_of_NAs
		sys.stderr.write("%s strains removed, done.\n"%len(rows_with_too_many_NAs_set))
		return passingdata
	
	remove_rows_with_too_many_NAs = classmethod(remove_rows_with_too_many_NAs)
	
	def remove_cols_with_too_many_NAs(cls, data_matrix, col_cutoff, rows_with_too_many_NAs_set=None, NA_set=Set([0, -2]), debug=0, is_cutoff_max=0):
		"""
		2008-05-19
			if is_cutoff_max=1, anything > row_cutoff is deemed as having too many NAs
			if is_cutoff_max=0 (cutoff is minimum), anything >= row_cutoff is deemed as having too many NAs
		2008-05-12
			classmethod
			more robust, standardize
			add NA_set
		"""
		sys.stderr.write("Removing columns with NA rate>=%s ..."%col_cutoff)
		no_of_rows, no_of_cols = data_matrix.shape
		cols_with_too_many_NAs_set = Set()
		total_rows_set = Set(range(no_of_rows))
		if rows_with_too_many_NAs_set:
			rows_to_be_checked = total_rows_set - rows_with_too_many_NAs_set
		else:
			rows_to_be_checked = total_rows_set
		
		col_index2no_of_NAs = {}
		
		for j in range(no_of_cols):
			no_of_NAs = 0.0
			for i in rows_to_be_checked:
				if data_matrix[i][j] in NA_set:
					no_of_NAs += 1
			if no_of_rows!=0:
				NA_ratio = no_of_NAs/no_of_rows
			else:
				NA_ratio = 0.0
			col_index2no_of_NAs[j] = NA_ratio
			if is_cutoff_max:
				if NA_ratio > col_cutoff:
					cols_with_too_many_NAs_set.add(j)
			else:
				if NA_ratio >= col_cutoff:
					cols_with_too_many_NAs_set.add(j)
		if debug:
			print
			print 'cols_with_too_many_NAs_set'
			print cols_with_too_many_NAs_set
		passingdata = PassingData(cols_with_too_many_NAs_set=cols_with_too_many_NAs_set, col_index2no_of_NAs=col_index2no_of_NAs)
		sys.stderr.write("%s cols removed, done.\n"%(len(cols_with_too_many_NAs_set)))
		return passingdata
	
	remove_cols_with_too_many_NAs = classmethod(remove_cols_with_too_many_NAs)
	
	def remove_identity_strains(self, data_matrix, rows_to_be_checked, cols_to_be_checked):
		"""
		2009-2-18
			class "dbSNP2data" has a few non-null arguments. feed it during initialization
		2007-04-16
			the similarity graph structure complicated the issue
			bug found by Chris Toomajian
			Now use the greedy graph algorithm to remove identity strains.
		2007-09-13
			remove parameter strain_index2no_of_NAs
		"""
		sys.stderr.write("Searching for identity strains ...")
		rows_to_be_checked_ls = list(rows_to_be_checked)
		rows_to_be_checked_ls.sort()	#from small to big
		if self.debug:
			import pdb
			pdb.set_trace()
		no_of_total_cols_to_be_checked = len(cols_to_be_checked)
		identity_pair_ls = []	#2007-04-16
		for i in range(len(rows_to_be_checked_ls)):
			row1_index = rows_to_be_checked_ls[i]	#watch this
			for j in rows_to_be_checked_ls[i+1:]:
				no_of_same_cols = 0
				for k in cols_to_be_checked:
					if data_matrix[row1_index][k] == data_matrix[j][k] or data_matrix[row1_index][k]==0 or data_matrix[j][k]==0:
						no_of_same_cols += 1
				if no_of_same_cols == no_of_total_cols_to_be_checked:
					identity_pair_ls.append([row1_index, j])
		if self.debug:
			import pdb
			pdb.set_trace()
		sys.stderr.write("done.\n")
		sys.stderr.write("Removing identity strains ...")
		import networkx as nx
		g = nx.Graph()
		g.add_edges_from(identity_pair_ls)
		from dbSNP2data import dbSNP2data
		dbSNP2data_instance = dbSNP2data(user='yh', passwd='secret', output_fname='/tmp/nothing')	#dbSNP2data has a few non-null arguments.
		vertex_list_to_be_deleted = dbSNP2data_instance.find_smallest_vertex_set_to_remove_all_edges(g)
		identity_strains_to_be_removed = Set(vertex_list_to_be_deleted)
		"""
		#2007-04-16 useless
		identity_strains_to_be_removed = Set()
		for src, tg_list in src2tg_list.iteritems():
			strain_with_least_NA = src
			least_no_of_NAs = strain_index2no_of_NAs[src]
			identity_strains_to_be_removed.add(src)	#add in src
			for tg in tg_list:
				identity_strains_to_be_removed.add(tg)	#add in tg
				if strain_index2no_of_NAs[tg] < least_no_of_NAs:
					strain_with_least_NA = tg
					least_no_of_NAs = strain_index2no_of_NAs[tg]
			identity_strains_to_be_removed.remove(strain_with_least_NA)	#remove the one with least NAs
		"""
		if self.debug:
			print
			print 'identity_strains_to_be_removed'
			print identity_strains_to_be_removed
		sys.stderr.write("%s identity strains, done.\n"%(len(identity_strains_to_be_removed)))
		return identity_strains_to_be_removed
	
	def write_data_matrix(self, data_matrix, output_fname, header, strain_acc_list, category_list, rows_to_be_tossed_out=Set(), cols_to_be_tossed_out=Set(), nt_alphabet=0):
		"""
		2008-02-06
			transform the 2D list into array if data_matrix is 2D list.
		2007-03-06
		2007-04-27
			add nt_alphabet
		"""
		sys.stderr.write("Writing data_matrix ...")
		writer = csv.writer(open(output_fname, 'w'), delimiter='\t')
		
		new_header = [header[0], header[1]]
		for i in range(2, len(header)):
			if i-2 not in cols_to_be_tossed_out:
				new_header.append(header[i])
		writer.writerow(new_header)
		
		if type(data_matrix)==list:	#2008-02-06 transform the 2D list into array
			data_matrix = num.array(data_matrix)
		no_of_rows, no_of_cols = data_matrix.shape
		for i in range(no_of_rows):
			if i not in rows_to_be_tossed_out:
				new_row = [strain_acc_list[i], category_list[i]]
				for j in range(no_of_cols):
					if j not in cols_to_be_tossed_out:
						if nt_alphabet:
							new_row.append(number2nt[data_matrix[i][j]])
						else:
							new_row.append(data_matrix[i][j])
				writer.writerow(new_row)
		del writer
		sys.stderr.write("Done.\n")
	
	def read_data(cls, input_fname, input_alphabet=0, turn_into_integer=1, double_header=0, delimiter='\t'):
		"""
		2008-05-18
			DEPRECATED. moved to pymodule.SNP
		2008-05-12
			add delimiter
		2008-05-07
			add option double_header
		2007-03-06
			different from the one from SelectStrains.py is map(int, data_row)
		2007-05-14
			add input_alphabet
		2007-10-09
			add turn_into_integer
		"""
		sys.stderr.write("Reading data ...")
		reader = csv.reader(open(input_fname), delimiter=delimiter)
		header = reader.next()
		if double_header:
			header = [header, reader.next()]
		data_matrix = []
		strain_acc_list = []
		category_list = []
		for row in reader:
			strain_acc_list.append(row[0])
			category_list.append(row[1])
			data_row = row[2:]
			no_of_snps = len(data_row)
			if input_alphabet:
				data_row = dict_map(nt2number, data_row)
				if no_of_snps!=len(data_row):
					print row
			else:
				if turn_into_integer:
					data_row = map(int, data_row)
			data_matrix.append(data_row)
		del reader
		sys.stderr.write("Done.\n")
		return header, strain_acc_list, category_list, data_matrix
	
	read_data = classmethod(read_data)
	
	def run(self):
		"""
		2007-02-27
		2007-09-14
			filtering_bits
		-read_data()
		-remove_rows_with_too_many_NAs()
		-remove_cols_with_too_many_NAs()
		-remove_identity_strains()
		-write_data_matrix()
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		delimiter = figureOutDelimiter(self.input_fname, report=self.report)
		header, strain_acc_list, category_list, data_matrix = read_data(self.input_fname, int(self.nt_alphabet_bits[0]), delimiter=delimiter)
		data_matrix = num.array(data_matrix)
		if self.filtering_bits[0]=='1':
			remove_rows_data = self.remove_rows_with_too_many_NAs(data_matrix, self.row_cutoff)
			rows_with_too_many_NAs_set = remove_rows_data.rows_with_too_many_NAs_set
			strain_index2no_of_NAs = remove_rows_data.row_index2no_of_NAs
		else:
			rows_with_too_many_NAs_set = Set()
		if self.filtering_bits[1]=='1':
			remove_cols_data = self.remove_cols_with_too_many_NAs(data_matrix, col_cutoff, rows_with_too_many_NAs_set)
			cols_with_too_many_NAs_set = remove_cols_data.cols_with_too_many_NAs_set			
		else:
			cols_with_too_many_NAs_set = Set()
		if self.filtering_bits[2]=='1':
			no_of_rows, no_of_cols = data_matrix.shape
			total_rows_set = Set(range(no_of_rows))
			rows_to_be_checked = total_rows_set - rows_with_too_many_NAs_set
			total_cols_set = Set(range(no_of_cols))
			cols_to_be_checked = total_cols_set - cols_with_too_many_NAs_set
			identity_strains_to_be_removed = self.remove_identity_strains(data_matrix, rows_to_be_checked, cols_to_be_checked)
		else:
			identity_strains_to_be_removed = Set()
		rows_to_be_tossed_out = rows_with_too_many_NAs_set | identity_strains_to_be_removed
		#self.write_data_matrix(data_matrix, self.output_fname, header, strain_acc_list, category_list, rows_to_be_tossed_out, cols_with_too_many_NAs_set, int(self.nt_alphabet_bits[1]))
		write_data_matrix(data_matrix, self.output_fname, header, strain_acc_list, category_list, rows_to_be_tossed_out, cols_with_too_many_NAs_set, nt_alphabet=int(self.nt_alphabet_bits[1]), delimiter=delimiter)

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print __doc__
		sys.exit(2)
	
	long_options_list = ["debug", "report", "help"]
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:o:n:c:d:a:brh", long_options_list)
	except:
		print __doc__
		sys.exit(2)
	
	input_fname = None
	output_fname = None
	row_cutoff = 0.4
	col_cutoff = 0.4
	filtering_bits = '111'
	nt_alphabet_bits = '00'
	debug = 0
	report = 0
	
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print __doc__
			sys.exit(2)
		elif opt in ("-i",):
			input_fname = arg
		elif opt in ("-o",):
			output_fname = arg
		elif opt in ("-n",):
			row_cutoff = float(arg)
		elif opt in ("-c",):
			col_cutoff = float(arg)
		elif opt in ("-d",):
			filtering_bits = arg
		elif opt in ("-a",):
			nt_alphabet_bits = arg
		elif opt in ("-b", "--debug"):
			debug = 1
		elif opt in ("-r", "--report"):
			report = 1

	if input_fname and output_fname:
		instance = FilterStrainSNPMatrix(input_fname, output_fname, row_cutoff, col_cutoff,\
			filtering_bits, nt_alphabet_bits, debug, report)
		instance.run()
	else:
		print __doc__
		sys.exit(2)