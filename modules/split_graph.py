from cavatModule import CavatModule
import db
from db import runQuery
import cavatDebug
from math import log

class split_graph(CavatModule):
    
    moduleName = 'Split graph detection'
    moduleDescription = 'Find out if a document\'s TLINKs form more than one independent graph, and report on the subgraphs if they do.'
    
    moduleVersion = '1'
    
    _minVersion = 0.1
    _maxVersion = 0.999
    
    superVerbose = cavatDebug.debug
    printGraphs = True
    extraStats = True


    def entropy(self,  stacks):
        total = float(sum(stacks))
        entropy = -0.0
        
        for stack in stacks:
            
            if stack <= 0:
                continue
            
            p = float(stack) / total
            entropy += p * log(p,  total)
        
        return -entropy


    def findSplitGraphs(self,  tlinks):
        
        # does the main body of work. takes a list of tlink argument pairs; [ [arg1, arg2], [arg1, arg2], ... ]
        
        
        # begin with an empty list of graphs
        graphs = []
        
        for tlink in tlinks:
            
            if self.superVerbose:
                print "\n> new tlink",  tlink
                print '-- graphs'
                for graph in graphs:
                    print '--  ',  graph
            
            linkAppended = False
            
            # check each subgraph to see if we can stick this tlink on
            for g,  graph in enumerate(graphs):
                
                
                # can we attach this tlink to this group?
                if tlink[0] in graph and not linkAppended:
                    graphs[g].add(tlink[1])
                    linkAppended = True
                    
                    if self.superVerbose:
                        print "pile found ",  graphs[g]
                    
                    # if so, check to see if the other end of the tlink will go anywhere
                    merged = False
                    if self.superVerbose:
                        print 'Checking for merges'
                    
                    for s,  secondGraph in enumerate(graphs):
                        
                        if merged:
                            break
                        
                        if s == g:
                            continue
                        
                        if self.superVerbose:
                            print 'g %s, s %s' % (g,  s)
                        
                        
                        if tlink[1] in secondGraph:
                            
                            # merge graphs
                            if self.superVerbose:
                                print "pre-merge",  graphs
                            
                            graphs[g] = graphs[g] | secondGraph
                            del graphs[s]
                            
                            merged = True
                            
                            if self.superVerbose:
                                print "postmerge",  graphs
                            
                            break
            
            
            if not linkAppended:
                for g,  graph in enumerate(graphs):
                    
                    if linkAppended:
                        break
                    
                    
                    if tlink[1] in graph:
                        graphs[g].add(tlink[0])
                        linkAppended = True
                        if self.superVerbose:
                            print "pile found",  graphs[g]
                        break
           
           
           # couldn't add the link anywhere; form a new pile
            if not linkAppended:
                if self.superVerbose:
                    print 'new pile created'
                # a graph is a list of tuples
                newgraph = set([tlink[0],  tlink[1]])
                graphs.append(newgraph)
        
        return graphs

    def checkDocument(self,  doc_id):

        self.superVerbose = cavatDebug.debug
        
        docName = self.startup(doc_id)
        if not docName:
            return False
        
        if self.superVerbose:
            print '# Checking %s (id %s)' % (docName, doc_id)

        # maintain a list of sets. each set represents a pile of related nodes (e.g. a linked part of the document's temporal graph).
        # when we add a tlink, check for either of its arguments' presence in any pile of other nodes; 
        # - if we find that it can be attached, add the other argument to that set, and then search all the other piles using the other end of the tlink
        # -   if we find a match, merge the two piles
        # when we've added all the tlinks, we will have a list containing dicts of separate subgraphs. Look up TLINK IDs at this point for output.
        
        if not runQuery('SELECT arg1, arg2 FROM tlinks WHERE doc_id = ' + doc_id):
            return 
        
        tlinks = db.cursor.fetchall()
        
        graphs = self.findSplitGraphs(tlinks)
        
        numSubgraphs = len(graphs)
        
        if self.superVerbose:
            print "\n>> Final graphs:"
            for graph in graphs:
                print '--  ',  graph
        
        
        if numSubgraphs > 1:
            
            numNodes = 0
            singleLinkGraphs = 0
            isolatedNodes = 0
            biggestSubgraph = 0
            
            for graph in graphs:
                
                graphSize = len(graph)
                
                numNodes += graphSize
                
                # a link describes two nodes, so the minimum size for a one-tlink graph would be 2. However, there are some looped TLINKs around, which would create a set of just one.
                if graphSize <= 2:
                    isolatedNodes += graphSize
                    singleLinkGraphs += 1
                
                if graphSize > biggestSubgraph:
                    biggestSubgraph = graphSize
            
            if not self.superVerbose:
                print '# Checking %s (id %s)' % (docName, doc_id)
            
            
            print 'Subgraphs found: %s - composed of %s nodes and linked by %s TLINKS.' % (numSubgraphs,  numNodes,  len(tlinks))
            
            if self.extraStats:
                print 'Isolated subgraphs, that contain just one TLINK: %s  (making up %2.1f%% of all subgraphs / consuming %2.1f%% of all nodes / described by %2.1f%% of all TLINKs);' %  (singleLinkGraphs,  float(singleLinkGraphs)*100 / numSubgraphs,  float(isolatedNodes)*100 / numNodes, float(singleLinkGraphs)*100 / len(tlinks))
                print 'Mean graph size %1.1f nodes; largest subgraph (size %d) has %2.1f%% of all nodes.' % (float(numNodes) / numSubgraphs,  biggestSubgraph,  float(biggestSubgraph)*100 / numNodes)
                print 'Entropy of subgraph sizes: ',  self.entropy(map(len,  graphs))

            
            if self.printGraphs:
                # measure graph sizes in nodes, not tlinks.
                count = {}
                
                for graph in graphs:
                    try:
                        count[len(graph)] += 1
                    except:
                        count[len(graph)] = 1
                
                
                for size,  freq in sorted(count.iteritems()):
                    print ' ' + str(size).rjust(4) + ' nodes: ('+ str(freq).rjust(2)+') ' + ('.' * freq)
            
            return False
            
        else:
            return True

