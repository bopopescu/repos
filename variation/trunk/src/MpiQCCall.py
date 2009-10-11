#!/usr/bin/env mpipython
"""

Examples:
	# parallel run on hpc-cmb
	mpiexec MpiQCCall.py -i /mnt/nfs/NPUTE_data/input/250k_method_3.csv -p /mnt/nfs/NPUTE_data/input/perlgen.csv -f /mnt/nfs/NPUTE_data/input/2010_149_384.csv -o /tmp/param_qc.csv
		
	# test parallel run on desktop
	mpirun -np 5 -machinefile  /tmp/hostfile /usr/bin/mpipython  ~/script/variation/src/MpiQCCall.py -i /mnt/nfs/NPUTE_data/input/250K_m3_70_n1000.csv -y 0.85 -p /mnt/nfs/NPUTE_data/input/perlgen.csv -f /mnt/nfs/NPUTE_data/input/2010_149_384.csv -o /tmp/param_qc -n 20 -v 0.3 -a 0.4 -w 0.2
	
	# run on a single node and output the matrix to output_fname.
	python ~/script/variation/src/MpiQCCall.py -i ~/panfs/NPUTE_data/input/250K_m3_85.csv -y 0.85 -p ~/panfs/NPUTE_data/input/perlgen.csv \
	-f ~/panfs/NPUTE_data/input/2010_149_384_v2.csv -u ~/panfs/NPUTE_data/matrix_output \
	-x 0.12 -a 1 -v 0.55 -w 0.3 -n 30
	
	# parallel run on hpc-cmb and output data (both before & after imputation into output_dir)
	mpiexec ~/script/variation/src/MpiQCCall.py -i ~/panfs/NPUTE_data/input/250K_m3_85.csv -y 0.85 -p ~/panfs/NPUTE_data/input/perlgen.csv \
	-f ~/panfs/NPUTE_data/input/2010_149_384_v2.csv -o ~/panfs/NPUTE_data/QC_output/250K_m3_85_vs_2010_149_384_v2_QC_x0.12_a1_v0.55_w0.3_n30 \
	-x 0.12 -a 1 -v 0.55 -w 0.3 -n 30 -u ~/panfs/NPUTE_data/matrix_output
	
	# test parallel run on desktop, using Strain X SNP format
	mpirun -np 3 -machinefile  /tmp/hostfile /usr/bin/mpipython  ~/script/variation/src/MpiQCCall.py -i /mnt/nfs/NPUTE_data/input/250K_m3_70_n1000.tsv -y 0.70 -p /mnt/nfs/NPUTE_data/input/perlegen.tsv -f /mnt/nfs/NPUTE_data/input/2010_149_384_v3_narrowed_by_250k_l3.tsv -o /tmp/param_qc_2008_05_19  -x 0.12 -a 1 -v 0.55 -w 0.3 -n 30 -u /tmp/out2
	
Description:
	a parallel program to do QC on genotype calls before/after imputation under various parameter settings.
	
	Heterozygous calls in QC datasets are ignored since 250k dataset doesn't include hets.
	
	In serial mode (interpreter is python or only one processor is available),
		it takes the first parameter setting and run thru on a single node and output the matrix to
		output_fname. The output_fname is not regarded as a prefix for two stat filenames.
"""
import sys, os, math
#bit_number = math.log(sys.maxint)/math.log(2)
#if bit_number>40:       #64bit
sys.path.insert(0, os.path.expanduser('~/lib/python'))
sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))
import getopt, csv, math, traceback
import Numeric, cPickle
from Scientific import MPI
from pymodule.MPIwrapper import mpi_synchronize, MPIwrapper
#from FilterStrainSNPMatrix import FilterStrainSNPMatrix	#for read_data()
from common import nt2number,number2nt, RawSnpsData_ls2SNPData
import dataParsers, FilterAccessions, FilterSnps, MergeSnpsData
from variation.genotyping.NPUTE.SNPData import SNPData as NPUTESNPData
from variation.genotyping.NPUTE.NPUTE import imputeData, NPUTE
from pymodule import PassingData, importNumericArray, SNPData, TwoSNPData
import copy
import snpsdata

