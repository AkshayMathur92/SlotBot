from mysql.connector import connect, Error
from mysql.connector.pooling import MySQLConnectionPool
import json, logging

class SlotBotDB:
    def __init__(self):
        try:
            dbConfig = json.load(open("./dbenv.json", 'r'))
            self.connectionPool = MySQLConnectionPool(
                pool_name = "slot_db_pool",
                pool_size = 10,
                **dbConfig)
        except Error as e:
            logging.error(e)
            raise Exception("Not able to conenct to DB") 
    
    def runSelectQuery(self, query):
        try:
            conn = self.connectionPool.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Error as error:
            logging.error(error)
        finally:
            if(cursor):
                cursor.close()
            if(conn):
                conn.close()
        return []

    def runUpdateQuery(self, query, args):
        try:
            conn = self.connectionPool.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
        except Error as error:
            logging.error(error)
            return False
        finally:
            if(cursor):
                cursor.close()
            if(conn):
                conn.close()
        return True

    def addUser(self, user, pincode):
        if self.isUserRegistered(user):
            raise SlotBotException("User is already registerd, use /reset to start again")
        query = "INSERT INTO user_pincode(user, pincode) VALUES(%s, %s)"
        args = (user,pincode)
        if self.runUpdateQuery(query, args):
            logging.info("New user added")
        else:
            logging.error("user cannot be added")
            raise SlotBotException("User was not added due to some error. Please try again in some time.")
    
    def addUserWithState(self, user, name):
        query = "INSERT INTO user_pincode(user, name) VALUES(%s, %s)"
        args = (user, name)
        if self.runUpdateQuery(query, args):
            logging.info("New user added")
        else:
            logging.error("user cannot be added")
            raise SlotBotException("User was not added due to some error. Please try again in some time.")
    
    def deleteUser(self, user):
        query = "DELETE FROM user_pincode WHERE user={}".format(user)
        result = self.runUpdateQuery(query, ())

    def isUserRegistered(self, user):
        query = "SELECT user FROM user_pincode WHERE user={}".format(user)
        result = self.runSelectQuery(query)
        return len(result) > 0
    
    def getPinCodes(self):
        query = "SELECT pincode FROM user_pincode GROUP BY pincode"
        result = self.runSelectQuery(query)
        pincodes = []
        for row in result: pincodes.extend(row)
        return pincodes
    
    def getUsersWithPincode(self, pincode):
        query = "SELECT user FROM user_pincode where pincode={}".format(pincode)
        result = self.runSelectQuery(query)
        users = []
        for row in result: users.extend(row)
        return users
    
    def getState(self, user):
        query = "SELECT state FROM user_pincode where user={}".format(user)
        result = self.runSelectQuery(query)
        if(len(result) > 0):
            return result[0][0]
        return 0
    
    def saveState(self, user ,state):
        query = "UPDATE user_pincode SET state = %s WHERE user = %s"
        args = (state, user)
        if not self.runUpdateQuery(query, args):
            logging.error("state not saved")
            raise SlotBotException("Please try again in some time.")
    
    def updatePincode(self, user, pincode):
        query = "UPDATE user_pincode SET pincode = %s WHERE user = %s"
        args = (pincode, user)
        if not self.runUpdateQuery(query, args):
            logging.error("pincode not saved")
            raise SlotBotException("Please try again in some time.")
    
    def saveAge(self, user ,age):
        query = "UPDATE user_pincode SET age = %s WHERE user = %s"
        args = (age, user)
        if not self.runUpdateQuery(query, args):
            logging.error("age not saved")
            raise SlotBotException("Please try again in some time.")
 
class SlotBotException(Exception):
    def __init__(self, message):
        self.message = message