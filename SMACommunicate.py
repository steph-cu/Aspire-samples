# Doxygen comment
## @file
# @brief Code to read SMA Modbus registers
"""
#======================================================================================
#   SMA 7  IPAddress : <ip>, <port>
#   SMA 50 IPAddress : <ip>, <port>
#   baudrate : 9600
#   Unit = 3
#
#	    NOTE: SMA 7 Does not support all the registers the SMA 50 has
#
#       NOTE: All Register Addresses in the Modbus Manual are (address + 1)
#             i.e. model information in the manual <register>, address used in code <register>
#
#====================================================================================
#                           <<< Functions >>>
#   CheckStatus(Value)      interprets the status data for the inverter
#   DecodeValue(rr, regtp)  decodes the result from the register
#   OpenClient()            Connects to SMA
#
#   Status()                Read Modbus Register 
#   AC_Lifetime()           Read Modbus Register 
#   AC_Power()              Read Modbus Register 
#   AC_AN_Voltage()         Read Modbus Register 
#   AC_Total_Current()      Read Modbus Register 
#   AC_Frequency()          Read Modbus Register 
#   AC_Phase_A_Current()    Read Modbus Register 
#   Reactive_Power()        Read Modbus Register 
#   Apparent_Power()        Read Modbus Register 
#   Power_Factor()          Read Modbus Register 
#   DC_Current()            Read Modbus Register 
#   DC_Voltage()            Read Modbus Register 
#   DC_Power()              Read Modbus Register 
#
#   NOTE: SMA50 registers only
#   AC_BN_Voltage()         Read Modbus Register 
#   AC_CN_Voltage()         Read Modbus Register 
#   AC_AB_Voltage()         Read Modbus Register
#   AC_BC_Voltage()         Read Modbus Register
#   AC_CA_Voltage()         Read Modbus Register
#   AC_Phase_B_Current()    Read Modbus Register
#   AC_Phase_C_Current()    Read Modbus Register
#
#   SMA()                   Connects to SMA using tcp modbus
#   main()                  main function
#====================================================================================
"""

from pymodbus.constants import Endian
from pymodbus.client import ModbusTcpClient
# from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
import asyncio 

#\class for SMA
#\brief Class for processing and sending messages to receive values back from the SMA
class SMACommunication:

    def __init__(self, ip, port, unit, timeout, baudrate):
        self.IP = ip # Use '<broadcast>' for broadcasts
        self.port = port
        self.unit = unit
        self.timeout = timeout
        self.baudrate = baudrate
        self.SMA50_IP = <alternate IP>
        # self.OpenClient()
        #self.SMAConnection = ModbusTcpClient('localhost')

    ## Interprets the status data for the inverter
    def CheckStatus(self, Value):
        if(Value == 1):
            Value = "OFF"
        elif(Value == 2):
            Value = "Wait for PV Voltage"
        elif(Value == 3):
            Value = "Starting"
        elif(Value == 4):
            Value = "MPP (Running Normal)"
        elif(Value == 5):
            Value = "Regulated"
        elif(Value == 6):
            Value = "Shutting Down"
        elif(Value == 7):
            Value = "Fault"
        elif(Value == 8):
            Value = "Waiting for electric utility compamy"
        else:
            Value = "Status not found"
        return Value

    #=======================================================================================================================
    ## Decodes the data type form the register
    def DecodeValue(self, rr, regtp):
        try:
            if(rr.isError()):
                raise Exception(rr)

            decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            if( regtp == "uint16"):
                returnValue = decoder.decode_16bit_uint()
            elif(regtp == "int16"):
                returnValue = decoder.decode_16bit_int()
            elif(regtp == "string(32)"):
                returnValue = decoder.decode_string(32)
            elif(regtp == "single"):
                returnValue = decoder.decode_32bit_float()
            elif(regtp == "uint32"):
                returnValue = decoder.decode_32bit_uint()
            elif(regtp == "int32"):
                returnValue = decoder.decode_32bit_int()
            elif(regtp == "double"):
                returnValue = decoder.decode_64bit_float()
            elif(regtp == "uint64"):
                returnValue = decoder.decode_64bit_uint()
            elif(regtp == "int64"):
                returnValue = decoder.decode_64bit_int()
            elif(regtp == "enum16"):
                returnValue = rr.registers
            else:
                raise Exception("register type not supported, check documentation to see type format")

    #        print("    Decoded ", regtp, "\t", returnValue) # debugging
            return returnValue

        except Exception as e:
            raise Exception (e)


