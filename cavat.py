#!/usr/bin/python 

import readline
from pyparsing import ParseException
import os
import sys
import string
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import MySQLdb
import atexit
import ConfigParser

from cavatGrammar import cavatStmt,  validTags, numericFields
from cavatMessages import *
import cavatDebug
import db
from db import runQuery

def buildSqlWhereClause(wheres):
    if len(sqlWheres) > 0:
        return ' WHERE ' + ' AND '.join(wheres)
    else:
        return ''
    

cavatVersion = 0.1


# process command-line arguments
inputLine = None # holds a command that's passed as an argument to CAVaT

if len(sys.argv) > 1 and sys.argv[1] == '-c':
    inputLine = ' '.join(sys.argv[2:])

else:
    print "# CAVaT Corpus Analysis and Validation for TimeML"
    print "# Version:  %s   Support:  leon@dcs.shef.ac.uk" % (str(cavatVersion))



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

# db variables
try:
    dbPrefix = config.get('cavat',  'dbprefix')
    dbUser = config.get('cavat',  'dbuser')
    dbHost = config.get('cavat',  'dbhost')
except Exception,  e:
    print '! Failure reading ini file: ' + str(e)
    sys.exit()

# if no pass or a blank pass is set in the database, prompt for a mysql password
try:
    dbPass = config.get('cavat',  'dbpass')
    if not dbPass:
        raise Exception
except Exception,  e:
    from getpass import getpass
    dbPass = getpass('Enter MySQL password for user "' + dbUser + '": ').strip()

dbName = None
try:
    dbName = config.get('cavat',  'dbname')
except:
    pass


