from cavatModule import CavatModule
import db
from db import runQuery
import cavatDebug
import sqlite3

class agenda():

    connection = None
    cursor = None
    name = None

    def __init__(self):
        self.connection = sqlite3.connect(':memory:')
        
        self.connection.isolation_level = None
        
        self.connection.execute('create table agenda (arg1, arg2, val)')
        self.connection.execute('create unique index args on agenda (arg1, arg2)')
        self.connection.execute('create index arg1 on agenda (arg1)')
        self.connection.execute('create index arg2 on agenda (arg2)')
        
        self.cursor = self.connection.cursor()
    
    
    def keys(self):
        self.cursor.execute('select arg1 || "." || arg2 from agenda')
        keys = set()
        for result in self.cursor.fetchall():
            keys.add(result[0])
        return keys
    
    def pop(self):
        # like dictionary.popitem()
        self.cursor.execute('select * from agenda limit 0,1')
        tlink = self.cursor.fetchone()

        if tlink:
            self.cursor.execute('delete from agenda where arg1 = ? and arg2 = ?', (tlink[0], tlink[1]))
            return tlink
        else:
            return None
    
    def val(self, arg1, arg2):
        # look up a value
        
        self.cursor.execute('select val from agenda where (arg1 = ? and arg2 = ?)', (arg1, arg2))
        val = self.cursor.fetchone()
        if not val:
            return None
        else:
            return val[0]
    
    def set(self, arg1, arg2, val):
        self.cursor.execute('insert or ignore into agenda(arg1, arg2, val) values (?, ?, ?)', (arg1, arg2, val))

    def len(self):
        self.cursor.execute('select * from agenda')
        return len(self.cursor.fetchall())

