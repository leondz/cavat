#!/usr/bin/python 

# basic requirements
import os
import shutil
import sys
import string

# CAVaT config
import ConfigParser

# for database
import db

# for processing CAVaT commands
try:
    from pyparsing import ParseException
except:
    sys.exit("Couldn't load 'pyparsing'. CAVaT requires this module in order to run. To install it under Ubuntu, try 'sudo apt-get install python-pyparsing'.")
from cavatGrammar import cavatStmt,  validTags, numericFields
import cavatGrammar
import cavatBrowse

# for interactive prompt
import readline
import atexit

# for output
from cavatMessages import *
import cavatDebug


cavatVersion = 0.24
db.version = cavatVersion

def buildSqlWhereClause(wheres):
    if len(sqlWheres) > 0:
        return ' WHERE ' + ' AND '.join(wheres)
    else:
        return ''
    


# process command-line arguments
inputLine = None # holds a command that's passed as an argument to CAVaT

if len(sys.argv) > 1 and sys.argv[1] == '-c':
    inputLine = ' '.join(sys.argv[2:])

else:
    print "# CAVaT Corpus Analysis and Validation for TimeML"
    print "# Version:  %s   Support:  leon@dcs.shef.ac.uk" % (str(cavatVersion))
    print "# Enter 'help' for on-line support."



# first time execution?
if not os.path.isfile('cavat.ini'):
    # assume that this is a fresh install, that the error 
    try:
            input = raw_input('! Could not open "cavat.ini". Is this your first time running CAVaT on this system? [Yn]: ')
    except:
        sys.exit()

    if input.lower() in ('y', ''):
        try:
            shutil.copy('cavat.ini-default', 'cavat.ini')
        except:
            sys.exit('! Failed to copy default cavat.ini-default to cavat.ini.' )
        
        print '# Copied default config file into cavat.ini'
    


# load ini file
config = ConfigParser.ConfigParser()
try:
    config.read('cavat.ini')
except Exception,  e:
    print '! Failed to load ini file cavat.ini'
    sys.exit()

# module variables
try:
    moduleDir = config.get('cavat',  'moduledir')
except:
    moduleDir = 'modules'


# db connection
dbName = None
try:
    dbName = config.get('cavat',  'dbname')
except:
    pass


db.connect(config)
if dbName:
    db.changeDb(dbName)

# use default history file if nothing else is specified
try:
    historyFile = config.get('cavat',  'historyfile')
except Exception,  e:
    historyFile = '.cavat_history'


# readline code for persistent command history
histfile = os.path.join(os.environ["HOME"], historyFile)

try:
    readline.read_history_file(histfile)
except IOError:
    pass

atexit.register(readline.write_history_file, histfile)



finishedProcessing = False

