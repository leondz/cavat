# read data from a set of timeml files in to a database

import sys
import nltk

# only run this if executed as a script - avoid doing complex imports if command line if we're just going to print help and quit
if __name__ == '__main__':

    if (len(sys.argv) != 3) or sys.argv[1] == '-h':
        print 'Script to take a directory of TimeML files and load them into a local MySQL database'
        print 'Usage: timeml_to_db.py <directory> <dbName>'
        print '         <directory> - a path ending in a slash to the TimeML data directory'
        print '         <dbName>    - database to dump the data in (will be emptied when the script is run, without confirmation); the prefix "timebank_" is automatically prepended'
        print 'NB: Login details for MySQL are set in the code'
        sys.exit()


import MySQLdb
import os
import string
from xml.dom import minidom
import xml.parsers.expat
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from nltk.stem import wordnet as wn
import re

import db

class ImportTimeML:

    doc_id = None
    conn = None
    cursor = None
    tlinkFieldMapping = {'eventInstanceID':'arg1',  'timeID':'arg1',  'relatedToEventInstance':'arg2',  'relatedToTime':'arg2'}

    tags = {}
    tagText = {}
    inTag = False
    wordOffset = 0
    sentenceOffset = 0
    posInSentence = 0
    bodyText = ''

    sentenceBound = re.compile(r'\.[\s]',  re.MULTILINE)

    def startElement(self,  name,  attrs):

        global elementID
        elementID = None
        
        
        # set elementID for tags that wrap around text, to capture the text
        if name == 'TIMEX3':
            elementID = attrs['tid']

        elif name == 'EVENT':
            elementID = attrs['eid']

        elif name == 'SIGNAL':
            elementID = attrs['sid']

        else:
            return

        self.inTag = True

        self.tags[elementID] = [name,  self.wordOffset,  self.sentenceOffset,  self.posInSentence]


    def endElement(self,  name):
        if self.inTag:
            self.tagText[elementID] = cData
            self.inTag = False


    def charData(self,  data):
        
        # ellipsis separated by spaces ('. . . ') tricks our sentence boundary calculation; change them to '...'
#        data = re.replace(re.compile('\. [\. ]+'), '..', data)
        data = data.replace('. . .', '...')

        
        self.bodyText += data
        newWords = len(nltk.word_tokenize(data)) # number of tokens in this chunk of text
        self.wordOffset += newWords # advance word offset
        data += ' '
#        print '|'+data+'|'
        self.sentenceOffset += len(self.sentenceBound.findall(data)) # count sentences in chunk of text and advance sentence offset; expat rtrims, so add a space for detection of final full stops with sentenceBound regexp.
        

        # check for sentence boundary crosses
        sentences = re.split(self.sentenceBound,  data)

        if len(sentences) > 1:
            self.posInSentence = len(nltk.word_tokenize(sentences.pop())) # only count word offset in latest sentence
        else:
            self.posInSentence += newWords
        
