#!/usr/bin/env python
"""
Examples:
	#output SNP plots by ranks according to results_by_gene's id=260 (one particular phenotype).
	DrawSNPRegion.py -e 260 -l 28 -L /Network/Data/250k/tmp-yh/call_method_17_LD_m0.3.tsv  -o /Network/Data/250k/tmp-yh/snp_region/
	
	#output SNP plots by ranks according to results_by_gene (analysis_method_id=7-Emma, call_method_id=17) (covering all phenotypes)
	DrawSNPRegion.py -l 28 -L /Network/Data/250k/tmp-yh/call_method_17_LD_m0.3.tsv -o /Network/Data/250k/tmp-yh/snp_region_all/
	
Description:
	2008-09-24 program to draw pvalues, gene-models, LD around one SNP.
		Top panel is pvalues from all different methods. Margarita and RF's values will be normalized in range of KW.
		Middle panel is gene model. Displaying CDS, intron, strand.
		Bottom panel is LD of all pairwise SNPs in that range.
"""

import sys, os, math
#bit_number = math.log(sys.maxint)/math.log(2)
#if bit_number>40:       #64bit
sys.path.insert(0, os.path.expanduser('~/lib/python'))
sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import time, csv, cPickle
import warnings, traceback
from pymodule import PassingData, figureOutDelimiter, getColName2IndexFromHeader
import Stock_250kDB
from pymodule import getGenomeWideResultFromFile
from sets import Set
from GenomeBrowser import GenomeBrowser	#GenomeBrowser.get_gene_id2model
from GeneListRankTest import GeneListRankTest	#GeneListRankTest.getGeneList()
import matplotlib; matplotlib.use("Agg")	#to avoid popup and collapse in X11-disabled environment
from matplotlib import rcParams
rcParams['font.size'] = 6
rcParams['legend.fontsize'] = 6
#rcParams['text.fontsize'] = 6	#deprecated. use font.size instead
rcParams['axes.labelsize'] = 6
rcParams['axes.titlesize'] = 8
rcParams['xtick.labelsize'] = 6
rcParams['ytick.labelsize'] = 6
from matplotlib.patches import Polygon, CirclePolygon
import pylab
from pymodule.yh_matplotlib_artists import ExonIntronCollection
import ImageColor

