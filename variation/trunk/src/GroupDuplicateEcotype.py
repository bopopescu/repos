#!/usr/bin/env python
"""

Examples:
	./src/GroupDuplicateEcotype.py -u yh -c

Description:
	program to 
	1. group duplicates, map all dupicated ecotpe ids to one target ecotype id. Upon determining which duplicate
		becomes target ecotype, precedence is given to ecotypes with data, GPS info, etc.
	2. find out ecotypes who have all-NA genotypes, are not genotyped or have no GPS data associated.
	3. create database tables/views to store findings above.
	
	2009-9-22 Note: truncate 3 tables (genotyping_all_na_ecotype_table, nativename_stkparent2tg_ecotypeid_table, ecotype_duplicate2tg_ecotypeid_table) 
		if overhaul is needed.
"""

import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
if bit_number>40:       #64bit
	sys.path.insert(0, os.path.expanduser('~/lib64/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script64/')))
else:   #32bit
	sys.path.insert(0, os.path.expanduser('~/lib/python'))
	sys.path.insert(0, os.path.join(os.path.expanduser('~/script/')))

import psycopg2, sys, getopt, csv, re
import Numeric as num
from sets import Set
from StockDB import StockDB, SNPs, Strain, Calls, Calls_BySeq, Ecotype

class GroupDuplicateEcotype(object):
	__doc__ = __doc__
	option_default_dict = {('drivername', 1,):['mysql', 'v', 1, 'which type of database? mysql or postgres', ],\
							('hostname', 1, ):['papaya.usc.edu', 'z', 1, 'hostname of the db server', ],\
							('dbname', 1, ):['stock', 'd', 1, '',],\
							('schema', 0, ): [None, 'k', 1, 'database schema name', ],\
							('db_user', 1, ):[None, 'u', 1, 'database username',],\
							('db_passwd',1, ):[None, 'p', 1, 'database password', ],\
							('genotyping_all_na_ecotype_table',1, ): ['genotyping_all_na_ecotype', 'n', 1, 'Table to hold ecotypes with all NA genotypes.'],\
							('no_genotyping_ecotype_view_name',1, ): ['view_no_genotyping_ecotype', 'o', 1, 'name for the view to look at ecotypes not genotyped (different from all-NA genotype).'],\
							('no_gps_ecotype_view_name',1, ): ['view_no_gps_ecotype', 's', 1, 'view the genotypes with no GPS data'],\
							('nativename_stkparent2tg_ecotypeid_table', 1, ): ['nativename_stkparent2tg_ecotypeid', 'a', 1, 'Table to map (nativename, stockparent) to tg_ecotypeid'],\
							('ecotype_duplicate2tg_ecotypeid_table', 1, ): ['ecotypeid_strainid2tg_ecotypeid', 't', 1, 'Table to map ecotypeid to tg_ecotypeid'],\
							('commit',0, int): [0, 'c', 0, 'commit db transaction. 2008-08-11 raw sql thru StockDB.metadata.bind, no transaction.'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
							#('ecotypeid2duplicate_view_name',1, ): ['view_ecotypeid2duplicate', 'y', 1, 'a view'],\
							#('ecotype_table', 1, ): ['ecotype', 'e', 1, "not ecotype because ecotype_usc has new entries."],\
	def __init__(self, **keywords):
		"""
		2008-05-15
		"""
		from pymodule import ProcessOptions
		self.ad = ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
	

	def createEcotypeid2duplicate_view(db, ecotypeid2duplicate_view_name):
		"""
		2008-08-11
			use StockDB
			useless
		2007-10-22
		"""
		sys.stderr.write( "Creating %s ..."%ecotypeid2duplicate_view_name)
		db.metadata.bind.execute("create or replace view %s as select distinct ecotypeid, replicate from %s order by ecotypeid, replicate"%(ecotypeid2duplicate_view_name, Calls_BySeq.table.name))
		sys.stderr.write(" Done.\n")
	createEcotypeid2duplicate_view = staticmethod(createEcotypeid2duplicate_view)
	
	def createNoGenotypingEcotypeView(db, no_genotyping_ecotype_view_name):
		"""
		2008-08-11
			use StockDB
		2007-10-22
		"""
		sys.stderr.write( "Creating %s ..."%no_genotyping_ecotype_view_name)
		db.metadata.bind.execute("create or replace view %s as select e.* from %s e where not exists (select e1.id, s.id from %s e1, %s s where s.ecotypeid=e1.id and e1.id=e.id)"%\
					(no_genotyping_ecotype_view_name, Ecotype.table.name, Ecotype.table.name, Strain.table.name))
		sys.stderr.write(" Done.\n")
	createNoGenotypingEcotypeView = staticmethod(createNoGenotypingEcotypeView)
	
	def createNoGPSEcotypeView(db, no_gps_ecotype_view_name):
		"""
		2008-08-11
			use StockDB
		2007-10-22
		"""
		sys.stderr.write( "Creating %s ..."%no_gps_ecotype_view_name)
		db.metadata.bind.execute("create or replace view %s as select e.* from %s e where latitude is null or longitude is null"%\
					(no_gps_ecotype_view_name, Ecotype.table.name))
		sys.stderr.write(" Done.\n")
	createNoGPSEcotypeView = staticmethod(createNoGPSEcotypeView)
	
	def createGenotypingAllNAEcotypeTable(db, table_name='genotyping_all_na_ecotype', commit=0):
		"""
		2008-12-18
			remove 'unsigned' from integer definition of genotyping_all_na_ecotype table
		2008-08-11
			use StockDB
		2007-10-22
			create a table to store all ecotypeid which have been genotyped (in table calls) but all results are NA.
		"""
		sys.stderr.write( "Creating table to record ecotypes with all-NA genotypes ...")
		rows = db.metadata.bind.execute("select distinct s.id, s.ecotypeid, c.allele from %s s, %s c where c.strainid=s.id "%(Strain.table.name, Calls.table.name))
		genotype_run2call_ls = {}
		for row in rows:
			strainid, ecotypeid, call1 = row
			key_pair = (ecotypeid, strainid)
			if key_pair not in genotype_run2call_ls:
				genotype_run2call_ls[key_pair] = []
			genotype_run2call_ls[key_pair].append(call1)
		
		genotyping_all_na_ecotypeid_duplicate_ls = []
		for key_pair, call_ls in genotype_run2call_ls.iteritems():
			if len(call_ls)==1 and (call_ls[0]=='N' or call_ls[0]=='n' or call_ls[0]=='NA'):
				genotyping_all_na_ecotypeid_duplicate_ls.append(key_pair)
		
		if commit:
			db.metadata.bind.execute("create table IF NOT EXISTS %s(id integer primary key auto_increment,\
				ecotypeid	integer,\
				strainid	integer,\
				foreign key (ecotypeid) references ecotype(id) on delete cascade on update cascade,\
				foreign key (strainid) references strain(id) on delete cascade on update cascade) engine=INNODB"%(table_name))
			for key_pair in genotyping_all_na_ecotypeid_duplicate_ls:
				ecotypeid, strainid = key_pair
				db.metadata.bind.execute("insert into %s(ecotypeid, strainid) values (%s, %s)"%(table_name, ecotypeid, strainid))
		sys.stderr.write( "Done.\n")
		return genotyping_all_na_ecotypeid_duplicate_ls, genotype_run2call_ls
	createGenotypingAllNAEcotypeTable = staticmethod(createGenotypingAllNAEcotypeTable)
	
	def get_no_genotyping_ecotypeid_set(db, no_genotyping_ecotype_view_name='no_genotyping_ecotype_view'):
		"""
		2008-08-11
			use StockDB
		"""
		sys.stderr.write( "Getting no_genotyping_ecotypeid_set ...")
		from sets import Set
		no_genotyping_ecotypeid_set = Set()
		rows = db.metadata.bind.execute("select id from %s"%(no_genotyping_ecotype_view_name))
		#rows = curs.fetchall()
		for row in rows:
			no_genotyping_ecotypeid_set.add(row.id)
		sys.stderr.write( "Done.\n")
		return no_genotyping_ecotypeid_set
	get_no_genotyping_ecotypeid_set = staticmethod(get_no_genotyping_ecotypeid_set)
	
	def get_no_gps_ecotypeid_set(db, no_gps_ecotype_view_name='no_gps_ecotype_view'):
		"""
		2008-08-11
			use StockDB
		"""
		sys.stderr.write( "Getting no_gps_ecotypeid_set ... ")
		from sets import Set
		no_gps_ecotypeid_set = Set()
		rows = db.metadata.bind.execute("select id from %s"%(no_gps_ecotype_view_name))
		#rows = curs.fetchall()
		for row in rows:
			no_gps_ecotypeid_set.add(row.id)
		sys.stderr.write( "Done.\n")
		return no_gps_ecotypeid_set
	get_no_gps_ecotypeid_set = staticmethod(get_no_gps_ecotypeid_set)	
	
	def createTableStructureToGroupEcotypeid(db, no_genotyping_ecotypeid_set, no_gps_ecotypeid_set,\
				genotyping_all_na_ecotypeid_duplicate_ls, \
				nativename_stkparent2tg_ecotypeid_table='nativename_stkparent2tg_ecotypeid', \
				ecotype_duplicate2tg_ecotypeid_table='ecotype_duplicate2tg_ecotypeid', commit=0):
		"""
		2008-12-18
			remove 'unsigned' from integer definition of nativename_stkparent2tg_ecotypeid_table
		2008-08-11
			use StockDB
		2008-05-15
			use left outer between table ecotype and ecotypeid2duplicate_view to include all ecotype ids in the result table
			create a view, ecotypeid2tg_ecotypeid to show more info for ecotype_duplicate2tg_ecotypeid_table
		2007-10-22
			map (nativename, stockparent) to an ecotypeid (AKA tg_ecotypeid)
			map all (ecotype,duplicate) to that ecotypeid
		2007-12-16
			mysql is case-insensitive, python is case-sensitive.
			key_pair (nativename, stockparent) should be case-insensitive. like 'Kz-9' and 'KZ-9'
			uppercase nativename and stockparent
		"""
		sys.stderr.write("Getting nativename_stkparent2ecotypeid_duplicate_ls...")
		nativename_stkparent2ecotypeid_duplicate_ls = {}
		ecotypeid2nativename_stockparent = {}
		#2008-05-15 use left outer join
		rows = db.metadata.bind.execute("select e.nativename, e.stockparent, e.id as ecotypeid, s.id from %s e left outer join %s s on s.ecotypeid=e.id order by nativename, stockparent, id"%\
					(Ecotype.table.name, Strain.table.name))
		#rows = curs.fetchall()
		for row in rows:
			nativename, stockparent, ecotypeid, strainid = row
			ecotypeid2nativename_stockparent[ecotypeid] = (nativename, stockparent)	#2007-12-16 before upper()
			nativename = nativename.upper()
			if stockparent:
				stockparent = stockparent.upper()
			key_pair = (nativename, stockparent)
			if key_pair not in nativename_stkparent2ecotypeid_duplicate_ls:
				nativename_stkparent2ecotypeid_duplicate_ls[key_pair] = []
			nativename_stkparent2ecotypeid_duplicate_ls[key_pair].append((ecotypeid, strainid))
		sys.stderr.write("Done.\n")
		
		sys.stderr.write("Constructing nativename_stkparent2tg_ecotypeid ecotype_duplicate2tg_ecotypeid...\n")
		nativename_stkparent2tg_ecotypeid = {}
		ecotype_duplicate2tg_ecotypeid = {}
		from sets import Set
		genotyping_all_na_ecotypeid_duplicate_set = Set(genotyping_all_na_ecotypeid_duplicate_ls)
		no_of_solid_mappings = 0
		no_of_mappings_with_data_but_no_gps = 0
		no_of_mappings_with_gps_but_no_data = 0
		no_of_worst_random_mappings = 0
		for key_pair, ecotypeid_duplicate_ls in nativename_stkparent2ecotypeid_duplicate_ls.iteritems():
			tg_ecotypeid_quality_pair = None
			ecotypeid_ls_with_data_but_no_gps = []
			ecotypeid_ls_with_gps_but_no_data = []
			ecotypeid_duplicate_ls.sort()	#in order, always pick the smaller id first
			for pair in ecotypeid_duplicate_ls:
				if pair[0] not in no_genotyping_ecotypeid_set and pair[0] not in no_gps_ecotypeid_set and pair not in genotyping_all_na_ecotypeid_duplicate_set:
					tg_ecotypeid_quality_pair = (pair[0], 'solid')
					no_of_solid_mappings += 1
					break
				elif pair[0] not in no_genotyping_ecotypeid_set and pair not in genotyping_all_na_ecotypeid_duplicate_set:
					ecotypeid_ls_with_data_but_no_gps.append(pair[0])
				elif pair[0] not in no_gps_ecotypeid_set:
					ecotypeid_ls_with_gps_but_no_data.append(pair[0])
			ecotypeid_ls_with_data_but_no_gps.sort()	#in order, always pick the smaller id first
			ecotypeid_ls_with_gps_but_no_data.sort()	#in order, always pick the smaller id first
			if tg_ecotypeid_quality_pair==None:	#use ecotypeid with data
				if ecotypeid_ls_with_data_but_no_gps:
					tg_ecotypeid_quality_pair = (ecotypeid_ls_with_data_but_no_gps[0], 'with_data_but_no_gps')
					no_of_mappings_with_data_but_no_gps += 1
				elif ecotypeid_ls_with_gps_but_no_data:
					tg_ecotypeid_quality_pair = (ecotypeid_ls_with_gps_but_no_data[0], 'with_gps_but_no_data')
					no_of_mappings_with_gps_but_no_data += 1
				else:
					tg_ecotypeid_quality_pair = (ecotypeid_duplicate_ls[0][0], 'worst_no_gps_no_data')
					no_of_worst_random_mappings += 1
			nativename_stkparent2tg_ecotypeid[key_pair] = tg_ecotypeid_quality_pair
			for pair in ecotypeid_duplicate_ls:
				ecotype_duplicate2tg_ecotypeid[pair] = tg_ecotypeid_quality_pair[0]
		no_of_total_mappings = float(len(nativename_stkparent2tg_ecotypeid))
		sys.stderr.write("\t%s(%s) solid mappings\n"%(no_of_solid_mappings, no_of_solid_mappings/no_of_total_mappings))
		sys.stderr.write("\t%s(%s) mappings_with_data_but_no_gps\n"%(no_of_mappings_with_data_but_no_gps, no_of_mappings_with_data_but_no_gps/no_of_total_mappings))
		sys.stderr.write("\t%s(%s) mappings_with_gps_but_no_data\n"%(no_of_mappings_with_gps_but_no_data, no_of_mappings_with_gps_but_no_data/no_of_total_mappings))
		sys.stderr.write("\t%s(%s) worst_no_gps_no_data_mappings\n"%(no_of_worst_random_mappings, no_of_worst_random_mappings/no_of_total_mappings))
		sys.stderr.write("Done.\n")
		
		
		if commit:
			sys.stderr.write("Submitting to db...")
			db.metadata.bind.execute("create table IF NOT EXISTS %s (id integer primary key auto_increment,\
				nativename	varchar(50),\
				stockparent	varchar(10),\
				tg_ecotypeid	integer,\
				quality	varchar(50),\
				foreign key (tg_ecotypeid) references ecotype(id) on delete cascade on update cascade) engine=INNODB"\
				%(nativename_stkparent2tg_ecotypeid_table))
			for key_pair, tg_ecotypeid_quality_pair in nativename_stkparent2tg_ecotypeid.iteritems():
				tg_ecotypeid, quality = tg_ecotypeid_quality_pair
				nativename, stockparent = ecotypeid2nativename_stockparent[tg_ecotypeid]
				if stockparent==None:
					stockparent='NULL'
				try:
					db.metadata.bind.execute("""insert into %s(nativename, stockparent, tg_ecotypeid, quality) values ("%s", "%s", %s, "%s")"""\
											%(nativename_stkparent2tg_ecotypeid_table, nativename, stockparent, tg_ecotypeid, quality))
				except:
					import traceback
					traceback.print_exc()
					print sys.exc_info()
					import pdb
					pdb.set_trace()
			
			db.metadata.bind.execute("create table IF NOT EXISTS %s(id integer primary key auto_increment,\
				ecotypeid integer unsigned,\
				strainid integer,\
				tg_ecotypeid integer unsigned,\
				foreign key (ecotypeid) references ecotype(id) on delete cascade on update cascade,\
				foreign key (tg_ecotypeid) references ecotype(id) on delete cascade on update cascade,\
				foreign key (strainid) references strain(id) on delete cascade on update cascade) engine=INNODB"\
				%(ecotype_duplicate2tg_ecotypeid_table))
			
			for pair, tg_ecotypeid in ecotype_duplicate2tg_ecotypeid.iteritems():
				ecotypeid, strainid = pair
				if strainid==None:	#2008-05-15
					strainid = 'NULL'
				db.metadata.bind.execute("insert into %s(ecotypeid, strainid, tg_ecotypeid) values (%s, %s, %s)"%\
							(ecotype_duplicate2tg_ecotypeid_table, ecotypeid, strainid, tg_ecotypeid))
			#2008-05-15
			db.metadata.bind.execute("create or replace view ecotypeid2tg_ecotypeid as select distinct e.id  as ecotypeid, \
				e.name, e.alias, e.nativename, e.stockparent, e2.strainid, e2.tg_ecotypeid from %s e, %s e2 where e.id=e2.ecotypeid order by ecotypeid"%\
						(Ecotype.table.name, ecotype_duplicate2tg_ecotypeid_table))
			sys.stderr.write("Done.\n")
		return nativename_stkparent2ecotypeid_duplicate_ls, nativename_stkparent2tg_ecotypeid, ecotype_duplicate2tg_ecotypeid
	createTableStructureToGroupEcotypeid = staticmethod(createTableStructureToGroupEcotypeid)
	
	def run(self):
		"""
		2008-05-15
		"""
		if self.debug:
			import pdb
			pdb.set_trace()
		"""
		import MySQLdb
		conn = MySQLdb.connect(db=self.dbname, host=self.hostname, user = self.user, passwd = self.passwd)
		curs = conn.cursor()
		"""
		db = StockDB(drivername=self.drivername, username=self.db_user,
				   password=self.db_passwd, hostname=self.hostname, database=self.dbname, schema=self.schema)
		db.setup(create_tables=False)
		session = db.session
		session.begin()
		
		#self.createEcotypeid2duplicate_view(db, self.ecotypeid2duplicate_view_name)
		
		self.createNoGenotypingEcotypeView(db, self.no_genotyping_ecotype_view_name)
		
		self.createNoGPSEcotypeView(db, self.no_gps_ecotype_view_name)
		
		genotyping_all_na_ecotypeid_duplicate_ls, genotype_run2call_ls = self.createGenotypingAllNAEcotypeTable(db, \
			table_name=self.genotyping_all_na_ecotype_table, commit=self.commit)
		
		no_genotyping_ecotypeid_set = self.get_no_genotyping_ecotypeid_set(db, no_genotyping_ecotype_view_name=self.no_genotyping_ecotype_view_name)
		
		no_gps_ecotypeid_set = self.get_no_gps_ecotypeid_set(db, no_gps_ecotype_view_name=self.no_gps_ecotype_view_name)
		
		nativename_stkparent2ecotypeid_duplicate_ls, nativename_stkparent2tg_ecotypeid, ecotype_duplicate2tg_ecotypeid = \
		self.createTableStructureToGroupEcotypeid(db, no_genotyping_ecotypeid_set, no_gps_ecotypeid_set, \
												genotyping_all_na_ecotypeid_duplicate_ls, \
												nativename_stkparent2tg_ecotypeid_table=self.nativename_stkparent2tg_ecotypeid_table, \
												ecotype_duplicate2tg_ecotypeid_table=self.ecotype_duplicate2tg_ecotypeid_table, \
												commit=self.commit)
		if self.commit:
			session.flush()
			session.commit()
			session.clear()
		else:	#default is also rollback(). to demonstrate good programming
			session.rollback()

def get_ecotypeid2duplicate_times(curs, stock_db, ecotypeid2duplicate_view_name='ecotypeid2duplicate_view'):
	"""
	2007-10-23
		not finished yet
	"""
	curs.execute("select ecotypeid, count(duplicate) from %s.%s group by ecotypeid"%(stock_db, ecotypeid2duplicate_view_name))


def get_nn_sp_duplicated_time2ecotype_duplicate_ls_ls(nativename_stkparent2ecotypeid_duplicate_ls):
	"""
	2007-10-23
	"""
	nn_sp_duplicated_time2ecotype_duplicate_ls_ls = {}
	for nativename_stkparent, ecotypeid_duplicate_ls in nativename_stkparent2ecotypeid_duplicate_ls.iteritems():
		nn_sp_duplicated_time = len(ecotypeid_duplicate_ls)
		if nn_sp_duplicated_time not in nn_sp_duplicated_time2ecotype_duplicate_ls_ls:
			nn_sp_duplicated_time2ecotype_duplicate_ls_ls[nn_sp_duplicated_time] = []
		nn_sp_duplicated_time2ecotype_duplicate_ls_ls[nn_sp_duplicated_time].append(ecotypeid_duplicate_ls)
	return nn_sp_duplicated_time2ecotype_duplicate_ls_ls

def convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(nn_sp_duplicated_time2ecotype_duplicate_ls_ls):
	"""
	2007-10-23
	"""
	nn_sp_duplicated_time_ls = nn_sp_duplicated_time2ecotype_duplicate_ls_ls.keys()
	nn_sp_duplicated_time_ls.sort()
	nn_sp_duplicated_time2index = {}
	import numpy
	m = numpy.zeros([len(nn_sp_duplicated_time_ls), 2], numpy.integer)
	for i in range(len(nn_sp_duplicated_time_ls)):
		nn_sp_duplicated_time = nn_sp_duplicated_time_ls[i]
		m[i,0] = nn_sp_duplicated_time
		m[i,1] = len(nn_sp_duplicated_time2ecotype_duplicate_ls_ls[nn_sp_duplicated_time])
		nn_sp_duplicated_time2index[nn_sp_duplicated_time] = i
	return m, nn_sp_duplicated_time2index

def get_nn_sp_duplicated_time_cross_another_set(nn_sp_duplicated_time2ecotype_duplicate_ls_ls, nn_sp_duplicated_time2index, set_to_be_intersected=None, is_ecotypeid_duplicate_pair_in_set=0):
	"""
	2007-10-23
	"""
	import numpy
	x_dim = len(nn_sp_duplicated_time2index)
	y_dim = max(nn_sp_duplicated_time2index.keys())	#the possible maximum number of occcurrences
	m = numpy.zeros([x_dim, y_dim], numpy.integer)
	new_ecotype_duplicate_ls_ls = []	#list of nn_sp_duplicated_time2ecotype_duplicate_ls_ls.values() - those in the set_to_be_intersected
	for nn_sp_duplicated_time, ecotype_duplicate_ls_ls in nn_sp_duplicated_time2ecotype_duplicate_ls_ls.iteritems():
		key2times = {}
		for ecotypeid_duplicate_ls in ecotype_duplicate_ls_ls:
			new_ecotype_duplicate_ls = []
			for ecotypeid_duplicate in ecotypeid_duplicate_ls:
				if is_ecotypeid_duplicate_pair_in_set:	#set_key might be (ecotypeid, duplicate) or just ecotypeid
					set_key = ecotypeid_duplicate
				else:
					set_key = ecotypeid_duplicate[0]
				if set_to_be_intersected:	#if intersected (either no gps, or all-NA), shall be removed
					if set_key not in set_to_be_intersected:
						new_ecotype_duplicate_ls.append(ecotypeid_duplicate)
						continue
				key = ecotypeid_duplicate[0]	#this is always ecotypeid
				if key not in key2times:
					key2times[key] = 0
				key2times[key] += 1
			new_ecotype_duplicate_ls_ls.append(new_ecotype_duplicate_ls)
		times2key_ls = {}
		for key, times in key2times.iteritems():
			if times not in times2key_ls:
				times2key_ls[times] = []
			times2key_ls[times].append(key)
		x_index = nn_sp_duplicated_time2index[nn_sp_duplicated_time]
		for times, key_ls in times2key_ls.iteritems():
			y_index = times-1
			m[x_index, y_index] = len(key_ls)
	reduced_nn_sp_duplicated_time2ecotype_duplicate_ls_ls = {}
	for ecotype_duplicate_ls in new_ecotype_duplicate_ls_ls:
		nn_sp_duplicated_time = len(ecotype_duplicate_ls)
		if nn_sp_duplicated_time not in reduced_nn_sp_duplicated_time2ecotype_duplicate_ls_ls:
			reduced_nn_sp_duplicated_time2ecotype_duplicate_ls_ls[nn_sp_duplicated_time] = []
		reduced_nn_sp_duplicated_time2ecotype_duplicate_ls_ls[nn_sp_duplicated_time].append(ecotype_duplicate_ls)
	
	return m, reduced_nn_sp_duplicated_time2ecotype_duplicate_ls_ls


"""
2007-10-22
functions to understand the duplication structure inside the database

hostname='localhost'
dbname='stock20071008'
dbname = 'stock'
import MySQLdb
conn = MySQLdb.connect(db=dbname,host=hostname)
curs = conn.cursor()
stock_db = dbname
createEcotypeid2duplicate_view(curs, stock_db)

createNoGenotypingEcotypeView(curs, stock_db)

createNoGPSEcotypeView(curs, stock_db)

genotyping_all_na_ecotypeid_duplicate_ls, genotype_run2call_ls = createGenotypingAllNAEcotypeTable(curs, stock_db, \
	table_name='genotyping_all_na_ecotype', commit=1)

no_genotyping_ecotypeid_set = get_no_genotyping_ecotypeid_set(curs, stock_db, no_genotyping_ecotype_view_name='no_genotyping_ecotype_view')

no_gps_ecotypeid_set = get_no_gps_ecotypeid_set(curs, stock_db, no_gps_ecotype_view_name='no_gps_ecotype_view')

nativename_stkparent2ecotypeid_duplicate_ls, nativename_stkparent2tg_ecotypeid, ecotype_duplicate2tg_ecotypeid = \
createTableStructureToGroupEcotypeid(curs, stock_db, no_genotyping_ecotypeid_set, no_gps_ecotypeid_set, \
genotyping_all_na_ecotypeid_duplicate_ls, ecotypeid2duplicate_view_name='ecotypeid2duplicate_view', \
nativename_stkparent2tg_ecotypeid_table='nativename_stkparent2tg_ecotypeid', \
ecotype_duplicate2tg_ecotypeid_table='ecotype_duplicate2tg_ecotypeid', commit=1)


##2007-10-23 to output tables
output_fname = 'script/variation/doc/paper/tables_figures.tex'
outf = open(output_fname, 'w')
nn_sp_duplicated_time2ecotype_duplicate_ls_ls = get_nn_sp_duplicated_time2ecotype_duplicate_ls_ls(nativename_stkparent2ecotypeid_duplicate_ls)

nn_sp_m, nn_sp_duplicated_time2index = convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(nn_sp_duplicated_time2ecotype_duplicate_ls_ls)

##cross nn_sp_duplicated_time2ecotype_duplicate_ls_ls to no set. just count how many duplicated ecotypeid's
m_X_ecotypeid_duplicated_times, useless_dict = get_nn_sp_duplicated_time_cross_another_set(nn_sp_duplicated_time2ecotype_duplicate_ls_ls, nn_sp_duplicated_time2index, set_to_be_intersected=None, is_ecotypeid_duplicate_pair_in_set=0)


##cross nn_sp_duplicated_time2ecotype_duplicate_ls_ls to sets of ecotypeid_duplicate with all-NA data
##reorganize nn_sp_duplicated_time2ecotype_duplicate_ls_ls
from sets import Set
m_X_genotyping_all_na_ecotypeid_duplicate_ls, reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls= get_nn_sp_duplicated_time_cross_another_set(nn_sp_duplicated_time2ecotype_duplicate_ls_ls, nn_sp_duplicated_time2index, set_to_be_intersected=Set(genotyping_all_na_ecotypeid_duplicate_ls), is_ecotypeid_duplicate_pair_in_set=1)

#convert the reorganized nn_sp_duplicated_time2ecotype_duplicate_ls_ls into matrix
reduced_1_m, reduced_1_nn_sp_duplicated_time2index = convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls)


##cross nn_sp_duplicated_time2ecotype_duplicate_ls_ls to no-gps-ecotypeid set
m_X_no_gps_duplicated_times, reduced_2_nn_sp_duplicated_time2ecotype_duplicate_ls_ls = get_nn_sp_duplicated_time_cross_another_set(nn_sp_duplicated_time2ecotype_duplicate_ls_ls, nn_sp_duplicated_time2index, set_to_be_intersected=no_gps_ecotypeid_set, is_ecotypeid_duplicate_pair_in_set=0)

#convert the reorganized nn_sp_duplicated_time2ecotype_duplicate_ls_ls into matrix
reduced_2_m, reduced_2_nn_sp_duplicated_time2index = convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(reduced_2_nn_sp_duplicated_time2ecotype_duplicate_ls_ls)


from pymodule.latex import outputMatrixInLatexTable
import numpy
t1 = numpy.concatenate([nn_sp_m, m_X_ecotypeid_duplicated_times, m_X_genotyping_all_na_ecotypeid_duplicate_ls, m_X_no_gps_duplicated_times], 1)
caption = ' Cross (nativename,stkparent) to ecotypeid duplicated times, ecotypeid-with-all-NA,  ecotypeid-with-no-gps'
table_label = 't_nn_sp_e_1'
header_ls = [(2,'nativename stkparent'),(m_X_ecotypeid_duplicated_times.shape[1], 'ecotypeid duplicate'), (m_X_genotyping_all_na_ecotypeid_duplicate_ls.shape[1], 'ecotypeid-with-all-NA'), (m_X_no_gps_duplicated_times.shape[1], 'ecotypeid-with-no-gps')]
outf.write(outputMatrixInLatexTable(t1, caption, table_label, header_ls))
outf.flush()



caption = ' (nativename,stkparent) duplicates after ecotypeid-with-all-NA removal'
table_label = 't_nn_sp_e_2'
header_ls = [(2,'nativename stkparent')]
outf.write(outputMatrixInLatexTable(reduced_1_m, caption, table_label, header_ls))
outf.flush()

caption = ' (nativename,stkparent) duplicates after ecotypeid-with-no-gps removal'
table_label = 't_nn_sp_e_3'
header_ls = [(2,'nativename stkparent')]
outf.write(outputMatrixInLatexTable(reduced_2_m, caption, table_label, header_ls))
outf.flush()

####optional here. if 0 is not removed, codes in next block still run
##delete the values with 0 ecotypeid_duplicate associated
del reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls[0]
##convert the reorganized nn_sp_duplicated_time2ecotype_duplicate_ls_ls into matrix
reduced_1_m, reduced_1_nn_sp_duplicated_time2index = convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls)


#cross reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls to no set. just count how many duplicated ecotypeid's
reduced_1_m_X_ecotypeid_duplicated_times, useless_dict = get_nn_sp_duplicated_time_cross_another_set(reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls, reduced_1_nn_sp_duplicated_time2index, set_to_be_intersected=None, is_ecotypeid_duplicate_pair_in_set=0)

##cross reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls to no-gps-ecotypeid set
reduced_1_m_X_no_gps_duplicated_times, reduced_11_nn_sp_duplicated_time2ecotype_duplicate_ls_ls = get_nn_sp_duplicated_time_cross_another_set(reduced_1_nn_sp_duplicated_time2ecotype_duplicate_ls_ls, reduced_1_nn_sp_duplicated_time2index, set_to_be_intersected=no_gps_ecotypeid_set, is_ecotypeid_duplicate_pair_in_set=0)

t4 = numpy.concatenate([reduced_1_m, reduced_1_m_X_ecotypeid_duplicated_times, reduced_1_m_X_no_gps_duplicated_times], 1)
caption = ' (nativename,stkparent) duplicates after ecotypeid-with-all-NA removal, cross it to ecotypeid duplicated times, ecotypeid-with-no-gps'
table_label = 't_nn_sp_e_4'
header_ls = [(2,'nativename stkparent all-NA removal'), (reduced_1_m_X_ecotypeid_duplicated_times.shape[1], 'ecotypeid duplicate'), (reduced_1_m_X_no_gps_duplicated_times.shape[1], 'ecotypeid-with-no-gps')]
outf.write(outputMatrixInLatexTable(t4, caption, table_label, header_ls))
outf.flush()

#convert the reorganized nn_sp_duplicated_time2ecotype_duplicate_ls_ls into matrix
reduced_11_m, reduced_11_nn_sp_duplicated_time2index = convert_nn_sp_duplicated_time2ecotype_duplicate_ls_ls_2matrix(reduced_11_nn_sp_duplicated_time2ecotype_duplicate_ls_ls)


caption = ' (nativename,stkparent) duplicates after all-NA and no-gps removal'
table_label = 't_nn_sp_e_5'
header_ls = [(2,'nativename stkparent')]
outf.write(outputMatrixInLatexTable(reduced_11_m, caption, table_label, header_ls))
outf.flush()



####final table
#no_genotyping_ecotypeid_set
#no_gps_ecotypeid_set

genotyping_all_na_ecotypeid_duplicate_set = Set(genotyping_all_na_ecotypeid_duplicate_ls)
genotyping_all_na_ecotypeid_ls = [row[0] for row in genotyping_all_na_ecotypeid_duplicate_ls]
genotyping_all_na_ecotypeid_set = Set(genotyping_all_na_ecotypeid_ls)
m = numpy.zeros([1,8], numpy.integer)

header_ls = ['all-NA runs', 'all-NA ecotypeid', 'no-genotyping', 'no-gps', 'all-NA and no-genotyping', 'all-NA and no-gps', 'no-genotyping and no-gps', 'intersect all 3']
m[0,0] = len(genotyping_all_na_ecotypeid_duplicate_set)
m[0,1] = len(genotyping_all_na_ecotypeid_set)
m[0,2] = len(no_genotyping_ecotypeid_set)
m[0,3] = len(no_gps_ecotypeid_set)
m[0,4] = len(genotyping_all_na_ecotypeid_set&no_genotyping_ecotypeid_set)
m[0,5] = len(genotyping_all_na_ecotypeid_set&no_gps_ecotypeid_set)
m[0,6] = len(no_genotyping_ecotypeid_set&no_gps_ecotypeid_set)
m[0,7] = len(genotyping_all_na_ecotypeid_set&no_genotyping_ecotypeid_set&no_gps_ecotypeid_set)

caption = 'overlapping between all weirdos'
table_label = 't_nn_sp_e_6'
outf.write(outputMatrixInLatexTable(m, caption, table_label, header_ls))
outf.flush()

"""
if __name__ == '__main__':
	from pymodule import ProcessOptions
	main_class = GroupDuplicateEcotype
	po = ProcessOptions(sys.argv, main_class.option_default_dict, error_doc=main_class.__doc__)
	
	instance = main_class(**po.long_option2value)
	instance.run()
	
	