class consistent(CavatModule):
    
    moduleName = 'Temporal graph consistency checker'
    moduleDescription = 'Using a point-based temporal algebra, determines whether or not a temporal graph is consistent'
    
    moduleVersion = '1'
    
    _minVersion = 0.1
    _maxVersion = 0.999

    superVerbose = False

    timemlPointRelations = {'before': {'a2.b1':'<'}, 
                                        'after': {'b2.a1':'<'}, 
                                        'includes': {'a1.b1':'<',  'b2.a2':'<'}, 
                                        'is_included': {'b1.a1':'<',  'a2.b2':'<'}, 
                                        'during': {'a1.b1':'=',  'a2.b2':'='}, 
                                        'simultaneous': {'a1.b1':'=',  'a2.b2':'='}, 
                                        'iafter': {'b2.a1':'='}, 
                                        'ibefore': {'a2.b1':'='}, 
                                        'identity': {'a1.b1':'=',  'a2.b2':'='}, 
                                        'begins': {'a1.b1':'=',  'a2.b2':'<'}, 
                                        'ends': {'a2.b2':'=',  'b1.a1':'<'}, 
                                        'begun_by': {'a1.b1':'=',  'b2.a2':'<'}, 
                                        'ended_by': {'b2.a2':'=',  'a1.b1':'<'}, 
                                        'during_inv': {'a1.b1':'=',  'a2.b2':'='}
                                        }

    database = None 
    agenda = None

    

    failReason = ''
    
    
    def addToAgenda(self,  fact):
        
        args = fact[0].split('.')
        (arg1, arg2) = args
        reversed = args[1] + '.' + args[0]
        
        if args[0] == args[1] and fact[1] != '=':
            return False
        
        # check for presence of fact in agenda or database. return true if it's already there.
        if fact[0] in self.database.keys():
            if self.database.val(arg1, arg2) != fact[1]:
                if self.superVerbose:
                    self.failReason = "Already asserted on database that relation is " + self.database.val(arg1, arg2)
                return False
            else:
                return True
        
        if fact[0] in self.agenda.keys():
            if self.agenda.val(arg1, arg2) != fact[1]:
                if self.superVerbose:
                    self.failReason = "Already asserted on agenda that relation is " + self.agenda.val(arg1, arg2)
                return False
            else:
                return True
        
        if reversed in self.agenda.keys():
            if self.agenda.val(arg2, arg1) == fact[1] and fact[1] != '=':
                if self.superVerbose:
                    self.failReason = 'Relation already exists on agenda in opposite direction, ' + reversed + ' ' + self.agenda.val(arg2, arg1)
                return False
            else:
                return True
        
        if reversed in self.database.keys():
            if self.database.val(arg2, arg1) == fact[1] and fact[1] != '=':
                if self.superVerbose:
                    self.failReason = 'Relation already exists on database in opposite direction, ' + reversed + ' ' + self.database.val(arg2, arg1)
                return False
            else:
                return True
        
        # add it
        self.agenda.set(arg1, arg2, fact[1])
        
        return True


    def consistencyCheck(self,  intervals, tlinks):
        # arguments are:
        # - intervals, a set of names of intervals present in the graph;
        # - tlinks, a set of 4-tuples, where each 4-tuple represents a tlink, as 4 strings - arg1, reltype, arg2, id
        # provide tuples for fastest processing, though any set type will work (e.g. tuple(intervals) tuple(tlinks) is superior)

        self.database = agenda()
        self.agenda = agenda()

        if self.superVerbose:
            for tlink in tlinks:
                print tlink

        # populate database with before relation that establishes proper intervals
        for intervalName in intervals:
            arg1 = intervalName + '_1'
            arg2 = intervalName + '_2'
            self.database.set(arg1, arg2, '<')
            
            if self.superVerbose:
                print "# Adding " , arg1, arg2, ' <'
       
        # add tlinks to agenda
        for tlink in tlinks:
            
            if self.superVerbose:
                print '# Processing TLINK', tlink
            
            assertions = self.timemlPointRelations[tlink[1].lower()]
            
            for k,  v in assertions.iteritems():
                k = k.replace('a',  tlink[0] + '_')
                k = k.replace('b',  tlink[2] + '_')
                
                assertion = [k,  v]
                if self.superVerbose:
                    print 'TLINK', tlink[3],   tlink[0],  tlink [1],  tlink[2], ' suggests ',  k,  v
                    print "# Asserting " + str(assertion)
                
                if self.addToAgenda(assertion):
                    continue
                    
                else:
                    args = k.split('.')
                    
                    self.failReason = "Inconsistent initial TLINKs - could not assert (%s %s %s)" % (args[0],  v,  args[1])
                    return False
        
        
        # while there are items in the agenda
        # take an item from agenda
        # generate all inferences between that item and db
        # add those to agenda
        # add item to db
        
        if self.superVerbose:
            print 'Initial agenda:',  self.agenda
            print 'Initial database:',  self.database
        
        while self.agenda.len():
            if self.superVerbose:
                print '-- database',  self.database
                print '-- agenda',  self.agenda
            (arg1, arg2,  value) = self.agenda.pop()
            
            if self.superVerbose:
                print 'processing',  arg1, arg2,  value
            
            for dbkey in self.database.keys():
                
                # reset these for each calculation
                [p1,  p2] = [arg1, arg2]
                r1 = value
                
                [p3,  p4] = dbkey.split('.')
                r2 = self.database.val(p3, p4)
                
                
                print dbkey, self.database.val(p3, p4)
                
                if p2 != p3:
                
                    if p2 == p4 or p1 == p3:
                        # check for a simultaneous relation
                        if r1 == '=':
                            [p1, p2] = [p2,  p1]
                        elif r2 == '=':
                            [p3,  p4] = [p4,  p3]
                    
                    elif p1 == p4:
                        # invert proposition / db item order
                        [p1,  p2,  p3,  p4] = [p3,  p4,  p1,  p2]
                        [r1,  r2] = [r2,  r1]
                
                if p2 != p3:
                    continue
                
                
                # now, we can do inference!
                propositionKey = p1 + '.' + p4
                
                if r1 == '<' or r2 == '<':
                    r3 = '<'
                else:
                    r3 = '='
                
                if self.superVerbose:
                    print 'new rule:  %s %s %s  (because  %s %s %s  ^  %s %s %s )' % (p1,  r3,  p4,  p1,  r1,  p2,  p3,  r2,  p4)
                
                if not self.addToAgenda([propositionKey,  r3]):
                    args = propositionKey.split('.')

                    self.failReason = "Inconsistent closure - could not assert (%s %s %s)" % (args[0],  r3,  args[1])
                    return False

                else:
                    self.database.set(arg1, arg2, value)

        return True
    
    def checkDocument(self,  doc_id):
        
        docName = self.startup(doc_id)
        if not docName:
            return False        
        
    # use an agenda-based closure algorithm.
    #   - find all intervals referenced by tlinks
    #   - split these into a start and end, and for each interval, add interval_start < interval_end to the database (which assumes we have only annotated proper intervals).
    #   - for each tlink, add axioms about the points that they link to the agenda
    #   - perform agenda based closure; before any agenda addition, check that the rule being added does not conflict with other rules. 
    #     a conflict is when we assign a new value for a pair that is already present; e.g., a<b conflicts with b=a, or b<a, or a=b
    #   - if we ever find a conflict, then the graph is inconsistent.
    #   - if we empty the agenda, the graph is consistent.

    
        if not runQuery('SELECT DISTINCT arg1 FROM tlinks WHERE doc_id = ' + doc_id):
            return
        
        intervals = set(db.cursor.fetchall())
        
        if not runQuery('SELECT DISTINCT arg2 FROM tlinks WHERE doc_id = ' + doc_id):
            return
        
        intervals = intervals.union(set(db.cursor.fetchall()))
        
        # move db result from list of tuples to list of strings
        intervals_ = []
        for interval in intervals:
            intervals_.append(interval[0])
        intervals = set(intervals_)
        
        
        # fetch tlinks
        if not runQuery('SELECT arg1, reltype, arg2, lid FROM tlinks WHERE doc_id = ' + doc_id):
            return
        
        tlinks = db.cursor.fetchall()
        
        result = self.consistencyCheck(intervals,  tlinks)
        
        if result:
            if cavatDebug.debug:
                print 'Consistent'
                
            if self.superVerbose:
                print self.database
                
            return True
            
        else:
            
            # only print doc name if it's not already there
            if not cavatDebug.debug:
                print "# Checking " + docName + ' (id ' + doc_id + ')'
                
            print '! ' + self.failReason
            return False
