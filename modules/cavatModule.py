# parent class for CAVaT
import db
from db import runQuery
import cavatDebug

class CavatModule:
    
    moduleName = '[undefined]'
    moduleDescription = ''
    
    moduleVersion = 0
    
    _minVersion = 0
    _maxVersion = 0


    def __init__(self):
        print '# ' + self.moduleName + ' v' + str(self.moduleVersion) + ' loaded'    
    
    
    def startup(self,  doc_id):
        
        if not runQuery('SELECT docname FROM documents WHERE id = ' + doc_id):
            # document not found
            print '! No document in corpus with id ' + doc_id
            return False
        
        results = db.cursor.fetchone()
        
        docName = str(results[0])
        
        if cavatDebug.debug:
            print "# Checking " + docName + ' (id ' + doc_id + ')'
        
        return docName
    
    
    def getCompatibility(self,  cavatVersion):
        # given a CAVaT version number, we should return True, False or None (for unknown compatiblity)
        
        if cavatVersion < self._minVersion:
            return False

        if cavatVersion > self._maxVersion:
            return None
        
        return True


    def checkDocument(self,  doc_id):
        
        docName = self.startup(doc_id)
        if not docName:
            return False        

        
        print 'Dummy check'
        return True

    def help(self):
        # print out help regarding module usage
        print '# ' + self.moduleDescription
        return
    
