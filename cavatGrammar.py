from pyparsing import Forward, Keyword, Word, oneOf, alphas, alphanums,  nums,  printables,  QuotedString,  Group,  Optional,  ParseException,  OneOrMore,  LineEnd,  Suppress,  QuotedString



# TimeML information
validTags = ['event',  'tlink',  'instance',  'signal',  'timex3']
numericFields = ['events.doc_id',  'events.position',  'events.sentence',  'instances.doc_id', 'signals.doc_id',  'signals.position',  'signals.sentence',  'timex3s.doc_id',  'timex3s.position',  'timex3s.sentence',  'tlinks.doc_id']

# field names
eventFields = "doc_id eid class text lemma position sentence eventid signalid pos tense aspect cardinality polarity modality"
instanceFields = "doc_id eiid eventid signalid pos tense aspect cardinality polarity modality"
signalFields = "doc_id sid text position sentence"
timex3Fields = "doc_id tid type functionindocument beginpoint endpoint quant freq temporalfunction value mod anchortimeid text position sentence"
tlinkFields = "doc_id lid origin signalid arg1 reltype arg2 signaltext"

idPrefixes = {'event': 'e',  'instance':'ei',  'signal':'s',  'timex3':'t',  'tlink':'l'}

# the top-level command
cavatStmt = Forward()

# top-level commands
showToken = Keyword("show",  caseless = True)
debugToken = Keyword("debug",  caseless = True)
corpusToken = Keyword("corpus",  caseless = True)
helpToken = Keyword("help",  caseless = True)
checkToken = Keyword("check",  caseless = True)
browseToken = Keyword("browse",  caseless = True)

# parameter values
onOff = oneOf('on off',  caseless = True)
tag = oneOf(' '.join(validTags),  caseless = True)
alphaNums_ = Word(alphanums + "_")
fileName = Word(alphanums + "_-.+%/")
reportType = oneOf("list distribution state",  caseless = True)
outputFormat = oneOf("screen csv tsv tex",  caseless = True)
browseFormat = oneOf("screen timeml csv",  caseless=True)
conditionValue = Group(Word(nums) | QuotedString('"\''))
state = oneOf("filled unfilled",  caseless = True)
tlinkPositionedArg = oneOf("arg1 arg2 signal",  caseless = True)
distanceUnits = oneOf("words sentences",  caseless = True)

# markers
EOL = Suppress(LineEnd())

# joining particles
particles = ['all',  'arg1',  'arg2',  'as',  'distance',  'doc', 'filled', 'from', 'help', 'import', 'in', 'info', 'is', 'list', 'not', 'of', 'signal', 'state', 'to', 'unfilled', 'use', 'verify', 'where']
for particle in particles:
    exec('%s_ = Keyword("%s", caseless = True)' % (particle,  particle))

# field specifiers, consisting of a tag name and fields of that tag
eventProperty = Keyword("event",  caseless = True).setResultsName("tag") + oneOf(eventFields,  caseless = True).setResultsName("property")
instanceProperty = Keyword("instance", caseless = True).setResultsName("tag") + oneOf(instanceFields,  caseless = True).setResultsName("property")
signalProperty = Keyword("signal",  caseless = True).setResultsName("tag") + oneOf(signalFields,  caseless = True).setResultsName("property")
timex3Property = Keyword("timex3",  caseless = True).setResultsName("tag") + oneOf(timex3Fields,  caseless = True).setResultsName("property")
tlinkProperty = Keyword("tlink",  caseless = True).setResultsName("tag") + oneOf(tlinkFields,  caseless = True).setResultsName("property")


# field name property, build from field specifiers
fieldName = Group(eventProperty | instanceProperty | signalProperty | timex3Property | tlinkProperty)

# basic where clause
simpleWhereClause = (
            where_  
            + oneOf(' '.join([eventFields,  instanceFields,  signalFields,  timex3Fields,  tlinkFields])).setResultsName("conditionField")
            + (
                is_ + Optional(not_.setResultsName("not_")) + alphaNums_.setResultsName("conditionValue")
                |
                state_ + is_ + Optional(not_.setResultsName("not_")) + state.setResultsName("state")
                )
        )

# top-level statement definition
cavatStmt << (
              
                helpToken.setResultsName("action") + Optional(OneOrMore(alphaNums_).setResultsName("query"))
                
                |
              
                showToken.setResultsName("action") + reportType.setResultsName("report") + of_ + 
                    (
                    
                        tag.setResultsName("tag") + tlinkPositionedArg.setResultsName("start") + tlinkPositionedArg.setResultsName("end") + distance_.setResultsName('distance')
                        
                        + Optional(in_ + distanceUnits.setResultsName('units'))
                        
                    |
                    
                        fieldName.setResultsName("result") 
                        
                        + Optional(simpleWhereClause.setResultsName("condition"))
                        
                    )
                    

                    + Optional(as_ + outputFormat.setResultsName("format"))
                    
                |
                
                corpusToken.setResultsName("action")  +
                    
                    (
                    
                    import_.setResultsName("import_") +  # can't use import as reserved word; use import_ instead.
                        (
                        fileName.setResultsName("directory") + to_ + alphaNums_.setResultsName("database")
                        |
                        alphaNums_.setResultsName("database") + from_ + fileName.setResultsName("directory") 
                        )
                
                    |
                    
                    use_.setResultsName("use") + alphaNums_.setResultsName("database")
                    
                    |
                    
                    info_.setResultsName("info")
                    
                    |
                    
                    list_.setResultsName("list")
                    
                    |
                    
                    verify_.setResultsName("verify") + Optional(alphaNums_).setResultsName("database")
                    
                    )
                |
                
                debugToken.setResultsName("action") + Optional(onOff.setResultsName("state"))
                
                |
                
                checkToken.setResultsName("action") +
                    (
                    list_.setResultsName("list")
                    |

                    (
                    alphaNums_.setResultsName("module") + 
                    
                        (
                            help_.setResultsName("help")
                            
                            |
                            
                            (
                                in_ + 
                                (
                                OneOrMore(fileName).setResultsName("target")
                                |
                                all_.setResultsName("target")
                                )
                            )
                        )
                    )
                )
            
                |
            
                browseToken.setResultsName("action") + 
                    (
                    doc_.setResultsName("doc") + fileName.setResultsName("target") 
                    |
                    tag.setResultsName("tag") + 
                        (
                        list_.setResultsName("list")
                        |
                        alphaNums_.setResultsName("value") + Optional(as_ + browseFormat.setResultsName("format"))
                        )
                )
            ) + EOL