while not finishedProcessing:
    
    input = None

    if not inputLine:
    
        try:
            input = raw_input('cavat> ')
            
        except KeyboardInterrupt:
            errorMsg('Cancelled',  True)
            continue
            
        except EOFError:
            errorMsg('EOF',  True)
            db.close()
            break
        
    else:
        input = inputLine
        finishedProcessing = True
    

    if not input:
        continue

    if input.lower() in ("x",  "q",  "exit",  "quit"):
        print "Thanks for using CAVaT."
        db.close()
        break


    try:
        t = cavatStmt.parseString(input)
    except ParseException,  pe:
        errorMsg('Syntax error: ' + unicode(pe))
        if input.startswith('corpus import'):
            errorMsg('Corpus directories should end with a trailing slash, and corpus names can only contain letters, numbers and special characters _ and -')
        continue


    if cavatDebug.debug:
        print t.dump()
    
    if t.action == 'show':
        
        if t.distance:
            errorMsg('Sorry; distance queries are not implemented yet.')
            continue
        
        if not dbName:
            errorMsg('First, select a corpus to run reports on, with "corpus use"')
            continue

        # build a select statement
        # execute select statement and build result array
        # output as determined (to file, to screen)

        sqlWheres = []
        sqlGroup = ''
        sqlCount = False
        sqlField = ''               # this string holds the field specification used in the SQL query (e.g. COUNT(*), reltype)
        sqlFieldName = ''       # this string holds the name of the field in the database, provided in the CAVaT query (e.g. reltype)
        sqlFieldPrint = ''          # this is the way that the field is referred to in output
        sqlTable = ''
        sqlOrder = ''
        sqlDistinct = ''

        sqlQuery = ''
        results = []
        
        whereCaption = ''
        
        
        format = 'screen'
        if t.format:
            format = t.format.lower()

        # unconditional? i.e., is there no where clause? if not, we're processing one of the more simple queries.
        
        # make sure that the request output field exists in out command parse
        
        tag = None
        try:
            tag = unicode(t.result.tag)
        except AttributeError:
            try:
                tag = unicode(t.tag)
            except AttributeError:
                errorMsg('Not sure which tag to operate on; t.tag and t.result.tag both empty. Please enable debug, enter your query again, and contact support.')
                continue
        
        tag = tag.lower()
        
        # check that we support this tag
        if tag in (validTags):
            
            # which field would we like to see?
            try:
                sqlFieldName = t.result.property
            except:
                sqlFieldName = ''
            
            sqlFieldPrint = sqlFieldName.lower()
            
            # check for queries on events that use eventinstance attributes
            if tag == 'event' and t.result.property in cavatGrammar.instanceFields.split(' '):
                sqlTable = 'instances'
            else:
                # db format uses tlinks instead of tlink; it's uniform
                sqlTable = tag + 's'
            
            dualTable_ts = False
            dualTable_ss = False
            dualTable_as = False
            
            if t.result.property == 'signaltext': # bring in signal table and signal text field
                sqlTable = 'signals s, '
                sqlFieldName = 's.text'
                sqlFieldPrint = 'signal text'
                
                if tag == 'tlink':
                    sqlTable += 'tlinks t'
                    sqlWheres.append('t.doc_id = s.doc_id')
                    sqlWheres.append('t.signalID = s.sid')
                    dualTable_ts = True
                    
                if tag == 'slink':
                    sqlTable += 'slinks sl'
                    sqlWheres.append('sl.doc_id = s.doc_id')
                    sqlWheres.append('sl.signalID = s.sid')
                    dualTable_ss = True
                    
                if tag == 'alink':
                    sqlTable += 'alinks a'
                    sqlWheres.append('a.doc_id = s.doc_id')
                    sqlWheres.append('a.signalID = s.sid')
                    dualTable_as = True
            
            
            
        else:
            errorMsg("tag '" + tag + "' unsupported, expected one of " + validTags)
            continue
        
        # sqlField is the one that we'll run our SQL query on; sqlFieldName is for presentation
        sqlField = sqlFieldName
        
        if t.condition:
            
            # check if we need to join tables
            # for when tag == event: this will be the case if either conditionField is in instances and sqlTable == events, or, if conditionField isn't in instances and sqlTable == instances
            # joins will be different, in the above 2 cases
            dualTable_ei = False
            
            if (t.conditionField in cavatGrammar.instanceFields.split(' ') and sqlTable == 'events'):
                dualTable_ei = True
                sqlField = 'e.' + sqlField
            if (t.conditionField not in cavatGrammar.instanceFields.split(' ') and sqlTable == 'instances'):
                dualTable_ei = True
                sqlField = 'i.' + sqlField
            
            # add both tables to the list, and include where clauses to bind them together
            if dualTable_ei:
                sqlTable = 'events e, instances i'
                sqlWheres.append('e.doc_id = i.doc_id')
                sqlWheres.append('i.eventID = e.eid')
            
            conditionField = t.condition.conditionField
            conditionFieldName = conditionField.capitalize()
        
            
            # do we need to join in another table?
            if conditionField == 'signaltext':
                conditionField = 's.text'
                conditionFieldName = 'signal text'
                
                # otherwise, this will already be included
                if not dualTable_ts or dualTable_ss or dualTable_as:
                    sqlTable = 'tlinks t, signals s'
                    sqlWheres.append('t.doc_id = s.doc_id')
                    sqlWheres.append('t.signalID = s.sid')
            
            
            # is this distribution report not a state report - e.g., does it list every class and its frequency?
            if not t.state:
                
                
                # just match condition value
                if not t.not_:
                    sqlWheres.append(conditionField +' = "' + t.condition.conditionValue+'"')
                    whereCaption = ' when ' + conditionFieldName + ' is "' + t.condition.conditionValue + '"'
                    
                # (or match anything but)
                else:
                    sqlWheres.append(conditionField +' <> "' + t.condition.conditionValue+'"')
                    whereCaption = ' when ' + conditionFieldName + ' differs from "' + t.condition.conditionValue + '"'
                
            else:
            # handle "state [not] <filled|unfilled>" conditions
                
                # state filled (also state not unfilled)
                if (not t.not_ and t.state.lower() == 'filled') or (t.not_ and t.state.lower() == 'unfilled'):
                    sqlWheres.append(conditionField +' IS NOT NULL')
                    whereCaption = ' when ' + conditionFieldName + ' is defined'
                    
                # state unfilled (state not filled)
                else:
                    sqlWheres.append(conditionField +' IS NULL')
                    whereCaption = ' when ' + conditionFieldName + ' is not defined'

        # process report type
        # a list report just shows the values as they are, without any accompanying data
        if t.report == 'list':
            pass
            
        elif t.report == 'distribution':
            # build a distribution report. here we will show unique values for a field, as well as their frequency in the selected corpus, showing most frequent first.
            # would be great to add a percentage column
            sqlGroup = ' GROUP BY ' + sqlFieldName
            sqlCount = 'COUNT(' + sqlFieldName + ') AS count '
            
            # run a quick pre-query to see the total number of results returned
            if not db.runQuery('SELECT '+ sqlCount + ' FROM ' + sqlTable + ' ' + buildSqlWhereClause(sqlWheres)):
                continue
            
            totalRecords = db.cursor.fetchone()[0]
            # add the .0 after totalrecords so that float division is performed
            sqlField = sqlFieldName + ', ' + sqlCount + ', (COUNT('+sqlFieldName+')/'+str(totalRecords)+'.0) AS percent'

            # if we are generating a report about a numeric value, sort the table by that value, not by frequency; this way round, it's easier to spot lumps / import into a histogram
            if (sqlTable + '.' + sqlFieldName).lower() in numericFields:
                sqlOrder = ' ORDER BY ' + sqlFieldName + ' ASC'
            else:
                sqlOrder = ' ORDER BY count DESC'
            
        # state is either "filled" or "unfilled", showing whether or not the attributed has been specified
        elif t.report == 'state':
            
            # for state reports:
            # - count all instances of tag in question
            # - find out how many of that tag have NULL for the field in question
            # - calculate (a) how many don't; (b) percentages of each group
            # - place into an array, pass to outputResults
            # - continue

            if not db.runQuery("SELECT COUNT(*) FROM " + sqlTable + buildSqlWhereClause(sqlWheres)):
                continue
            totalTags = db.cursor.fetchone()[0]
            
            sqlWheres.append(sqlFieldName + ' IS NOT NULL')

            if not db.runQuery('SELECT COUNT(*) FROM ' + sqlTable + buildSqlWhereClause(sqlWheres)):
                continue
            filledTags = db.cursor.fetchone()[0]
            
            unfilledTags = totalTags - filledTags
            
            if totalTags == 0:
                [unfilledPct,  filledPct] = ['N/A'] * 2
            else:
                filledPct = "%0.1f" % (float(filledTags) * 100 / totalTags)
                unfilledPct = "%0.1f" % (float(unfilledTags) * 100 / totalTags)
            
            results.append(['State of ' + tag.upper() + ' ' + sqlFieldName + whereCaption,  'Count'])
            results.append([sqlFieldName + ' filled',  '(' + filledPct + '%)',  filledTags])
            results.append([sqlFieldName + ' unfilled',  '(' + unfilledPct + '%)',  unfilledTags])
            
            outputResults(results,  t.report,  format)
            
            continue

        else:
            errorMsg(t.report + " unsupported, expected 'list', 'distribution' or 'state'")
    
        
        # build the WHERE clause from a list of conditions stored in sqlWheres
        sqlWhere = buildSqlWhereClause(sqlWheres)
        
        if len(results) == 0:
        
            # build and execute query
            sqlQuery = 'SELECT '+ sqlDistinct + sqlField + ' FROM ' + sqlTable + ' ' + sqlWhere + sqlGroup + sqlOrder

            if not db.runQuery(sqlQuery):
                continue
            
            results = list(db.cursor.fetchall())
            
            if t.report == 'distribution':
                results.insert(0,  [tag.upper() + ' ' + sqlFieldPrint + whereCaption,  'Frequency',  'Proportion'])
                results.append(['Total',  totalRecords])
            elif t.report == 'list':
                results.insert(0,  [tag.upper() + ' ' + sqlFieldPrint + whereCaption])
        
        # detach result-printing from result-gathering, so that we can print results regardless of where the data come from (e.g. sqlQuery, manual calculations)
        # output results as a list - switch this depending on output request (tsv, csv, latex would be handy - latex with headers bold, first column left aligned all others right)
        
        outputResults(results,  t.report,  format)
    
    
    elif t.action == 'corpus':
        
        if t.use:
            # code for db switching
            if db.changeDb(t.database):
                print "# Corpus database changed to " + t.database
                # do a version check here
                
                if not db.runQuery('SELECT data FROM info WHERE `key` = "cavat_version"'):
                    continue
                
                try:
                   dbVersion = float(db.cursor.fetchone()[0])
                except:
                    dbVersion = 0.0
                
                if dbVersion < db.version:
                    errorMsg('Database was created with an earlier version of CAVaT, not all checks or queries may work. Re-import the corpus to upgrade this database.')
                elif dbVersion > db.version:
                    errorMsg('Database was created with a newer version of CAVaT, not all checks or queries may work.')
                
                dbName = t.database
                
                continue
            
            else:
                print '! Failed to change database to ' + t.database
            
        elif t.info:
            # show corpus info - select * from info, print
            
            if not db.runQuery('SELECT * FROM info ORDER BY `key` ASC',  "no info table found?"):
                continue
            
            results = db.cursor.fetchall()
            
            print "\n# Info for corpus in database '" + dbName +"' (prefix is '" + db.prefix + "')\n"
            
            for row in results:
                print unicode(row[0]).rjust(30,  ' ') + ":  " + row[1]
            
            if not db.runQuery('SELECT COUNT(*) FROM documents'):
                continue
            
            results = db.cursor.fetchone()
            
            print "\n# Total %s documents in this corpus, including:" % (results)
            
            for tag in validTags:
                if not db.runQuery('SELECT COUNT(*) FROM ' + tag + 's'):
                    continue
                
                results = db.cursor.fetchone()
                
                print '# - %s %ss' % (unicode(results[0]).rjust(6, ' '), tag.upper())
                
            
        elif t.import_:
            
            if not t.directory.endswith('/'):
                errorMsg('Import directory must end with a slash (/), e.g. /data/corpora/timebankv1.2/data/timeml/')
                continue
            
            import importTimeML
            i = importTimeML.ImportTimeML()
            
            if not cavatDebug.debug:
                # don't care about seeing each file processed
                sys.stdout = open('/dev/null',  'w')
            
            targetDb = t.database
            
            e = None
            try:
                i.importCorpusToDb(t.directory,  targetDb)
                db.cursor.execute('INSERT INTO info(`key`, `data`) VALUES("cavat_version", ' + str(cavatVersion) + ')')
                db.conn.commit()
            except Exception,  e:
