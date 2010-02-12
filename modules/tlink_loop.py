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



    def uniq(self, seq, idfun=None):  
        
        # order preserving 
        if idfun is None: 
            def idfun(x): return x 
        seen = {} 
        result = [] 
        for item in seq: 
            marker = idfun(item) 
            # in old Python versions: 
            # if seen.has_key(marker) 
            # but in new ones: 
            if marker in seen: continue 
            seen[marker] = 1 
            result.append(item) 
        return result

    
    def checkDocument(self,  doc_id):
        
        if not runQuery('SELECT docname FROM documents WHERE id = ' + doc_id):
            # document not found
            print '! No document in corpus with id ' + doc_id
            return
        
        results = db.cursor.fetchone()
        
        docName = str(results[0])
        
        if cavatDebug.debug:
            print "# Checking " + docName + ' (id ' + doc_id + ')'

        loopedTlinks = []

        # look at where we're linking an event instance to itself
        if not runQuery('SELECT lid, relType, arg1, arg2 FROM tlinks WHERE arg1 = arg2 AND doc_id = ' + doc_id + ' ORDER BY CAST(SUBSTRING(lid,2) AS SIGNED)'):
            return
        
        loopedTlinks = db.cursor.fetchall()
        
        # look at where we're linking an event instance to itself
        if not runQuery('SELECT lid, reltype, arg1, arg2 FROM tlinks AS t, instances AS i1, instances AS i2 WHERE t.arg1 = i1.eiid AND t.arg2 = i2.eiid AND t.doc_id = i1.doc_id AND t.doc_id = i2.doc_id AND i1.eventID = i2.eventID AND t.doc_id = ' + doc_id + ' ORDER BY CAST(SUBSTRING(lid,2) AS SIGNED)'):
            return
        
        loopedTlinks = self.uniq(loopedTlinks + db.cursor.fetchall())
        
        
        if loopedTlinks:
            print "# Checking " + docName + ' (id ' + doc_id + ')'
            
            for row in loopedTlinks: 
                print 'TLINK ID %s matches, type %s, event %s / %s' % (row[0],  row[1],  row[2],  row[3])
            
            return False
            
        else:
            if cavatDebug.debug:
                print 'No looping TLINKs found in this document.'
            
            return True
