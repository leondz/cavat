from cavatMessages import errorMsg
import MySQLdb
import cavatDebug
import sys


conn = None
cursor = None

def connect(host,  user,  passwd):
    
    global conn,  cursor
    
    # connect
    try:
        conn = MySQLdb.connect (host,  user,  passwd)
    except Exception,  e:
        import sys
        sys.exit('Database connection failed - ' + str(e))

    cursor = conn.cursor()

    return


def changeDb(dbName):
    
    global conn,  cursor

    conn.select_db(dbName)
    cursor = conn.cursor()
    return


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