#        print 'Ended at sentence',  self.sentenceOffset,  'word',  self.posInSentence
        
        
        if self.inTag:
            global cData
            cData = data
        pass


    def insertNodes(self,  nodes,  attribs,  table,  tlinks=False):

        for node in nodes:
            
            nodeData = {}
            
            # fill all attribute fields
            # skip unspecified attributes, so that defaults are taken from the SQL schema
            for attrib in attribs:
                if node.hasAttribute(attrib):
                    nodeData[attrib] = node.getAttribute(attrib)
            
            # one of either valueFromFunction or value is set
            if 'tid' in attribs:
                if node.hasAttribute('valueFromFunction'):
                    nodeData['value'] = node.getAttribute['valueFromFunction']

            # different attribute names are used for timexs and events, occuring as arg1 and arg2 of a TLINK. let's call them all arg1 & arg2
            if tlinks:
                for tlinkAttrib in self.tlinkFieldMapping.keys():
                    if node.hasAttribute(tlinkAttrib):
                        nodeData[self.tlinkFieldMapping[tlinkAttrib]] = node.getAttribute(tlinkAttrib)


            sql = 'INSERT INTO ' + table + ' (doc_id, `' + ('`,`'.join(nodeData.keys())) + '`) VALUES (' + str(self.doc_id)
            for key in nodeData.keys() :
                sql += ', "' + nodeData[key] + '"'
            sql += ')'
            
            #print sql
            try:
                self.cursor.execute(sql)
            except Exception,  e:
                print sql,  str(e)
                sys.exit()




    def importCorpusToDb(self,  directory,  dbName):
        # global vars
        
        if not self.conn:
            self.conn = db.conn
            self.cursor = db.cursor


        print >> sys.stderr,  '==============================================================='
        print >> sys.stderr,  'Reading from ' + directory
        print >> sys.stderr,  'Writing to DB ' + dbName
        print >> sys.stderr,  '==============================================================='



        tTable = string.maketrans("",  "")

        l = wn.WordNetLemmatizer()
        timebankToWordnet = {
            'ADJECTIVE': 'a',
            'NOUN': 'n' ,
            'OTHER': 'a',
            'PREPOSITION': 'a',  # would like to use 's' here, but it's not in nltk.corpus.reader.wordnet POS_LIST; just defined as ADJ_SAT constant
            'VERB': 'v'
            }


        # reset database
        tableCreationSql = open('db_header.sql').read()

        self.cursor.execute('DROP DATABASE IF EXISTS %s' % dbName)
        self.cursor.execute('CREATE DATABASE %s' % dbName)
        self.conn.select_db(dbName)


        for creationSql in tableCreationSql.split(';'):
            if len(creationSql.strip()) > 0:
                self.cursor.execute(creationSql)

        
        # read directory
        fileList = os.listdir(directory)
        fileList.sort()

        for fileName in fileList:
            
            self.tags = {}
            self.tagText = {}
            self.inTag = False
            self.wordOffset = 0
            self.sentenceOffset = 0
            self.posInSentence = 0
            self.bodyText = ''

            
            if not os.path.isfile(directory+fileName):
                continue;
            
            if fileName[0] == '.':
                #skip hidden files
                continue;
            
            self.cursor.execute('INSERT INTO documents(docname) VALUES ("' + fileName + '")')
            self.doc_id = int(self.cursor.lastrowid)

            print fileName,  'as',  self.doc_id

            # break into sentences
            timeMlFile = open(directory+fileName)
            self.bodyText = timeMlFile.read() # load file
            self.bodyText = re.sub(r'<[^>]*?>', '', self.bodyText) # strip tags
            self.bodyText = re.sub(r'[\n\r\t\s]+', ' ', self.bodyText) # collapse whitespace
            timeMlFile.close()

 
            self.bodyText = self.bodyText.replace('. . .', '...')
            sentences = self.sentenceBound.split(self.bodyText)
            for i,  sentence in enumerate(sentences):
                self.cursor.execute('INSERT INTO sentences(doc_id, sentenceID, text) VALUES(%d, %d, "%s")' % (self.doc_id,  i,  MySQLdb.escape_string(sentence)))

            # get minidom data - element attribute cataloguing

            try:
                timemldoc  = minidom.parse(directory+fileName)
            except:
                print 'Failed to parse'
                return

            eventNodes = timemldoc.getElementsByTagName('EVENT')
            makeInstanceNodes = timemldoc.getElementsByTagName('MAKEINSTANCE')
            timexNodes = timemldoc.getElementsByTagName('TIMEX3')
            signalNodes = timemldoc.getElementsByTagName('SIGNAL')
            tlinkNodes = timemldoc.getElementsByTagName('TLINK')
            slinkNodes = timemldoc.getElementsByTagName('SLINK')
            alinkNodes = timemldoc.getElementsByTagName('ALINK')

            eventAttribs = ['eid',  'class']
            makeInstanceAttribs = ['eiid',  'eventID',  'signalID',  'pos',  'tense',  'aspect',  'cardinality',  'polarity',  'modality']
            timexAttribs = ['tid', 'type',  'functionInDocument',  'beginPoint',  'endPoint',  'quant',  'freq',  'temporalFunction',  'value',  'mod',  'anchorTimeID']
            signalAttribs = ['sid']
            tlinkAttribs = ['lid',  'origin',  'signalID',  'relType']
            slinkAttribs = ['lid',  'origin',  'signalID',  'relType',  'eventInstanceID',  'subordinatedEventInstance']
            alinkAttribs = ['lid',  'origin',  'signalID',  'relType',  'eventInstanceID',  'relatedToEventInstance']

            self.insertNodes(eventNodes,  eventAttribs,  'events')
            self.insertNodes(makeInstanceNodes,  makeInstanceAttribs,  'instances')
            self.insertNodes(timexNodes,  timexAttribs,  'timex3s')
            self.insertNodes(signalNodes,  signalAttribs,  'signals')
            self.insertNodes(tlinkNodes,  tlinkAttribs,  'tlinks',  True)
            self.insertNodes(slinkNodes,  slinkAttribs,  'slinks')
            self.insertNodes(alinkNodes,  alinkAttribs,  'alinks')


            # get position data
            
            file = open(directory+fileName)
            xmlData = file.read()
            file.close()

            parser = xml.parsers.expat.ParserCreate()

            parser.StartElementHandler = self.startElement
            parser.EndElementHandler = self.endElement
            parser.CharacterDataHandler = self.charData



            parser.Parse(xmlData)

            # add text data for tags that contain text (event, timex, signal)
        
            for tag in self.tags:
                if tag[0] == 's':
                    table = 'signals'
                    idColumn = 'sid'
                    
                elif tag[0] == 'e':
                    table = 'events'
                    idColumn = 'eid'
                    
                    # work out lemma; get first instance of this event and take pos from it, then call wordnet lemmatize
                    self.cursor.execute('SELECT pos FROM instances WHERE eventID = "%s" AND doc_id = %d' % (tag,  self.doc_id))
                    
                    pos= self.cursor.fetchone()[0]
                    
                    if pos == '':
                        pos = 'OTHER'

                    lemmatext = string.lower(string.strip(str(self.tagText[tag]))).translate(tTable,  string.punctuation)
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        lemma = l.lemmatize(lemmatext,  timebankToWordnet[pos])
                    self.cursor.execute('UPDATE events SET lemma = "%s" WHERE eid = "%s" AND doc_id = %d' % (MySQLdb.escape_string(lemma), tag,  self.doc_id))
                    
                elif tag[0] == 't':
                    table = 'timex3s'
                    idColumn = 'tid'
                    
                else:
                    # unknown element type - ignore
                    continue
            
                self.cursor.execute('UPDATE %s SET position = %s, sentence = %s, inSentence = %s WHERE %s = "%s" AND doc_id = %d' % (table,  self.tags[tag][1],  self.tags[tag][2],  self.tags[tag][3],   idColumn,  tag,  self.doc_id))
                self.cursor.execute('UPDATE %s SET text = "%s" WHERE %s = "%s" AND doc_id = %d' % (table,  MySQLdb.escape_string(self.tagText[tag]),  idColumn,  tag,  self.doc_id))
            
            self.cursor.execute('UPDATE documents SET body = "%s" WHERE id = %d' % (MySQLdb.escape_string(self.bodyText), self.doc_id))
            
            
        
        

        print 'Updating DB metadata'

        self.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_at", NOW())')
        self.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_to_db", %s)',  (dbName,))
        self.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_from_directory", %s)',  (directory,))

        if os.path.exists(directory + '.nfo'):
            nfo = open(directory + '.nfo',  'r')
            for line in nfo:
                line = line.strip()
                if line.find('::') != -1:
                    key,  data = line.split('::')
                elif len(line) > 0:
                    key,  data = ['comment',  line]
                else:
                    continue

                self.cursor.execute('INSERT INTO info(`key`, `data`) VALUES(%s, %s)',  (key, data))





if __name__ == '__main__':
    
    i = ImportTimeML()
    i.conn = MySQLdb.connect (host = "localhost", user = "timebank", passwd = "timebank")
    i.cursor = conn.cursor()
    
    
    directory = sys.argv[1] + '/'
    dbName = 'timebank_' + sys.argv[2]

    i.importCorpusToDb(directory,  dbName)
