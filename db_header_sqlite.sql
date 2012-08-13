CREATE TABLE IF NOT EXISTS `documents` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `docname` varchar(200) NOT NULL,
  `body` mediumtext collate nocase
);
CREATE TABLE IF NOT EXISTS `events` (
  `doc_id` int  NOT NULL,
  `eid` varchar(100) NOT NULL,
  `class` text  NOT NULL collate nocase,
  `text` text collate nocase,
  `lemma` text collate nocase,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `info` (
  `key` varchar(40) NOT NULL,
  `data` text NOT NULL collate nocase
);
CREATE TABLE IF NOT EXISTS `instances` (
  `doc_id` int  NOT NULL,
  `eiid` varchar(100) NOT NULL,
  `eventID` varchar(100) NOT NULL,
  `signalID` varchar(100) default NULL,
  `pos` varchar(100) default NULL collate nocase,
  `tense` varchar(100) default NULL collate nocase,
  `aspect` varchar(100) default NULL collate nocase,
  `cardinality` varchar(100) default NULL collate nocase,
  `polarity` varchar(100) default NULL collate nocase,
  `modality` varchar(100) default NULL collate nocase,
  `vform` varchar(100) default NULL collate nocase,
  `mood` varchar(100) default NULL collate nocase,
  `pred` varchar(100) default NULL collate nocase
);
CREATE TABLE IF NOT EXISTS `signals` (
  `doc_id` int  NOT NULL,
  `sid` varchar(100) NOT NULL,
  `text` text collate nocase,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `timex3s` (
  `doc_id` int  NOT NULL,
  `tid` varchar(100) NOT NULL,
  `type` text  NOT NULL collate nocase,
  `functionInDocument` text  NOT NULL default 'NONE',
  `beginPoint` varchar(100) default NULL,
  `endPoint` varchar(100) default NULL,
  `quant` text collate nocase,
  `freq` text collate nocase,
  `temporalFunction` text  NOT NULL default 'false' collate nocase,
  `value` text NOT NULL collate nocase,
  `mod` text  default NULL collate nocase,
  `anchorTimeID` varchar(100) default NULL collate nocase,
  `text` text collate nocase,
  `position` int  default NULL,
  `sentence` int  default NULL,
  `inSentence` int  default NULL
);
CREATE TABLE IF NOT EXISTS `tlinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text collate nocase,
  `signalID` varchar(100) default NULL collate nocase,
  `arg1` varchar(100) NOT NULL collate nocase,
  `relType` text  NOT NULL collate nocase,
  `arg2` varchar(100) NOT NULL collate nocase
);
CREATE TABLE IF NOT EXISTS `slinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL collate nocase,
  `origin` text collate nocase,
  `signalID` varchar(100) default NULL collate nocase,
  `eventInstanceID` varchar(100) NOT NULL collate nocase,
  `relType` text  NOT NULL collate nocase,
  `subordinatedEventInstance` varchar(100) NOT NULL collate nocase
);
CREATE TABLE IF NOT EXISTS `alinks` (
  `doc_id` int  NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text collate nocase,
  `signalID` varchar(100) default NULL collate nocase,
  `eventInstanceID` varchar(100) NOT NULL collate nocase,
  `relType` text  NOT NULL collate nocase,
  `relatedToEventInstance` varchar(100) NOT NULL collate nocase
);
CREATE TABLE IF NOT EXISTS `sentences` (
  `doc_id` int  NOT NULL,
  `sentenceID` int  NOT NULL,
  `offset` int,
  `text` MEDIUMTEXT collate nocase
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
CREATE UNIQUE INDEX "ikey" ON "info" (`key`);

