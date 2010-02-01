# parent module for CAVaT

class CavatModule:
    
    moduleName = '[undefined]'
    moduleDescription = ''
    
    moduleVersion = 0
    
    _minVersion = 0
    _maxVersion = 0


    def __init__(self):
        print '# ' + self.moduleName + ' v.' + self.moduleVersion + ' loaded'    
    
    
    def getCompatibility(self,  cavatVersion):
        # given a CAVaT version number, we should return True, False or None (for unknown compatiblity)
        
        if cavatVersion < self._minVersion:
            return False

        if cavatVersion > self._maxVersion:
            return None
        
        return True


    def checkDocument(self,  doc_id):
        print 'Dummy check'
        return
