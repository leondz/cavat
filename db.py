from cavatMessages import errorMsg
import cavatDebug
import os
import sys


conn = None
cursor = None
version = None
engine = None
prefix = ''

# connect should load details it needs from the config into module variables, and then connect and return the appropriate connection 
# takes a config object as its sole parameter
def connect(config):
    
    global engine,  prefix
    
    try:
        engine = config.get('cavat',  'dbtype')
        prefix = config.get('cavat',  'dbprefix')
    except Exception,  e:
        print '! Failure reading ini file: ' + str(e)
        sys.exit()
    
    if engine == 'mysql':
        
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            import MySQLdb

        
        try:
            dbHost = config.get('cavat',  'dbhost')
            dbUser = config.get('cavat',  'dbuser')
        except Exception,  e:
            print '! Failure reading db user+host: ' + str(e)
            sys.exit()
            

        # if no pass or a blank pass is set in the database, prompt for a mysql password
        try:
            dbPass = config.get('cavat',  'dbpass')
            if not dbPass:
                raise Exception
        except Exception,  e:
            from getpass import getpass
            dbPass = getpass('Enter MySQL password for user "' + dbUser + '": ').strip()
        
        return mysql_connect(dbHost,  dbUser, dbPass)

    if engine == 'sqlite':
        # expand ~
        prefix = os.path.expanduser(prefix)
        
        # check to see if dir exists (prefix is a path to the db dir)
        try:
            if not os.path.exists(prefix):
                os.makedirs(prefix)
        except:
            print '! Could not create directory: ' + prefix
            return False
        
        return sqlite_connect()


def mysql_connect(host,  user,  passwd):
    
    global conn,  cursor
    
    # connect
    try:
        conn = MySQLdb.connect (host,  user,  passwd,  reconnect=1)
    except Exception,  e:
        import sys
        sys.exit('Database connection failed - ' + str(e))

    cursor = conn.cursor()

    return

# dummy function; changing db and connection to a db are the same thing for sqlite.
def sqlite_connect():
    return


# takes a dbname and optionally a dbprefix, and switches the connection to using that db
def changeDb(dbName):
    
    global engine
    
    if engine == 'mysql':
        return mysql_changeDb(dbName)
    elif engine == 'sqlite':
        return sqlite_changeDb(dbName)


# takes a dbname, sets up an sqlite connection to the db file.
def sqlite_changeDb(dbname):
    
    global prefix,  conn,  cursor

    import sqlite3

    if cavatDebug.debug:
        print 'Prefix:', prefix, 'DB name:', dbname

    try:
        conn = sqlite3.connect(os.path.join(prefix,  dbname))
    except Exception,  e:
        print '! SQLite Connection failed: ' + str(e)
        return False
    
    cursor = conn.cursor()

    return True

def mysql_changeDb(dbName):

    global prefix,  conn,  cursor

    try:
        conn.select_db(prefix + '_' + dbName)
    except:
        errorMsg('Could not switch to database '+dbName)
        return False
    
    cursor = conn.cursor()
    return True


def runQuery(sqlQuery,  failureMessage = 'Query failed.'):
    
    if cavatDebug.debug:
        print sqlQuery

    try:
        cursor.execute(sqlQuery)
        
    except Exception,  e:
        errorMsg(failureMessage)
        errorMsg("SQL was: \t" + str(sqlQuery))
        errorMsg("SQL error: \t"+ str(e))
        return False

    return True


def listCorpora():
    
    global engine,  prefix,  cursor
    
    if cavatDebug.debug:
        print 'Prefix is', prefix
    
    corporaList = []
    
    if engine == 'mysql':
        runQuery('SHOW DATABASES LIKE "' + prefix + '%"')
        results = cursor.fetchall()
        
        for row in results:
            listedDb = str(row[0])
            
            # strip prefix from databases
            listedDb = listedDb.replace(prefix + '_',  '')
            corporaList.append(listedDb)
        

    if engine == 'sqlite':
        corporaList = os.listdir(prefix)

    corporaList.sort
    
    if cavatDebug.debug:
        print corporaList

    return corporaList


def close():

    if cursor != None:
        cursor.close()

    if conn != None:
        conn.close()
    
    return
