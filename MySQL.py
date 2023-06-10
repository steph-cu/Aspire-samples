#---- MYSQL ------------------------------------------------
#   Python library for MYSQL commands for OpenADR server and client
#  
#============================================================================================================================
#               <<< Functions >>>
#            --- General Functions ---
#
#   __init__(con, cur)                  --> constructor to use connection and cursor for MySQL 
#   sql_connect()                       --> connects to MySQL
#   Close()                             --> Close the sql connection
#   show_tables()                       --> Shows all the tables in MySQL
#   show_databases()                    --> Shows the available databases
#   read_table(Table)                   --> Reads the data inside the specified table, prints to screen
#   get_from_table(Table, ID, Column)   --> gets the data from the table
#   drop_table(Table)                   --> Deletes the entire table (You will have to create a table after this command)
#   delete_entry(Table, ID)             --> Deletes the entry in the table with the ID
#
#           --- Table Specific Functions ---
#               < Equipment >
#
#   createTable_equipment()         --> Creates the equipment table for sql
#   Insert_equipment()              --> Called by createTable_equipment()
#   add_equipment(ID,IP, State)     --> Adds an entry into equipment table
#   update_equipment(ID, IP, State) --> Updates the entry in the table with ID
#
#
#                 < battery >
#
#   createTable_battery()                       --> Creates the user table for SQL
#   Insert_battery()                            --> Called by createTable_user()
#   update_battery(ID, charge_demand,power)     --> Updates the user with ID
#
#
#               < reference >
#   
#   createTable_reference()         --> Create the reference table for sql
#   Insert_reference()              --> called by createTable_reference
#   add_reference(x,x,x,x)          --> Add a new reference
#   update_reference(x,x,x,x,x,...) --> update a reference in the table
#   
#
#               < externalreference >
#
#   createTable_External_reference()    --> create te externalreference table 
#   Insert_externalreference()          --> called by createTable_External_reference
#   add_externalreference()             --> Add a new externalreference
#   update_externalreference()          --> update externalreference in the table
#   
#==============================================================================================================================
import mysql.connector
from mysql.connector import Error
import time as TIME
import datetime
from datetime import *



#=============> MYSQL <=================================================
class SQL:

    def __init__(self):
        self.sql_connect()
        self.Close()
        

    def sql_connect(self):
        try:
            #print("connecting to mysql ")
            connect = False
            timeout = 0
 
            while connect  == False and timeout < 3:
                self.connection =  mysql.connector.connect( # connect to SQL database
                    host="localhost",
                    user="ems",
                    password="evrems2023",
                    database="ems"
                )
                if self.connection.is_connected():
                    #print("\t\t Creating cursor \n\n")
                    self.cmd = self.connection.cursor(buffered=True)
                    connect = True
                else:
                    print("\t No Connection \n")
                    timeout += 1
                    if(timeout > 3):
                        print("TIME OUT, Please try again")
                        raise Exception("\n\n\n\n\nFailed to connect, No Cursor created \n\n\n\n\n\n")
                    TIME.sleep(1)

        except Exception as e:
            print(e)


    def Close(self):
        self.connection.close()

