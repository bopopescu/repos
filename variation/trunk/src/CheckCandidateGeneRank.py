#!/usr/bin/env python
"""

Examples:
	CheckCandidateGeneRank.py -e 1-5 -l 1  -o /tmp/hist_of_results_by_gene_candidate_score_rank
	
	#draw histograms for results_method with phenotype_method (id=1-186) on candidate gene list 28 and store figures in database. 
	CheckCandidateGeneRank.py -s ~/mnt2/panfs/250k/snps_context_g0_m20000 -m 20000 -e 1-186 -l 28 -o /tmp/hist_of_results_by_gene_candidate_score_rank/ -j 17 -c
	
	#draw histograms for results_by_gene with phenotype_method (id=1-186) on candidate gene list 28 and store figures in database. 
	CheckCandidateGeneRank.py -s ~/mnt2/panfs/250k/snps_context_g0_m20000 -m 20000 -e 1-186 -l 28 -o /tmp/hist_of_results_by_gene_candidate_score_rank/ -j 17 -c -w 2

Description:
	2008-09-28
	program to draw histogram of ranks of candidate genes vs those of non-candidate genes.
	it also draws histogram of scores with same partition.
	
	if results_type==1, the partition is carried on SNPs according to their association with genes. (results_method)
	if results_type==2, the partition is carried on genes by their candidacy category directly. (results_by_gene)
	
"""
import sys, os, math
#bit_number = math.log(sys.maxint)/math.log(2)
#if bit_number>40:       #64bit
#	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
#	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64')))
sys.path.insert(0, os.path.expanduser('~/lib/python'))
sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import matplotlib as mpl; mpl.use("Agg")
import time, csv, cPickle
import warnings, traceback
from pymodule import PassingData, figureOutDelimiter, getColName2IndexFromHeader, getListOutOfStr
import Stock_250kDB
from Stock_250kDB import ResultsByGene, ResultsMethod
from sets import Set
from GeneListRankTest import GeneListRankTest, SnpsContextWrapper
#from sqlalchemy.orm import join
from matplotlib import rcParams
rcParams['font.size'] = 6
rcParams['legend.fontsize'] = 4
#rcParams['text.fontsize'] = 6	#deprecated. use font.size instead
rcParams['axes.labelsize'] = 4
rcParams['axes.titlesize'] = 6
rcParams['xtick.labelsize'] = 4
rcParams['ytick.labelsize'] = 4
import pylab
import StringIO