class DrawSNPRegion(GeneListRankTest):
	__doc__ = __doc__
	option_default_dict = {('drivername', 1,):['mysql', 'v', 1, 'which type of database? mysql or postgres', ],\
							('hostname', 1, ): ['papaya.usc.edu', 'z', 1, 'hostname of the db server', ],\
							('dbname', 1, ): ['stock_250k', 'd', 1, 'database name', ],\
							('schema', 0, ): [None, 'k', 1, 'database schema name', ],\
							('db_user', 1, ): [None, 'u', 1, 'database username', ],\
							('db_passwd', 1, ): [None, 'p', 1, 'database password', ],\
							('LD_fname', 1, ): [None, 'L', 1, 'the file containing LD info, output of MpiLD.py', ],\
							("results_id_ls", 0, ): [None, 'e', 1, 'comma-separated results_by_gene id list'],\
							("min_distance", 1, int): [20000, 'm', 1, 'minimum distance allowed from the SNP to gene'],\
							("get_closest", 0, int): [0, 'g', 0, 'only get genes closest to the SNP within that distance'],\
							('min_MAF', 1, float): [0.1, 'n', 1, 'minimum Minor Allele Frequency.'],\
							("list_type_id", 1, int): [None, 'l', 1, 'Gene list type. must be in table gene_list_type beforehand.'],\
							('results_directory', 0, ):[None, 't', 1, 'The results directory. Default is None. use the one given by db.'],\
							("output_dir", 1, ): [None, 'o', 1, 'directory to store all images'],\
							('call_method_id', 0, int):[17, 'i', 1, 'Restrict results based on this call_method. Default is no such restriction.'],\
							('analysis_method_id', 0, int):[7, 'a', 1, 'Restrict results based on this analysis_method. Default is no such restriction.'],\
							('no_of_top_hits', 1, int): [1000, 'f', 1, 'how many number of top hits based on score or -log(pvalue).'],\
							('commit', 0, int):[0, 'c', 0, 'commit the db operation. this commit happens after every db operation, not wait till the end.'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	
	def __init__(self,  **keywords):
		"""
		2008-09-24
		"""
		GeneListRankTest.__init__(self, **keywords)
		#from pymodule import ProcessOptions
		#self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
	
	
	def get_LD(self, LD_fname):
		"""
		2008-09-24
		"""
		sys.stderr.write("Reading in LD info from %s ...\n"%(LD_fname))
		snp_pair2r2 = {}
		reader = csv.reader(open(LD_fname), delimiter='\t')
		col_name2index = getColName2IndexFromHeader(reader.next())
		counter = 0
		for row in reader:
			snp1 = row[col_name2index['snp1']].split('_')
			snp1 = map(int, snp1)
			snp2 = row[col_name2index['snp2']].split('_')
			snp2 = map(int, snp2)
			r2 = float(row[col_name2index['r2']])
			if snp1<snp2:
				snp_pair = (snp1[0], snp1[1], snp2[0], snp2[1])
			else:
				snp_pair = (snp2[0], snp2[1], snp1[0], snp1[1])
			snp_pair2r2[snp_pair] = r2
			counter += 1
			if counter%100000==0:
				sys.stderr.write('%s\t%s'%('\x08'*100, counter))
				if self.debug:
					#break
					pass
		LD_info = PassingData(snp_pair2r2=snp_pair2r2)
		sys.stderr.write("Done.\n")
		return LD_info
	
	def getGeneAnnotation(self):
		"""
		2008-09-24
		"""
		from annot.bin.codense.common import db_connect
		hostname = 'banyan'
		dbname = 'graphdb'
		schema = 'genome'
		postgres_conn, postgres_curs = db_connect(hostname, dbname, schema)
		gene_id2model, chr_id2gene_id_ls = GenomeBrowser.get_gene_id2model(postgres_curs)
		gene_annotation = PassingData()
		gene_annotation.gene_id2model = gene_id2model
		gene_annotation.chr_id2gene_id_ls = chr_id2gene_id_ls
		return gene_annotation
	
	def getSimilarGWResultsGivenResultsByGene(self, rg, results_directory):
		"""
		2008-09-24
		"""
		rg_rm = Stock_250kDB.ResultsMethod.get(rg.results_method_id)
		sys.stderr.write("Getting results with phenotype=%s and call_method=%s ..."%(rg_rm.phenotype_method_id, rg_rm.call_method_id))
		if self.debug:
			analysis_method_id_set = Set([1,7])
		else:
			analysis_method_id_set = Set([1,5,6,7])
		rows = Stock_250kDB.ResultsMethod.query.filter_by(phenotype_method_id=rg_rm.phenotype_method_id, call_method_id=rg_rm.call_method_id)
		analysis_method_id2gwr = {}
		for rm in rows:
			if rm.analysis_method_id in analysis_method_id_set:
				genome_wide_result = self.getResultMethodContent(rm, results_directory, min_MAF=0, construct_chr_pos2index=True)
				analysis_method_id2gwr[rm.analysis_method_id] = genome_wide_result
		sys.stderr.write("Done.\n")
		return analysis_method_id2gwr
	
	def getSNPInfo(self, db):
		"""
		2008-09-24
			in order
		"""
		sys.stderr.write("Getting info of all SNPs in chromosomal order ...")
		chr_pos_ls = []
		chr_pos2index = {}
		snps_id2index = {}
		i = 0
		block_size = 50000
		rows = db.metadata.bind.execute("select id, chromosome, position from %s where end_position is null"%Stock_250kDB.Snps.table.name)
		#.query.offset(i).limit(block_size)
		#while rows.count()!=0:
		for row in rows:
			chr_pos = (row.chromosome, row.position)
			chr_pos_ls.append(chr_pos)
			chr_pos2index[chr_pos] = len(chr_pos2index)
			snps_id2index[row.id] = len(snps_id2index)
			i += 1
		#	if self.debug and i>40000:
		#		break
		#	rows = Stock_250kDB.Snps.query.offset(i).limit(block_size)
		snp_info = PassingData()
		snp_info.chr_pos_ls = chr_pos_ls
		snp_info.chr_pos2index = chr_pos2index
		snp_info.snps_id2index = snps_id2index
		sys.stderr.write("Done.\n")
		return snp_info
	
	def add_mid_point(self, chr_pos_ls, chr_pos2adjacent_window):
		"""
		2008-09-24
			called by getSNPsAroundThisSNP()
		"""
		new_chr_pos = chr_pos_ls[-1]
		old_chr_pos = chr_pos_ls[-2]
		if old_chr_pos not in chr_pos2adjacent_window:
			chr_pos2adjacent_window[old_chr_pos] = []
		if new_chr_pos not in chr_pos2adjacent_window:
			chr_pos2adjacent_window[new_chr_pos] = []
		mid_point = (new_chr_pos[1]+old_chr_pos[1])/2.
		chr_pos2adjacent_window[old_chr_pos].append(mid_point)
		chr_pos2adjacent_window[new_chr_pos].append(mid_point)
	
	def getSNPsAroundThisSNP(self, this_snp, snp_info, min_distance=20000):
		"""
		2008-09-24
		"""
		sys.stderr.write("\t Get SNPs around this snp ...")
		chr_pos = snp_info.chr_pos_ls[snp_info.snps_id2index[this_snp.snps_id]]
		chromosome, position = chr_pos
		chr_pos_ls = []
		chr_pos2adjacent_window = {}
		j = 0
		for i in range(min_distance*2):
			new_pos = position - min_distance + i
			new_chr_pos = (chromosome, new_pos)
			if new_chr_pos in snp_info.chr_pos2index:
				chr_pos_ls.append(new_chr_pos)
				if j!=0:
					self.add_mid_point(chr_pos_ls, chr_pos2adjacent_window)
				j += 1
		#deal with the leftest point of the 1st chr_pos
		chr_pos = chr_pos_ls[0]
		window_size = chr_pos2adjacent_window[chr_pos][0]-chr_pos[1]
		chr_pos2adjacent_window[chr_pos] = [chr_pos[1]-window_size, chr_pos[1]+window_size]
		
		#deal with the rightest point of the 1st chr_pos
		chr_pos = chr_pos_ls[-1]
		window_size = chr_pos[1] - chr_pos2adjacent_window[chr_pos][0]
		chr_pos2adjacent_window[chr_pos] = [chr_pos[1]-window_size, chr_pos[1]+window_size]
		snp_region = PassingData(chr_pos_ls=chr_pos_ls, chr_pos2adjacent_window=chr_pos2adjacent_window)
		sys.stderr.write("Done.\n")
		return snp_region
	
	analysis_method_id2color = {1:'b',
							5:'r',
							6:'g',
							7:'k'}
	
	analysis_method_id2name = {1:'KW',
							5:'Margarita',
							6:'RF',
							7:'Emma'}
	
	def getXY(self, snps_within_this_region, analysis_method_id2gwr, analysis_method_id):
		"""
		2008-09-24
			of GW results, get values for each SNP position, adjust value for analysis_method_id=5,6
		"""
		x_ls = []
		y_ls = []
		gwr = analysis_method_id2gwr[analysis_method_id]
		if 1 in analysis_method_id2gwr:
			ref_gwr = analysis_method_id2gwr[1]
		elif 7 in analysis_method_id2gwr:
			ref_gwr = analysis_method_id2gwr[7]
		else:
			ref_gwr = None
		for chr_pos in snps_within_this_region.chr_pos_ls:
			data_obj = gwr.get_data_obj_by_chr_pos(chr_pos[0], chr_pos[1])
			if data_obj is not None:
				x_ls.append(chr_pos[1])
				if (analysis_method_id==5 or analysis_method_id==6) and ref_gwr:
					value = (data_obj.value-gwr.min_value)/(gwr.max_value-gwr.min_value)*(ref_gwr.max_value-ref_gwr.min_value)
				else:
					value = data_obj.value
				y_ls.append(value)
		return x_ls, y_ls
		
		
	
	def drawPvalue(self, ax1, ax2, snps_within_this_region, analysis_method_id2gwr):
		"""
		2008-09-24
		"""
		sys.stderr.write("\t Drawing pvalues  ...")
		analysis_method_id_ls = analysis_method_id2gwr.keys()
		analysis_method_id_ls.sort()
		pscatter_ls = []
		legend_ls = []
		for analysis_method_id in analysis_method_id_ls:
			gwr = analysis_method_id2gwr[analysis_method_id]
			x_ls, y_ls = self.getXY(snps_within_this_region, analysis_method_id2gwr, analysis_method_id)
			pscatter = ax1.scatter(x_ls, y_ls, edgecolor=self.analysis_method_id2color[analysis_method_id], facecolor='w')
			legend_ls.append(self.analysis_method_id2name[analysis_method_id])
			pscatter_ls.append(pscatter)
		ax2.legend(pscatter_ls, legend_ls, shadow=True, loc='lower right')
		sys.stderr.write("Done.\n")
		#return legend_ls
	
	def plot_one_gene(self, ax, gene_id, gene_id2model, candidate_gene_set=None, y_value=1, gene_width=1.0):
		"""
		2008-09-24
			draw a single gene on the canvas, adaped from GenomeBrowser.plot_one_gene()
		"""
		gene_model = gene_id2model.get(gene_id)
		if gene_model:
			c_start_ls = None
			c_end_ls = None
			if gene_model.cds_start!=None and gene_model.cds_stop!=None:
				c_start_ls = gene_model.cds_start
				c_end_ls = gene_model.cds_stop
			elif gene_model.mrna_start!=None and gene_model.mrna_stop!=None:
				c_start_ls = gene_model.mrna_start
				c_end_ls = gene_model.mrna_stop
			elif gene_model.start!=None and gene_model.stop!=None:
				c_start_ls = [gene_model.start]
				c_end_ls = [gene_model.stop]
			if c_start_ls and c_end_ls:
				if gene_id in candidate_gene_set:
					facec = 'y'
				else:
					facec = 'w'
				if gene_model.strand=="1":
					exon_start_ls = c_start_ls
					exon_stop_ls = c_end_ls
					is_arrow = True
				elif gene_model.strand=="-1":	#to draw opposite strand, 1st is to order c_start_ls and c_end_ls in descending order. 2nd is to swap c_start_ls and c_end_ls.
					#c_start_ls.reverse()	#2008-02-04 it's already in descending order in db.
					#c_end_ls.reverse()	#2008-02-04 it's already in descending order in db.
					exon_start_ls = c_end_ls
					exon_stop_ls = c_start_ls
					is_arrow = True
				else:	#no arrow
					exon_start_ls = c_start_ls
					exon_stop_ls = c_end_ls
					is_arrow = False
				g_artist = ExonIntronCollection(c_start_ls, c_end_ls, y=y_value, is_arrow=is_arrow, width=gene_width, alpha=0.3, \
											facecolors=facec, picker=True, linewidths=0.7, box_line_widths=0.3)
				ax.add_artist(g_artist)
				if gene_model.strand=="-1":
					text_start_pos = c_end_ls[0]
				else:
					text_start_pos = c_end_ls[-1]
				#mid_point = (c_start_ls[0]+c_end_ls[-1])/2.
				ax.text(text_start_pos, y_value, gene_model.symbol, size=8)
				
	def drawGeneModel(self, ax, snps_within_this_region, gene_annotation, candidate_gene_set, gene_width=1.0, gene_position_cycle=4):
		"""
		2008-09-24
		"""
		sys.stderr.write("\t Drawing gene model  ...")
		left_chr, left_pos = snps_within_this_region.chr_pos_ls[0]
		right_chr, right_pos = snps_within_this_region.chr_pos_ls[-1]
		left_chr = str(left_chr)
		right_chr = str(right_chr)
		no_of_genes_drawn = 0
		for gene_id in gene_annotation.chr_id2gene_id_ls[left_chr]:
			gene_model = gene_annotation.gene_id2model[gene_id]
			if gene_model.start!=None and gene_model.stop!=None and gene_model.stop>left_pos:
				if left_chr==right_chr:	#same chromosome
					if gene_model.start>right_pos:	#totally out of range, skip it
						continue
				y_value = no_of_genes_drawn%gene_position_cycle	#cycling through the y position to avoid clogging
				self.plot_one_gene(ax, gene_id, gene_annotation.gene_id2model, candidate_gene_set, y_value=-1-y_value, gene_width=gene_width)
				no_of_genes_drawn += 1
		if left_chr!=right_chr:
			for gene_id in gene_annotation.chr_id2gene_id_ls[right_chr]:
				gene_model = gene_annotation.gene_id2model[gene_id]
				if gene_model.start!=None and gene_model.stop!=None and gene_model.start<right_pos:
					y_value = no_of_genes_drawn%gene_position_cycle	#cycling through the y position to avoid clogging
					self.plot_one_gene(ax, gene_id, gene_annotation.gene_id2model, candidate_gene_set, y_value=-1-y_value, gene_width=gene_width)
					no_of_genes_drawn += 1
		sys.stderr.write("Done.\n")
	
	def drawLD(self, ax1, ax2, snps_within_this_region, LD_info, y_value=-5):
		"""
		2008-09-28
			represent r2 by HSL color, rather than a grayscale intensity. matplotlib doesn't support hsl notation (i'm not aware).
			Use ImageColor.getrgb to convert hsl representation to RGB format.
		2008-09-24
			draw LD in the bottom axe
		"""
		sys.stderr.write("\t Drawing LD info  ...")
		no_of_snps = len(snps_within_this_region.chr_pos_ls)
		left_chr, left_pos = snps_within_this_region.chr_pos_ls[0]
		right_chr, right_pos = snps_within_this_region.chr_pos_ls[-1]
		#ax1.hlines(y_value, left_pos, right_pos, linewidth=0.3)
		for i in range(no_of_snps):
			chr_pos1 = snps_within_this_region.chr_pos_ls[i]
			ax1.vlines(chr_pos1[1], y_value, 0, linestyle='dashed', alpha=0.3, linewidth=0.3)
			for j in range(i+1, no_of_snps):
				chr_pos2 = snps_within_this_region.chr_pos_ls[j]
				if chr_pos1<chr_pos2:
					snp_pair = (chr_pos1[0], chr_pos1[1], chr_pos2[0], chr_pos2[1])
				else:
					snp_pair = (chr_pos2[0], chr_pos2[1], chr_pos1[0], chr_pos1[1])
				if snp_pair in LD_info.snp_pair2r2:
					r2 = LD_info.snp_pair2r2[snp_pair]
					s11, s12 = snps_within_this_region.chr_pos2adjacent_window[chr_pos1]
					s21, s22 = snps_within_this_region.chr_pos2adjacent_window[chr_pos2]
					#draw a plot to understand this. a parallegram below SNPs, it's the intersection of two adjacent windows 
					x1 = (s12+s21)/2.
					y1 = (s12-s21)/2.
					x2 = (s12+s22)/2.
					y2 = (s12-s22)/2.
					x3 = (s11+s22)/2.
					y3 = (s11-s22)/2.
					x4 = (s11+s21)/2.
					y4 = (s11-s21)/2.
					xs = [x1, x2, x3, x4]
					ys = [y1, y2, y3, y4]
					hue_value = int(round(r2*255))	#r2 is [0,1], 255 is the maximum hue value.
					fc = ImageColor.getrgb('hsl(%s'%hue_value+',100%,50%)')	#"hsl(hue, saturation%, lightness%)" where hue is the colour given as an
					# angle between 0 and 360 (red=0, green=120, blue=240),
					#saturation is a value between 0% and 100% (gray=0%, full color=100%), and lightness is a value between 0% and 100% (black=0%, normal=50%, white=100%).
					fc = [color_value/255. for color_value in fc]	#matplotlib accepts rgb in [0-1] range
					poly = Polygon(zip(xs, ys), facecolor=fc, linewidth=0)
					ax2.add_patch(poly)
		sys.stderr.write("Done.\n")
	
	def drawRegionAroundThisSNP(self, rg, this_snp, candidate_gene_set, gene_annotation, snp_info, analysis_method_id2gwr, LD_info, output_dir, min_distance, list_type_id):
		"""
		2008-09-24
		"""
		sys.stderr.write("Drawing region ... \n")
		rg_rm = Stock_250kDB.ResultsMethod.get(rg.results_method_id)
		phenotype = Stock_250kDB.PhenotypeMethod.get(rg_rm.phenotype_method_id)
		if this_snp.snps_id in snp_info.snps_id2index:
			chr_pos = snp_info.chr_pos_ls[snp_info.snps_id2index[this_snp.snps_id]]
		else:
			return
		gene_model = gene_annotation.gene_id2model.get(this_snp.gene_id)
		gene_id = this_snp.gene_id
		if gene_model is None:
			gene_model = PassingData(gene_id=this_snp.gene_id, symbol='')
		list_type = Stock_250kDB.GeneListType.get(list_type_id)
		fname_basename = 'phenotype_%s_%s_rank_%s_snp_%s_%s_list_type_%s_%s_gene_%s_%s'%\
										(phenotype.id, phenotype.short_name, this_snp.rank, chr_pos[0], chr_pos[1], list_type_id, list_type.short_name, gene_id, gene_model.symbol)
		fname_basename = fname_basename.replace('/', '_')
		output_fname_prefix = os.path.join(output_dir, fname_basename)
		snps_within_this_region = self.getSNPsAroundThisSNP(this_snp, snp_info, self.min_distance)
		pylab.clf()
		#fig = pylab.figure()
		ax1 = pylab.axes([0.1,0.5, 0.8, 0.45])
		ax2 = pylab.axes([0.1,0.05, 0.8, 0.45], frameon=False)
		self.drawPvalue(ax1, ax2, snps_within_this_region, analysis_method_id2gwr)
		gene_position_cycle = 4
		self.drawGeneModel(ax1, snps_within_this_region, gene_annotation, candidate_gene_set, gene_width=1.0, gene_position_cycle=gene_position_cycle)
		LD_boundary_y_value = -gene_position_cycle-1
		self.drawLD(ax1, ax2, snps_within_this_region, LD_info, y_value=LD_boundary_y_value)
		ax1_ylim = ax1.get_ylim()
		ax1.set_ylim((LD_boundary_y_value, ax1_ylim[1]))	#LD panel right under gene models
		ax1.set_xticklabels([])	#remove xtick labels on ax1 because ax2's xtick labels cover this.
		ax2.set_xlim(ax1.get_xlim())	#make the two plots within the same X range
		ax2.set_ylim((-min_distance, 0))	#has to force here, don't know why. otherwise it's (0,1)
		ax2.set_yticks([])	#remove all Y ticks on LD plot
		#ax2.colorbar()
		#ax2.gray()
		pylab.savefig('%s.png'%output_fname_prefix, dpi=400)
		pylab.savefig('%s.svg'%output_fname_prefix, dpi=300)
		if self.debug:
			pylab.show()
		sys.stderr.write("Done.\n")
	
	def generate_params(self, param_obj):
		"""
		2008-09-24
			copied from a version of MpiGeneListRankTest.py
		"""
		sys.stderr.write("Generating parameters ...")
		i = 0
		block_size = 5000
		query = Stock_250kDB.ResultsByGene.query
		if param_obj.call_method_id!=0:
			query = query.filter(Stock_250kDB.ResultsByGene.results_method.has(call_method_id=param_obj.call_method_id))
		if param_obj.analysis_method_id!=0 and param_obj.analysis_method_id is not None:
			query = query.filter(Stock_250kDB.ResultsByGene.results_method.has(analysis_method_id=param_obj.analysis_method_id))
		query = query.filter_by(min_distance=param_obj.min_distance).filter_by(get_closest=param_obj.get_closest)
		rows = query.offset(i).limit(block_size)
		results_id_ls = []
		while rows.count()!=0:
			for row in rows:
				results_id_ls.append(row.id)
				i += 1
			rows = query.offset(i).limit(block_size)
		
		sys.stderr.write("%s results. "%(len(results_id_ls)))
		return results_id_ls
	
	def run(self):
		"""
		2008-09-24
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		db = Stock_250kDB.Stock_250kDB(drivername=self.drivername, username=self.db_user,
				   password=self.db_passwd, hostname=self.hostname, database=self.dbname, schema=self.schema)
		db.setup(create_tables=False)
		session = db.session
		candidate_gene_list = self.getGeneList(self.list_type_id)
		candidate_gene_set = Set(candidate_gene_list)
		gene_annotation = self.getGeneAnnotation()
		snp_info = self.getSNPInfo(db)
		LD_info = self.get_LD(self.LD_fname)
		if not os.path.isdir(self.output_dir):
			os.makedirs(self.output_dir)
		if not self.results_id_ls:
			param_obj = PassingData(call_method_id=self.call_method_id, analysis_method_id=self.analysis_method_id,\
								min_distance=self.min_distance, get_closest=self.get_closest)
			self.results_id_ls = self.generate_params(param_obj)
		for results_id in self.results_id_ls:
			rg = Stock_250kDB.ResultsByGene.get_by(id=results_id)
			analysis_method_id2gwr = self.getSimilarGWResultsGivenResultsByGene(rg, self.results_directory)
			if self.results_directory:	#given a directory where all results are.
				result_fname = os.path.join(self.results_directory, os.path.basename(rg.filename))
			else:
				result_fname = rg.filename
			if not os.path.isfile(result_fname):
				sys.stderr.write("%s doesn't exist.\n"%result_fname)
				continue
			reader = csv.reader(open(result_fname), delimiter='\t')
			col_name2index = getColName2IndexFromHeader(reader.next())
			counter = 0
			prev_snp = None
			for row in reader:
				counter += 1
				if counter>self.no_of_top_hits:	#only the top hits
					continue
				gene_id = int(row[col_name2index['gene_id']])
				#if gene_id not in candidate_gene_set:
				#	continue
				score = float(row[col_name2index['score']])
				snps_id = int(row[col_name2index['snps_id']])
				disp_pos = int(row[col_name2index['disp_pos']])
				this_snp = PassingData(rank=counter, gene_id=gene_id, score=score, snps_id=snps_id, disp_pos=disp_pos)
				if prev_snp == None:
					prev_snp = this_snp
				elif prev_snp.snps_id == this_snp.snps_id:	#skip if it's the same SNP
					continue
				self.drawRegionAroundThisSNP(rg, this_snp, candidate_gene_set, gene_annotation, snp_info, \
											analysis_method_id2gwr, LD_info, self.output_dir, self.min_distance, self.list_type_id)
				prev_snp = this_snp
			del analysis_method_id2gwr

if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = DrawSNPRegion
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()