import MySQLdb
import nltk

# find all events, timexs, signals; log doc_id, sentence and token id, as well as the string
# for each one, look up the appropriate sentence
#   tokenise the sentence; does the string at the appropriate offset match the start of the tag's string?
#   if not, report the problem, and display the sentence.

# log in to database
db_user = 'timebank'
db_pass = 'timebank'
db_name = 'timebank_test'

# connect
try:
    conn = MySQLdb.connect ('localhost',  db_user,  db_pass,  reconnect=1)
except Exception,  e:
    import sys
    sys.exit('Database connection failed - ' + str(e))

conn.select_db(db_name) 
cursor = conn.cursor()

cursor.execute('SELECT id, docname FROM documents')
doc_ids = cursor.fetchall()

docname = {}
for doc_id in doc_ids:
  (id, name) = doc_id
  docname[id] = name

cursor.execute('SELECT doc_id, tid as id, sentence, inSentence, text FROM timex3s')
timex3s = cursor.fetchall()

cursor.execute('SELECT doc_id, eid as id, sentence, inSentence, text FROM events')
events = cursor.fetchall()

cursor.execute('SELECT doc_id, sid as id, sentence, inSentence, text FROM signals')
signals = cursor.fetchall()


for tag_list in [timex3s, events, signals]:
  for tag in tag_list:
    (doc_id, id, sentence, inSentence, tag_text) = tag
    cursor.execute('SELECT text FROM sentences WHERE doc_id = %d AND sentenceID = %d' % (doc_id, sentence))
    sentence_text = cursor.fetchone()[0]
    sentence_words = nltk.word_tokenize(sentence_text)
    sentence_word = sentence_words[inSentence]
    if sentence_word != tag_text and not tag_text.startswith(sentence_word) and tag_text.find(sentence_word) == -1 and sentence_word.find(tag_text) == -1:
      print '-- Misalignment:'
      print 'doc', doc_id, docname[doc_id], 'sentence', sentence, 'token', inSentence, 'tag', id
      print 'tag text:     ', tag_text
      print 'sentence word:', sentence_word
      print sentence_text