#---------------------------------------------------------------
    def show_tables(self):
        print("\n Tables: ")
        self.cmd.execute("SHOW TABLES")
        for table_name in self.cmd:
            t = str(table_name)
            t=t.split("'")
            print("\t",t[1])
        print("\n")

    def show_databases(self):
        print("\n Databases: ")
        self.cmd.execute("SHOW DATABASES")
        for name in self.cmd:
            print("\t",name)
    
        print("\n")
    
    
    
    def read_table(self,Table, ID, Column):
        if Column == '' and ID == '':
            print("\n ", Table, ": ")
            if(Table == 'users'):
                print("    ID   First   Last   A#   Email     Password   level      \n")
            elif(Table == 'equipment'):
                print("    ID \t  IP Address   State   Fault   Voltage  Current  Power  SOC \n")
            elif(Table == 'reference'):
                print("    ID  Mode/State  Range/Type  BDV Minimum  Voltage (AC)   Voltage (DC)   Current  Power  Over Current  Internal resistance NHR_mode NHR_enable NHR_safety NHR_slewVolt NHR_slewCurr NHR_slewPower NHR_slewRes NHR_Rgain MX_shape MX_cliplevel Reset NHR_parallel NHR_slaveunits time\n")
            elif(Table == 'externalreference'):
                print("    ID   Power Limit")
            elif(Table == 'battery'):
                print("    ID  Status  SOC  Charge_Rate  Power_Delivery")
            self.cmd.execute("SELECT * FROM " + Table)
        elif Column != '' and ID != '':
            sql = "SELECT "+str(Column)+ " FROM " + str(Table) + " WHERE ID= '" + str(ID)+ "';"
            self.cmd.execute(sql)
        elif Column != '' and ID == '':
            sql = "SELECT "+str(Column)+ " FROM " + str(Table) + ";"
            self.cmd.execute(sql)
        elif ID != '' and Column == '':
            try:
                if(Table == 'users'):
                    print("    ID   First   Last   A#   Email     Password   level      \n")
                elif(Table == 'equipment'):
                    print("    ID \t IP Address   State   Fault   Voltage  Current  Power  SOC \n")
                elif(Table == 'reference'):
                    print("    ID  Mode/State  Range/Type  BDV Minimum  Voltage (AC)   Voltage (DC)   Current  Power  Over Current  Internal resistance NHR_mode NHR_enable NHR_safety NHR_slewVolt NHR_slewCurr NHR_slewPower NHR_slewRes NHR_Rgain MX_shape MX_cliplevel Reset NHR_parallel NHR_slaveunits time\n")
                elif(Table == 'externalreference'):
                    print("    ID   Power Limit")
                elif(Table == 'battery'):
                    print("    ID  Status  SOC  Charge_Rate  Power_Delivery")
                sql = "SELECT * FROM " + str(Table) + " WHERE ID= '" + str(ID)+ "';"
                self.cmd.execute(sql)
            except Exception as e:
                print(ID, " not found in table.\n")
        else:
            print("Can not read from " , Table, "with ", ID, " and ", Column)

        for name in self.cmd:
            print("   ",name)
    
        print("\n")


    def get_from_table(self,Table, ID, Column):
        if Column != '' and ID != '':
            try:
                sql = "SELECT "+str(Column)+ " FROM " + str(Table) + " WHERE ID= '" + str(ID)+ "';"
            except Exception as e:
                sql = "SELECT "+str(Column)+ " FROM " + str(Table) + " WHERE id= '" + str(ID)+ "';"
            #print(sql)
            self.cmd.execute(sql)

            if Column == "ID" or Column =="Avaliable" or Column =="IP" or Column =="State" or Column =="Fault":
                for name in self.cmd:
                    t = str(name)
                    t=t.split("'")
                    #print(t)
                    return t[1]
            else:
                for I in self.cmd:
                    #print(I[0])
                    #i = str(I)
                    #print("\n ", i)
                    #i = i.replace(",", "")
                    #i = i.replace("(", "")
                    #i = i.replace(")", "")
                    #print(i)
                    return I[0]
        else:
            print("Can not read from " , Table, "with ", ID, " and ", Column)


    def get_from_schedule(self, Table, ID, Column):
        if Column != '' and ID != '':
            sql = "SELECT "+str(Column)+ " FROM " + str(Table) + " WHERE equipment= '" + str(ID)+ "';"
            #print(sql)
            self.cmd.execute(sql)

            for I in self.cmd:
                # print(I[0])
                return I[0]
        else:
            print("Can not read from scheduling with ", ID, " and ", Column)


    def get_active_event(self, Table, ID, Column):
        if Column != '' and ID != '':
            sql = "SELECT "+str(Column)+ " FROM "+ str(table) +"scheduling WHERE equipment='" + str(ID)+ "' AND date='" + str(date.today()) + "' AND start<='" + str(TIME.strftime("%H:%M:%S", TIME.localtime()))  +"' AND end>='" + str(TIME.strftime("%H:%M:%S", TIME.localtime())) +"';"
            #print(sql)
            self.cmd.execute(sql)

            for I in self.cmd:
                #print(I[0])
                return I[0]
        else:
            print("Can not read from scheduling with ", ID, " and ", Column)


    def drop_table(self, Table):
        sql = "DROP TABLE IF EXISTS " + str(Table)
        print("\n",sql)
        self.cmd.execute(sql)
        self.connection.commit()
        print("<< Dropped >> ", Table, "\n")


    def delete_entry(self,Table, ID):
        sql = "DELETE FROM " + str(Table) +" WHERE ID= '" + str(ID) + "';" # delete from table
        print("\n",sql)
        self.cmd.execute(sql)
        self.connection.commit()
        print("<< Deleted >> ", ID, "\n")
       
    
    #===============> Equipment <===============================================================
    def createTable_equipment(self):
        try:
            empty = True
            con = self.connection.is_connected()
            if con:
        
                #print(cmd.rowcount)
                self.cmd.execute("SHOW TABLES")
                for table_name in self.cmd:
                    t = str(table_name)
                    t=t.split("'")
                    #print("\t",t[1])
                
                    if(t[1] == 'equipment'):
                        empty = False
                    
                if(empty):
                    self.cmd.execute("CREATE TABLE IF NOT EXISTS equipment ( \
                                `ID` VARCHAR(100) NOT NULL, \
                                `IP` VARCHAR(15) NOT NULL, \
                                `State` VARCHAR(255) NOT NULL, \
                                `Fault` VARCHAR(500), \
                                `Voltage` int,\
                                `Current` FLOAT(8),\
                                `Power` FLOAT(8),\
                                `SOC` int,\
                                UNIQUE INDEX `IP_UNIQUE` (`IP` ASC) VISIBLE, \
                                UNIQUE INDEX `ID_UNIQUE` (`ID` ASC) VISIBLE);")
    
                    self.Insert_equipment()
    
        except Exception as err:
            print(f"\tError: '{err}'")
    
    
    def Insert_equipment(self):
        if self.connection.is_connected():
            # Insert value if it does not exist
            sql = "INSERT INTO equipment (ID, IP, State) VALUES (%s, %s, %s);"
            val = [
                    ('NHR_ONE', '192.168.225.61', 'Unknown'),    
                    ('NHR_TWO', '192.168.225.63', 'Unknown'),
                    ('NHR_THREE', '192.162.225.62', 'Unknown'),
                    ('GK', '192.168.225.65', 'Unknown'),
                    ('MX_THIRTY', '192.168.225.252', 'Unknown'),
                    ('Regatron', '192.168.225.45', 'Unknown'),
                    ('Yaskawa', '192.168.225.245', 'Unknown'),
                    ('Fronius_SEVEN_SIX', '192.168.225.77', 'Unknown'),
                    ('Fronius_TWENTY', '192.168.225.75', 'Unknown'),
                    ('SMA_FIFTY', '192.168.225.50', 'Unknown'),
                    ('SMA_SEVEN', '192.168.225.21', 'Unknown'),
                    ('Logix_Blue', '192.168.225.5', 'Unknown'),
                    ('Dynapower', '192.168.225.13', 'Unknown'),
                    ('Leviton', '192.168.225.99', 'Unknown'),
                    ('Grizl', '192.168.225.128', 'Unknown')
                   ]
            self.cmd.executemany(sql, val)
            self.connection.commit() # Save the vallue to the database
    

    def add_equipment( self, ID, IP, State):
        eq = False

        if self.connection.is_connected():
            sql = "SELECT ID FROM equipment; "
            self.cmd.execute(sql)
    
            for I in self.cmd:
                i = str(I)
                i = i.split("'")
                if(i[1] == ID ):
                    eq = True
    
            if(not eq):
                print("<<< Inserting >>>", ID, "\n")
                sql = "INSERT INTO equipment (ID, IP, State) VALUES (%s, %s, %s);"
                val = (ID, IP, State)
                self.cmd.execute(sql, val)
                self.connection.commit()
            else:
                print(ID, " << already exists \n")
    
    
    
    def update_equipment(self, ID, IP='', State='', Fault='', Voltage=None, Current=None, Power=None, SOC=None):
        if IP != '':
            sql = "UPDATE equipment SET IP = %s WHERE ID = %s;"
            val = (str(IP),ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if State != '':
            sql = "UPDATE equipment SET State = %s WHERE ID = %s;"
            val = (str(State),ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Fault != '':
            sql = "UPDATE equipment SET Fault = %s WHERE ID = %s;"
            val = (Fault,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Voltage != None:
            sql = "UPDATE equipment SET Voltage = %s WHERE ID = %s;"
            val = (Voltage,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Current != None:
            sql = "UPDATE equipment SET Current = %s WHERE ID = %s;"
            val = (Current,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Power != None:
            sql = "UPDATE equipment SET Power = %s WHERE ID = %s;"
            val = (Power,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if SOC != None:
            sql = "UPDATE equipment SET SOC = %s WHERE ID = %s;"
            val = (SOC,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        
        #print("< Updated >", ID," ", IP," ", State," ", Fault," ", Voltage,"V  ", Current,"A  ", Power,"W  ", SOC, "%\n")

#============> End Equipment <=============================================================================


#===================== Battery ==================================================================================
    def createTable_battery(self):
        try:
            empty = True
            con = self.connection.is_connected()
            if con:
        
                #print(self.cmd.rowcount)
                self.cmd.execute("SHOW TABLES")
                for table_name in self.cmd:
                    t = str(table_name)
                    t=t.split("'")
                    #print("\t",t[1])
                
                    if(t[1] == 'battery'):
                        empty = False
                    
                if(empty):
                    self.cmd.execute("CREATE TABLE IF NOT EXISTS battery ( \
                                `ID` VARCHAR(255) NOT NULL, \
                                `Status` VARCHAR(255),\
                                `SOC` int,\
                                `Charge_Rate` VARCHAR(255), \
                                `Power_Delivery` VARCHAR(255), \
                                UNIQUE INDEX `ID_UNIQUE` (`ID` ASC) VISIBLE);")
    
                    self.Insert_battery()
    
        except Exception as err:
            print(f"\tError: '{err}'")
    
    
    def Insert_battery(self):
        if self.connection.is_connected():
            # Insert value if it does not exist
            sql = "INSERT INTO battery (ID) VALUES (%s);"
            val =  [("Logix_Blue", ),
                    ("Control", ) ]
            self.cmd.executemany(sql, val)
            self.connection.commit() # Save the vallue to the database


    def add_battery( self, ID):
        eq = False
        ID = "'" + ID + "'" #<--- use this if ID is a string 
        if self.connection.is_connected():
            sql = "SELECT ID FROM battery; "
            self.cmd.execute(sql)
    
            for I in self.cmd: # compare ID with the table entries
                #print(I)
                i = str(I)
                #print("\n ", i)
                i = i.replace(",", "")
                i = i.replace("(", "")
                i = i.replace(")", "")
                #print("\n  " , i)
                if(i == str(ID) ):
                    eq = True
    
            if(not eq):
                ID = ID.replace("'","")
                sql = "INSERT INTO battery (ID) VALUES (%s);"
                val =  (ID, )
                self.cmd.execute(sql, val)
                self.connection.commit() # Save the vallue to the database
                print("<<< Inserting Battery >>>", ID, "\n")
            else:
                print(ID, " << Already Exists \n")
    
    
    
    def update_battery(self, ID,Status=None, SOC=None, charge=None, Power=None):
        if Status != None:
            sql = "UPDATE battery SET Status = %s WHERE ID = %s;"
            val = (str(Status),ID)
            self.cmd.execute(sql, val)
            print(self.cmd.statement)
            self.connection.commit()  
        if SOC != None:
            sql = "UPDATE battery SET SOC = %s WHERE ID = %s;"
            val = (SOC,ID)
            self.cmd.execute(sql, val)
            print(self.cmd.statement)
            self.connection.commit()
        if charge != None:
            sql = "UPDATE battery SET Desired_Charge_Rate = %s WHERE ID = %s;"
            val = (str(charge),ID)
            self.cmd.execute(sql, val)
            print(self.cmd.statement)
            self.connection.commit()
        if Power != None:
            sql = "UPDATE battery SET Power_Delivery = %s WHERE ID = %s;"
            val = (str(Power),ID)
            self.cmd.execute(sql, val)
            print(self.cmd.statement)
            self.connection.commit()        
            
        #print("< Updated >", ID,  " ",Status, " ", SOC, " ", charge," ", Power, "\n")

    def update_battery_schedule(self, ID, Schedule = None):
        if Schedule != None:
            sql = "UPDATE battery SET alter_schedule = %s WHERE ID = %s;"
            val = (str(Schedule),ID)
            self.cmd.execute(sql, val)
            self.connection.commit()        
        #print("< Updated >", ID,  " ",Status, " ", SOC, " ", charge," ", Power, "\n")

#========== End battery =========================================================================

# ============ Reference ================================================================

    def createTable_reference(self):
        try:
            empty = True
            con = self.connection.is_connected()
            if con:
        
                #print(self.cmd.rowcount)
                self.cmd.execute("SHOW TABLES")
                for table_name in self.cmd:
                    t = str(table_name)
                    t=t.split("'")
                    #print("\t",t[1])
                
                    if(t[1] == 'reference'):
                        empty = False
                    
                if(empty):
                    self.cmd.execute("CREATE TABLE IF NOT EXISTS reference ( \
                                `ID` VARCHAR(100) NOT NULL, \
                                `Mode_State` VARCHAR(100) DEFAULT 'OFF', \
                                `Range_Type` int DEFAULT 0,\
                                `BDV_Minimum` FLOAT(16), \
                                `Voltage_AC` FLOAT(16), \
                                `Voltage_DC` int, \
                                `Current` FLOAT(16), \
                                `Power` FLOAT(16), \
                                `Over_Current` int, \
                                `Internal_Resistance` FLOAT(16),\
                                `NHR_mode` int  DEFAULT 0,\
                                `NHR_enable` int DEFAULT 0,\
                                `NHR_safety` VARCHAR(255),\
                                `NHR_slewVolt` FLOAT(16),\
                                `NHR_slewCurr` FLOAT(16),\
                                `NHR_slewPower` FLOAT(16),\
                                `NHR_slewRes` FLOAT(16),\
                                `NHR_Rgain` FLOAT(16),\
				                `MX_shape` int DEFAULT 0,\
				                `MX_cliplevel` int DEFAULT 10,\
                                `Reset` BOOLEAN,\
				                `NHR_parallel` int,\
				                `NHR_slaveunits` int,\
                                `time` int,\
                                UNIQUE INDEX `ID_UNIQUE` (`ID` ASC) VISIBLE);")
    
                    self.Insert_reference()
    
        except Exception as err:
            print(f"\tError: '{err}'")
    
    
    def Insert_reference(self):
        if self.connection.is_connected():
            # Insert value if it does not exist
            sql = "INSERT INTO reference (ID) VALUES (%s);"
            val = [
                    ('NHR_ONE',),    
                    ('NHR_TWO',),
                    ('NHR_THREE',),
                    ('MX_THIRTY',),
                    ('GK',),
                    ('Regatron',),
                    ('Grizl',),
                    ('ABB East'),
                    ('ABB West')
                   ]
            self.cmd.executemany(sql, val)
            self.connection.commit() # Save the vallue to the database
    

    def add_reference( self, ID, Voltage, Current, Power):
        eq = False
        if self.connection.is_connected():
            sql = "SELECT ID FROM reference; "
            self.cmd.execute(sql)
    
            for I in self.cmd:
                i = str(I)
                i = i.split("'")
                if(i[1] == ID ):
                    eq = True
    
            if(not eq):
                print("<<< Inserting >>>", ID, ", ", Voltage, ",", Current, ",", Power, "\n")
                sql = "INSERT INTO reference (ID, Voltage, Current, Power) VALUES (%s, %s, %s, %s);"
                val = (ID, Voltage, Current, Power)
                self.cmd.execute(sql, val)
                self.connection.commit()
            else:
                print(ID, " << already exists \n")
    
    
    
    def update_reference(self, ID, State=None, Range=None, BDV=None, Voltage_AC=None, Voltage=None, Current=None, Power=None, OCurr=None, IRes=None, NHR_mode=None, NHR_enable=None, NHR_safety=None, NHR_slewVolt=None, NHR_slewCurr=None, NHR_slewPower=None, NHR_slewRes=None, NHR_Rgain=None, MX_shape=None, MX_cliplevel=None, Reset=None, NHR_parallel=None, NHR_slaveunits=None, time=TIME.time()):
        # print(time)
        if State != "":
            sql = "UPDATE reference SET Mode_State = %s WHERE ID = %s;"
            val = (State,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Range != None:
            sql = "UPDATE reference SET Range_Type = %s WHERE ID = %s;"
            val = (Range,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if BDV != None:
            sql = "UPDATE reference SET BDV_Minimum = %s WHERE ID = %s;"
            val = (BDV,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Voltage_AC != None:
            sql = "UPDATE reference SET Voltage_AC = %s WHERE ID = %s;"
            val = (Voltage_AC,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Voltage != None:
            sql = "UPDATE reference SET Voltage_DC = %s WHERE ID = %s;"
            val = (Voltage,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Current != None:
            sql = "UPDATE reference SET Current = %s WHERE ID = %s;"
            val = (Current,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Power != None:
            sql = "UPDATE reference SET Power = %s WHERE ID = %s;"
            val = (Power,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if OCurr != None:
            sql = "UPDATE reference SET Over_Current = %s WHERE ID = %s;"
            val = (OCurr,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if IRes != None:
            sql = "UPDATE reference SET Internal_Resistance = %s WHERE ID = %s;"
            val = (IRes,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_mode != None:
            sql = "UPDATE reference SET NHR_mode = %s WHERE ID = %s;"
            val = (NHR_mode,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_enable != None:
            sql = "UPDATE reference SET NHR_enable = %s WHERE ID = %s;"
            val = (NHR_enable,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_safety != None:
            sql = "UPDATE reference SET NHR_safety = %s WHERE ID = %s;"
            val = (NHR_safety,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_slewVolt != None:
            sql = "UPDATE reference SET NHR_slewVolt = %s WHERE ID = %s;"
            val = (NHR_slewVolt,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_slewCurr != None:
            sql = "UPDATE reference SET NHR_slewCurr = %s WHERE ID = %s;"
            val = (NHR_slewCurr,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_slewPower != None:
            sql = "UPDATE reference SET NHR_slewPower = %s WHERE ID = %s;"
            val = (NHR_slewPower,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_slewRes != None:
            sql = "UPDATE reference SET NHR_slewRes = %s WHERE ID = %s;"
            val = (NHR_slewRes,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_Rgain != None:
            sql = "UPDATE reference SET NHR_Rgain = %s WHERE ID = %s;"
            val = (NHR_Rgain,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if MX_shape != None:
            sql = "UPDATE reference SET MX_shape = %s WHERE ID = %s;"
            val = (MX_shape,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if MX_cliplevel != None:
            sql = "UPDATE reference SET MX_cliplevel = %s WHERE ID = %s;"
            val = (MX_cliplevel,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if Reset != None:
            sql = "UPDATE reference SET Reset = %s WHERE ID = %s;"
            val = (Reset,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_parallel != None:
            sql = "UPDATE reference SET NHR_parallel = %s WHERE ID = %s;"
            val = (NHR_parallel,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()
        if NHR_slaveunits != None:
            sql = "UPDATE reference SET NHR_slaveunits = %s WHERE ID = %s;"
            val = (NHR_slaveunits,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()

        ##---------------------- THIS WILL SEND AN EVENT TO THE CLIENT WHEN AN VALUE IS CHANGED ------------------------
        ## comment out to disable this

        sql = "UPDATE reference SET time = %s WHERE ID = %s;"  # this updates time everytime the reference is changed, so it will send an event too
        val = (time,ID)
        self.cmd.execute(sql, val)
        self.connection.commit()

        ##--------------------------------------------------------------------------------------------------------------

        print("< Updated >", ID," ", State," ", Range," ", BDV," ", Voltage_AC," ", Voltage," ", Current," ", Power," ", OCurr," ", IRes," ",NHR_mode," ", NHR_enable," ", NHR_safety," ", NHR_slewVolt," ", NHR_slewCurr," ", NHR_slewPower," ", NHR_slewRes," ", NHR_Rgain," ", MX_shape," ", MX_cliplevel," ", Reset," ", NHR_parallel," ", NHR_slaveunits, " ", time, "\n")



    def update_reference_charger(self, ID, State=None): # this function allows the test server to update the status of the chargers without interfering with user updates
        if State != "":
            sql = "UPDATE reference SET Mode_State = %s WHERE ID = %s;"
            val = (State,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()

        # print("< Updated >", ID," ", State, "\n")

#=============================== End Reference =========================================================

#=================================== Externalref ========================================
    def createTable_External_reference(self):
        try:
            empty = True
        
            if self.connection.is_connected():
        
                #print(self.cmd.rowcount)
                self.cmd.execute("SHOW TABLES")
                for table_name in self.cmd:
                    t = str(table_name)
                    t=t.split("'")
                    #print("\t",t[1])
                
                    if(t[1] == 'externalreference'):
                        empty = False
                    
                if(empty):
                    self.cmd.execute("CREATE TABLE IF NOT EXISTS externalreference ( \
                                `ID` VARCHAR(100) NOT NULL, \
                                `Power_Limit` int, \
                                UNIQUE INDEX `ID_UNIQUE` (`ID` ASC) VISIBLE);")
    
                    self.Insert_externalreference()
    
        except Exception as err:
            print(f"\tError: '{err}'")
    
    
    def Insert_externalreference(self):
        if self.connection.is_connected():
            # Insert value if it does not exist
            sql = "INSERT INTO externalreference (ID) VALUES (%s);"
            val = [
                    ('Fronius_SEVEN_SIX',), 
                    ('Fronius_TWENTY',),
                    ('SMA_FIFTY',),
                    ('SMA_SEVEN',),
                    ('Yaskawa',)
                   ]
            self.cmd.executemany(sql, val)
            self.connection.commit() # Save the vallue to the database
    

    def add_externalreference( self, ID, Power):
        eq = False
        if self.connection.is_connected():
            sql = "SELECT ID FROM externalreference; "
            self.cmd.execute(sql)
    
            for I in self.cmd:
                i = str(I)
                i = i.split("'")
                if(i[1] == ID ):
                    eq = True
    
            if(not eq):
                print("<<< Inserting >>>", ID, ", ", Power, "\n")
                sql = "INSERT INTO externalreference (ID, Voltage, Current, Power) VALUES (%s, %s, %s, %s);"
                val = (ID, Voltage, Current, Power)
                self.cmd.execute(sql, val)
                self.connection.commit()
            else:
                print(ID, " << already exists \n")
    
    
    
    def update_externalreference(self, ID, Power):
        if Power != None:
            sql = "UPDATE externalreference SET Power_Limit = %s WHERE ID = %s;"
            val = (Power,ID)
            self.cmd.execute(sql, val)
            self.connection.commit()

        print("< Updated >", ID," ", Power,"\n")

    def insert_event(self, ven_id=None, signal_name=None, signal_type=None, signal_id=None, dtstart=None, duration=None, signal_payload=None) :
        print("inserting event")
        if(ven_id != None and signal_name != None and signal_id != None and dtstart != None and duration != None and signal_payload != None) :
            sql = "DELETE FROM events where "
            val = ()
            if ven_id != '':
                sql = sql + "ven_id = %s "
                val = val + (ven_id,)
                if signal_name != '' or signal_type != '' or dtstart != '':
                    sql = sql + "AND "
            if signal_name != '':
                sql = sql + "signal_name = %s "
                val = val + (signal_name,)
                if signal_type != '' or dtstart != '':
                    sql = sql + "AND "
            if signal_type != '':
                sql = sql + "signal_type = %s "
                val = val + (signal_type,)
                sql = sql + "AND "
            sql = sql + "(UNIX_TIMESTAMP(dtstart) + duration < UNIX_TIMESTAMP(CURRENT_DATE()));"
            #sql = "DELETE FROM events where ven_id = %s and signal_name = %s and signal_type = %s and (UNIX_TIMESTAMP(dtstart) + duration < UNIX_TIMESTAMP(CURRENT_DATE()))" #Clean up old entries each insert
            #val = (ven_id, signal_name, signal_type)
            print(sql)
            self.cmd.execute(sql,val)
            self.connection.commit()
            #sql = "SELECT * FROM events WHERE (ven_id = %s and signal_name = %s and signal_type = %s and signal_id = %s and dtstart = %s)"
            #val = (ven_id, signal_name, signal_type, signal_id, dtstart)
            #result = self.cmd.execute(sql, val)
            sql = "SELECT * FROM events WHERE ("
            val = ()
            if ven_id != '':
                sql = sql + "ven_id = %s "
                val = val + (ven_id,)
                if signal_name != '' or signal_type != '' or dtstart != '':
                    sql = sql + "AND "
            if signal_name != '':
                sql = sql + "signal_name = %s "
                val = val + (signal_name,)
                if signal_type != '' or dtstart != '':
                    sql = sql + "AND "
            if signal_type != '':
                sql = sql + "signal_type = %s "
                val = val + (signal_type,)
                if dtstart != '' :
                    sql = sql + "AND "
            if dtstart != '':
                sql = sql + "dtstart = %s"
                val = val + (dtstart,)
            sql = sql + ");"
            print(sql)
            print(val)
            #sql = "SELECT * FROM events WHERE ven_id = %s and signal_name = %s and signal_type = %s and (UNIX_TIMESTAMP(dtstart) + duration >= UNIX_TIMESTAMP(%s)) and (UNIX_TIMESTAMP(dtstart) + duration <= UNIX_TIMESTAMP(%s) )"
            #val = (ven_id, signal_name, signal_type, dtstart, dtend)
            self.cmd.execute(sql,val)
            self.cmd.fetchall()

            if(self.cmd.rowcount > 0 ):
                print("Update event")
                sql = "UPDATE events SET ven_id = %s, signal_name = %s, signal_type = %s, signal_id = %s, dtstart = %s, duration = %s, signal_payload = %s WHERE (ven_id = %s and signal_name = %s and signal_type = %s and dtstart = %s);"
                val = (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload, ven_id, signal_name, signal_type, dtstart)
                print(sql)
                print(val)
                self.cmd.execute(sql, val)
                self.connection.commit()
            else :
                print("Insert event")
                sql = "INSERT INTO events (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                val = (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload)
                print(sql)
                print(val)
                self.cmd.execute(sql, val)
                print(self.cmd.statement)
                self.connection.commit()
        else :
            Exception("Not all parameters defined.")

    def select_events(self, ven_id='', signal_name='', signal_type='', dtstart='', dtend='') :
        sql = "DELETE FROM events where "
        val = ()
        if ven_id != '':
            sql = sql + "ven_id = %s "
            val = val + (ven_id,)
            if signal_name != '' or signal_type != '' or dtstart != '':
                sql = sql + "AND "
        if signal_name != '':
            sql = sql + "signal_name = %s "
            val = val + (signal_name,)
            if signal_type != '' or dtstart != '':
                sql = sql + "AND "
        if signal_type != '':
            sql = sql + "signal_type = %s "
            val = val + (signal_type,)
            sql = sql + "AND "
        sql = sql + "(UNIX_TIMESTAMP(dtstart) + duration < UNIX_TIMESTAMP(CURRENT_DATE()));"
        #sql = "DELETE FROM events where ven_id = %s and signal_name = %s and signal_type = %s and (UNIX_TIMESTAMP(dtstart) + duration < UNIX_TIMESTAMP(CURRENT_DATE()))" #Clean up old entries each insert
        #val = (ven_id, signal_name, signal_type)
        #print(sql)
        #print(val)
        self.cmd.execute(sql,val)
        self.connection.commit()
        #print(self.cmd.statement)
        sql = "SELECT * FROM events WHERE "
        val = ()
        if ven_id != '':
            sql = sql + "ven_id = %s "
            val = val + (ven_id,)
            if signal_name != '' or signal_type != '' or dtstart != '':
                sql = sql + "AND "
        if signal_name != '':
            sql = sql + "signal_name = %s "
            val = val + (signal_name,)
            if signal_type != '' or dtstart != '':
                sql = sql + "AND "
        if signal_type != '':
            sql = sql + "signal_type = %s "
            val = val + (signal_type,)
            if dtstart != '' and dtend != '' :
                sql = sql + "AND "
        if dtstart != '' and dtend != '':
            sql = sql + "(UNIX_TIMESTAMP(dtstart) + duration >= UNIX_TIMESTAMP(%s)) AND (UNIX_TIMESTAMP(dtstart) + duration <= UNIX_TIMESTAMP( %s) )"
            val = val + (dtstart, dtend,)
        sql = sql + ";"
        #print(sql)
        #print(val)
        #sql = "SELECT * FROM events WHERE ven_id = %s and signal_name = %s and signal_type = %s and (UNIX_TIMESTAMP(dtstart) + duration >= UNIX_TIMESTAMP(%s)) and (UNIX_TIMESTAMP(dtstart) + duration <= UNIX_TIMESTAMP(%s) )"
        #val = (ven_id, signal_name, signal_type, dtstart, dtend)
        result = self.cmd.execute(sql,val)
        #self.connection.commit()
        #print(result.cmd.with_rows)
        #print(self.cmd.statement)
        #if(self.cmd.with_rows > 0) :
        #    print(self.cmd.fetchall())
        #for result in self.cmd.execute(sql) :
        #    if result.with_rows:
        #        print(result.fetchall())

        return self.cmd




#============================End Externalref =========================================================
