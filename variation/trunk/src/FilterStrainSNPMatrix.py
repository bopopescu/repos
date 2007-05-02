#!/usr/bin/env python
"""
Usage: FilterStrainSNPMatrix.py [OPTIONS] -i INPUT_FILE -o OUTPUT_FILE

Option:
	-i ...,	input file
	-o ...,	output file
	-n ...,	row NA ratio cutoff, 0.4(default)
	-c ...,	column NA ratio cutoff, 0.4(default)
	-d,	need to do filtering
	-a,	use alphabet to represent nucleotide, not number
	-b, --debug	enable debug
	-r, --report	enable more progress-related output
	-h, --help	show this help

Examples:
	#filter out snps and strains with too many NAs and identity strains
	FilterStrainSNPMatrix.py -i justin_data.csv -o justin_data_filtered.csv -r -d
	
	#translate integer nucleotide into english letter (no filtering)
	./src/FilterStrainSNPMatrix.py -n 1.1 -c 1.1 -a -i data/justin_data_filtered.csv -o data/justin_data_filtered_for_yan.csv

Description:
	The input StrainSNP matrix is in integer format.
	Filter out strains with too many NAs, SNPs with too many NAs (after strains removed), identity strains
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64/annot/bin')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script/annot/bin')))
import getopt, csv, math
import Numeric as num
from sets import Set
from common import number2nt

class FilterStrainSNPMatrix:
	def __init__(self, input_fname=None, output_fname=None, row_cutoff=0.6, col_cutoff=0.6,\
		need_to_filter=0, nt_alphabet=0, debug=0, report=0):
		"""
		2007-02-27
		2007-04-27
			add need_to_filter
			add nt_alphabet
		"""
		self.input_fname = input_fname
		self.output_fname = output_fname
		self.row_cutoff = float(row_cutoff)
		self.col_cutoff = float(col_cutoff)
		self.need_to_filter = int(need_to_filter)
		self.nt_alphabet = int(nt_alphabet)
		self.debug = int(debug)
		self.report = int(report)
	
	def remove_rows_with_too_many_NAs(self, data_matrix, row_cutoff):
		sys.stderr.write("Removing rows with too many NAs...")
		no_of_rows, no_of_cols = data_matrix.shape
		rows_with_too_many_NAs_set = Set()
		strain_index2no_of_NAs = {}
		for i in range(no_of_rows):
			no_of_NAs = 0.0
			for j in range(no_of_cols):
				if data_matrix[i][j] == 0:
					no_of_NAs += 1
			NA_ratio = no_of_NAs/no_of_cols
			strain_index2no_of_NAs[i] = NA_ratio
			if NA_ratio >= row_cutoff:
				rows_with_too_many_NAs_set.add(i)
		if self.debug:
			print
			print 'rows_with_too_many_NAs_set'
			print rows_with_too_many_NAs_set
		sys.stderr.write("%s strains removed, done.\n"%len(rows_with_too_many_NAs_set))
		return rows_with_too_many_NAs_set, strain_index2no_of_NAs
	
	def remove_cols_with_too_many_NAs(self, data_matrix, col_cutoff, rows_with_too_many_NAs_set):
		sys.stderr.write("Removing columns with too many NAs...")
		no_of_rows, no_of_cols = data_matrix.shape
		cols_with_too_many_NAs_set = Set()
		total_rows_set = Set(range(no_of_rows))
		rows_to_be_checked = total_rows_set - rows_with_too_many_NAs_set
		for j in range(no_of_cols):
			no_of_NAs = 0.0
			for i in rows_to_be_checked:
				if data_matrix[i][j] == 0:
					no_of_NAs += 1
			NA_ratio = no_of_NAs/no_of_rows
			if NA_ratio >= col_cutoff:
				cols_with_too_many_NAs_set.add(j)
		if self.debug:
			print
			print 'cols_with_too_many_NAs_set'
			print cols_with_too_many_NAs_set
		sys.stderr.write("%s cols removed, done.\n"%(len(cols_with_too_many_NAs_set)))
		return cols_with_too_many_NAs_set
	
	def remove_identity_strains(self, data_matrix, rows_to_be_checked, cols_to_be_checked, strain_index2no_of_NAs):
		"""
		2007-04-16
			the similarity graph structure complicated the issue
			bug found by Chris Toomajian
			Now use the greedy graph algorithm to remove identity strains.
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
		dbSNP2data_instance = dbSNP2data()
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
	
	def read_data(self, input_fname):
		"""
		2007-03-06
			different from the one from SelectStrains.py is map(int, data_row)
		"""
		sys.stderr.write("Reading data ...")
		reader = csv.reader(open(input_fname), delimiter='\t')
		header = reader.next()
		data_matrix = []
		strain_acc_list = []
		category_list = []
		for row in reader:
			strain_acc_list.append(row[0])
			category_list.append(row[1])
			data_row = row[2:]
			data_row = map(int, data_row)
			data_matrix.append(data_row)
		del reader
		sys.stderr.write("Done.\n")
		return header, strain_acc_list, category_list, data_matrix
	
	def run(self):
		"""
		2007-02-27
		
		-read_data()
		-remove_rows_with_too_many_NAs()
		-remove_cols_with_too_many_NAs()
		-remove_identity_strains()
		-write_data_matrix()
		"""
		header, strain_acc_list, category_list, data_matrix = self.read_data(self.input_fname)
		data_matrix = num.array(data_matrix)
		if self.need_to_filter:
			rows_with_too_many_NAs_set, strain_index2no_of_NAs = self.remove_rows_with_too_many_NAs(data_matrix, self.row_cutoff)
			cols_with_too_many_NAs_set = self.remove_cols_with_too_many_NAs(data_matrix, col_cutoff, rows_with_too_many_NAs_set)
			
			no_of_rows, no_of_cols = data_matrix.shape
			total_rows_set = Set(range(no_of_rows))
			rows_to_be_checked = total_rows_set - rows_with_too_many_NAs_set
			total_cols_set = Set(range(no_of_cols))
			cols_to_be_checked = total_cols_set - cols_with_too_many_NAs_set
			identity_strains_to_be_removed = self.remove_identity_strains(data_matrix, rows_to_be_checked, cols_to_be_checked, strain_index2no_of_NAs)
		else:
			rows_with_too_many_NAs_set = Set()
			cols_with_too_many_NAs_set = Set()
			identity_strains_to_be_removed = Set()
		
		rows_to_be_tossed_out = rows_with_too_many_NAs_set | identity_strains_to_be_removed
		self.write_data_matrix(data_matrix, self.output_fname, header, strain_acc_list, category_list, rows_to_be_tossed_out, cols_with_too_many_NAs_set, self.nt_alphabet)


if __name__ == '__main__':
	if len(sys.argv) == 1:
		print __doc__
		sys.exit(2)
	
	long_options_list = ["debug", "report", "help"]
	try:
		opts, args = getopt.getopt(sys.argv[1:], "i:o:n:c:dabrh", long_options_list)
	except:
		print __doc__
		sys.exit(2)
	
	input_fname = None
	output_fname = None
	row_cutoff = 0.4
	col_cutoff = 0.4
	need_to_filter = 0
	debug = 0
	report = 0
	nt_alphabet = 0
	
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
			need_to_filter = 1
		elif opt in ("-a",):
			nt_alphabet = 1
		elif opt in ("-b", "--debug"):
			debug = 1
		elif opt in ("-r", "--report"):
			report = 1

	if input_fname and output_fname:
		instance = FilterStrainSNPMatrix(input_fname, output_fname, row_cutoff, col_cutoff,\
			need_to_filter, nt_alphabet, debug, report)
		instance.run()
	else:
		print __doc__
		sys.exit(2)