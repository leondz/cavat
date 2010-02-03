from cavatModule import CavatModule
import db
from db import runQuery
import cavatDebug

class tlink_loop(CavatModule):
    
    moduleName = 'TLINK loop checker'
    moduleDescription = 'Find TLINKs that reference the same event instance with both arguments, and are thus redundant / misleading'
    
    moduleVersion = '1'
    
    _minVersion = 0.1
    _maxVersion = 0.999
    
    def checkDocument(self,  doc_id):
        
        if not runQuery('SELECT docname FROM documents WHERE id = ' + doc_id):
            return
        
        results = db.cursor.fetchone()
        
        docName = str(results[0])
        
        if cavatDebug.debug:
            print "# Checking " + docName + ' (id ' + doc_id + ')'
        
        # look at where we're linking an event instance to itself
        if not runQuery('SELECT lid,relType, arg1 FROM tlinks WHERE arg1 = arg2 AND doc_id = ' + doc_id + ' ORDER BY CAST(SUBSTRING(lid,2) AS SIGNED)'):
            return
        
        results = db.cursor.fetchall()
        
        if results:
            
            print "# Checking " + docName + ' (id ' + doc_id + ')'
            
            for row in results: 
                print 'TLINK ID %s matches, type %s, event %s' % (row[0],  row[1],  row[2])
        else:
            if cavatDebug.debug:
                print 'No looping TLINKs found in this document.'
