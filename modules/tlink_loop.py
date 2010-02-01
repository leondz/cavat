from cavatModule import CavatModule
import db
from db import runQuery
from cavatDebug import debug

class tlink_loop(CavatModule):
    
    moduleName = 'TLINK loop checker'
    moduleDescription = 'Find TLINKs that reference the same event instance with both arguments, and are thus redundant / misleading'
    
    moduleVersion = '1'
    
    _minVersion = 0.1
    _maxVersion = 0.999
    
    def checkDocument(self,  doc_id):

        if not runQuery('SELECT docname FROM documents WHERE id = ' + doc_id):
            return
        
        results = db.cursor.fetchall()
        
        docName = str(results[0])
        
        
        # fetch and print doc name
        print 'Dummy check for document ' + docName
