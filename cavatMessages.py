import math
import sys

from cavatDebug import debug

def round_figures(x, n):
    # round, but trim the number of figures returned after the decimal for large numbers.
    amount_to_round = 3
    
    try: # log10(0) raises an exception
        amount_to_round = int(n - math.ceil(math.log10(abs(x))))
    except ValueError,  e:
        amount_to_round = 1
    
    return round(x, amount_to_round)

def errorMsg(message,  LF = False):
    
        # should we do a linefeed before the error message (e.g. if Ctrl-C has been pressed)?
        if LF:
            print
        
        sys.stderr.write('! ' + str(message) + "\n")


def latexSafe(data):
    data = data.replace('%',  '\\%')
    data = data.replace('_',  '\\_')
    return data
    


def outputResults(results,  reportType,  format = 'screen'):

    screenSeparator = '  \t '
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
            row = map(unicode, row)
            print '"' + '","'.join(row) + '"'
        
    elif format == 'tex':
        header = results.pop(0)
        
        
        columns = len(header)
        
        # latex-escape any percentage symbols (otherwise they act as comments)
        header = map(unicode,  header)
        header = map(latexSafe,  header)
        
        caption = reportType.capitalize() + ' of ' + header[0].replace(' "',  ' ``')
        label = 'tab:' + '-'.join(header).replace(' ',  '').replace('"',  '') + '-' + reportType
        
        print "\\begin{table}"
        print "\\caption{" + caption + "}"
        print "\\label{" + label + "}"
        print "\\begin{tabular}{ | l " + ('| r ') * columns + "| }"
        
        print "\\hline"
        print '\\textbf{' + '} & \\textbf{'.join(header) + '} \\\\'
        print "\\hline"

        
        for row in results:
            
            row = list(row)
            
            if reportType == 'distribution':
                if len(row) > 2:
                    row[2] = str(round_figures(float(row[2]) * 100, 3)) + '%'
                else:
                    print '\\hline'
                    row.append('')
            
            
            row = map(unicode,  row)
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
            
            row = map(unicode, row)
            
            if reportType == 'list':
                print row[0]
                
            elif reportType == 'distribution':
                # convert row to list (originally tuple from mysql result), and then re-order to give count / label
                row = list(row)
                [row[0],  row[1]] = [row[1],  row[0]]
                
                # handle Total row, which has no percentage column
                if len(row) > 2:
                    row[2] = round_figures(float(row[2]) * 100, 3)
                    print str(row[0]).rjust(rightPad,  ' ') + screenSeparator + row[1] + screenSeparator + str(row[2]) + '%'
                else:
                    print str(row[0]).rjust(rightPad,  ' ') + screenSeparator + row[1]
                
            elif reportType == 'state':
                # re-order columns, so that we have count / state / percentage
                [row[0],  row[1],  row[2]] = [row[2],  row[0],  row[1]]
                print str(row[0]).rjust(rightPad,   ' ') + screenSeparator + row[1] + screenSeparator + row[2]
                
            else:
                print "\t".join(row)


def outputBrowse(browsed, tag, format = 'screen'):

    if format == 'screen':
        
        for k, v in browsed.iteritems():
            print "%s:  %s" % (k.ljust(13),  v)

    elif format == 'timeml':
        
        tagOutput = '<' + tag.upper()
        
        for k, v in browsed.iteritems():
            
            if v is None: # all columns will be returned from db; don't include empty attributes in the output timeml
                continue
            
            # skip doc_id meta-information
            if k == 'doc_id':
                continue
            
            # map tlink arg1/arg2 onto interval-type-specific attribute names
            
            if tag == 'tlink':
                if k == 'arg1':
                    if v[0] == 'e':
                        k = 'eventInstanceID'
                    elif v[0] == 't':
                        k = 'timeID'
                elif k == 'arg2':
                    if v[0] == 'e':
                        k = 'relatedToEventInstance'
                    elif v[0] == 't':
                        k = 'relatedToTime'
            
            
            tagOutput += ' ' + k + '="' + str(v) + '"'
        
        tagOutput += ' />'
        
        print tagOutput

    if format == 'csv':
        
        print '"' + '","'.join(browsed.keys()) + '"'
        print '"' + '","'.join(map(unicode, browsed.values())) + '"'
        
