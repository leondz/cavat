#!/usr/bin/python 

import readline
from pyparsing import ParseException
import os
import sys
import string
import MySQLdb
import atexit
from cavatGrammar import cavatStmt,  validTags

def buildSqlWhereClause(wheres):
    if len(sqlWheres) > 0:
        return ' WHERE ' + ' AND '.join(wheres)
    else:
        return ''
    
    
def latexSafe(data):
    data = data.replace('%',  '\\%')
    data = data.replace('_',  '\\_')
    return data
    
def errorMsg(message,  LF = False):
    
        # should we do a linefeed before the error message (e.g. if Ctrl-C has been pressed)?
        if LF:
            print
        
        sys.stderr.write('! ' + message + "\n")


def runQuery(sqlQuery,  failureMessage = 'Query failed.'):
    global cursor,  debug

    if debug:
        print sqlQuery

    try:
        cursor.execute(sqlQuery)
        
    except Exception,  e:
        errorMsg(failureMessage)
        errorMsg("SQL was: \t" + sqlQuery)
        errorMsg("SQL error: \t"+ str(e))
        return False

    return True
    

def outputResults(results,  reportType,  format = 'screen'):

    screenSeparator = '  '
    rightPad = 11

    global debug
    if debug:
        print "results: ",  results
        print "report type: ",  reportType
        print "format: ",  format

    
    
    if format == 'csv':
        
        # dump out a CSV
        for row in results:
            
            # convert all entities to string
            row = map(str, row)
            print '"' + '","'.join(row) + '"'
        
    elif format == 'tex':
        header = results.pop(0)
        
        
        columns = len(header)
        
        # latex-escape any percentage symbols (otherwise they act as comments)
        header = map(str,  header)
        header = map(latexSafe,  header)
        
        caption = reportType.capitalize() + ' of ' + header[0]
        label = 'tab:' + '-'.join(header).replace(' ',  '') + '-' + reportType
        
        print "\\begin{table}"
        print "\\caption{" + caption + "}"
        print "\\label{" + label + "}"
        print "\\begin{tabular}{ | l " + ('| r ') * columns + "| }"
        
        print "\\hline"
        print '\\textbf{' + '} & \\textbf{'.join(header) + '} \\\\'
        print "\\hline"
        
        for row in results:
            
            row = map(str,  row)
            row = map(latexSafe,  row)
            
            print ' & '.join(row) + ' \\\\'
        
        print "\\hline"
        print "\\end{tabular}"
        print "\\end{table}"
        
        
    else:
        
        # first row is always headers
        # screen printing mode
        header = results.pop(0)
        headline = ''
        
        if reportType == 'list':
            headline = header[0]
            
        elif reportType == 'state' or reportType == 'distribution': # switch column order for screen, to keep numbers displayed close to their label
            [header[0],  header[1]] = [header[1],  header[0]]
            headline = str(header[0]).rjust(rightPad,  ' ') + screenSeparator + screenSeparator.join(header[1:])
        
        print headline
        print ' ' + '=' * (len(headline) + (rightPad - 2))

        for row in results:
            
            row = map(str,  row)
            
            if reportType == 'list':
                print row[0]
                
            elif reportType == 'distribution':
                # convert row to list (originally tuple from mysql result), and then re-order to give count / label
                row = list(row)
                [row[0],  row[1]] = [row[1],  row[0]]
                print str(row[0]).rjust(rightPad,  ' ') + screenSeparator + row[1]
                
            elif reportType == 'state':
                # re-order columns, so that we have count / state / percentage
                [row[0],  row[1],  row[2]] = [row[2],  row[0],  row[1]]
                print str(row[0]).rjust(rightPad,   ' ') + screenSeparator + row[1] + screenSeparator + row[2]
                
            else:
                print "\t".join(row)
    
    



histfile = os.path.join(os.environ["HOME"], ".cavat_history")
try:
    readline.read_history_file(histfile)
except IOError:
    pass

atexit.register(readline.write_history_file, histfile)

dbName = 'timebank'
dbPrefix = 'timebank'

