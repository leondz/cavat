CREATE TABLE IF NOT EXISTS `documents` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `docname` varchar(200) NOT NULL,
  `body` mediumtext
);
CREATE TABLE IF NOT EXISTS `events` (
  `doc_id` int  NOT NULL,
  `eid` varchar(100) NOT NULL,
  `class` text  NOT NULL,
  `text` text,
  `lemma` text,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `info` (
  `key` varchar(40) NOT NULL,
  `data` text NOT NULL
);
CREATE TABLE IF NOT EXISTS `instances` (
  `doc_id` int  NOT NULL,
  `eiid` varchar(100) NOT NULL,
  `eventID` varchar(100) NOT NULL,
  `signalID` varchar(100) default NULL,
  `pos` text  NOT NULL,
  `tense` text  NOT NULL,
  `aspect` text  NOT NULL,
  `cardinality` varchar(100) default NULL,
  `polarity` text  NOT NULL,
  `modality` varchar(100) default NULL,
  `vform` varchar(100) default NULL,
  `mood` varchar(100) default NULL
);
CREATE TABLE IF NOT EXISTS `signals` (
  `doc_id` int  NOT NULL,
  `sid` varchar(100) NOT NULL,
  `text` text,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `timex3s` (
  `doc_id` int  NOT NULL,
  `tid` varchar(100) NOT NULL,
  `type` text  NOT NULL,
  `functionInDocument` text  NOT NULL default 'NONE',
  `beginPoint` varchar(100) default NULL,
  `endPoint` varchar(100) default NULL,
  `quant` text,
  `freq` text,
  `temporalFunction` text  NOT NULL default 'false',
  `value` text NOT NULL,
  `mod` text  default NULL,
  `anchorTimeID` varchar(100) default NULL,
  `text` text,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `tlinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text,
  `signalID` varchar(100) default NULL,
  `arg1` varchar(100) NOT NULL,
  `relType` text  NOT NULL,
  `arg2` varchar(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS `slinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text,
  `signalID` varchar(100) default NULL,
  `eventInstanceID` varchar(100) NOT NULL,
  `relType` text  NOT NULL,
  `subordinatedEventInstance` varchar(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS `alinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL,
  `signalID` varchar(100) default NULL,
  `eventInstanceID` varchar(100) NOT NULL,
  `relType` text  NOT NULL,
  `relatedToEventInstance` varchar(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS `sentences` (
  `doc_id` int  NOT NULL,
  `sentenceID` int  NOT NULL,
  `text` MEDIUMTEXT
);
CREATE UNIQUE INDEX "docid" ON "documents" (`id`);
CREATE INDEX "docname" ON "documents" (`docname`);
CREATE UNIQUE INDEX "eid" ON "events" (`doc_id`,`eid`);
CREATE INDEX "docevent" ON "events" (`doc_id`);
CREATE UNIQUE INDEX "eiid" ON "instances" (`doc_id`,`eiid`);
CREATE INDEX "docinst" ON "instances" (`doc_id`);
CREATE UNIQUE INDEX "sid" ON "signals" (`doc_id`,`sid`);
CREATE INDEX "docsid" ON "signals" (`doc_id`);
CREATE UNIQUE INDEX "tid" ON "timex3s" (`doc_id`,`tid`);
CREATE INDEX "doctimex" ON "timex3s" (`doc_id`);
CREATE UNIQUE INDEX "tlid" ON "tlinks" (`doc_id`,`lid`);
CREATE UNIQUE INDEX "slid" ON "slinks" (`doc_id`,`lid`);
CREATE UNIQUE INDEX "alid" ON "alinks" (`doc_id`,`lid`);
CREATE UNIQUE INDEX "sentence" ON "sentences" (`doc_id`,`sentenceID`);
