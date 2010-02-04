import sys
import math
from cavatDebug import debug

def round_figures(x, n):
    return round(x, int(n - math.ceil(math.log10(abs(x)))))

def errorMsg(message,  LF = False):
    
        # should we do a linefeed before the error message (e.g. if Ctrl-C has been pressed)?
        if LF:
            print
        
        sys.stderr.write('! ' + message + "\n")


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
            row = map(str, row)
            print '"' + '","'.join(row) + '"'
        
    elif format == 'tex':
        header = results.pop(0)
        
        
        columns = len(header)
        
        # latex-escape any percentage symbols (otherwise they act as comments)
        header = map(str,  header)
        header = map(latexSafe,  header)
        
        caption = reportType.capitalize() + ' of ' + header[0]
        label = 'tab:' + '-'.join(header).replace( ' ',  '') + '-' + reportType
        
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
                row[2] = round_figures(float(row[2]) * 100, 3)
                print str(row[0]).rjust(rightPad,  ' ') + screenSeparator + row[1] + screenSeparator + str(row[2]) + '%'
                
            elif reportType == 'state':
                # re-order columns, so that we have count / state / percentage
                [row[0],  row[1],  row[2]] = [row[2],  row[0],  row[1]]
                print str(row[0]).rjust(rightPad,   ' ') + screenSeparator + row[1] + screenSeparator + row[2]
                
            else:
                print "\t".join(row)