db.connect(dbHost,  dbUser,  dbPass)
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
            break
            
        except EOFError:
            errorMsg('EOF')
            break
        
    else:
        input = inputLine
        finishedProcessing = True
    

    if not input:
        errorMsg('Enter "help" to explore the command hierarchy.')
        continue

    if input.lower() in ("x",  "q",  "exit",  "quit"):
        print "Thanks for using CAVaT."
        break


    try:
        t = cavatStmt.parseString(input)
    except ParseException,  pe:
        errorMsg('Syntax error: ' + str(pe))
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
        
        # make sure that the request output field exists
        
        tag = None
        try:
            tag = str(t.result.tag)
        except AttributeError:
            try:
                tag = str(t.tag)
            except AttributeError:
                errorMsg('Not sure which tag to operate on; t.tag and t.result.tag both empty. Please enable debug, enter your query again, and contact support.')
                continue
        
        if tag in (validTags):
            sqlTable = tag.lower() + 's'
            try:
                sqlFieldName = t.result.property
            except:
                sqlFieldName = ''
            
        else:
            errorMsg("tag '" + tag + "' unsupported, expected one of " + validTags)
            continue
        
        sqlField = sqlFieldName
        
        if t.condition:
            
            if not t.state:
            
                if not t.not_:
                    sqlWheres.append(t.condition.conditionField +' = "' + t.condition.conditionValue+'"')
                    whereCaption = ' when ' + t.condition.conditionField.capitalize() + ' is "' + t.condition.conditionValue + '"'
                    
                else:
                    sqlWheres.append(t.condition.conditionField +' <> "' + t.condition.conditionValue+'"')
                    whereCaption = ' when ' + t.condition.conditionField.capitalize() + ' differs from "' + t.condition.conditionValue + '"'
                
            else:
                
                if (not t.not_ and t.state.lower() == 'filled') or (t.not_ and t.state.lower() == 'unfilled'):
                    sqlWheres.append(t.condition.conditionField +' IS NOT NULL')
                    whereCaption = ' when ' + t.condition.conditionField.capitalize() + ' is defined'
                    
                else:
                    sqlWheres.append(t.condition.conditionField +' IS NULL')
                    whereCaption = ' when ' + t.condition.conditionField.capitalize() + ' is not defined'

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
            if not runQuery('SELECT '+ sqlCount + ' FROM ' + sqlTable + ' ' + buildSqlWhereClause(sqlWheres)):
                continue
            
            totalRecords = db.cursor.fetchone()[0]
            sqlField = sqlFieldName + ', ' + sqlCount + ', CAST((COUNT('+sqlFieldName+')/'+str(totalRecords)+') AS DECIMAL(10,10)) AS percent'

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

            if not runQuery("SELECT COUNT(*) FROM " + sqlTable + buildSqlWhereClause(sqlWheres)):
                continue
            totalTags = db.cursor.fetchone()[0]
            
            sqlWheres.append(sqlFieldName + ' IS NOT NULL')

            if not runQuery('SELECT COUNT(*) FROM ' + sqlTable + buildSqlWhereClause(sqlWheres)):
                continue
            filledTags = db.cursor.fetchone()[0]
            
            unfilledTags = totalTags - filledTags
            
            filledPct = "%0.1f" % (float(filledTags) * 100 / totalTags)
            unfilledPct = "%0.1f" % (float(unfilledTags) * 100 / totalTags)
            
            results.append(['State of ' + tag.capitalize() + ' ' + sqlFieldName + whereCaption,  'Count'])
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

            if not runQuery(sqlQuery):
                continue
            
            results = list(db.cursor.fetchall())
            
            if t.report == 'distribution':
                results.insert(0,  [tag.capitalize() + ' ' + sqlFieldName + whereCaption,  'Frequency',  'Proportion'])
                results.append(['Total',  totalRecords])
            elif t.report == 'list':
                results.insert(0,  [tag.capitalize() + ' ' + sqlFieldName + whereCaption])
        
        # detach result-printing from result-gathering, so that we can print results regardless of where the data come from (e.g. sqlQuery, manual calculations)
        # output results as a list - switch this depending on output request (tsv, csv, latex would be handy - latex with headers bold, first column left aligned all others right)
        
        outputResults(results,  t.report,  format)
    
    
    elif t.action == 'corpus':
        
        if t.use:
            # code for db switching
            
            if t.database != dbPrefix:
                dbName = dbPrefix + '_' + t.database
            else:
                dbName = dbPrefix
            
            try:
                db.changeDb(dbName)
            except Exception,  e:
                errorMsg("Corpus database change failed "+str(e))
                continue
            
            print "# Corpus database changed to " + t.database
            
        elif t.info:
            # show corpus info - select * from info, print
            
            if not runQuery('SELECT * FROM info ORDER BY `key` ASC',  "no info table found?"):
                continue
            
            results = db.cursor.fetchall()
            
            print "\n# Info for corpus in database '" + dbName +"' (prefix is '" + dbPrefix + "')\n"
            
            for row in results:
                print str(row[0]).rjust(30,  ' ') + ":  " + row[1]
            
            
        elif t.import_:
            
            if not t.directory.endswith('/'):
                errorMsg('Import directory must end with a slash (/), e.g. /data/corpora/timebankv1.2/data/timeml/')
                continue
            
            import importTimeML
            i = importTimeML.ImportTimeML()
            
            
            if not cavatDebug.debug:
                # don't care about seeing each file processed
                sys.stdout = open('/dev/null',  'w')
            
            if t.database == dbPrefix:
                targetDb = dbPrefix
            else:
                targetDb = dbPrefix + '_' + t.database
            
            
            try:
                i.importCorpusToDb(t.directory,  targetDb)
            except Exception,  e:
                errorMsg(str(e))
                
                if not cavatDebug.debug:
                    # restore stdout
                    sys.stdout = sys.__stdout__

                continue

            if not cavatDebug.debug:
                # restore stdout
                    sys.stdout = sys.__stdout__
            
            print '# Corpus ' + t.database + ' imported. Enter "corpus use ' + t.database + '" to start using it.'

        
        elif t.verify:
            # check sql syntax and version of corpus (maybe check version on use, too)
            errorMsg("corpus verify not implemented")
            
        elif t.list:
            # show available databases
            print "# Listing available databases for 'corpus use'"
            
            if not runQuery('SHOW DATABASES LIKE "' + dbPrefix + '%"'):
                continue
            
            results = db.cursor.fetchall()
            
            for row in results:
                listedDb = str(row[0])
                
                # strip prefix from databases
                if listedDb != dbPrefix:
                    listedDb = listedDb.replace(dbPrefix + '_',  '')
                
                print '', listedDb


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
            print '#   corpus - For working with corpora and databases'
            print '#   show - Report generation'
            print '#   check - Run a corpus validation module'
            print '#   debug - Toggle debug mode'
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
                errorMsg(str(e) + '. Path is ' + str(sys.path))
                continue
            
            # instantiate and check module compatibility
            try:
                exec('checker = ' + moduleName + '()')
            except Exception,  e:
                errorMsg(str(e))
                continue
            
            compatible = checker.getCompatibility(cavatVersion)
            
            if compatible == None:
                errorMsg('Warning: module may not be compatible')
            elif compatible:
                pass
            else:
                errorMsg('Module is not compatible with this version of CAVaT; check skipped')
                continue
            
            # build a list containing id(s) of documents to be processed
            sourceList = t.target
            docList = []
            
            if sourceList[0].lower() == 'all':
                
                if not runQuery('SELECT id FROM documents'):
                    continue
                
                results = db.cursor.fetchall()
                
                for row in results:
                    docList.append(str(row[0]))
                
            elif not sourceList[0].isdigit():
                # it's not a document id; try to look up all strings in docList against documents.docname
                
                for source in sourceList:
                    if not runQuery('SELECT id FROM documents WHERE docname = "' + source + '"'):
                        continue
                    
                    results = db.cursor.fetchone()
                    
                    if not results:
                        errorMsg('Document "' + source + '" not in corpus')
                        continue
                    
                    docList.append(str(results[0]))
                
            elif sourceList[0].isdigit():
                pass
                
            else:
                errorMsg('Unsure how to interpret document list')
                
            
            
            
            # for each doc in list, call the module
            if cavatDebug.debug:
                print 'Running check on doc_ids: ' + str(docList)

            for doc in docList:
                checker.checkDocument(doc)
    
    
    else:
        errorMsg("Unsupported command; please enable debug ('debug on'), try again, and contact support with the output.")
    
    
    