#============ Open Client ===================
    def OpenClient(self):
        try:
            self.SMAConnection = ModbusTcpClient(self.IP, port = self.port, timeout = self.timeout, baudrate = self.baudrate)
    # connect to SMA
            #print("\n Connecting to SMA: IpAddress", self.IP," Port", self.port )
            open = self.SMAConnection.connect() # open is True/False
            if( not open):
                raise Exception (" Connection Failed ", self.IP,"\n")
            
        except Exception as e:
            print(e)
            print("SMA OpenClient error")

#========== Status ==============================
#
# Register: <register> (SunSpec); <register> (SMA) operating status
# or
# Register: <register> (SMA); Overexcited vs Underexcited
#
# format : <register>
#================================================
    def Status(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_input_registers(<register>,1,slave=126) # Operating Status
            Value = self.DecodeValue(rr, "uint16")
            self.SMAConnection.close()
            return Value
   
        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA Status error")
            return 0.0


#========== AC Lifetime ===========================
#
# Register: <register> (SMA); Total yield
# ? why is this named AC lifetime?
#==================================================
    def Ac_Lifetime(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,4,slave=self.unit) # AC lifetime
            Value = self.DecodeValue(rr, "uint64")
            self.SMAConnection.close()
            return Value/1000
 
        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Lifetime error")
            return 0.0


#========== AC Power =============================
#
# Register <register>; Power
#=================================================
    def Ac_Power(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>-1,2,slave=self.unit) # AC Power
            Value = self.DecodeValue(rr, "int32")
            self.SMAConnection.close()
            return Value/1000
      
        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Power error")
            return 0.0

#========== AC AN Voltage =======================
#
# Register <register>; Grid Voltage phase L1
#================================================
    def Ac_AN_Voltage(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC AN Voltage
            Value = self.DecodeValue(rr, "uint32")
            self.SMAConnection.close()
            return Value/100
    
        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC AN Voltage error")
            return 0.0


#========== AC Total Current ===================
#
# Register <register>; Grid Current
#================================================
    def Ac_Total_Current(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC Total Current
            Value = self.DecodeValue(rr, "uint32")
            self.SMAConnection.close()
            return Value/1000

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Total Current error")
            return 0.0

#========== AC Frequency ========================
#
# Register <register>; Grid frequency
#================================================
    def Ac_Frequency(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC  Frequency
            Value = self.DecodeValue(rr, "uint32")
            self.SMAConnection.close()
            return Value/100

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Frequency error")
            return 0.0


#========== AC Phase A Current =================
#
# Register <register>; Grid Current Phase L1
#================================================
    def Ac_Phase_A_Current(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC Phase A Current
            Value = self.DecodeValue(rr, "int32")
            self.SMAConnection.close()
            return Value/1000

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Phase A current error")
            return 0.0


#========== Reactive Powrer ===================
#
# Register <register>; Reactive Power (VAr)
#================================================
    def Reactive_Power(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # Reactive Power
            Value = self.DecodeValue(rr, "int32")
            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA Reactive Power error")
            return 0.0


#========== Apparent Power ====================
#
# Register <register>; Apparent Power
#================================================
    def Apparent_Power(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # Apparent Power
            Value = self.DecodeValue(rr, "int32")
            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA Apparent Power error")
            return 0.0

#==========  Power Factor =====================
#
# Register <register>; Displacement Power Factor
#================================================
    def Power_Factor(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # Power Factor
            Value = self.DecodeValue(rr, "uint32")
            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA Power Factor error")
            return 0.0


#==========  DC Current ========================
#
# Register <register>; DC Current Input
#================================================
    def DC_Current(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # DC Current
            Value = self.DecodeValue(rr, "int32")
            print("Current: ", Value/1000)
            self.SMAConnection.close()
            return Value/1000

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA DC Current error")
            return 0.0

#==========  DC Voltage =======================
#
# Register <register>; DC voltage input
#================================================
    def DC_Voltage(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # DC Voltage
            Value = self.DecodeValue(rr, "int32")
            print("Voltage: ", Value/100)
            self.SMAConnection.close()
            return Value/100

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA DC Voltage error")
            return 0.0

#==========  DC Power =======================
#
# Register <register>; Total Power input
#================================================
    def DC_Power(self):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # DC Power
            Value = self.DecodeValue(rr, "int32")
            print("Power: ", Value)
            self.SMAConnection.close()
            #return Value
            return Value/1000

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA DC Power error")
            return 0.0


# SMA 50 Registers ONLY (SMA 7 does not support these registers)
#==========  AC BN Voltage ====================
#
# Register <register>; Grid voltage phase L2
#================================================
    def AC_BN_Voltage(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<regsister>,2,slave=self.unit) # AC BN Voltage
                Value = self.DecodeValue(rr, "uint32")
            
            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC BN Voltage error")
            return 0.0


#==========  AC CN Voltage ==================
#
# Register <register>; Grid Voltage phase L3
#================================================
    def AC_CN_Voltage(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC CN Voltage
                Value = self.DecodeValue(rr, "uint32")

            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC CN Voltage error")
            return 0.0


#==========  AC AB Voltage =================
#
# Register <register>; Grid Voltage phase L1 against L2
#================================================
    def AC_AB_Voltage(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,salve=self.unit) # AC AB Voltage
                Value = self.DecodeValue(rr, "uint32")

            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC AB Voltage error")
            return 0.0


#==========  AC BC Voltage =================
#
# Register <register>; Grid Voltage phase L2 against L3
#================================================
    def AC_BC_Voltage(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC BC Voltage
                Value = self.DecodeValue(rr, "uint32")

            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC BC Voltage error")
            return 0.0


#==========  AC CA Voltage ===================
#
# Register <register>; Grid Voltage phase L3 against L1
#================================================
    def AC_CA_Voltage(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC CA Voltage
                Value = self.DecodeValue(rr, "uint32")

            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC CA Voltage error")
            return 0.0


#==========  AC  Phase B Current ===============
#
# Register <register>; Grid Current phase L1
#================================================
    def AC_Phase_B_Current(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC Phase B Current
                Value = self.DecodeValue(rr, "int32")

            self.SMAConnection.close()
            return Value


        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC PhaseB Current error")
            return 0.0


#==========  AC  Phase C Current =============
#
# Register <register>; Grid Current phase L2
#================================================
    def AC_Phase_C_Current(self):
        try:
            self.OpenClient()
            if (self.IP == self.SMA50_IP):
                rr = self.SMAConnection.read_holding_registers(<register>,2,slave=self.unit) # AC Phase C Current
                Value = self.DecodeValue(rr, "int32")

            self.SMAConnection.close()
            return Value

        except Exception as e:
            self.SMAConnection.close()
            print(e)
            print("SMA AC Phase C Current error")
            return 0.0


#=========== Max_Output_Active_Power =============
#
# Register <register>; Set Active Power Limit
# 0 W - 7730 W (SunnyBoy) or 0 - 66000W (Sunny TriPower)
#================================================
    def Max_Output_Active_Power(self, amount):
        try:
            self.OpenClient()
            rr = self.SMAConnection.read_holding_registers(<registser>,2,slave=self.unit) # AC Phase C Current (from SunnyBoy)
            Value = self.DecodeValue(rr, "uint32")
            print("Output Active Power:\t",Value, "W\n" )
            print("Set Active Power to: \t",amount,"W\n")
            temp_power = [0,0]
            temp_power[0] = (int(amount) >> 16) & 0xFFFF
            temp_power[1] = int(amount) & 0xFFFF
            self.SMAConnection.write_registers(<register>,temp_power,slave=self.unit)
            rr = self.SMAConnection.read_holding_registers(<registrer>,2,slave=self.unit) # AC Phase C Current (from SunnyBoy)
            Value = self.DecodeValue(rr, "uint32")
            print("Output Active Power:\t",Value, "W\n" )
            self.SMAConnection.close()
        except Exception as e:
            self.SMAConnection.close()
            print("Problem with changing Max_output_active_Power")
            print(e)
    

 
            
async def main():
    SMA = SMACommunication(ip=<ip>, port=<port>, unit=3, timeout=8, baudrate=9600)
    print("Daily energy")
    SMA.DC_Voltage()
    SMA.DC_Current()
    SMA.DC_Power()
    
    # SEL_OBJ.Status(type="Device")
    print("Done with the Status")

#================================================================================

if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())