#                if cavatDebug.debug:
                import traceback
                sys.stderr.write(repr(traceback.extract_tb(sys.exc_info()[2])))

                errorMsg(str(e))

            # cleanup
            if not cavatDebug.debug:
                # restore stdout
                    sys.stdout = sys.__stdout__
            
            if dbName:
                db.changeDb(dbName) # import will have mangled this; reset it.
            
            if not e:
                print '# Corpus ' + t.database + ' imported. Enter "corpus use ' + t.database + '" to start using it.'

        
        elif t.verify:
            # check sql syntax and version of corpus (maybe check version on use, too)
            errorMsg("corpus verify not implemented")
            
        elif t.list:
            # show available databases
            print "# Listing available databases for 'corpus use'"
            
            results = db.listCorpora()
            
            print ', '.join(results)


        else:
            errorMsg("Command not understood, use corpus <use|info|check|list|import>.")
        
        
    
    
    
    elif t.action == 'debug':
        
        
        if t.state == "on":
            cavatDebug.debug = True
        else:
            cavatDebug.debug = False


        if cavatDebug.debug:
            print "# Debugging is enabled."
        else:
            print "# Debugging is disabled."
        
        continue





    elif t.action == 'help':
        print '# ============================================================================================ CAVaT help'
        
        try:
            query = t.query[0]
        except Exception:
            
            print '# Top level commands:'
            print '#   corpus   - For working with corpora and databases'
            print '#   show     - Report generation'
            print '#   check    - Run a corpus validation module'
            print '#   debug    - Toggle debug mode'
            print '#   browse   - Show details on an object in the current corpus'           
            print '#   exit     - Leave CAVaT'
            print '# Visit http://code.google.com/p/cavat/ for a full reference.'
            print '# Enter "help" followed by one of these to see the command syntax'
            continue
        
        if query == 'show':
            print '# show: Run a report, and return the results'
            print '# '            
            print '# Basic form is  '
            print '#   show <"distribution"|"list"|"state"> of <tag> <attribute>'
            print '# Distribution, list and state are report types; tag is a TimeML tag, and attribute is a field related to that tag,'
            print '# where <tag> may be one of: '+', '.join(validTags) + '.'
            print '# '
            print '# Special output:  ... as <"screen"|"csv"|"tex">'
            print '# Screen is for screen output in a fixed-width font (the default); csv returns comma-separated values, and tex a LaTex-format table.'
            print '# '
            print '# Restricted cases: ... where <attribute> is <value>'
            print '# Only performs the report for matching cases'
            print '# Also, you may use ... where <attributed> is ["not"] filled, to only match cases where a field is complete/incomplete'
            print '# '
            print '# Overall syntax:'
            print '#   <show> [where] [output]'
            print '# '
            print '# Examples:'
            print '#   show distribution of tlink reltype'
            print '#   show state of tlink signalid as tex'
            print '#   show list of instance lemma as csv'
            print '#   show distribution of timex3 position where sentence is 0'
            print '#   show distribution of tlink reltype where signalid is filled as tex'
            
            continue
            
        elif query == 'corpus':
            print '# corpus: Perform corpus maintenance'
            print '# '
            print '# Basic form is:'
            print '#   corpus <"import"|"use"|"info"|"list"|"verify">'
            print '# '
            print '# To load a directory of TimeML files (e.g. a corpus) into a new or existing CAVaT database, the following forms are valid.'
            print '#   corpus import <corpusName> from <directory>'
            print '#   corpus import <directory> to <corpusName>'
            print '# The directory name needs to end in a slash, and CAVaT\'s database user must have the appropriate permissions to create or update the database.'
            print '# '
            print '# To choose or change to another corpus:'
            print '#   corpus use <corpusName>'
            print '# '
            print '# To view a list of available corpora (for use with "corpus use"):'
            print '#   corpus list'
            print '# '
            print '# To verify the SQL syntax and version of a corpus'
            print '#   corpus verify [corpusName]'
            print '# '
            print '# Examples:'
            print '#   corpus list'
            print '#   corpus import /h/me/timebank/ to timebank_1_2'
            print '#   corpus verify'
            print '#   corpus use timebank_1_2'
            
            continue
            
        elif query == 'debug':
            print '# debug: Enable / disable debugging mode'
            print '# '
            print '# Syntax is:'
            print '#   debug ["on"|"off"]'
            print '# '
            print '# Entering "debug" on its own reports on the current state; debug on and debug off can be used to adjust the value.'
            print '# Debugging information includes parse tree data and SQL executed, amongst other query-specific data.'
            
            continue
            
        elif query == 'browse':
            print '# browse: Examine an annotated object'
            print '# '
            print '# Syntax is:'
            print '#   browse <object type> <object ID>'
            print '# Where object type is a TimeML tag, and object ID is the unique label of an instance of that tag.'
            
            continue
            
        elif query == 'help':
            print '# help: View on-line help'
            print '# '
            print '# Syntax is:'
            print '#   help [command]'
            print '# Where command is a top-level CAVaT command. Enter "help" alone to see a list of those commands.'
            
            continue
            
        elif query == 'check':
            print '# check: Run a plug-in module over a document or documents'
            print '# '
            print '# Syntax is:'
            print '#   check <module> in <docIds+|documentNames+|"all">'
            print '#   check list'
            print '# '
            print '# The modules are quite diverse. They are stored in ./modules/ as .py files, which inherit from ./cavatModule.py .'
            print '# It is recommended that modules support a "help" command, which provides information about running them.'
            print '# '
            print '# Examples:'
            print '#   check list'
            print '#   check tlink_loop help'
            print '#   check tlink_loop in wsj_0136.tml'
            print '#   check tlink_loop in 5 6 7 8'
            
            continue
            
        else:
            print '# No further help is available on this topic.'
        
    elif t.action == 'check':
        
        # return a list of files in the module directory, apart from svn data, the __init__ package file, and compiled python
        if t.list:
            print '# Available modules:'
            dirList = os.listdir(moduleDir + '/')
            for module in dirList:
                if module != '__init__.py' and module.find('.pyc') == -1 and module[0] != '.':
                    print '# - ' +module.replace('.py',  '')
            
        else:
            moduleName = t.module.lower()
            
            # check for module presence
            modulePath = moduleDir + '/' + moduleName + '.py'
            if not os.path.exists(modulePath):
                errorMsg('No module of that name is installed - looking for ' + modulePath)
                continue
            
            # try to import module
            if cavatDebug.debug:
                print 'Loading ' + modulePath
            
            try:
                exec('from modules.' + moduleName + ' import ' + moduleName)
                
            except Exception,  e:
                import traceback
                sys.stderr.write(repr(traceback.extract_tb(sys.exc_info()[2])))
                errorMsg(unicode(e) + '. Path is ' + unicode(sys.path))
                continue
            
            # instantiate and check module compatibility
            try:
                exec('checker = ' + moduleName + '()')
            except Exception,  e:
                errorMsg(unicode(e))
                continue
            
            compatible = checker.getCompatibility(cavatVersion)
            
            if compatible == None:
                errorMsg('Warning: module may not be compatible')
            elif compatible:
                pass
            else:
                errorMsg('Module is not compatible with this version of CAVaT; check skipped')
                continue
            
            if t.help:
                checker.help()
                continue
            
            # build a list containing id(s) of documents to be processed
            if t.target:
                sourceList = t.target
                
            else:
                # do we have a browse context set?
                if dbName not in cavatBrowse.doc.keys():
                    
                    errorMsg('Please specify document(s)')
                    continue
                    
                else:
                    sourceList = [unicode(cavatBrowse.doc[dbName])]

            
            docList = []
            
            if sourceList[0].lower() == 'all':
                
                if not db.runQuery('SELECT id FROM documents'):
                    continue
                
                results = db.cursor.fetchall()
                
                for row in results:
                    docList.append(unicode(row[0]))
                
            elif not sourceList[0].isdigit():
                # it's not a document id; try to look up all strings in docList against documents.docname
                
                for source in sourceList:
                    if not db.runQuery('SELECT id FROM documents WHERE docname = "' + source + '"'):
                        continue
                    
                    results = db.cursor.fetchone()
                    
                    if not results:
                        errorMsg('Document "' + source + '" not in corpus')
                        continue
                    
                    docList.append(unicode(results[0]))
                
                
            elif sourceList[0].isdigit():
                
                for source in sourceList:
                    if not db.runQuery('SELECT id FROM documents WHERE id = "' + source + '"'):
                        continue
                    
                    results = db.cursor.fetchone()
                    
                    if not results:
                        errorMsg('Document ID "' + source + '" not in corpus')
                        continue
                    
                    docList.append(source)
                
            else:
                errorMsg('Unsure how to interpret document list')
                
            
            
            if len(docList) == 0:
                errorMsg('No valid document references to check')
                continue
            
            allGood = True
            
            # for each doc in list, call the module
            if cavatDebug.debug:
                print 'Running check on doc_ids: ' + unicode(docList)

            for doc in docList:
                checkResult = checker.checkDocument(doc)
                allGood = allGood and checkResult
            
            if allGood: # if the documents pass, we may not see any other output - so inform user of result.
                print '# Check OK.'
    
    
    elif t.action == 'browse':
        if not dbName:
            errorMsg('Please select a corpus with "corpus use" first; "corpus list" will show which corpora are available.')
            continue

        if t.doc:
    
            if t.list:
                if not db.runQuery('SELECT id, docname FROM documents ORDER BY id ASC'):
                    continue
                

                for doc_ in db.cursor.fetchall():
                    print 'DOCUMENT',  unicode(doc_[0]).rjust(6), ' ', doc_[1]
                
                continue

            
            # fetch document id
            browsedoc = None
            docname = None
            
            # populate both name and id fields
            if t.target.isdigit():
                browsedoc = t.target
                if not db.runQuery('SELECT docname FROM documents WHERE id = "%s"' % (t.target)):
                    errorMsg('Document ID %s not found in corpus' % (t.target))
                    continue
                docname = db.cursor.fetchone()[0]
                
            else:
                docname = t.target
                if not db.runQuery('SELECT id FROM documents WHERE docname = "%s"' % (t.target)):
                    errorMsg('Document %s not found in corpus' % (t.target))
                    continue
                browsedoc = db.cursor.fetchone()[0]
                
            # set value in cavatBrowse.doc for this corpus
            print '# Now browsing document id %s in this corpus (%s)' % (browsedoc, docname)
            cavatBrowse.doc[dbName] = int(browsedoc)
        
        elif t.tag:
            if t.tag not in validTags:
                errorMsg('Unsupported tag: ' + t.tag)
                continue
            
            # if there's no selected document, abort
            if dbName not in cavatBrowse.doc.keys():
                errorMsg('Please choose a document with "browse doc <doc_id|docname>" first.')
                continue

            # work out the name of the id attribute and column for this tag/table
            idPrefix = cavatGrammar.idPrefixes[t.tag]
            idColumn = idPrefix + 'id'

            if t.list: # are we just going to list all IDs?
                if not db.runQuery('SELECT %s FROM %ss WHERE doc_id = %s ORDER BY %s' % (idColumn,  t.tag,  cavatBrowse.doc[dbName],  idColumn)):
                    continue
                
                results = list(db.cursor.fetchall())
                for result in results:
                    print t.tag.upper(), result[0]
                
                
            elif t.value: # show detail for one specific tag
                
                # can reference tags by id or string id - e.g., <signal sid="s1"> can be viewed with browse signal 1 or browse signal s1
                if t.value.isdigit():
                    value = idPrefix + t.value
                else:
                    value = t.value.lower()
                
                # get all fields for the appropriate tag
                if not db.runQuery('SELECT * FROM %ss WHERE doc_id = %s AND %s = "%s"' % (t.tag,  cavatBrowse.doc[dbName], idColumn,  value)):
                    continue
                
                # get a list of column headings too
                try:
                    results = list(db.cursor.fetchone())
                except:
                    errorMsg('Element not found in this document')
                    continue
                fields = [name for (name, a, b, c, d, e, f) in db.cursor.description]
                # build a dict using column headings as keys
                browsed = dict(zip(fields, results))
                
                # call method for output in cavatMessages
                if t.format:
                    outputBrowse(browsed,  t.tag,  t.format)
                else:
                    outputBrowse(browsed,  t.tag)
        
        elif t.sentence:
            if not db.runQuery('SELECT text FROM sentences WHERE doc_id = %d AND sentenceID = %d' % (cavatBrowse.doc[dbName], int(t.id))):
                continue
                
            try:
                print db.cursor.fetchone()[0].decode('utf-8')
            except TypeError:
                errorMsg("Couldn't find sentence %d in this document" % t.id)
        
    else:
        errorMsg("Unsupported command; please enable debug ('debug on'), try again, and contact support with the output.")
    
    
    
