#!/usr/bin/env python
"""
2008-04-28
A wrapper on top of sqlalchemy around a database. Mostly copied from collective.lead.Database. Can't directly use it because
of trouble in understanding how to use adapter involved in TreadlocalDatabaseTransactions.
"""
import sys, os, math
bit_number = math.log(sys.maxint)/math.log(2)
#if bit_number>40:       #64bit
sys.path.insert(0, os.path.expanduser('~/lib/python'))
sys.path.insert(0, os.path.join(os.path.expanduser('~/script')))

import sqlalchemy, threading
from sqlalchemy.engine.url import URL
from sqlalchemy import Table
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker

class TableClass(object):
	"""
	2008-05-03
		a base class for any class to hold a db table.
		to assign (key, value) to a class corresponding to a table
	"""
	def __init__(self, **keywords):
		for key, value in keywords.iteritems():
			setattr(self, key, value)


class Database(object):
	__doc__ = __doc__
	option_default_dict = {('v', 'drivername', 1, '', 1, ):'mysql',\
							('z', 'hostname', 1, '', 1, ):'papaya.usc.edu',\
							('d', 'database',1, '', 1, ):None,\
							('k', 'schema',0, '', 1, ):None,\
							('u', 'username',1, '', 1, ):None,\
							('p', 'password',1, '', 1, ):None,\
							('o', 'port', 1, '', 0, ):None,\
							('c', 'commit', 0, '', 0, int):0,\
							('b', 'debug', 0, '', 0, int):0,\
							('r', 'report', 0, '', 0, int):0}
	"""
	2008-02-28
		argument_default_dict is a dictionary of default arguments, the key is a tuple, ('argument_name', is_argument_required, argument_type)
		argument_type is optional
	"""
	def __init__(self, **keywords):
		from pymodule import process_function_arguments, turn_option_default_dict2argument_default_dict
		argument_default_dict = turn_option_default_dict2argument_default_dict(self.option_default_dict)
		self.ad = process_function_arguments(keywords, argument_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		
		self._threadlocal = threading.local()
		self.tables = {}
		self.mappers = {}
		self._engine = None
		
	#@property
	def _url(self):
		return URL(drivername=self.drivername, username=self.username,
				   password=self.password, host=self.hostname,
				   port=self.port, database=self.database)
	_url = property(_url)
	
	def _setup_tables(self, metadata, tables):
		"""Map the database structure to SQLAlchemy Table objects
		"""
		"""
		tables['call_QC'] = Table('call_QC', metadata, autoload=True)
		"""
		pass
	
	def _setup_mappers(self, tables, mappers):
		"""Map the database Tables to SQLAlchemy Mapper objects
		"""
		"""
		mappers['call_QC'] = mapper(Call_QC, tables['call_QC'], properties={'call_info_obj': relation(Call_Info),\
																		'qc_method_obj':relation(QCMethod)})
		"""
		pass
	
	#@property
	def _engine_properties(self):
		return {}
	_engine_properties = property(_engine_properties)
	
	def invalidate(self):
		self._initialize_engine()
		
	# IDatabase implementation - code using (not setting up) the database
	# uses this
	
	#@property
	def session(self):
		"""
		2008-07-09
			use the new sessionmaker() in version 0.4 to create Session
			use scoped_session to create a thread-local context
		"""
		if getattr(self._threadlocal, 'session', None) is None:
			# Without this, we may not have mapped things properly, nor
			# will we necessarily start a transaction when the client
			# code begins to use the session.
			ignore = self.engine
			Session = scoped_session(sessionmaker(autoflush=True, transactional=True, bind=self.engine))
			self._threadlocal.session = Session()
		return self._threadlocal.session
	session = property(session)
	
	#@property
	def connection(self):
		return self.engine.contextual_connect()
	connection = property(connection)
	
	#@property
	def engine(self):
		if self._engine is None:
			self._initialize_engine()
		
		return self._engine
	engine = property(engine)
	
	# Helper methods
	
	def _initialize_engine(self):
		"""
		metadata.create_all()	#2008-07-09 create all tables
		2008-07-09
			close and reset the old session if self._threadlocal.session is not None
			change  self._metadata to metadata in "self.tables[name] = table.tometadata(metadata)"
		2008-07-08
			for postgres, set the schema	(doesn't work)
		"""
		kwargs = dict(self._engine_properties).copy()
		if 'strategy' not in kwargs:
			kwargs['strategy'] = 'threadlocal'
		if 'convert_unicode' not in kwargs:
			kwargs['convert_unicode'] = True
		
		engine = sqlalchemy.create_engine(self._url, **kwargs)
		metadata = sqlalchemy.MetaData(engine)
		
		if getattr(self._threadlocal, 'session', None) is not None:	#2008-07-09 close and reset the old session
			self._threadlocal.session.close()
			self._threadlocal.session = None
		"""
		if getattr(self, 'schema', None):	#2008-07-08 for postgres, set the schema, doesn't help. specify "schema=" in Table()
			con = engine.connect()
			con.execute("set search_path to %s"%self.schema)
			#sys.stderr.write('set schema')
			metadata.bind = con	#necessary. otherwise, schema is still not set.
		"""
		
		# We will only initialize once, but we may rebind metadata if
		# necessary

		if not self.tables:
			self._setup_tables(metadata, self.tables)
			metadata.create_all()	#2008-07-09 create all tables
			self._setup_mappers(self.tables, self.mappers)
		else:
			for name, table in self.tables.items():
				self.tables[name] = table.tometadata(metadata)	#2008-07-09 change self._metadata to metadata
		
		self._engine = engine
		self._metadata = metadata

class ElixirDB(object):
	"""
	2008-08-07
		expose metadata from elixir
	2008-07-11
		elixir db base class
	"""
	option_default_dict = {('drivername', 1,):['postgres', 'v', 1, 'which type of database? mysql or postgres', ],\
							('hostname', 1, ):['localhost', 'z', 1, 'hostname of the db server', ],\
							('database', 1, ):[None, 'd', 1, '',],\
							('schema', 0, ): [None, 'k', 1, 'database schema name', ],\
							('username', 1, ):[None, 'u', 1, 'database username',],\
							('password', 1, ):[None, 'p', 1, 'database password', ],\
							('port', 0, ):[None, 'o', 1, 'database port number'],\
							('commit',0, int): [0, 'c', 0, 'commit db transaction'],\
							('debug', 0, int):[0, 'b', 0, 'toggle debug mode'],\
							('report', 0, int):[0, 'r', 0, 'toggle report, more verbose stdout/stderr.']}
	from elixir import metadata	#2008-08-07
	metadata = metadata
	def __init__(self, **keywords):
		"""
		2008-07-09
		"""
		from pymodule import ProcessOptions
		ProcessOptions.process_function_arguments(keywords, self.option_default_dict, error_doc=self.__doc__, class_to_have_attr=self)
		
		from elixir import setup_all, metadata, entities
		if getattr(self, 'schema', None):	#for postgres
			for entity in entities:
				using_table_options_handler(entity, schema=self.schema)
		
		metadata.bind = self._url
		setup_all(create_tables=True)	#create_tables=True causes setup_all to call elixir.create_all(), which in turn calls metadata.create_all()
	
	def _url(self):
		return URL(drivername=self.drivername, username=self.username,
				   password=self.password, host=self.hostname,
				   port=self.port, database=self.database)
	_url = property(_url)
	
	def session(self):
		"""
		2008-07-09
		"""
		from elixir import session
		return session
	session = property(session)
	
	def connection(self):
		return self.session.connection
	connection = property(connection)

from elixir import Entity, Field, using_options, using_table_options
from elixir import DateTime, String
from datetime import datetime
class ElixirREADME(Entity):
	"""
	2008-08-07
	"""
	title = Field(String(2000))
	description = Field(String(60000))
	created_by = Field(String(128))
	updated_by = Field(String(128))
	date_created = Field(DateTime, default=datetime.now)
	date_updated = Field(DateTime)
	using_options(tablename='readme')
	using_table_options(mysql_engine='InnoDB')

def formReadmeObj(argv, ad, READMEClass):
	"""
	2008-05-06
		create a readme instance (like a log) based on the program's sys.argv and argument dictionary
	"""
	readme_description_ls = []
	argument_ls = ad.keys()
	argument_ls.sort()
	for argument in argument_ls:
		if argument=='passwd' or argument=='password':	#password info not into db
			continue
		value = ad[argument]
		readme_description_ls.append('%s=%s'%(argument, value))
	readme = READMEClass(title=' '.join(argv), description='; '.join(readme_description_ls))
	return readme

def db_connect(hostname, dbname, schema=None, password=None, user=None):
	"""
	2008-07-29
		copied from annot.bin.codense.common
		add the code to deal with importing psycopg
	2007-03-07
		add password and user two options
	02-28-05
		establish database connection, return (conn, curs).
		copied from CrackSplat.py
	03-08-05
		parameter schema is optional
	"""
	connection_string = 'host=%s dbname=%s'%(hostname, dbname)
	if password:
		connection_string += ' password=%s'%password
	if user:
		connection_string += ' user=%s'%user
	
	try:
		import psycopg
	except ImportError:
		try:
			import psycopg2 as psycopg
		except ImportError:
			sys.stderr.write("Neither psycopg nor psycopg2 is installed.\n")
			raise
	conn = psycopg.connect(connection_string)
	curs = conn.cursor()
	if schema:
		curs.execute("set search_path to %s"%schema)
	return (conn, curs)

if __name__ == '__main__':
	from pymodule import process_options, generate_program_doc
	main_class = Database
	opts_dict = process_options(sys.argv, main_class.option_default_dict, error_doc=generate_program_doc(sys.argv[0], main_class.option_default_dict)+main_class.__doc__)
	
	"""
	
	#from /usr/lib/python2.5/site-packages/zope/interface/adapter.txt
	from zope.interface.adapter import AdapterRegistry
	registry = AdapterRegistry()
	registry.register([Database], ITransactionAware, '', 12)
	
	from zope.component import registry
	from zope.component import tests
	components = registry.Components('comps')
	
	#from /usr/lib/zope2.10/lib/python/zope/, interface/ component/registry.txt
	print components.registerAdapter(TreadlocalDatabaseTransactions)
	print components.getAdapter(ITransactionAware, Database)
	"""
	instance = main_class(**opts_dict)
	if instance.debug:
		import pdb
		pdb.set_trace()
	session = instance.session
	print dir(session.query(Results))
	
	for row in session.query(ResultsMethod).list():
		print row.id
		print row.short_name
	
	i = 0
	while i <10:
		row = session.query(Results).offset(i).limit(1).list()	#all() = list() returns a list of objects. first() returns the 1st object. one() woud raise error because 'Multiple rows returned for one()'
		print len(row)
		row = row[0]
		i += 1
		print row.id
		print row.chr
		print row.start_pos
		print row.score
		print row.method_id
		print row.results_method_obj.short_name
		print row.phenotype_method_id
		print row.phenotype_method_obj.short_name
