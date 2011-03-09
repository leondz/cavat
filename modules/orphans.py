from cavatModule import CavatModule
import db
from db import runQuery
import cavatDebug

class orphans(CavatModule):
    
    moduleName = 'Orphaned tag detection'
    moduleDescription = 'List events, instances, signals and timex3s that are unattached. May report false positives (e.g. over-report orphans) as DB format ignores SLINKs and ALINKs.'
    
    moduleVersion = '1'
    
    _minVersion = 0.1
    _maxVersion = 0.999
    
    def checkDocument(self,  doc_id):
        
        docName = self.startup(doc_id)
        if not docName:
            return False

        
        orphans = set()
        
        # orphan cases:
        #  timex3 not in a link
        #  instance not in a link
        #  event not got an instance
        #  instance not got an event
        #  signals not referenced by any tlink or instance
        #  

        # build a list of intervals already in tlinks

        linkedIntervals = set()
        
        queries = ['SELECT DISTINCT arg2 FROM tlinks WHERE doc_id = ',  'SELECT DISTINCT arg1 FROM tlinks WHERE doc_id = ',  'SELECT DISTINCT eventInstanceID FROM slinks WHERE doc_id = ',  'SELECT DISTINCT subordinatedEventInstance FROM slinks WHERE doc_id = ',  'SELECT DISTINCT eventInstanceID FROM alinks WHERE doc_id = ',  'SELECT DISTINCT relatedToEventInstance FROM alinks WHERE doc_id = ']
        for query in queries:
            if not runQuery(query + doc_id):
                return
            args = list(db.cursor.fetchall())
            for arg in args:
                linkedIntervals.add(arg[0])



        # first is easiest - check for timex3s that aren't mentioned in a tlink
        if not runQuery('SELECT tid FROM timex3s WHERE doc_id = ' + doc_id):
            return
        
        timex3s = db.cursor.fetchall()
        
        
        for timex3 in timex3s:
            if timex3[0] not in linkedIntervals:
                orphans.add('TIMEX3 ' + str(timex3[0]) + ' not in any link')
        
        
        # next, check for instances not in tlinks
        if not runQuery('SELECT eiid FROM instances WHERE doc_id = ' + doc_id):
            return
        
        instances = set()
        for instance_ in list(db.cursor.fetchall()):
            instances.add(instance_[0])
        
        for missing in instances.difference(linkedIntervals):
            orphans.add('INSTANCE ' + str(missing) + ' not in any link')
        
        
        # then, find events that don't have any instances
        if not runQuery('SELECT eid FROM events WHERE doc_id = ' + doc_id):
            return
        
        events = set()
        for event_ in list(db.cursor.fetchall()):
            events.add(instance_[0])
        
        if not runQuery('SELECT DISTINCT eventID FROM instances WHERE doc_id = ' + doc_id):
            return
        
        instancedEvents = set()
        for event_ in list(db.cursor.fetchall()):
            instancedEvents.add(instance_[0])
        
        for missing in events.difference(instancedEvents):
            orphans.add('EVENT ' + str(missing) + ' is never instanced')
        
        
        # instances that don't reference an event, or reference an invalid event
        # (instances where eventID == '')  union  (instancedEvents [eventID] minus events [eid])
        for missing in instancedEvents.difference(events):
            orphans.add('INSTANCE' + str(missing) + ' references absent eventID')
        
        if not runQuery('SELECT eiid FROM instances WHERE (eventID = "" OR eventID IS NULL) AND doc_id = ' + doc_id):
            return
        
        for instance_ in list(db.cursor.fetchall()):
            orphans.add('INSTANCE ' + str(instance_[0]) + 'does not reference an event')


        # signals not referenced by any tlink, alink, slink or instance
        if not runQuery('SELECT sid FROM signals WHERE doc_id = %s AND sid NOT IN (SELECT signalID FROM tlinks WHERE doc_id = %s AND signalID IS NOT NULL) AND sid NOT IN (SELECT signalID FROM slinks WHERE doc_id = %s AND signalID IS NOT NULL) AND sid NOT IN (SELECT signalID FROM alinks WHERE doc_id = %s AND signalID IS NOT NULL) AND sid NOT IN (SELECT signalID FROM instances WHERE doc_id = %s AND signalID IS NOT NULL)' % (doc_id,  doc_id, doc_id,  doc_id, doc_id)):
            return
        
        for sid_ in list(db.cursor.fetchall()):
            orphans.add('SIGNAL ' + str(sid_[0]) + 'is not referenced by any TLINK, SLINK, ALINK or MAKEINSTANCE')
        
        
        
        if len(orphans) > 0:

            print "# Checking " + docName + ' (id ' + doc_id + ')'
            
            orphans = list(orphans)
            orphans.sort()
            
            for orphan in orphans:
                print orphan
            
            return False
            
        else:
            return True