conn = MySQLdb.connect (host = "localhost", user = "timebank", passwd = "timebank")
conn.select_db(dbName)
cursor = conn.cursor()

numericFields = ['events.doc_id',  'events.position',  'events.sentence',  'instances.doc_id', 'signals.doc_id',  'signals.position',  'signals.sentence',  'timex3s.doc_id',  'timex3s.position',  'timex3s.sentence',  'tlinks.doc_id']



print "# CAVaT Corpus Analysis and Validation for TimeML"
print "# Support:  leon@dcs.shef.ac.uk"

debug = False

while True:
    
    input = None
    
    try:
        input = raw_input('cavat> ')
        
    except KeyboardInterrupt:
        errorMsg('Cancelled',  True)
        break
        
    except EOFError:
        errorMsg('EOF')
        break
    
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

    if debug:
        print t.dump()
    
    if t.action == 'show':

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
        if t.result.tag in (validTags):
            sqlTable = t.result.tag.lower() + 's'
            sqlFieldName = t.result.property
            
        else:
            errorMsg("tag '" + t.result.tag + "' unsupported, expected one of " + validTags)
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
            sqlField = sqlFieldName + ', COUNT(' + sqlFieldName + ') AS count '

            # if we are generating a report about a numeric value, sort the table by that value, not by frequency; this was round, it's easier to spot lumps / import into a histogram
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
            totalTags = cursor.fetchone()[0]
            
            sqlWheres.append(sqlFieldName + ' IS NOT NULL')

            if not runQuery('SELECT COUNT(*) FROM ' + sqlTable + buildSqlWhereClause(sqlWheres)):
                continue
            filledTags = cursor.fetchone()[0]
            
            unfilledTags = totalTags - filledTags
            
            filledPct = "%0.1f" % (float(filledTags) * 100 / totalTags)
            unfilledPct = "%0.1f" % (float(unfilledTags) * 100 / totalTags)
            
            results.append(['State of ' + t.result.tag.capitalize() + ' ' + sqlFieldName + whereCaption,  'Count'])
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
            
            results = list(cursor.fetchall())
            
            if t.report == 'distribution':
                results.insert(0,  [t.result.tag.capitalize() + ' ' + sqlFieldName + whereCaption,  'Frequency'])
            elif t.report == 'list':
                results.insert(0,  [t.result.tag.capitalize() + ' ' + sqlFieldName + whereCaption])
        
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
                conn.select_db(dbName)
            except Exception,  e:
                errorMsg("Corpus database change failed "+str(e))
                continue
            
            print "# Corpus database changed to " + t.database
            cursor = conn.cursor()
            
        elif t.info:
            # show corpus info - select * from info, print
            
            if not runQuery('SELECT * FROM info ORDER BY `key` ASC',  "no info table found?"):
                continue
            
            results = cursor.fetchall()
            
            print "\n# Info for corpus in database '" + dbName +"' (prefix is '" + dbPrefix + "')\n"
            
            for row in results:
                print str(row[0]).rjust(30,  ' ') + ":  " + row[1]
            
            
        elif t.import_:
            
            if not t.directory.endswith('/'):
                errorMsg('Import directory must end with a slash (/), e.g. /data/corpora/timebankv1.2/data/timeml/')
                continue
            
            import importTimeML
            i = importTimeML.ImportTimeML()
            
            
            if not debug:
                # don't care about seeing each file processed
                sys.stdout = open('/dev/null',  'w')
                
            try:
                i.importCorpusToDb(t.directory,  dbPrefix + '_' + t.database)
            except Exception,  e:
                errorMsg(str(e))
                
                if not debug:
                    # restore stdout
                    sys.stdout = sys.__stdout__

                continue

            if not debug:
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
            
            results = cursor.fetchall()
            
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
            debug = True
        else:
            debug = False


        if debug:
            print "# Debugging is enabled."
        else:
            print "# Debugging is disabled."
        
        continue





    elif t.action == 'help':
        errorMsg('Not implemented, sorry')
    
    
    else:
        errorMsg("Unsupported command")
    
    
    
