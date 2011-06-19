from cavatMessages import errorMsg
import MySQLdb
import cavatDebug
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
    
    engine = config.get('cavat',  'dbtype')
    prefix = config.get('cavat',  'dbprefix')
    
    if engine == 'mysql':
        try:
            dbUser = config.get('cavat',  'dbuser')
            dbHost = config.get('cavat',  'dbhost')
        except Exception,  e:
            print '! Failure reading ini file: ' + str(e)
            sys.exit()
            

        # if no pass or a blank pass is set in the database, prompt for a mysql password
        try:
            dbPass = config.get('cavat',  'dbpass')
            if not dbPass:
                raise Exception
        except Exception,  e:
            from getpass import getpass
            dbPass = getpass('Enter MySQL password for user "' + dbUser + '": ').strip()
        
        return mysql_connect(dbHost, dbUser, dbPass)



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

# takes a dbname and optionally a dbprefix, and switches the connection to using that db
def changeDb(dbName):
    
    global engine,  prefix,  conn,  cursor
    
    if engine == 'mysql':
        
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
    
    corporaList = []
    
    if engine == 'mysql':
        runQuery('SHOW DATABASES LIKE "' + prefix + '%"')
        results = cursor.fetchall()
        
        for row in results:
            listedDb = str(row[0])
            
            # strip prefix from databases
            listedDb = listedDb.replace(prefix + '_',  '')
            corporaList.append(listedDb)
        

    corporaList.sort

    return corporaList


def close():
    cursor.close()
    conn.close()
    return
