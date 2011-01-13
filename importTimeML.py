# read data from a set of timeml files in to a database

import sys

# only run this check if executed as a script 
# goal is to avoid doing complex imports at command line if we're just going to print help and quit
if __name__ == '__main__':

    if (len(sys.argv) != 3) or sys.argv[1] == '-h':
        print 'Script to take a directory of TimeML files and load them into a local MySQL database'
        print 'Usage: timeml_to_db.py <directory> <dbName>'
        print '         <directory> - a path ending in a slash to the TimeML data directory'
        print '         <dbName>    - database to dump the data in (will be emptied when the script is run, without confirmation); the prefix "timebank_" is automatically prepended'
        print 'NB: Login details for MySQL are set in the code'
        sys.exit()


import db
import MySQLdb
import nltk
import nltk.data
import os
import re
import string
from xml.dom import minidom
import xml.parsers.expat
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from nltk.stem import wordnet as wn


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
    parsedText = ''
    trailingSpace = False

    sentenceDetector = nltk.data.load('tokenizers/punkt/english.pickle') 

    
    def cleanText(self, text):
        text = text.replace('. . .', '...') # SJMN doc
        text = text.replace('Inc.', 'Inc')  # wsj_0928
        text = text.replace('U.K.', 'UK')   # wsj_0583
        text = text.replace('p.m.', 'pm')   # NYT19980212.0019
        text = re.sub(r'[\n\r\t\s]+', ' ', text) # collapse whitespace
        return text


    def startElement(self,  name,  attrs):

        global elementID
        elementID = None
        
        
        # set elementID for tags that wrap around text, to capture the text
        try:
            if name == 'TIMEX3':
                elementID = attrs['tid']
            elif name == 'EVENT':
                elementID = attrs['eid']
            elif name == 'SIGNAL':
                elementID = attrs['sid']
            else:
                return

        except:
            raise Exception('Missing ID in ' + str(attrs) + '- should contain (e.g.) eid/tid/sid')

        self.inTag = True

        self.tags[elementID] = [name, len(self.parsedText)] # store the byte offset of this tag, calculated by the length of parsedText so far
