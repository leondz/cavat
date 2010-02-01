from pyparsing import Forward, Keyword, Word, oneOf, alphas, alphanums,  nums,  printables,  QuotedString,  Group,  Optional,  ParseException,  OneOrMore,  LineEnd,  Suppress,  QuotedString


# TimeML tags
validTags = ['event',  'tlink',  'instance',  'signal',  'timex3']

# field names
eventFields = "doc_id eid class text lemma position sentence eventid signalid pos tense aspect cardinality polarity modality"
instanceFields = "doc_id eiid eventid signalid pos tense aspect cardinality polarity modality"
signalFields = "doc_id sid text position sentence"
timex3Fields = "doc_id tid type functionindocument beginpoint endpoint quant freq temporalfunction value mod anchortimeid text position sentence"
tlinkFields = "doc_id lid origin signalid arg1 reltype arg2"

cavatStmt = Forward()

# top-level commands
showToken = Keyword("show",  caseless = True)
debugToken = Keyword("debug",  caseless = True)
corpusToken = Keyword("corpus",  caseless = True)
helpToken = Keyword("help",  caseless = True)
checkToken = Keyword("check",  caseless = True)

# parameter values
onOff = oneOf('on off',  caseless = True)
tag = oneOf(' '.join(validTags),  caseless = True)
alphaNums_ = Word(alphanums + "_")
fileName = Word(alphanums + "_-.+%/")
reportType = oneOf("list distribution state",  caseless = True)
outputFormat = oneOf("screen csv tsv tex",  caseless = True)
conditionValue = Group(Word(nums) | QuotedString('"\''))
state = oneOf("filled unfilled",  caseless = True)

# markers
EOL = Suppress(LineEnd())

# joining particles
all_ = Keyword("all",  caseless = True)
as_ = Keyword("as",  caseless = True)
filled_ = Keyword("filled",  caseless = True)
from_ = Keyword("from",  caseless = True)
import_ = Keyword("import",  caseless = True)
in_ = Keyword("in",  caseless = True)
info_ = Keyword("info",  caseless = True)
is_ = Keyword("is",  caseless = True)
list_ = Keyword("list",  caseless = True)
not_ = Keyword("not",  caseless = True)
of_ = Keyword("of",  caseless = True)
state_ = Keyword("state",  caseless = True)
to_ = Keyword("to",  caseless = True)
unfilled_ = Keyword("unfilled",  caseless = True)
use_ = Keyword("use",  caseless = True)
verify_ = Keyword("verify",  caseless = True)
where_ = Keyword("where",  caseless = True)

# field specifiers, consisting of a tag name and fields of that tag
eventProperty = Keyword("event",  caseless = True).setResultsName("tag") + oneOf(eventFields,  caseless = True).setResultsName("property")
instanceProperty = Keyword("instance", caseless = True).setResultsName("tag") + oneOf(instanceFields,  caseless = True).setResultsName("property")
signalProperty = Keyword("signal",  caseless = True).setResultsName("tag") + oneOf(signalFields,  caseless = True).setResultsName("property")
timex3Property = Keyword("timex3",  caseless = True).setResultsName("tag") + oneOf(timex3Fields,  caseless = True).setResultsName("property")
tlinkProperty = Keyword("tlink",  caseless = True).setResultsName("tag") + oneOf(tlinkFields,  caseless = True).setResultsName("property")



# field name property, build from field specifiers
fieldName = Group(eventProperty | instanceProperty | signalProperty | timex3Property | tlinkProperty)

simpleWhereClause = (
            where_  
            + oneOf(' '.join([eventFields,  instanceFields,  signalFields,  timex3Fields,  tlinkFields])).setResultsName("conditionField")
            + (
                is_ + Optional(not_.setResultsName("not_")) + alphaNums_.setResultsName("conditionValue")
                |
                state_ + is_ + Optional(not_.setResultsName("not_")) + state.setResultsName("state")
                )
        )


cavatStmt << (
              
                helpToken.setResultsName("action") + Optional(OneOrMore(alphaNums_).setResultsName("query"))
                
                |
              
                showToken.setResultsName("action") + reportType.setResultsName("report") + of_ + fieldName.setResultsName("result") 
                    
                    + Optional(simpleWhereClause.setResultsName("condition"))

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
                    
                    verify_.setResultsName("verify")
                    
                    )
                |
                
                debugToken.setResultsName("action") + Optional(onOff.setResultsName("state"))
                
                |
                
                checkToken.setResultsName("action") + alphaNums_.setResultsName("module") + in_ + 
                    (
                    OneOrMore(fileName).setResultsName("target")
                    |
                    all_.setResultsName("target")
                    )
                
                ) + EOL