num = importNumericArray()

class MpiQCCall(MPIwrapper):
	__doc__ = __doc__
	option_default_dict = {('input_fname', 1, ): ['', 'i', 1, '250k call file'],\
							('callProbFile', 0, ): ['', 't', 1, '250k probability file'],\
							('fname_2010_149_384', 1, ): ['', 'f', 1, ''],\
							('fname_perlegen', 1, ): ['', 'p', 1, ''],\
							('output_fname', 0, ): [None, 'o', 1, 'final stat output filename prefix. two files would be generated. 1st file is strain/snp detailed data. \
									2nd file is average strain/snp data.'],\
							('output_dir', 1, ): [None, 'u', 1, 'if given, output matrix before and after imputation into a directory'],\
							('min_call_probability', 1, float): [None, 'y', 1, 'the minimum probability used in the input_fname for a call to be non-NA.', ],\
							('max_call_mismatch_rate_ls', 1, ): ["0.05,0.1,0.15,0.20,0.25,0.3", 'x', 1, 'maximum mismatch rate of an array call_info entry. used to exclude bad arrays.'],\
							('max_call_NA_rate_ls', 1, ): ["0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8", 'a', 1, 'maximum NA rate of an array call_info entry. used to exclude bad arrays.'],\
							('max_snp_mismatch_rate_ls', 1, ): ["0.05,0.1,0.15,0.2,0.25,0.3", 'w', 1, 'maximum snp error rate, used to exclude bad SNPs', ],\
							('max_snp_NA_rate_ls', 1, ): ["0.1,0.2,0.3,0.4,0.5,0.6,0.7", 'v', 1, 'maximum snp NA rate, used to exclude SNPs with too many NAs', ],\
							('npute_window_size_ls', 1): ["10,30,50", 'n', 1, 'NPUTE window size',],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	def __init__(self, **keywords):
		"""
		2008-05-08
		"""
		from pymodule import ProcessOptions
		self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
	
	def generate_parameters(self, parameter_names, parameter_depth=2):
		"""
		2008-05-19
			min_call_probability = self.min_call_probability
		2008-05-11
			put NA rate into passing parameters as well. too much memory consumption on each computing node
		"""
		sys.stderr.write( "Generating parameter settings ...")
		param_d = PassingData()
		for parameter_name in parameter_names:
			parameter_value = getattr(self, parameter_name)
			parameter_value = parameter_value.split(',')
			parameter_value = map(float, parameter_value)
			setattr(self, parameter_name, parameter_value)
		
		"""
		#2008-05-19 commented out. use self.min_call_probability
		#figure out call probability from input_fname
		import re
		call_prob_pattern = re.compile(r'_(\d+)\.csv')
		call_prob_p_result = call_prob_pattern.search(self.input_fname)
		if call_prob_p_result:
			min_call_probability = float(call_prob_p_result.groups()[0])
		else:
			min_call_probability = -1
		"""
		min_call_probability = self.min_call_probability
		
		#only 1st 4, last 2 passed to computing node
		parameters = []
		for max_call_mismatch_rate in getattr(self, parameter_names[0]):
			for max_call_NA_rate in getattr(self, parameter_names[1]):
				for max_snp_mismatch_rate in getattr(self, parameter_names[2]):
					for max_snp_NA_rate in getattr(self, parameter_names[3]):
						for npute_window_size in getattr(self, parameter_names[4]):
							parameters.append([min_call_probability, max_call_mismatch_rate, max_call_NA_rate, \
										max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size])
		
		param_d.parameters = parameters
		param_d.max_snp_NA_rate_ls = self.max_snp_NA_rate_ls
		param_d.npute_window_size_ls = self.npute_window_size_ls
		sys.stderr.write(" %s parameter settings to process. Done.\n"%len(parameters))
		return param_d
	
	def input_handler(self, parameter_list, message_size, report=0):
		"""
		"""
		if report:
			sys.stderr.write("Fetching stuff...\n")
		param_d = parameter_list[0]
		if param_d.index<len(param_d.parameters):
			data_to_return = param_d.parameters[param_d.index]
			param_d.index += 1
		else:
			data_to_return = None
		if report:
			sys.stderr.write("Fetching done.\n")
		return data_to_return
	
	def doFilter(self, snpData, snpData_qc_strain, snpData_qc_snp, min_call_probability, max_call_mismatch_rate, max_call_NA_rate,\
				max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size , output_dir=None):
		"""
		2009-10-11
			replace imputeData() with NPUTE.samplingImpute(..., no_of_accessions_per_sampling=300, coverage=3) to avoid memory blowup. 
		2008-12-22
			replace '=' and ',' with '_' in the output filename
		2008-05-19
			matrix_ls has to be of length >0 before concatenation
		2008-05-19
			use SNPData structure
		2008-05-18
			add onlyCommon=True to FilterAccessions.filterByError()
		2008-05-17
			add argument output_dir. if it's available, output data matrix before and after imputation
		2008-05-12
			add
			qcdata.no_of_accessions_filtered_by_mismatch
			qcdata.no_of_accessions_filtered_by_na
			qcdata.no_of_snps_filtered_by_mismatch
			qcdata.no_of_snps_filtered_by_na
			qcdata.no_of_monomorphic_snps_removed
		
		2008-05-11
			split up from computing_node_handler
		"""
		qcdata = PassingData()
		twoSNPData = TwoSNPData(SNPData1=snpData, SNPData2=snpData_qc_strain, \
						row_matching_by_which_value=0, debug=self.debug)
		row_id2NA_mismatch_rate = twoSNPData.cmp_row_wise()
		del twoSNPData
		
		newSnpData = SNPData.removeRowsByMismatchRate(snpData, row_id2NA_mismatch_rate, max_call_mismatch_rate)
		qcdata.no_of_accessions_filtered_by_mismatch = newSnpData.no_of_rows_filtered_by_mismatch
		
		newSnpData = SNPData.removeRowsByNARate(newSnpData, max_call_NA_rate)
		qcdata.no_of_accessions_filtered_by_na = newSnpData.no_of_rows_filtered_by_na
		
		twoSNPData = TwoSNPData(SNPData1=newSnpData, SNPData2=snpData_qc_snp, \
						row_matching_by_which_value=0, debug=self.debug)
		col_id2NA_mismatch_rate = twoSNPData.cmp_col_wise()
		del twoSNPData
		newSnpData = SNPData.removeColsByMismatchRate(newSnpData, col_id2NA_mismatch_rate, max_snp_mismatch_rate)
		qcdata.no_of_snps_filtered_by_mismatch = newSnpData.no_of_cols_filtered_by_mismatch
		
		newSnpData = SNPData.removeColsByNARate(newSnpData, max_snp_NA_rate)
		qcdata.no_of_snps_filtered_by_na = newSnpData.no_of_cols_filtered_by_na
		
		twoSNPData = TwoSNPData(SNPData1=newSnpData, SNPData2=snpData_qc_snp, \
						row_matching_by_which_value=0, debug=self.debug)
		newSnpData = twoSNPData.mergeTwoSNPData(priority=2)
		del twoSNPData
		#MergeSnpsData.merge(snpsd_250k_tmp, snpsd_ls_qc_snp, unionType=0, priority=2)
		
		newSnpData = SNPData.removeMonomorphicCols(newSnpData)
		qcdata.no_of_monomorphic_snps_removed = newSnpData.no_of_monomorphic_cols
		
		#FilterSnps.filterMonomorphic(snpsd_250k_tmp)
		
		if output_dir:
			#output data here
			if not os.path.isdir(output_dir):
				os.makedirs(output_dir)
			output_fname_prefix_ls = ['min_oligo_call_probability_%s'%min_call_probability,\
									'max_array_mismatch_rate_%s'%max_call_mismatch_rate,\
									'max_array_NA_rate_%s'%max_call_NA_rate,\
									'max_snp_mismatch_rate_%s'%max_snp_mismatch_rate,\
									'max_snp_NA_rate_%s'%max_snp_NA_rate,\
									'npute_window_size_%s'%npute_window_size]
			output_fname = os.path.join(output_dir, '_'.join(output_fname_prefix_ls + ['before_imputation.tsv']))
			newSnpData.tofile(output_fname)
			#chromosomes = [snpsd_250k_tmp[i].chromosome for i in range(len(snpsd_250k_tmp))]
			#snpsdata.writeRawSnpsDatasToFile(output_fname, snpsd_250k_tmp, chromosomes=chromosomes, deliminator=',', withArrayIds = True)
		
		"""
		qcdata.no_of_snps_filtered_by_mismatch = 0
		qcdata.no_of_snps_filtered_by_na = 0
		qcdata.no_of_monomorphic_snps_removed = 0
		for snpsd in snpsd_250k_tmp:
			qcdata.no_of_snps_filtered_by_mismatch += snpsd.no_of_snps_filtered_by_mismatch
			qcdata.no_of_snps_filtered_by_na += snpsd.no_of_snps_filtered_by_na
			qcdata.no_of_monomorphic_snps_removed += snpsd.no_of_monomorphic_snps_removed
		"""
		
		#snpData0 = RawSnpsData_ls2SNPData(snpsd_250k_tmp)
		
		twoSNPData0 = TwoSNPData(SNPData1=newSnpData, SNPData2=snpData_qc_strain, \
						row_matching_by_which_value=0)
		row_id2NA_mismatch_rate0 = twoSNPData0.cmp_row_wise()
		col_id2NA_mismatch_rate0 = twoSNPData0.cmp_col_wise()
		del twoSNPData0
		
		result = []
		#for npute_window_size in npute_window_size_ls:
		#snpsd_250k_tmp_1 = copy.deepcopy(snpsd_250k_tmp)	#deepcopy, otherwise snpsd_250k_tmp_1[i].snps = [] would clear snpsd_250k_tmp up as well
		if len(newSnpData.row_id_ls)>5:
			snps_name_ls = newSnpData.col_id_ls
			## 2009-10-8 use NPUTE.samplingImpute()
			imputed_matrix, new_snps_name_ls = NPUTE.samplingImpute(snps_name_ls, newSnpData.data_matrix, \
																input_file_format=1, input_NA_char=0, lower_case_for_imputation=False,\
																npute_window_size=int(npute_window_size), \
																no_of_accessions_per_sampling=300, coverage=3)
			snpData_imputed = SNPData(row_id_ls = newSnpData.row_id_ls, col_id_ls=new_snps_name_ls, data_matrix=imputed_matrix)
			"""
			## 2009-10-8 use NPUTE.samplingImpute() instead. comment out below
			chr2no_of_snps = NPUTE.get_chr2no_of_snps(snps_name_ls)
			chr_ls = chr2no_of_snps.keys()
			chr_ls.sort()
			snpData_imputed = SNPData(row_id_ls = newSnpData.row_id_ls, col_id_ls=[])
			matrix_ls = []
			for chromosome in chr_ls:
				if chr2no_of_snps[chromosome]>5:	#enough for imputation
					npute_data_struc = NPUTESNPData(snps_name_ls=snps_name_ls, data_matrix=newSnpData.data_matrix, chromosome=chromosome, \
									input_file_format=1, input_NA_char=0)
					imputeData(npute_data_struc, int(npute_window_size))
					matrix_ls.append(npute_data_struc.snps)
					snpData_imputed.col_id_ls += npute_data_struc.chosen_snps_name_ls
			if len(matrix_ls)>0:
				snpData_imputed.data_matrix = num.transpose(num.concatenate(matrix_ls))
			"""			
			if output_dir:	#2008-05-16 write the data out if output_fname is available
				#chromosomes = [snpsd_250k_tmp[i].chromosome for i in range(len(snpsd_250k_tmp))]	#already produced in the previous before_imputation output
				output_fname = os.path.join(output_dir, '_'.join(output_fname_prefix_ls + ['after_imputation.tsv']))
				#snpsdata.writeRawSnpsDatasToFile(output_fname, snpsd_250k_tmp, chromosomes=chromosomes, deliminator=',', withArrayIds = True)
				snpData_imputed.tofile(output_fname)
			
			twoSNPData1 = TwoSNPData(SNPData1=snpData_imputed, SNPData2=snpData_qc_strain, \
							row_matching_by_which_value=0)
			qcdata.row_id2NA_mismatch_rate1 = twoSNPData1.cmp_row_wise()
			qcdata.col_id2NA_mismatch_rate1 = twoSNPData1.cmp_col_wise()
			del twoSNPData1, snpData_imputed
		else:
			snpData_imputed = None
			#qcdata.row_id2NA_mismatch_rate1 = {}
			#qcdata.col_id2NA_mismatch_rate1 = {}
		del newSnpData
		"""
		for i in range(len(snpsd_250k_tmp)):
			#snpsd_250k_tmp_1[i].snps = []	#clear it up
			
			if len(snpsd_250k_tmp[i].accessions)>5 and len(snpsd_250k_tmp[i].positions)>5:	#not enough for imputation
				npute_data_struc = NPUTESNPData(inFile=snpsd_250k_tmp[i], input_NA_char='NA', input_file_format=4, lower_case_for_imputation=0)
				imputeData(npute_data_struc, int(npute_window_size))
				snpsd_250k_tmp[i].snps = npute_data_struc.snps
				del npute_data_struc
			"""
		qcdata.row_id2NA_mismatch_rate0 = row_id2NA_mismatch_rate0
		qcdata.col_id2NA_mismatch_rate0 = col_id2NA_mismatch_rate0
		
		qcdata.min_call_probability = min_call_probability
		qcdata.max_call_mismatch_rate = max_call_mismatch_rate
		qcdata.max_call_NA_rate = max_call_NA_rate
		qcdata.max_snp_mismatch_rate = max_snp_mismatch_rate
		qcdata.max_snp_NA_rate = max_snp_NA_rate
		qcdata.npute_window_size = npute_window_size
		result.append(qcdata)
		return result
	
	def computing_node_handler(self, communicator, data, computing_parameter_obj):
		"""
		2007-03-07
		"""
		node_rank = communicator.rank
		sys.stderr.write("Node no.%s working...\n"%node_rank)
		data = cPickle.loads(data)
		min_call_probability, max_call_mismatch_rate, max_call_NA_rate, max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size = data[:6]
		init_data = computing_parameter_obj.init_data
		result = self.doFilter(init_data.snpData_250k, init_data.snpData_2010_149_384, init_data.snpData_perlegen, \
							min_call_probability, max_call_mismatch_rate, max_call_NA_rate,\
							max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size, computing_parameter_obj.output_dir)
		sys.stderr.write("Node no.%s done with %s QC.\n"%(node_rank, len(result)))
		return result
	
	def summarize_NA_mismatch_ls(self, NA_mismatch_ls_ls, avg_var_name_pair_ls):
		"""
		05/12/2008
			called by output_node_handler()
			calculate average NA_rate, mismatch_rate, relative_NA_rate from NA_mismatch_ls_ls
		"""
		passingdata = PassingData()
		for avg_var_name_pair in avg_var_name_pair_ls:
			ls_var_name, avg_var_name, std_var_name = avg_var_name_pair
			setattr(passingdata, ls_var_name, [])
			setattr(passingdata, avg_var_name, -1)
			setattr(passingdata, std_var_name, -1)
		for i in range(len(NA_mismatch_ls_ls)):
			NA_mismatch_ls = NA_mismatch_ls_ls[i]
			
			NA_rate, mismatch_rate, no_of_NAs, no_of_totals, \
			no_of_mismatches, no_of_non_NA_pairs, \
			relative_NA_rate, relative_no_of_NAs, relative_no_of_totals = NA_mismatch_ls
			
			if NA_rate!=-1 and mismatch_rate!=-1 and relative_NA_rate!=-1:	#no non-valid values
				passingdata.NA_rate_ls.append(NA_rate)
				passingdata.mismatch_rate_ls.append(mismatch_rate)
				passingdata.relative_NA_rate_ls.append(relative_NA_rate)
		for avg_var_name_pair in avg_var_name_pair_ls:
			ls_var_name, avg_var_name, std_var_name = avg_var_name_pair
			this_ls = getattr(passingdata, ls_var_name)
			sample_size = len(this_ls)
			setattr(passingdata, 'sample_size', sample_size)
			if sample_size>0:
				setattr(passingdata, avg_var_name, num.average(this_ls))
			if sample_size>1:
				setattr(passingdata, std_var_name, num.std(this_ls))
		return passingdata
	
	def output_node_handler(self, communicator, parameter_list, data):
		"""
		2008-05-19
			row is strain. col is snp. reversed due to utilization of SNPData
		05/14/2008
			flush outf and outf_avg
		05/12/2008
			common_var_name_ls
		"""
		writer, writer_avg, common_var_name_ls, avg_var_name_pair_ls, partial_header_avg, outf, outf_avg = parameter_list
		result = cPickle.loads(data)
		id2NA_mismatch_rate_name_ls = ['row_id2NA_mismatch_rate0', 'col_id2NA_mismatch_rate0', 'row_id2NA_mismatch_rate1', 'col_id2NA_mismatch_rate1']
		for qcdata in result:
			common_ls = []
			for common_var_name in common_var_name_ls:
				common_ls.append(getattr(qcdata, common_var_name))
			for id2NA_mismatch_rate_name in id2NA_mismatch_rate_name_ls:
				if not hasattr(qcdata, id2NA_mismatch_rate_name):
					continue
				id2NA_mismatch_rate = getattr(qcdata, id2NA_mismatch_rate_name)
				row_id_ls = id2NA_mismatch_rate.keys()
				row_id_ls.sort()	#try to keep them in call_info_id order
				if id2NA_mismatch_rate_name[:3]=='row':
					type_of_id = 'strain'
				else:
					type_of_id = 'snp'
				if id2NA_mismatch_rate_name[-1]=='0':
					after_imputation = 0
				else:
					after_imputation = 1
				for row_id in row_id_ls:
					NA_mismatch_ls = id2NA_mismatch_rate[row_id]
					writer.writerow([type_of_id, repr(row_id), after_imputation] + common_ls + NA_mismatch_ls)
				
				if id2NA_mismatch_rate:	#not empty dictionary
					summary_data = self.summarize_NA_mismatch_ls(id2NA_mismatch_rate.values(), avg_var_name_pair_ls)
					summary_ls = []
					for summary_var_name in partial_header_avg:
						summary_ls.append(getattr(summary_data, summary_var_name))
					writer_avg.writerow([type_of_id, after_imputation] + common_ls + summary_ls)
		outf.flush()
		outf_avg.flush()
	
	def create_init_data(self):
		"""
		2009-6-5
			add argument ignore_het=1 to snpData_2010_149_384 & snpData_perlegen
		2008-05-12
			initial data loading on node 0
		"""
		init_data = PassingData()
		init_data.snpData_250k = SNPData(input_fname=self.input_fname, turn_into_array=1)
		init_data.snpData_2010_149_384 = SNPData(input_fname=self.fname_2010_149_384, turn_into_array=1, ignore_2nd_column=1, ignore_het=1)
		init_data.snpData_perlegen = SNPData(input_fname=self.fname_perlegen, turn_into_array=1, ignore_2nd_column=1, ignore_het=1)
		param_d = self.generate_parameters(self.parameter_names)
		init_data.param_d = param_d
		return init_data
	
	@classmethod
	def generate_avg_variable_names(cls, avg_var_name_ls=['NA_rate', 'mismatch_rate', 'relative_NA_rate']):
		"""
		2008-05-13 generalize here so that get_qccall_results() from misc.py could use
			avg_var_name_pair_ls is for summarize_NA_mismatch_ls() to get average/std
			partial_header_avg	is only for output file header
		"""
		avg_var_name_pair_ls = []	#generate variable names for a summary data object
		partial_header_avg = []
		for avg_var_name in avg_var_name_ls:
			avg_var_name_pair_ls.append(('%s_ls'%avg_var_name, 'avg_%s'%avg_var_name, 'std_%s'%avg_var_name))
			partial_header_avg.append('avg_%s'%avg_var_name)
			partial_header_avg.append('std_%s'%avg_var_name)
		partial_header_avg.append('sample_size')
		return avg_var_name_pair_ls, partial_header_avg
		
	#2008-05-13 put them here so that get_qccall_results() from misc.py could use
	#common_var_name_ls is for both output and getting variable values from passingdata
	common_var_name_ls = ['min_call_probability', 'max_call_mismatch_rate', 'no_of_accessions_filtered_by_mismatch', \
							'max_call_NA_rate', 'no_of_accessions_filtered_by_na',\
							'max_snp_mismatch_rate', 'no_of_snps_filtered_by_mismatch',\
							'max_snp_NA_rate', 'no_of_snps_filtered_by_na', 'no_of_monomorphic_snps_removed','npute_window_size']
	avg_var_name_ls = ['NA_rate', 'mismatch_rate', 'relative_NA_rate']	#solely serves avg_var_name_pair_ls
	
	def divideAndSendSNPData(self, snpData, free_computing_nodes, assembleSignal='assemble', block_size=400):
		"""
		2009-6-9
			snpData.data_matrix is too big, so divide and send it
		"""
		if self.report:
			sys.stderr.write("Dividing and sending SNPData ... \n")
		data_matrix = snpData.data_matrix
		snpData.data_matrix = None
		for node in free_computing_nodes:
			data_pickle = cPickle.dumps(snpData, -1)
			self.communicator.send(data_pickle, node, 0)
			del data_pickle
		no_of_blocks = int(math.ceil(len(data_matrix)/float(block_size)))
		for i in range(no_of_blocks):
			start_row_index = i*block_size
			end_row_index = (i+1)*block_size
			data = data_matrix[start_row_index:end_row_index,:]
			for node in free_computing_nodes:	#send it to the computing_node
				sys.stderr.write("passing block %s to node %s ..."%(i , node))
				data_pickle = cPickle.dumps(data, -1)
				self.communicator.send(data_pickle, node, 0)
				del data_pickle
				sys.stderr.write(" Done.\n")
			del data
		#send the assemble signal
		for node in free_computing_nodes:
			data_pickle = cPickle.dumps(assembleSignal, -1)
			self.communicator.send(data_pickle, node, 0)
			del data_pickle
		if self.report:
			sys.stderr.write(" Done.\n")
	
	def receiveAndAssembleSNPData(self, assembleSignal='assemble'):
		"""
		2009-6-9
			counterpart of divideAndSendSNPData()
		"""
		if self.report:
			sys.stderr.write("Receiving and assembling SNPData ... \n")
		data, source, tag = self.communicator.receiveString(0, 0)
		snpData = cPickle.loads(data)
		del data
		
		keep_receiving = 1
		data_block_ls = []
		while keep_receiving:
			data, source, tag = self.communicator.receiveString(0, 0)
			received_data = cPickle.loads(data)
			del data
			if received_data==assembleSignal:	#signal to end
				break
			else:
				data_block_ls.append(received_data)
		snpData.data_matrix = num.concatenate(data_block_ls)	#concatenate all blocks into one matrix rowwise
		del data_block_ls
		if self.report:
			sys.stderr.write("Done with data matrix shape=%s.\n"%repr(snpData.data_matrix.shape))
		return snpData
	
	def run(self):
		"""
		2008-05-09
		"""
		self.parameter_names = ['max_call_mismatch_rate_ls', 'max_call_NA_rate_ls', \
			'max_snp_mismatch_rate_ls', 'max_snp_NA_rate_ls', 'npute_window_size_ls']
		self.communicator = MPI.world.duplicate()
		if self.communicator.size==1:	# 2009-10-8 only one cpu. Run in serial.
			import pdb
			#pdb.set_trace()
			init_data = self.create_init_data()
			min_call_probability, max_call_mismatch_rate, max_call_NA_rate, max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size = init_data.param_d.parameters[0][:6]
			result = self.doFilter(init_data.snpData_250k, init_data.snpData_2010_149_384, init_data.snpData_perlegen, \
							min_call_probability, max_call_mismatch_rate, max_call_NA_rate,\
							max_snp_mismatch_rate, max_snp_NA_rate, npute_window_size, self.output_dir)
			sys.exit(2)
		
		node_rank = self.communicator.rank
		free_computing_nodes = range(1, self.communicator.size-1)	#exclude the 1st and last node
		data_to_pickle_name_ls = ['snpData_2010_149_384', 'snpData_perlegen', 'param_d']
		assembleSignal = 'assemble'
		if node_rank == 0:
			init_data = self.create_init_data()
			param_d = init_data.param_d
			self.divideAndSendSNPData(init_data.snpData_250k, free_computing_nodes, assembleSignal=assembleSignal, block_size=400)
			for data_to_pickle_name in data_to_pickle_name_ls:
				sys.stderr.write("passing %s ... \n"%(data_to_pickle_name))
				for node in free_computing_nodes:	#send it to the computing_node
					sys.stderr.write("passing initial data to nodes from %s to %s ..."%(node_rank, node))
					data_pickle = cPickle.dumps(getattr(init_data, data_to_pickle_name), -1)
					self.communicator.send(data_pickle, node, 0)
					del data_pickle
					sys.stderr.write(" Done.\n")
				sys.stderr.write("Done.\n")
			del init_data
		elif node_rank in free_computing_nodes:
			init_data = PassingData()
			init_data.snpData_250k = self.receiveAndAssembleSNPData(assembleSignal=assembleSignal)
			for data_to_pickle_name in data_to_pickle_name_ls:
				data, source, tag = self.communicator.receiveString(0, 0)
				setattr(init_data, data_to_pickle_name, cPickle.loads(data))
				del data
		else:
			pass
		
		self.synchronize()
		
		if node_rank == 0:
			param_d.index = 0
			parameter_list = [param_d]
			self.input_node(parameter_list, free_computing_nodes, input_handler=self.input_handler)
		elif node_rank in free_computing_nodes:
			computing_parameter_obj = PassingData(init_data=init_data, output_dir=self.output_dir)
			self.computing_node(computing_parameter_obj, self.computing_node_handler)
		else:
			outf = open('%s.csv'%self.output_fname, 'w')
			writer = csv.writer(outf)
			outf_avg = open('%s.avg.csv'%self.output_fname, 'w')
			writer_avg = csv.writer(outf_avg)
			
			common_var_name_ls = self.common_var_name_ls
			
			header = ['strain or snp', 'id', 'after_imputation'] + common_var_name_ls + \
				['NA_rate', 'mismatch_rate', 'no_of_NAs', 'no_of_totals', 'no_of_mismatches', 'no_of_non_NA_pairs', 'relative_NA_rate', 'relative_no_of_NAs', 'relative_no_of_totals']
			writer.writerow(header)
			
			avg_var_name_ls = self.avg_var_name_ls
			avg_var_name_pair_ls, partial_header_avg = self.generate_avg_variable_names(avg_var_name_ls)
			header_avg = ['strain or snp', 'after_imputation'] + common_var_name_ls + partial_header_avg
			writer_avg.writerow(header_avg)
			
			parameter_list = [writer, writer_avg, common_var_name_ls, avg_var_name_pair_ls, partial_header_avg, outf, outf_avg]
			self.output_node(free_computing_nodes, parameter_list, self.output_node_handler)
			del writer, writer_avg
			outf.close()
			outf_avg.close()
		
		self.synchronize()	#to avoid some node early exits
		
if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = MpiQCCall
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()
	