#        print elementID, len(self.parsedText), self.parsedText

    def endElement(self,  name):
        if self.inTag:
            self.tagText[elementID] = cData
            self.inTag = False


    def charData(self,  data):
        self.parsedText += data # append the data to parsedText
        punktCompensation = 0
        punktCompensation = data.count('." ') + data.count(".'' ") + data.count('?" ') + data.count('.) ')
        if punktCompensation: # compensate for chars omitted by punkt-sentence-tokenization decisions
            print '|' + data + '|'
            self.parsedText += 'x'*punktCompensation
        if self.inTag:
            global cData
            cData = data


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
            self.parsedText = ''

            
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
            timeMlFile.close()
 
            self.bodyText = self.cleanText(self.bodyText)
            sentences = self.sentenceDetector.tokenize(self.bodyText)
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


            xmlData = self.cleanText(xmlData) # collapse whitespace
            parser.Parse(xmlData) # run sax parser - includes offset calculation

            # calculate sentence offset lookup table. sentence regex always matches a 2 char string.

            # of the format {sentence ID : byte offset of sentence's start in document}
            sentenceOffset = {0:0}
            sentenceID = 1
            for sentence in sentences:
                sentenceOffset[sentenceID] = sentenceOffset[sentenceID - 1] + len(sentence) +1 # what's this +1 for? the trailing \n - punkt does not cut anything else out when tokenising.
                sentenceID += 1
            print sentenceOffset

            wordOffset = {}
            for sentenceID, sentenceText in enumerate(sentences):
                wordOffset[sentenceID] = {}
                sentenceTokens = nltk.word_tokenize(sentenceText)
                rightRemainder = sentenceText
                tokenID = 0

                # repeatedly chop tokens, in order from the right-hand part of the sentence. measure what's left; sentence length - (remainder + what we chopped off) = char offset of where the token started
                for token in sentenceTokens:
                    rightRemainder = rightRemainder.lstrip()
                    rightRemainder = re.sub('^' + re.escape(token), '', rightRemainder)
                    byteOffset_inSentence = len(sentenceText) - len(rightRemainder) - len(token)
                    byteOffset_inDoc = sentenceOffset[sentenceID] + byteOffset_inSentence
                    wordOffset[sentenceID][tokenID] = byteOffset_inDoc
                    print '\t'.join([token, str(sentenceID), str(tokenID), str(byteOffset_inDoc)])
                    tokenID += 1


            # add text data for tags that contain text (event, timex, signal)
            for tag in self.tags:
                if tag[0] == 's':
                    table = 'signals'
                    idColumn = 'sid'
                    
                elif tag[0] == 'e':
                    table = 'events'
                    idColumn = 'eid'
                    
                    # look up PoS for lemmatiser
                    self.cursor.execute('SELECT pos FROM instances WHERE eventID = "%s" AND doc_id = %d' % (tag,  self.doc_id))
                    
                    try:
                        pos= self.cursor.fetchone()[0]
                    except:
                        print 'Failed to find PoS for eventID %s in doc %s - possibly a missing MAKEINSTANCE' % (tag,  fileName)
                        return
                    
                    if pos == '':
                        pos = 'OTHER'

                    # work out lemma; get first instance of this event and take pos from it, then call wordnet lemmatize
                    lemmatext = string.lower(string.strip(str(self.tagText[tag]))).translate(tTable,  string.punctuation)
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        lemma = l.lemmatize(lemmatext,  timebankToWordnet[pos])
                    
                    # save lemma
                    self.cursor.execute('UPDATE events SET lemma = "%s" WHERE eid = "%s" AND doc_id = %d' % (MySQLdb.escape_string(lemma), tag,  self.doc_id))
                    
                elif tag[0] == 't':
                    table = 'timex3s'
                    idColumn = 'tid'
                    
                else:
                    # unknown element type - ignore
                    continue

                # calculate sentence and word offset for the start tag

                sentence = 0
                token = 0

                byteOffset = self.tags[tag][1]

                print tag, 'byte', byteOffset,

                # for sentence
                offsets = sentenceOffset.values()
                smallerOffsets = filter(lambda y: y <= byteOffset, offsets)
                correctOffset = max(smallerOffsets) # which is the largest sentence byte-offset that's less than the tag offset?
                sentence = [k for k, v in sentenceOffset.iteritems() if v == correctOffset][0] # find the ID of the sentence that has this byte offset

                print 'sentence', sentence,

                # for token
                offsets = wordOffset[sentence].values()
                smallerOffsets = filter(lambda y: y <= byteOffset, offsets) # which is the largest word-offset that's less than the tag offset?
                correctOffset = max(smallerOffsets) # store largest token-start byte-offset that's less than element start offset, that is, the offset of the word-start boundary equal-to/just-before this one
                token = [k for k, v in wordOffset[sentence].iteritems() if v == correctOffset][0] # look up the token number

                print 'token', token
            
                self.cursor.execute('UPDATE %s SET position = %s, sentence = %s, inSentence = %s WHERE %s = "%s" AND doc_id = %d' % (table,  byteOffset,  sentence,  token,  idColumn,  tag,  self.doc_id))
                self.cursor.execute('UPDATE %s SET text = "%s" WHERE %s = "%s" AND doc_id = %d' % (table,  MySQLdb.escape_string(self.tagText[tag]),  idColumn,  tag,  self.doc_id))
            
            self.cursor.execute('UPDATE documents SET body = "%s" WHERE id = %d' % (MySQLdb.escape_string(self.bodyText), self.doc_id))
            
            
        
        print 'From SAX parse:'
        print self.parsedText
        print 'From sentences + tokenisation'
        print ' '.join(sentences)

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
