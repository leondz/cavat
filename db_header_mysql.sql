-- phpMyAdmin SQL Dump
-- version 3.1.5
-- http://www.phpmyadmin.net
--

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `timebank`
--

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE IF NOT EXISTS `documents` (
  `id` int(10) unsigned NOT NULL auto_increment,
  `docname` varchar(200) NOT NULL,
  `body` mediumtext,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `docname` (`docname`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

CREATE TABLE IF NOT EXISTS `events` (
  `doc_id` int(10) unsigned NOT NULL,
  `eid` varchar(100) NOT NULL,
  `class` enum('OCCURRENCE','PERCEPTION','REPORTING','ASPECTUAL','STATE','I_STATE','I_ACTION') NOT NULL,
  `text` text,
  `lemma` text,
  `position` int(10) unsigned default NULL,
  `sentence` int(10) unsigned default NULL,
  `inSentence` int(10) unsigned default NULL,
  UNIQUE KEY `doc_id_2` (`doc_id`,`eid`),
  KEY `doc_id` (`doc_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `info`
--

CREATE TABLE IF NOT EXISTS `info` (
  `key` varchar(40) NOT NULL,
  `data` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `instances`
--

CREATE TABLE IF NOT EXISTS `instances` (
  `doc_id` int(10) unsigned NOT NULL,
  `eiid` varchar(100) NOT NULL,
  `eventID` varchar(100) NOT NULL,
  `signalID` varchar(100) default NULL,
  `pos` enum('ADJECTIVE','NOUN','VERB','PREPOSITION','OTHER') default NULL,
  `tense` enum('FUTURE','INFINITIVE','PAST','PASTPART','PRESENT','PRESPART','NONE') default NULL,
  `aspect` enum('PROGRESSIVE','PERFECTIVE','PERFECTIVE_PROGRESSIVE','NONE') default NULL,
  `cardinality` varchar(100) default NULL,
  `polarity` enum('NEG','POS') NOT NULL,
  `modality` varchar(100) default NULL,
  `vform` varchar(100) default NULL,
  `mood` varchar(100) default NULL,
  `pred` varchar(100) default NULL,
  UNIQUE KEY `doc_id_2` (`doc_id`,`eiid`),
  KEY `doc_id` (`doc_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `signals`
--

CREATE TABLE IF NOT EXISTS `signals` (
  `doc_id` int(10) unsigned NOT NULL,
  `sid` varchar(100) NOT NULL,
  `text` text,
  `position` int(10) unsigned default NULL,
  `sentence` int(10) unsigned default NULL,
  `inSentence` int(10) unsigned default NULL,
  UNIQUE KEY `doc_id_2` (`doc_id`,`sid`),
  KEY `doc_id` (`doc_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `timex3s`
--

CREATE TABLE IF NOT EXISTS `timex3s` (
  `doc_id` int(10) unsigned NOT NULL,
  `tid` varchar(100) NOT NULL,
  `type` enum('DATE','TIME','DURATION','SET') NOT NULL,
  `functionInDocument` enum('CREATION_TIME','EXPIRATION_TIME','MODIFICATION_TIME','PUBLICATION_TIME','RELEASE_TIME','RECEPTION_TIME','NONE') NOT NULL default 'NONE',
  `beginPoint` varchar(100) default NULL,
  `endPoint` varchar(100) default NULL,
  `quant` text,
  `freq` text,
  `temporalFunction` enum('true','false') NOT NULL,
  `value` text NOT NULL,
  `mod` enum('BEFORE','AFTER','ON_OR_BEFORE','ON_OR_AFTER','LESS_THAN','MORE_THAN','EQUAL_OR_LESS','EQUAL_OR_MORE','START','MID','END','APPROX') default NULL,
  `anchorTimeID` varchar(100) default NULL,
  `text` text,
  `position` int(10) unsigned default NULL,
  `sentence` int(10) unsigned default NULL,
  `inSentence` int(10) unsigned default NULL,
  UNIQUE KEY `doc_id_2` (`doc_id`,`tid`),
  KEY `doc_id` (`doc_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tlinks`
--

CREATE TABLE IF NOT EXISTS `tlinks` (
  `doc_id` int(10) unsigned NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text,
  `signalID` varchar(100) default NULL,
  `arg1` varchar(100) NOT NULL,
  `relType` enum('BEFORE','AFTER','INCLUDES','IS_INCLUDED','DURING','SIMULTANEOUS','IAFTER','IBEFORE','IDENTITY','BEGINS','ENDS','BEGUN_BY','ENDED_BY','DURING_INV') NOT NULL,
  `arg2` varchar(100) NOT NULL,
  UNIQUE KEY `doc_id` (`doc_id`,`lid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `slinks`
--

CREATE TABLE IF NOT EXISTS `slinks` (
  `doc_id` int(10) unsigned NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text,
  `signalID` varchar(100) default NULL,
  `eventInstanceID` varchar(100) NOT NULL,
  `relType` enum('MODAL', 'EVIDENTIAL', 'NEG_EVIDENTIAL', 'FACTIVE', 'COUNTER_FACTIVE', 'CONDITIONAL') NOT NULL,
  `subordinatedEventInstance` varchar(100) NOT NULL,
  UNIQUE KEY `doc_id` (`doc_id`,`lid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `alinks`
--

CREATE TABLE IF NOT EXISTS `alinks` (
  `doc_id` int(10) unsigned NOT NULL,
  `lid` varchar(100) NOT NULL,
  `origin` text,
  `signalID` varchar(100) default NULL,
  `eventInstanceID` varchar(100) NOT NULL,
  `relType` enum('INITIATES', 'CULMINATES', 'TERMINATES', 'CONTINUES', 'REINITIATES') NOT NULL,
  `relatedToEventInstance` varchar(100) NOT NULL,
  UNIQUE KEY `doc_id` (`doc_id`,`lid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `sentences`
--

CREATE TABLE IF NOT EXISTS `sentences` (
  `doc_id` int(10) unsigned NOT NULL,
  `sentenceID` int(10) unsigned NOT NULL,
  `offset` int(10) unsigned,
  `text` MEDIUMTEXT,
  UNIQUE KEY `doc_id` (`doc_id`,`sentenceID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

