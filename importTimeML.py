# read data from a set of timeml files in to a database

import sys

# only run this check if executed as a script 
# goal is to avoid doing complex imports at command line if we're just going to print help and quit
if __name__ == '__main__':
    print 'To be called by CAVaT only.'
    sys.exit()


import db
try:
    import nltk
    import nltk.data
except:
    sys.exit("Couldn't load 'nltk'. CAVaT requires this module in order to run. To install it under Ubuntu, try 'sudo apt-get install python-nltk'.")    
import os
import re
import string
from xml.dom import minidom
import xml.parsers.expat
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from nltk.stem import wordnet as wn

if db.engine == 'sqlite':
    import sqlite3

class ImportTimeML:

    doc_id = None
    conn = None
    cursor = None
    engine = None
    tlinkFieldMapping = {'eventInstanceID':'arg1',  'timeID':'arg1',  'relatedToEventInstance':'arg2',  'relatedToTime':'arg2'}

    tags = {}
    tagText = {}
    inTag = False
    wordOffset = 0
    sentenceOffset = 0
    posInSentence = 0
    parsedText = ''
    trailingSpace = False
    
    commitEveryDoc = False

    # punkt may cause extra splits on some combinations of spaces and punctuation; we will compensate for these.
    punktCompensate = ['." ',  ".'' ",  '?" ',  '.) ',  "?''",  '.; ',  '."; ']

    sentenceDetector = nltk.data.load('tokenizers/punkt/english.pickle') 
    
    event_only_mode = False

    cData = ''
    
    def cleanText(self, text):
        text = text.replace('. . .', '...') # SJMN doc
        text = text.replace('Inc.', 'Inc')  # wsj_0928
        text = text.replace('U.K.', 'UK')   # wsj_0583
        text = text.replace('p.m.', 'pm')   # NYT19980212.0019
        # when xml elements have space on both sides, the text offsets of words in cleaned xml and cleaned plaintext will differ
        # e.g. "  fish swim." becomes " fish swim", but " <event> fish</event> swim." becomes "  fish swim"
        # to remedy this, we should take special notice of element tags that have space on both sides.
        text = re.sub(r'[\n\r\t\s]+(<[^>]+>)[\n\r\t\s]+',  r' \1',  text)
        text = re.sub(r'[\n\r\t\s]+(</[^>]+>)[\n\r\t\s]+',  r'\1 ',  text)
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
            self.tagText[elementID] = self.cData
            self.inTag = False


    def charData(self,  data):
        self.parsedText += data # append the data to parsedText
        punktCompensation = 0
        for sequence in self.punktCompensate:
            punktCompensation += data.count(sequence)
        if punktCompensation: # compensate for chars omitted by punkt-sentence-tokenization decisions
            print '|' + data + '|'
            self.parsedText += 'x'*punktCompensation
        if self.inTag:
            self.cData = unicode(data)


    def insertNodes(self,  nodes,  attribs,  table,  tlinks=False):

        for node in nodes:
            
            # nodedata will be populated from the node using the list of predefined node attributes passed in 'attribs'
            nodeData = {}
            
            # fill all attribute fields
            # skip unspecified attributes, so that defaults are taken from the SQL schema
            for attrib in attribs:
                if node.hasAttribute(attrib):
                    nodeData[attrib] = node.getAttribute(attrib)

            # for each artificial instance, fill empty eiid and eventID with eid
            if table == 'instances' and self.event_only_mode:
                # does the node have an eid? this is our clue that instances has been copied from events
                if node.hasAttribute('eid'):
                    if 'eiid' not in nodeData.keys():
                        nodeData['eiid'] = node.getAttribute('eid')
                    if 'eventID' not in nodeData.keys():
                        nodeData['eventID'] = node.getAttribute('eid')

            # one of either valueFromFunction or value is set
            if 'tid' in attribs:
                if node.hasAttribute('valueFromFunction'):
                    nodeData['value'] = node.getAttribute('valueFromFunction')

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
                db.cursor.execute(sql)
            # timeml 1.3/iso transition might have two event tags with the same eid but differing eiids.
            # this will attempt to insert events with duplicate eids but different eiids, though as instances are a copy of events, we can safely ignore duplicate event eids
            except sqlite3.IntegrityError:
                if self.event_only_mode and table == 'events':
                    continue
                    
            # reject any constraint or db problems
            except Exception,  e:
                print sql.encode('utf-8'), type(e), str(e)
                sys.exit()




    def importCorpusToDb(self,  directory,  dbName):
        # global vars

        directory = os.path.expanduser(directory)

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
        tableCreationSql = open('db_header_'+db.engine+'.sql').read()

        if db.engine == 'mysql':
            db.cursor.execute('DROP DATABASE IF EXISTS %s' % dbName)
            db.cursor.execute('CREATE DATABASE %s' % dbName)
        
        if db.engine == 'sqlite':
            db_path = os.path.join(db.prefix,  dbName)
            if os.path.exists(db_path):
                os.unlink(db_path)
        
        db.changeDb(dbName)


        for creationSql in tableCreationSql.split(';'):
            if len(creationSql.strip()) > 0:
                db.cursor.execute(creationSql)

        if db.engine == 'sqlite':
            db.conn.commit()


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
            
            db.cursor.execute('INSERT INTO documents(docname) VALUES ("' + fileName + '")')
            self.doc_id = int(db.cursor.lastrowid)

            print fileName,  'as',  self.doc_id

            # break into sentences
            timeMlFile = open(directory+fileName)
            self.bodyText = timeMlFile.read() # load file
            self.bodyText = re.sub(r'<[^>]*?>', '', self.bodyText) # strip tags
            timeMlFile.close()
 
            # collapse whitespaces (this is also done before processing by sax parser)
            self.bodyText = self.cleanText(self.bodyText)

            sentences = self.sentenceDetector.tokenize(self.bodyText)
            sentences[0] = sentences[0].lstrip()
            for i,  sentence in enumerate(sentences):
                db.cursor.execute('INSERT INTO sentences(doc_id, sentenceID, text) VALUES(?, ?, ?)',  (self.doc_id,  i,  sentence.decode('utf-8')))

            # get minidom data - element attribute cataloguing

            try:
                timemldoc  = minidom.parse(directory+fileName)
            except Exception, e:
                print 'Failed to parse', e
                return

            eventNodes = timemldoc.getElementsByTagName('EVENT')
            makeInstanceNodes = timemldoc.getElementsByTagName('MAKEINSTANCE')
            timexNodes = timemldoc.getElementsByTagName('TIMEX3')
            signalNodes = timemldoc.getElementsByTagName('SIGNAL')
            tlinkNodes = timemldoc.getElementsByTagName('TLINK')
            slinkNodes = timemldoc.getElementsByTagName('SLINK')
            alinkNodes = timemldoc.getElementsByTagName('ALINK')

            eventAttribs = ['eid',  'class']
            makeInstanceAttribs = ['eiid',  'eventID',  'signalID',  'pos',  'tense',  'aspect',  'cardinality',  'polarity',  'modality', 'vform', 'mood', 'pred']
            timexAttribs = ['tid', 'type',  'functionInDocument',  'beginPoint',  'endPoint',  'quant',  'freq',  'temporalFunction',  'value',  'mod',  'anchorTimeID']
            signalAttribs = ['sid']
            tlinkAttribs = ['lid',  'origin',  'signalID',  'relType']
            slinkAttribs = ['lid',  'origin',  'signalID',  'relType',  'eventInstanceID',  'subordinatedEventInstance']
            alinkAttribs = ['lid',  'origin',  'signalID',  'relType',  'eventInstanceID',  'relatedToEventInstance']

            if len(makeInstanceNodes) == 0 and len(eventNodes) > 0:
                # assume that makeinstance info is listed on events; copy events to instances
                print 'EVENTs are present, but there are no MAKEINSTANCE elements; entering EVENT-only mode'
                self.event_only_mode = True
                # duplicate event data into makeinstance data
                makeInstanceNodes = xml.dom.minicompat.NodeList(eventNodes)

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
                sentenceOffset[sentenceID] = sentenceOffset[sentenceID - 1] + len(sentence) + 1 # what's this +1 for? the trailing \n - punkt does not cut anything else out when tokenising.
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
                    db.cursor.execute('SELECT pos FROM instances WHERE eventID = "%s" AND doc_id = %d' % (tag,  self.doc_id))
                    
                    try:
                        pos= db.cursor.fetchone()[0]
                    except:
                        print 'Failed to find PoS for eventID %s in doc %s - possibly a missing MAKEINSTANCE' % (tag,  fileName)
                        return
                    
                    if pos == '':
                        pos = 'OTHER'

                    # work out lemma; get first instance of this event and take pos from it, then call wordnet lemmatize
                    lemmatext = self.tagText[tag]
                    lemmatext = string.lower(string.strip(lemmatext))
                    if pos not in timebankToWordnet.keys():
                        wnPos = 'n' # default pos
                    else:
                        wnPos = timebankToWordnet[pos]
                    
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        lemma = l.lemmatize(lemmatext,  wnPos)
                    
                    # save lemma
                    db.cursor.execute('UPDATE events SET lemma = ? WHERE eid = ? AND doc_id = ?',  (lemma, tag,  self.doc_id))
                    
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
                try:
                    offsets = wordOffset[sentence].values()
                except:
                    print 'no token'
                    token = None
                else:
                    smallerOffsets = filter(lambda y: y <= byteOffset, offsets) # which is the largest word-offset that's less than the tag offset?
                    correctOffset = max(smallerOffsets) # store largest token-start byte-offset that's less than element start offset, that is, the offset of the word-start boundary equal-to/just-before this one
                    token = [k for k, v in wordOffset[sentence].iteritems() if v == correctOffset][0] # look up the token number

                    print 'token', token
            
                db.cursor.execute('UPDATE %s SET position = ?, sentence = ?, inSentence = ? WHERE %s = ? AND doc_id = ?' % 
                                  (table,  idColumn),  (byteOffset,  sentence,  token, tag,  self.doc_id))
                db.cursor.execute('UPDATE %s SET text = ? WHERE %s = ? AND doc_id = ?' % 
                                  (table,  idColumn),  (self.tagText[tag],  tag,  self.doc_id))
            
            db.cursor.execute('UPDATE documents SET body = ? WHERE id = ?',  (self.bodyText.decode('utf-8'), self.doc_id))
            
            if db.engine == 'sqlite' and self.commitEveryDoc:
                db.conn.commit()
        
            print 'From SAX parse:'
            print self.parsedText.encode('utf-8')
            print 'From sentences + tokenisation:'
            print ' '.join(sentences)
            

        # finished importing documents - write corpus-level data
        print 'Updating DB metadata'

        if db.engine == 'mysql':
            db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_at", NOW())')
        elif db.engine == 'sqlite':
            db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_at", datetime("now") || " UTC")')
        
        # use tailing commas so that strings aren't interpreted as a list of characters, but instead a single string entry.
        db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_to_db", ?)',  (dbName, ))
        db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("imported_from_directory", ?)',  (directory, ))

        # parse the corpus .nfo and add it to the info table
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

                db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES(?, ?)',  (key, data))
        
        # save everything
        if db.engine == 'sqlite':
            db.conn.commit()
        
        return




if __name__ == '__main__':
    sys.exit('Only to be executed from CAVaT.')
