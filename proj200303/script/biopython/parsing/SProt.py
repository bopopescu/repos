# Copyright 1999 by Jeffrey Chang.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""SProt.py

This module provides code to work with the sprotXX.dat file from
SwissProt.
http://www.expasy.ch/sprot/sprot-top.html

Tested with:
Release 37, Release 38, Release 39


Classes:
Record             Holds SwissProt data.
Reference          Holds reference data from a SwissProt entry.
Iterator           Iterates over entries in a SwissProt file.
Dictionary         Accesses a SwissProt file using a dictionary interface.
ExPASyDictionary   Accesses SwissProt records from ExPASy.
RecordParser       Parses a SwissProt record into a Record object.
SequenceParser     Parses a SwissProt record into a Seq object.

_Scanner           Scans SwissProt-formatted data.
_RecordConsumer    Consumes SwissProt data to a Record object.
_SequenceConsumer  Consumes SwissProt data to a Seq object.


Functions:
index_file         Index a SwissProt file for a Dictionary.

"""
from types import *
import os
import string
from Bio import File
from Bio import Index
from Bio import Alphabet
from Bio import Seq
from Bio import SeqRecord
from Bio.ParserSupport import *
from Bio.WWW import ExPASy
from Bio.WWW import RequestLimiter

class Record:
    """Holds information from a SwissProt record.

    Members:
    entry_name        Name of this entry, e.g. RL1_ECOLI.
    data_class        Either 'STANDARD' or 'PRELIMINARY'.
    molecule_type     Type of molecule, 'PRT',
    sequence_length   Number of residues.

    accessions        List of the accession numbers, e.g. ['P00321']
    created           A tuple of (date, release).
    sequence_update   A tuple of (date, release).
    annotation_update A tuple of (date, release).

    description       Free-format description.
    gene_name         Gene name.  See userman.txt for description.
    organism          The source of the sequence.
    organelle         The origin of the sequence.
    organism_classification  The taxonomy classification.  List of strings.
                             (http://www.ncbi.nlm.nih.gov/Taxonomy/)
    taxonomy_id       A list of NCBI taxonomy id's.
    references        List of Reference objects.
    comments          List of strings.
    cross_references  List of tuples (db, id1[, id2][, id3]).  See the docs.
    keywords          List of the keywords.
    features          List of tuples (key name, from, to, description).
                      from and to can be either integers for the residue
                      numbers, '<', '>', or '?'

    seqinfo           tuple of (length, molecular weight, CRC32 value)
    sequence          The sequence.
    
    """
    def __init__(self):
    	# added by hy
    	self.fasta = ''
	# added by hy
        self.entry_name = None
        self.data_class = None
        self.molecule_type = None
        self.sequence_length = None
        
        self.accessions = []
        self.created = None
        self.sequence_update = None
        self.annotation_update = None
        
        self.description = ''
        self.gene_name = ''
        self.organism = ''
        self.organelle = ''
        self.organism_classification = []
        self.taxonomy_id = []
        self.references = []
        self.comments = []
        self.cross_references = []
        self.keywords = []
        self.features = []
        
        self.seqinfo = None
        self.sequence = ''

class Reference:
    """Holds information from 1 references in a SwissProt entry.

    Members:
    number      Number of reference in an entry.
    positions   Describes extent of work.  list of strings.
    comments    Comments.  List of (token, text).
    references  References.  List of (dbname, identifier)
    authors     The authors of the work.
    title       Title of the work.
    location    A citation for the work.
    
    """
    def __init__(self):
        self.number = None
        self.positions = []
        self.comments = []
        self.references = []
        self.authors = ''
        self.title = ''
        self.location = ''

class Iterator:
    """Returns one record at a time from a SwissProt file.

    Methods:
    next   Return the next record from the stream, or None.

    """
    def __init__(self, handle, parser=None):
        """__init__(self, handle, parser=None)

        Create a new iterator.  handle is a file-like object.  parser
        is an optional Parser object to change the results into another form.
        If set to None, then the raw contents of the file will be returned.

        """
        if type(handle) is not FileType and type(handle) is not InstanceType:
            raise ValueError, "I expected a file handle or file-like object"
        self._uhandle = File.UndoHandle(handle)
        self._parser = parser

    def next(self):
        """next(self) -> object

        Return the next swissprot record from the file.  If no more records,
        return None.

        """
        lines = []
        while 1:
            line = self._uhandle.readline()
            if not line:
                break
            lines.append(line)
            if line[:2] == '//':
                break
            
        if not lines:
            return None
            
        data = string.join(lines, '')
        if self._parser is not None:
            return self._parser.parse(File.StringHandle(data))
        return data

class Dictionary:
    """Accesses a SwissProt file using a dictionary interface.

    """
    __filename_key = '__filename'
    
    def __init__(self, indexname, parser=None):
        """__init__(self, indexname, parser=None)

        Open a SwissProt Dictionary.  indexname is the name of the
        index for the dictionary.  The index should have been created
        using the index_file function.  parser is an optional Parser
        object to change the results into another form.  If set to None,
        then the raw contents of the file will be returned.

        """
        self._index = Index.Index(indexname)
        self._handle = open(self._index[self.__filename_key])
        self._parser = parser

    def __len__(self):
        return len(self._index)

    def __getitem__(self, key):
        start, len = self._index[key]
        self._handle.seek(start)
        data = self._handle.read(len)
        if self._parser is not None:
            return self._parser.parse(File.StringHandle(data))
        return data

    def __getattr__(self, name):
        return getattr(self._index, name)

    def keys(self):
        # I only want to expose the keys for SwissProt.
        k = self._index.keys()
        k.remove(self.__filename_key)
        return k

class ExPASyDictionary:
    """Access SwissProt at ExPASy using a read-only dictionary interface.

    """
    def __init__(self, delay=5.0, parser=None):
        """__init__(self, delay=5.0, parser=None)

        Create a new Dictionary to access SwissProt.  parser is an optional
        parser (e.g. SProt.RecordParser) object to change the results
        into another form.  If set to None, then the raw contents of the
        file will be returned.  delay is the number of seconds to wait
        between each query.

        """
        self.parser = parser
        self.limiter = RequestLimiter(delay)

    def __len__(self):
        raise NotImplementedError, "SwissProt contains lots of entries"
    def clear(self):
        raise NotImplementedError, "This is a read-only dictionary"
    def __setitem__(self, key, item):
        raise NotImplementedError, "This is a read-only dictionary"
    def update(self):
        raise NotImplementedError, "This is a read-only dictionary"
    def copy(self):
        raise NotImplementedError, "You don't need to do this..."
    def keys(self):
        raise NotImplementedError, "You don't really want to do this..."
    def items(self):
        raise NotImplementedError, "You don't really want to do this..."
    def values(self):
        raise NotImplementedError, "You don't really want to do this..."
    
    def has_key(self, id):
        """has_key(self, id) -> bool"""
        try:
            self[id]
        except KeyError:
            return 0
        return 1

    def get(self, id, failobj=None):
        try:
            return self[id]
        except KeyError:
            return failobj
        raise "How did I get here?"

    def __getitem__(self, id):
        """__getitem__(self, id) -> object

        Return a SwissProt entry.  id is either the id or accession
        for the entry.  Raises a KeyError if there's an error.
        
        """
        # First, check to see if enough time has passed since my
        # last query.
        self.limiter.wait()

        try:
            handle = ExPASy.get_sprot_raw(id)
        except IOError:
            raise KeyError, id
        
        if self.parser is not None:
            return self.parser.parse(handle)
        return handle.read()

class RecordParser(AbstractParser):
    """Parses SwissProt data into a Record object.

    """
    def __init__(self):
        self._scanner = _Scanner()
        self._consumer = _RecordConsumer()

    def parse(self, handle):
        self._scanner.feed(handle, self._consumer)
        return self._consumer.data

class SequenceParser(AbstractParser):
    """Parses SwissProt data into a Seq object.

    """
    def __init__(self, alphabet = Alphabet.generic_protein):
        """Initialize a RecordParser.

        Arguments:
        o alphabet - The alphabet to use for the generated Seq objects. If
        not supplied this will default to the generic protein alphabet.
        """
        self._scanner = _Scanner()
        self._consumer = _SequenceConsumer(alphabet)

    def parse(self, handle):
        self._scanner.feed(handle, self._consumer)
        return self._consumer.data

class _Scanner:
    """Scans SwissProt-formatted data.

    Tested with:
    Release 37
    Release 38
    """

    def feed(self, handle, consumer):
        """feed(self, handle, consumer)

        Feed in SwissProt data for scanning.  handle is a file-like
        object that contains swissprot data.  consumer is a
        Consumer object that will receive events as the report is scanned.

        """
        if isinstance(handle, File.UndoHandle):
            uhandle = handle
        else:
            uhandle = File.UndoHandle(handle)
        
        while uhandle.peekline():
            self._scan_record(uhandle, consumer)

    def _scan_record(self, uhandle, consumer):
        consumer.start_record()
        for fn in self._scan_fns:
            fn(self, uhandle, consumer)

            # In Release 38, ID N33_HUMAN has a DR buried within comments.
            # Check for this and do more comments, if necessary.
            # XXX handle this better
            if fn is self._scan_dr.im_func:
                self._scan_cc(uhandle, consumer)
                self._scan_dr(uhandle, consumer)
        consumer.end_record()

    def _scan_line(self, line_type, uhandle, event_fn,
                   exactly_one=None, one_or_more=None, any_number=None,
                   up_to_one=None):
        # Callers must set exactly one of exactly_one, one_or_more, or
        # any_number to a true value.  I do not explicitly check to
        # make sure this function is called correctly.
        
        # This does not guarantee any parameter safety, but I
        # like the readability.  The other strategy I tried was have
        # parameters min_lines, max_lines.
        
        if exactly_one or one_or_more:
            read_and_call(uhandle, event_fn, start=line_type)
        if one_or_more or any_number:
            while 1:
                if not attempt_read_and_call(uhandle, event_fn,
                                             start=line_type):
                    break
        if up_to_one:
            attempt_read_and_call(uhandle, event_fn, start=line_type)
    # added by hy
    def _scan_fasta(self, uhandle, consumer):
        self._scan_line('>', uhandle, consumer.fasta, any_number=1)
    # added by hy

    def _scan_id(self, uhandle, consumer):
        self._scan_line('ID', uhandle, consumer.identification, exactly_one=1)

    def _scan_ac(self, uhandle, consumer):
        # Until release 38, this used to match exactly_one.
        # However, in release 39, 1A02_HUMAN has 2 AC lines, and the
        # definition needed to be expanded.
        self._scan_line('AC', uhandle, consumer.accession, any_number=1)
    
    def _scan_dt(self, uhandle, consumer):
        self._scan_line('DT', uhandle, consumer.date, exactly_one=1)
        self._scan_line('DT', uhandle, consumer.date, exactly_one=1)
        self._scan_line('DT', uhandle, consumer.date, exactly_one=1)

    def _scan_de(self, uhandle, consumer):
        self._scan_line('DE', uhandle, consumer.description, one_or_more=1)
    
    def _scan_gn(self, uhandle, consumer):
        self._scan_line('GN', uhandle, consumer.gene_name, any_number=1)
    
    def _scan_os(self, uhandle, consumer):
        self._scan_line('OS', uhandle, consumer.organism_species,
                        one_or_more=1)
    
    def _scan_og(self, uhandle, consumer):
        self._scan_line('OG', uhandle, consumer.organelle, any_number=1)
    
    def _scan_oc(self, uhandle, consumer):
        self._scan_line('OC', uhandle, consumer.organism_classification,
                        one_or_more=1)

    def _scan_ox(self, uhandle, consumer):
        self._scan_line('OX', uhandle, consumer.taxonomy_id,
                        any_number=1)

    def _scan_reference(self, uhandle, consumer):
        while 1:
            if safe_peekline(uhandle)[:2] != 'RN':
                break
            self._scan_rn(uhandle, consumer)
            self._scan_rp(uhandle, consumer)
            self._scan_rc(uhandle, consumer)
            self._scan_rx(uhandle, consumer)
            # ws:2001-12-05 added, for record with RL before RA
            self._scan_rl(uhandle, consumer)
            self._scan_ra(uhandle, consumer)
            self._scan_rt(uhandle, consumer)
            self._scan_rl(uhandle, consumer)
    
    def _scan_rn(self, uhandle, consumer):
        self._scan_line('RN', uhandle, consumer.reference_number,
                        exactly_one=1)
    
    def _scan_rp(self, uhandle, consumer):
        self._scan_line('RP', uhandle, consumer.reference_position,
                        one_or_more=1)
    
    def _scan_rc(self, uhandle, consumer):
        self._scan_line('RC', uhandle, consumer.reference_comment,
                        any_number=1)
    
    def _scan_rx(self, uhandle, consumer):
        self._scan_line('RX', uhandle, consumer.reference_cross_reference,
                        up_to_one=1)
    
    def _scan_ra(self, uhandle, consumer):
        self._scan_line('RA', uhandle, consumer.reference_author,
                        one_or_more=1)
    
    def _scan_rt(self, uhandle, consumer):
        self._scan_line('RT', uhandle, consumer.reference_title,
                        any_number=1)
    
    def _scan_rl(self, uhandle, consumer):
        # This was one_or_more, but P82909 in TrEMBL 16.0 does not
        # have one.
        self._scan_line('RL', uhandle, consumer.reference_location,
                        any_number=1)
    
    def _scan_cc(self, uhandle, consumer):
        self._scan_line('CC', uhandle, consumer.comment, any_number=1)
    
    def _scan_dr(self, uhandle, consumer):
        self._scan_line('DR', uhandle, consumer.database_cross_reference,
                        any_number=1)
    
    def _scan_kw(self, uhandle, consumer):
        self._scan_line('KW', uhandle, consumer.keyword, any_number=1)
    
    def _scan_ft(self, uhandle, consumer):
        self._scan_line('FT', uhandle, consumer.feature_table, any_number=1)
    
    def _scan_sq(self, uhandle, consumer):
        self._scan_line('SQ', uhandle, consumer.sequence_header, exactly_one=1)
    
    def _scan_sequence_data(self, uhandle, consumer):
        self._scan_line('  ', uhandle, consumer.sequence_data, one_or_more=1)
    
    def _scan_terminator(self, uhandle, consumer):
        self._scan_line('//', uhandle, consumer.terminator, exactly_one=1)

    _scan_fns = [
    	# added by hy
        _scan_fasta,
	# added by hy
        _scan_id,
        _scan_ac,
        _scan_dt,
        _scan_de,
        _scan_gn,
        _scan_os,
        _scan_og,
        _scan_oc,
        _scan_ox,
        _scan_reference,
        _scan_cc,
        _scan_dr,
        _scan_kw,
        _scan_ft,
        _scan_sq,
        _scan_sequence_data,
        _scan_terminator
        ]

class _RecordConsumer(AbstractConsumer):
    """Consumer that converts a SwissProt record to a Record object.

    Members:
    data    Record with SwissProt data.

    """
    def __init__(self):
        self.data = None
        
    def start_record(self):
        self.data = Record()
        
    def end_record(self):
        self._clean_record(self.data)
    # added by hy
    def fasta(self, line):
    	self.data.fasta = line[1:len(line)-1]
    # added by hy

    def identification(self, line):
        cols = string.split(line)
        self.data.entry_name = cols[1]
        self.data.data_class = self._chomp(cols[2])    # don't want ';'
        self.data.molecule_type = self._chomp(cols[3]) # don't want ';'
        self.data.sequence_length = int(cols[4])

        # data class can be 'STANDARD' or 'PRELIMINARY'
        # ws:2001-12-05 added IPI
        if self.data.data_class not in ['STANDARD', 'PRELIMINARY', 'IPI']: 
            raise SyntaxError, "Unrecognized data class %s in line\n%s" % \
                  (self.data.data_class, line)
        # molecule_type should be 'PRT' for PRoTein
        if self.data.molecule_type != 'PRT':
            raise SyntaxError, "Unrecognized molecule type %s in line\n%s" % \
                  (self.data.molecule_type, line)
    
    def accession(self, line):
        cols = string.split(self._chomp(string.rstrip(line[5:])), ';')
        for ac in cols:
            self.data.accessions.append(string.lstrip(ac))
    
    def date(self, line):
        uprline = string.upper(line)
        if string.find(uprline, 'CREATED') >= 0:
            cols = string.split(line)
            # ws:2001-12-05 prevent e.g. (IPIrel. , created)
            # !no number given! from crashing
            if self._chomp(cols[3]) == '':                            #<=
                self.data.created = cols[1], 0                        #<=
	    else:	                                              #<=
                self.data.created = cols[1], int(self._chomp(cols[3]))
        elif string.find(uprline, 'LAST SEQUENCE UPDATE') >= 0:
            cols = string.split(line)
            # ws:2001-12-05 prevent e.g. (IPIrel. , created)
            # !no number given! from crashing
            if self._chomp(cols[3]) == '':                            #<=
                self.data.sequence_update = cols[1], 0                #<=
	    else:                                                     #<=
                self.data.sequence_update = cols[1], int(self._chomp(cols[3]))
        elif string.find(uprline, 'LAST ANNOTATION UPDATE') >= 0:
            cols = string.split(line)
            # ws:2001-12-05 prevent e.g. (IPIrel. , created)
            # !no number given! from crashing
            if self._chomp(cols[3]) == '':                               #<=
                self.data.annotation_update = cols[1], 0                 #<=
	    else:                                                        #<=
                self.data.annotation_update = cols[1], \
                                              int(self._chomp(cols[3]))  #<=
        else:
            raise SyntaxError, "I don't understand the date line %s" % line
    
    def description(self, line):
        self.data.description = self.data.description + line[5:]
    
    def gene_name(self, line):
        self.data.gene_name = self.data.gene_name + line[5:]
    
    def organism_species(self, line):
        self.data.organism = self.data.organism + line[5:]
    
    def organelle(self, line):
        self.data.organelle = self.data.organelle + line[5:]
    
    def organism_classification(self, line):
        line = self._chomp(string.rstrip(line[5:]))
        cols = string.split(line, ';')
        for col in cols:
            self.data.organism_classification.append(string.lstrip(col))

    def taxonomy_id(self, line):
        # The OX line is in the format:
        # OX   DESCRIPTION=ID[, ID]...;
        # If there are too many id's to fit onto a line, then the ID's
        # continue directly onto the next line, e.g.
        # OX   DESCRIPTION=ID[, ID]...
        # OX   ID[, ID]...;
        # Currently, the description is always "NCBI_TaxID".

        # To parse this, I need to check to see whether I'm at the
        # first line.  If I am, grab the description and make sure
        # it's an NCBI ID.  Then, grab all the id's.
        line = self._chomp(string.rstrip(line[5:]))
        index = string.find(line, '=')
        if index >= 0:
            descr = line[:index]
            assert descr == "NCBI_TaxID", "Unexpected taxonomy type %s" % descr
            ids = string.split(line[index+1:], ',')
        else:
            ids = string.split(line, ',')
        self.data.taxonomy_id.extend(map(string.strip, ids))
    
    def reference_number(self, line):
        rn = string.rstrip(line[5:])
        assert rn[0] == '[' and rn[-1] == ']', "Missing brackets %s" % rn
        ref = Reference()
        ref.number = int(rn[1:-1])
        self.data.references.append(ref)
    
    def reference_position(self, line):
        assert self.data.references, "RP: missing RN"
        self.data.references[-1].positions.append(string.rstrip(line[5:]))
    
    def reference_comment(self, line):
        assert self.data.references, "RC: missing RN"
        cols = string.split(string.rstrip(line[5:]), ';')
        ref = self.data.references[-1]
        for col in cols:
            if not col:  # last column will be the empty string
                continue
            # The token is everything before the first '=' character.
            index = string.find(col, '=')
            token, text = col[:index], col[index+1:]
            # According to the spec, there should only be 1 '='
            # character.  However, there are too many exceptions to
            # handle, so we'll ease up and allow anything after the
            # first '='.
            #if col == ' STRAIN=TISSUE=BRAIN':
            #    # from CSP_MOUSE, release 38
            #    token, text = "TISSUE", "BRAIN"
            #elif col == ' STRAIN=NCIB 9816-4, AND STRAIN=G7 / ATCC 17485':
            #    # from NDOA_PSEPU, release 38
            #    token, text = "STRAIN", "NCIB 9816-4 AND G7 / ATCC 17485"
            #elif col == ' STRAIN=ISOLATE=NO 27, ANNO 1987' or \
            #     col == ' STRAIN=ISOLATE=NO 27 / ANNO 1987':
            #    # from NU3M_BALPH, release 38, release 39
            #    token, text = "STRAIN", "ISOLATE NO 27, ANNO 1987"
            #else:
            #    token, text = string.split(col, '=')
            ref.comments.append((string.lstrip(token), text))
    
    def reference_cross_reference(self, line):
        assert self.data.references, "RX: missing RN"
        # The basic (older?) RX line is of the form:
        # RX   MEDLINE; 85132727.
        # but there are variants of this that need to be dealt with (see below)
        
        # CLD1_HUMAN in Release 39 and DADR_DIDMA in Release 33
        # have extraneous information in the RX line.  Check for
        # this and chop it out of the line.
        # (noticed by katel@worldpath.net)
        ind = string.find(line, '[NCBI, ExPASy, Israel, Japan]')
        if ind >= 0:
            line = line[:ind]

        # RX lines can also be used of the form
        # RX   PubMed=9603189;
        # reported by edvard@farmasi.uit.no
        # and these can be more complicated like:
        # RX   MEDLINE=95385798; PubMed=7656980;
        # We look for these cases first and deal with them
        if string.find(line, "=") != -1:
            cols = string.split(line)
            assert len(cols) > 1, "I don't understand RX line %s" % line

            for info_col in cols[1:]:
                id_cols = string.split(info_col, "=")
                if len(id_cols) == 2:
                    self.data.references[-1].references.append(
                        (self._chomp(id_cols[0]), self._chomp(id_cols[1])))
                else:
                    raise AssertionError("I don't understand RX line %s"
                                         % line)
        # otherwise we assume we have the type 'RX   MEDLINE; 85132727.'
        else:
            cols = string.split(line)
            # normally we split into the three parts
            if len(cols) == 3:
                self.data.references[-1].references.append(
                    (self._chomp(cols[1]), self._chomp(cols[2])))
            else:
                raise AssertionError("I don't understand RX line %s" % line)
    
    def reference_author(self, line):
        assert self.data.references, "RA: missing RN"
        ref = self.data.references[-1]
        ref.authors = ref.authors + line[5:]
    
    def reference_title(self, line):
        assert self.data.references, "RT: missing RN"
        ref = self.data.references[-1]
        ref.title = ref.title + line[5:]
    
    def reference_location(self, line):
        assert self.data.references, "RL: missing RN"
        ref = self.data.references[-1]
        ref.location = ref.location + line[5:]
    
    def comment(self, line):
        if line[5:8] == '-!-':   # Make a new comment
            self.data.comments.append(line[9:])
        elif line[5:8] == '   ': # add to the previous comment
            if not self.data.comments:
                # TCMO_STRGA in Release 37 has comment with no topic
                self.data.comments.append(line[9:])
            else:
                self.data.comments[-1] = self.data.comments[-1] + line[9:]
        elif line[5:8] == '---':
            # If there are no comments, and it's not the closing line,
            # make a new comment.
            if not self.data.comments or self.data.comments[-1][:3] != '---':
                self.data.comments.append(line[5:])
            else:
                self.data.comments[-1] = self.data.comments[-1] + line[5:]
        else:  # copyright notice
            self.data.comments[-1] = self.data.comments[-1] + line[5:]
    
    def database_cross_reference(self, line):
        # From CLD1_HUMAN, Release 39:
        # DR   EMBL; [snip]; -. [EMBL / GenBank / DDBJ] [CoDingSequence]
        # DR   PRODOM [Domain structure / List of seq. sharing at least 1 domai
        # DR   SWISS-2DPAGE; GET REGION ON 2D PAGE.
        line = line[5:]
        # Remove the comments at the end of the line
        i = string.find(line, '[')
        if i >= 0:
            line = line[:i]
        cols = string.split(self._chomp(string.rstrip(line)), ';')
        for i in range(len(cols)):
            cols[i] = string.lstrip(cols[i])
        self.data.cross_references.append(tuple(cols))
    
    def keyword(self, line):
        cols = string.split(self._chomp(string.rstrip(line[5:])), ';')
        for col in cols:
            self.data.keywords.append(string.lstrip(col))
    
    def feature_table(self, line):
        line = line[5:]    # get rid of junk in front
        name = string.rstrip(line[0:8])
        try:
            from_res = int(line[9:15])
        except ValueError:
            from_res = string.lstrip(line[9:15])
        try:
            to_res = int(line[16:22])
        except ValueError:
            to_res = string.lstrip(line[16:22])
        description = string.rstrip(line[29:70])

        if not name:  # is continuation of last one
            assert not from_res and not to_res
            name, from_res, to_res, old_description = self.data.features[-1]
            del self.data.features[-1]
            description = "%s %s" % (old_description, description)
            
            # special case -- VARSPLIC, reported by edvard@farmasi.uit.no
            if name == "VARSPLIC":
                description = self._fix_varsplic_sequences(description)
        self.data.features.append((name, from_res, to_res, description))

    def _fix_varsplic_sequences(self, description):
        """Remove unwanted spaces in sequences.

        During line carryover, the sequences in VARSPLIC can get mangled
        with unwanted spaces like:
        'DISSTKLQALPSHGLESIQT -> PCRATGWSPFRRSSPC LPTH'
        We want to check for this case and correct it as it happens.
        """
        descr_cols = string.split(description, " -> ")
        if len(descr_cols) == 2:
            first_seq = descr_cols[0]
            second_seq = descr_cols[1]
            extra_info = ''
            # we might have more information at the end of the
            # second sequence, which should be in parenthesis
            extra_info_pos = string.find(second_seq, " (")
            if extra_info_pos != -1:
                extra_info = second_seq[extra_info_pos:]
                second_seq = second_seq[:extra_info_pos]

            # now clean spaces out of the first and second string
            first_seq = string.replace(first_seq, " ", "")
            second_seq = string.replace(second_seq, " ", "")

            # reassemble the description
            description = first_seq + " -> " + second_seq + extra_info

        return description
    
    def sequence_header(self, line):
        cols = string.split(line)
        assert len(cols) == 8, "I don't understand SQ line %s" % line
        # Do more checking here?
        self.data.seqinfo = int(cols[2]), int(cols[4]), cols[6]
    
    def sequence_data(self, line):
        seq = string.rstrip(string.replace(line, " ", ""))
        self.data.sequence = self.data.sequence + seq
    
    def terminator(self, line):
        pass

    def _chomp(self, word, to_chomp='.,;'):
        # Remove the punctuation at the end of a word.
        if word[-1] in to_chomp:
            return word[:-1]
        return word

    #def _clean(self, line, rstrip=1):
    #    if rstrip:
    #        return string.rstrip(line[5:])
    #    return line[5:]

    def _clean_record(self, rec):
        # Remove trailing newlines
        members = ['description', 'gene_name', 'organism', 'organelle']
        for m in members:
            attr = getattr(rec, m)
            setattr(rec, m, string.rstrip(attr))
        for ref in rec.references:
            self._clean_references(ref)

    def _clean_references(self, ref):
        # Remove trailing newlines
        members = ['authors', 'title', 'location']
        for m in members:
            attr = getattr(ref, m)
            setattr(ref, m, string.rstrip(attr))

class _SequenceConsumer(AbstractConsumer):
    """Consumer that converts a SwissProt record to a Seq object.

    Members:
    data      Record with SwissProt data.
    alphabet  The alphabet the generated Seq objects will have.

    """
    def __init__(self, alphabet = Alphabet.generic_protein):
        """Initialize a Sequence Consumer

        Arguments:
        o alphabet - The alphabet to use for the generated Seq objects. If
        not supplied this will default to the generic protein alphabet.
        """
        self.data = None
        self.alphabet = alphabet
        
    def start_record(self):
        seq = Seq.Seq("", self.alphabet)
        self.data = SeqRecord.SeqRecord(seq)
        self.data.description = ""
        
    def end_record(self):
        self.data.description = string.rstrip(self.data.description)

    def identification(self, line):
        cols = string.split(line)
        self.data.name = cols[1]

    def accession(self, line):
        ids = string.split(string.rstrip(line[5:]), ';')
        self.data.id = ids[0]

    def description(self, line):
        self.data.description = self.data.description + \
                                string.strip(line[5:]) + "\n"
        
    def sequence_data(self, line):
        seq = Seq.Seq(string.rstrip(string.replace(line, " ", "")),
                      self.alphabet)
        self.data.seq = self.data.seq + seq

def index_file(filename, indexname, rec2key=None):
    """index_file(filename, indexname, rec2key=None)

    Index a SwissProt file.  filename is the name of the file.
    indexname is the name of the dictionary.  rec2key is an
    optional callback that takes a Record and generates a unique key
    (e.g. the accession number) for the record.  If not specified,
    the entry name will be used.

    """
    if not os.path.exists(filename):
        raise ValueError, "%s does not exist" % filename
    
    index = Index.Index(indexname, truncate=1)
    index[Dictionary._Dictionary__filename_key] = filename
    
    iter = Iterator(open(filename), parser=RecordParser())
    while 1:
        start = iter._uhandle.tell()
        rec = iter.next()
        length = iter._uhandle.tell() - start
        
        if rec is None:
            break
        if rec2key is not None:
            key = rec2key(rec)
        else:
            key = rec.entry_name
            
        if not key:
            raise KeyError, "empty sequence key was produced"
        elif index.has_key(key):
            raise KeyError, "duplicate key %s found" % key

        index[key] = start, length