class CheckCandidateGeneRank(GeneListRankTest):
	__doc__ = __doc__
	option_default_dict = {('drivername', 1,):['mysql', 'v', 1, 'which type of database? mysql or postgres', ],\
							('hostname', 1, ): ['papaya.usc.edu', 'z', 1, 'hostname of the db server', ],\
							('dbname', 1, ): ['stock_250k', 'd', 1, 'database name', ],\
							('schema', 0, ): [None, 'k', 1, 'database schema name', ],\
							('db_user', 1, ): [None, 'u', 1, 'database username', ],\
							('db_passwd', 1, ): [None, 'p', 1, 'database password', ],\
							("phenotype_id_ls", 1, ): [None, 'e', 1, 'comma/dash-separated phenotype_method id list, like 1,3-7'],\
							("min_distance", 1, int): [20000, 'm', 1, 'minimum distance allowed from the SNP to gene'],\
							("get_closest", 0, int): [0, 'g', 0, 'only get genes closest to the SNP within that distance'],\
							('min_MAF', 1, float): [0.1, 'n', 1, 'minimum Minor Allele Frequency. deprecated.'],\
							('min_sample_size', 0, int): [5, 'i', 1, 'minimum size for candidate gene sets to draw histogram'],\
							("list_type_id", 1, int): [None, 'l', 1, 'Gene list type. must be in table gene_list_type beforehand.'],\
							("snps_context_picklef", 0, ): [None, 's', 1, 'given the option, if the file does not exist yet, to store a pickled snps_context_wrapper into it, min_distance and flag get_closest will be attached to the filename. If the file exists, load snps_context_wrapper out of it.'],\
							('results_directory', 0, ):[None, 't', 1, 'The results directory. Default is None. use the one given by db.'],\
							("results_type", 1, int): [1, 'w', 1, 'which type of results. 1; ResultsMethod, 2: ResultsByGene'],\
							("output_dir", 0, ): [None, 'o', 1, 'directory to store output'],\
							('call_method_id', 0, int):[0, 'j', 1, 'Restrict results based on this call_method. Default is no such restriction.'],\
							("allow_two_sample_overlapping", 1, int): [0, 'x', 0, 'whether to allow one SNP to be assigned to both candidate and non-candidate gene group'],\
							('commit', 0, int):[0, 'c', 0, 'commit the db operation.'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	
	
	def __init__(self,  **keywords):
		"""
		2008-07-24
			split results_id_ls if it exists, to accomodate MpiGeneListRankTest which removed this option
		2008-07-10
		"""
		from pymodule import ProcessOptions
		self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		
		self.phenotype_id_ls = getListOutOfStr(self.phenotype_id_ls, data_type=int)
		if self.output_dir and not os.path.isdir(self.output_dir):
			os.makedirs(self.output_dir)
			
	def getResultsIDLs(self, db, ResultsClass, results_type, phenotype_id_ls, min_distance=20000, get_closest=0, \
					min_MAF=None, call_method_id=None):
		"""
		2008-10-15
			add option ResultsClass & results_type
		2008-09-28
		"""
		sys.stderr.write("Getting results_id_ls ...")
		phenotype_id2results_id_ls = {}
		if results_type==1:
			rows = ResultsClass.query.filter(ResultsMethod.phenotype_method_id.in_(phenotype_id_ls))
			if call_method_id is not None:
				rows = rows.filter_by(call_method_id=call_method_id)
		elif results_type==2:
			rows = ResultsClass.query.filter_by(min_distance=min_distance).filter_by(get_closest=get_closest).\
				filter(ResultsByGene.results_method.has(ResultsMethod.phenotype_method_id.in_(phenotype_id_ls)))
			if min_MAF is not None:
				rows = rows.filter(ResultsByGene.min_MAF>=min_MAF-0.0001).filter(ResultsByGene.min_MAF<=min_MAF+0.0001)
				#.order_by(ResultsMethod.analysis_method_id)
		counter = 0
		for row in rows:
			if results_type==1:
				phenotype_id = row.phenotype_method_id
				analysis_method_id = row.analysis_method_id
			elif results_type==2:
				phenotype_id = row.results_method.phenotype_method_id
				analysis_method_id = row.results_method.analysis_method_id
			if phenotype_id not in phenotype_id2results_id_ls:
				phenotype_id2results_id_ls[phenotype_id] = []
			phenotype_id2results_id_ls[phenotype_id].append((analysis_method_id, row.id))
			counter += 1
		
		#sort results_id_ls for each phenotype according to analysis_method_id
		for phenotype_id, results_id_ls in phenotype_id2results_id_ls.iteritems():
			results_id_ls.sort()	#sorted by analysis_method_id
			phenotype_id2results_id_ls[phenotype_id] = [row[1] for row in results_id_ls]
		sys.stderr.write("%s results. Done.\n"%(counter))
		return phenotype_id2results_id_ls
	
	def getScoreRankFromRBG(self, rbg, candidate_gene_set, results_directory):
		"""
		2008-09-28
			rename getScoreRank to getScoreRankFromRBG
		"""
		sys.stderr.write("Getting score & rank list ...")
		if results_directory:	#given a directory where all results are.
			result_fname = os.path.join(results_directory, os.path.basename(rbg.filename))
		else:
			result_fname = rbg.filename
		if not os.path.isfile(result_fname):
			sys.stderr.write("%s doesn't exist.\n"%result_fname)
			return None
		#if rbg.results_method.analysis_method_id==13:
		#	sys.stderr.write("Skip analysis_method_id=13.\n")
		#	return None
		reader = csv.reader(open(result_fname), delimiter='\t')
		col_name2index = getColName2IndexFromHeader(reader.next())
		counter = 0
		candidate_score_ls = []
		non_candidate_score_ls = []
		candidate_rank_ls = []
		non_candidate_rank_ls = []
		for row in reader:
			gene_id = int(row[col_name2index['gene_id']])
			score = float(row[col_name2index['score']])
			if gene_id in candidate_gene_set:
				candidate_score_ls.append(score)
				candidate_rank_ls.append(counter)
			else:
				non_candidate_score_ls.append(score)
				non_candidate_rank_ls.append(counter)
			counter += 1
		del reader
		analysis_method = Stock_250kDB.AnalysisMethod.get(rbg.results_method.analysis_method_id)
		
		score_rank_data = PassingData(candidate_score_ls=candidate_score_ls, candidate_rank_ls=candidate_rank_ls,\
								non_candidate_score_ls=non_candidate_score_ls, non_candidate_rank_ls=non_candidate_rank_ls,\
								analysis_method=analysis_method)
		
		sys.stderr.write("Done.\n")
		return score_rank_data
	
	def plotSubHistogram(self, candidate_data_ls, non_candidate_data_ls, which_figure, sub_title, xlabel, \
						no_of_rows=2, max_no_of_bins=200, legend_loc='upper right'):
		"""
		2008-10-16
			add option max_no_of_bins=200
		2008-10-01
			reduce the handle length in the legend
		2008-09-28
		"""
		pylab.subplot(no_of_rows,2,which_figure)
		pylab.title(sub_title)
		pylab.xlabel(xlabel)
		hist_patch_ls = []
		legend_ls = []
		no_of_bins = min(2*max_no_of_bins, int(len(non_candidate_data_ls)/5))
		h1 = pylab.hist(non_candidate_data_ls, no_of_bins, alpha=0.3, normed=1, linewidth=0)
		hist_patch_ls.append(h1[2][0])
		legend_ls.append('non-candidate gene')
		no_of_bins = min(max_no_of_bins, int(len(candidate_data_ls)/5))
		h2 = pylab.hist(candidate_data_ls, no_of_bins, alpha=0.3, normed=1, facecolor='r', linewidth=0)
		hist_patch_ls.append(h2[2][0])
		legend_ls.append('candidate gene')
		pylab.legend(hist_patch_ls, legend_ls, loc=legend_loc, handlelen=0.02)
	
	def plotHistForOnePhenotype(self, phenotype_method, list_type, score_rank_data_ls, output_dir=None, data_type='score', commit=0):
		"""
		2008-10-16
			add option commit
			save fig into StringIO to skip file storage to be directly passed onto a database binary variable
		2008-09-28
		"""
		sys.stderr.write("Drawing histogram ...")
		pylab.clf()
		#calculate the number of rows needed according to how many score_rank_data, always two-column
		no_of_rows = len(score_rank_data_ls)/2.
		if no_of_rows%1>0:
			no_of_rows = int(no_of_rows)+1
		else:
			no_of_rows = int(no_of_rows)
		
		for i in range(len(score_rank_data_ls)):
			score_rank_data = score_rank_data_ls[i]
			if data_type=='score':
				candidate_data_ls = score_rank_data.candidate_score_ls
				non_candidate_data_ls = score_rank_data.non_candidate_score_ls
				legend_loc='upper right'
			else:
				candidate_data_ls = score_rank_data.candidate_rank_ls
				non_candidate_data_ls = score_rank_data.non_candidate_rank_ls
				legend_loc='upper left'	#not to block the right-end high rank peaks
			sub_title = score_rank_data.analysis_method.short_name
			xlabel = data_type
			self.plotSubHistogram(candidate_data_ls, non_candidate_data_ls, i+1, sub_title, xlabel, no_of_rows=no_of_rows, legend_loc=legend_loc)
		ax = pylab.axes([0.1, 0.1, 0.8,0.8], frameon=False)
		ax.set_xticks([])
		ax.set_yticks([])
		title = 'Phenotype %s %s vs %s %s'%(phenotype_method.id, phenotype_method.short_name, list_type.id, list_type.short_name)
		ax.set_title(title)
		png_data = None
		svg_data = None
		if commit:
			png_data = StringIO.StringIO()
			svg_data = StringIO.StringIO()
			pylab.savefig(png_data, format='png', dpi=300)
			pylab.savefig(svg_data, format='svg', dpi=300)
		elif output_dir:
			output_fname_prefix = os.path.join(output_dir, title.replace('/', '_'))
			output_fname_prefix = '%s_%s'%(output_fname_prefix, data_type)
			pylab.savefig('%s.png'%output_fname_prefix, dpi=300)
			pylab.savefig('%s.svg'%output_fname_prefix, dpi=300)
		sys.stderr.write("Done.\n")
		return png_data, svg_data
	
	def getHistType(self, call_method_id, min_distance, get_closest, min_MAF, allow_two_sample_overlapping, results_type):
		"""
		2008-10-16
		"""
		sys.stderr.write("Getting ScoreRankHistogramType ...")
		rows = Stock_250kDB.ScoreRankHistogramType.query.filter_by(call_method_id=call_method_id).\
				filter_by(min_distance=min_distance).filter_by(get_closest =get_closest).\
				filter(Stock_250kDB.ScoreRankHistogramType.min_MAF>=min_MAF-0.0001).filter(Stock_250kDB.ScoreRankHistogramType.min_MAF<=min_MAF+0.0001).\
				filter_by(allow_two_sample_overlapping = allow_two_sample_overlapping).filter_by(results_type=results_type)
		if rows.count()>0:
			hist_type = rows.first()
		else:
			hist_type = Stock_250kDB.ScoreRankHistogramType(call_method_id=call_method_id, min_distance=min_distance,\
										get_closest =get_closest,
										min_MAF = min_MAF, results_type=results_type,
										allow_two_sample_overlapping = allow_two_sample_overlapping, results_type=results_type)
		sys.stderr.write("Done.\n")
		return hist_type
	
	def run(self):
		"""
		2008-10-19
			save figures in database if commit
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		db = Stock_250kDB.Stock_250kDB(drivername=self.drivername, username=self.db_user,
				   password=self.db_passwd, hostname=self.hostname, database=self.dbname, schema=self.schema)
		db.setup(create_tables=False)
		session = db.session
		session.begin()
		
		if self.results_type==1:
			ResultsClass = Stock_250kDB.ResultsMethod
			snps_context_wrapper = self.dealWithSnpsContextWrapper(self.snps_context_picklef, self.min_distance, self.get_closest)
		elif self.results_type==2:
			ResultsClass = Stock_250kDB.ResultsByGene
		else:
			sys.stderr.write("Invalid results type : %s.\n"%self.results_type)
			return None
		
		hist_type = self.getHistType(self.call_method_id, self.min_distance, self.get_closest, self.min_MAF, self.allow_two_sample_overlapping, self.results_type)
		
		candidate_gene_list = self.getGeneList(self.list_type_id)
		if len(candidate_gene_list)<self.min_sample_size:
			sys.stderr.write("Candidate gene list of %s too small: %s.\n"%(self.list_type_id, len(candidate_gene_list)))
			sys.exit(4)
		candidate_gene_set = Set(candidate_gene_list)
		list_type = Stock_250kDB.GeneListType.get(self.list_type_id)
		if list_type is None:
			sys.exit(3)
		
		phenotype_id2results_id_ls = self.getResultsIDLs(db, ResultsClass, self.results_type, self.phenotype_id_ls, \
														self.min_distance, self.get_closest, self.min_MAF, self.call_method_id)
		
			
		param_data = PassingData(results_directory=self.results_directory, candidate_gene_list=candidate_gene_list, \
			min_MAF=self.min_MAF, allow_two_sample_overlapping=self.allow_two_sample_overlapping, need_the_value=1)	#need_the_value means to get the pvalue/score
		for phenotype_id, results_id_ls in phenotype_id2results_id_ls.iteritems():
			if hist_type.id:	#hist_type already in database
				rows = Stock_250kDB.ScoreRankHistogram.query.filter_by(phenotype_method_id=phenotype_id).\
					filter_by(list_type_id=self.list_type_id).filter_by(hist_type_id=hist_type.id)
				if rows.count()>0:
					row = rows.first()
					sys.stderr.write("Histogram already in database. id=%s, phenotype_id=%s, list_type_id=%s, hist_type_id=%s.\n"%\
									(row.id, row.phenotype_method_id, row.list_type_id, row.hist_type_id))
					continue
			phenotype_method = Stock_250kDB.PhenotypeMethod.get(phenotype_id)
			if not phenotype_method:
				continue
			score_rank_data_ls = []
			sys.stderr.write("Checking phenotype %s (%s) ...\n"%(phenotype_method.id, phenotype_method.short_name))
			for results_id in results_id_ls:
				try:
					rm = ResultsClass.get(results_id)
					if self.results_type==1:
						permData = self.prepareDataForPermutationRankTest(rm, snps_context_wrapper, param_data)
						if not permData:
							continue
						score_rank_data = PassingData(candidate_score_ls=permData.candidate_gene_snp_value_ls, \
												candidate_rank_ls=permData.candidate_gene_snp_rank_ls,\
								non_candidate_score_ls=permData.non_candidate_gene_snp_value_ls, non_candidate_rank_ls=permData.non_candidate_gene_snp_rank_ls,\
								analysis_method=rm.analysis_method)
						del permData
					elif self.results_type==2:
						score_rank_data = self.getScoreRankFromRBG(rm, candidate_gene_set, self.results_directory)
					if score_rank_data:
						score_rank_data_ls.append(score_rank_data)
				except:
						sys.stderr.write("Exception happened for results_id=%s, phenotype_id=%s.\n"%(results_id, phenotype_id))
						traceback.print_exc()
						sys.stderr.write('%s.\n'%repr(sys.exc_info()))
						continue
			if score_rank_data_ls:

				score_png_data, score_svg_data = self.plotHistForOnePhenotype(phenotype_method, list_type, score_rank_data_ls, self.output_dir, data_type='score', commit=self.commit)
				rank_png_data, rank_svg_data = self.plotHistForOnePhenotype(phenotype_method, list_type, score_rank_data_ls, self.output_dir, data_type='rank', commit=self.commit)
				if self.commit:
					score_rank_hist = Stock_250kDB.ScoreRankHistogram(phenotype_method_id=phenotype_id, list_type_id=list_type.id)
					score_rank_hist.hist_type = hist_type
					score_rank_hist.score_hist = score_png_data.getvalue()
					score_rank_hist.score_hist_svg = score_svg_data.getvalue()
					score_rank_hist.rank_hist = rank_png_data.getvalue()
					score_rank_hist.rank_hist_svg = rank_svg_data.getvalue()
					session.save(score_rank_hist)
					del score_png_data, score_svg_data, rank_png_data, rank_svg_data
		if self.commit:
			session.flush()
			session.commit()
			session.clear()
		else:	#default is also rollback(). to demonstrate good programming
			session.rollback()
			
		
if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = CheckCandidateGeneRank
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()