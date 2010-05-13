from cavatMessages import errorMsg
import MySQLdb
import cavatDebug
import sys


conn = None
cursor = None
version = None

def connect(host,  user,  passwd):
    
    global conn,  cursor
    
    # connect
    try:
        conn = MySQLdb.connect (host,  user,  passwd,  reconnect=1)
    except Exception,  e:
        import sys
        sys.exit('Database connection failed - ' + str(e))

    cursor = conn.cursor()

    return


def changeDb(dbName):
    
    global conn,  cursor
    
    try:
        conn.select_db(dbName)
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

def close():
    cursor.close()
    conn.close()
    return
