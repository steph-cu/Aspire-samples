// ******************************************************************************************************** //
#include "global_3LADAB.h"
// ******************************************************************************************************** //

// ******************************************** Init_GPIO_CANB ******************************************** //
void Init_GPIO_CANB()
{
    GPIO_SetupPinMux(21, GPIO_MUX_CPU1, 3);  //GPIO21 - CANRXB
    GPIO_SetupPinMux(20, GPIO_MUX_CPU1, 3);  //GPIO20 - CANTXB
    GPIO_SetupPinOptions(21, GPIO_INPUT, GPIO_ASYNC);
    GPIO_SetupPinOptions(20, GPIO_OUTPUT, GPIO_PUSHPULL);
}

// ******************************************* Init_GPIO_CANA ******************************************** //
void Init_GPIO_CANA()
{
    GPIO_SetupPinMux(18, GPIO_MUX_CPU1, 3);  //GPIO18 - CANRXA
    GPIO_SetupPinMux(19, GPIO_MUX_CPU1, 3);  //GPIO19 - CANTXA
    GPIO_SetupPinOptions(18, GPIO_INPUT, GPIO_ASYNC);
    GPIO_SetupPinOptions(19, GPIO_OUTPUT, GPIO_PUSHPULL);
}

// ********************************************** Init_CANB ********************************************** //
void Init_CANB()
{
    int16_t iMsg;

    // Activate CAN module software reset
    // 1. Set INIT bit to shut down CAN communication.
    // 2. Set SWR bit.

    EALLOW;
    CanbRegs.CAN_CTL.bit.Init = 1; // Keep the bus inactive during bit timing configuration, enabled later using function "Enable_CANB()"
    CanbRegs.CAN_CTL.bit.SWR = 1; //This bit will get cleared automatically one clock cycle after execution of software reset.
    EDIS;


    while(CanbRegs.CAN_IF1CMD.bit.Busy) {} // Wait for busy bit to clear

    // Clear the message value bit in the arbitration register.  This indicates
    // the message is not valid and is a "safe" condition to leave the message
    // object.  The same arb reg is used to program all the message objects.

    CanbRegs.CAN_IF1CMD.bit.DIR = 1;
    CanbRegs.CAN_IF1CMD.bit.Arb = 1;
    CanbRegs.CAN_IF1CMD.bit.Control = 1;

    CanbRegs.CAN_IF1ARB.all = 0;

    CanbRegs.CAN_IF1MCTL.all = 0;

    CanbRegs.CAN_IF2CMD.bit.DIR = 1;
    CanbRegs.CAN_IF2CMD.bit.Arb = 1;
    CanbRegs.CAN_IF2CMD.bit.Control = 1;

    CanbRegs.CAN_IF2ARB.all = 0;

    CanbRegs.CAN_IF2MCTL.all = 0;

    for(iMsg = 1; iMsg <= 32; iMsg+=2) // Loop through to program all 32 message objects
    {
        while(CanbRegs.CAN_IF1CMD.bit.Busy)
        {

        } // Wait for busy bit to clear

        CanbRegs.CAN_IF1CMD.bit.MSG_NUM = iMsg;

        while(CanbRegs.CAN_IF2CMD.bit.Busy)
        {

        } // Wait for busy bit to clear

        CanbRegs.CAN_IF2CMD.bit.MSG_NUM = iMsg + 1; // Initiate programming the message object
    }

    volatile uint32_t discardRead = CanbRegs.CAN_ES.all; // Acknowledge any pending status interrupts.

    ClkCfgRegs.CLKSRCCTL2.bit.CANBBCLKSEL = 0;

    setCANBBitRate(200000000, 250000);

    CanbRegs.CAN_CTL.bit.IE0 = 1;
    CanbRegs.CAN_GLB_INT_EN.bit.GLBINT0_EN = 1;
}

// ********************************************** Init_CANB ********************************************** //
void Init_CANA()
{

    int16_t iMsg;

    // Activate CAN A module software reset
    // 1. Set INIT bit to shut down CAN communication.
    // 2. Set SWR bit.
    EALLOW;
    CanaRegs.CAN_CTL.bit.Init = 1;  // Keep the bus inactive during bit timing configuration, enabled later using function "Enable_CANB()"
    CanaRegs.CAN_CTL.bit.SWR = 1; //This bit will get cleared automatically one clock cycle after execution of software reset.
    EDIS;

    while(CanaRegs.CAN_IF1CMD.bit.Busy) {} // Wait for busy bit to clear


    // Clear the message value bit in the arbitration register.  This indicates
    // the message is not valid and is a "safe" condition to leave the message
    // object.  The same arb reg is used to program all the message objects.

    CanaRegs.CAN_IF1CMD.bit.DIR = 1;
    CanaRegs.CAN_IF1CMD.bit.Arb = 1;
    CanaRegs.CAN_IF1CMD.bit.Control = 1;

    CanaRegs.CAN_IF1ARB.all = 0;

    CanaRegs.CAN_IF1MCTL.all = 0;

    CanaRegs.CAN_IF2CMD.bit.DIR = 1;
    CanaRegs.CAN_IF2CMD.bit.Arb = 1;
    CanaRegs.CAN_IF2CMD.bit.Control = 1;

    CanaRegs.CAN_IF2ARB.all = 0;

    CanaRegs.CAN_IF2MCTL.all = 0;

    for(iMsg = 1; iMsg <= 32; iMsg+=2) // Loop through to program all 32 message objects
    {
        while(CanaRegs.CAN_IF1CMD.bit.Busy) 
        {
            // Wait for busy bit to clear
        }

        CanaRegs.CAN_IF1CMD.bit.MSG_NUM = iMsg;

        while(CanaRegs.CAN_IF2CMD.bit.Busy)
        {
            // Wait for busy bit to clear
        }
        CanaRegs.CAN_IF2CMD.bit.MSG_NUM = iMsg + 1; // Initiate programming the message object
    }

    volatile uint32_t discardRead = CanaRegs.CAN_ES.all; // Acknowledge any pending status interrupts.

    ClkCfgRegs.CLKSRCCTL2.bit.CANABCLKSEL = 0;

    setCANABitRate(200000000, 250000);

    CanaRegs.CAN_CTL.bit.IE0 = 1;
    CanaRegs.CAN_GLB_INT_EN.bit.GLBINT0_EN = 1;
}

// ******************************************* setCANBBitRate ********************************************* //

// Set the CAN bit rate based on device clock (Hz) and desired bit rate (Hz)
uint32_t setCANBBitRate(uint32_t sourceClock, uint32_t bitRate)
{
    uint32_t desiredRatio;
    uint32_t canBits;
    uint32_t preDivide;
    uint32_t regValue;
//    uint16_t canControlValueA;// originally just canControlValue;
    uint16_t canControlValueB;

    desiredRatio = sourceClock / bitRate; // Calculate the desired clock rate.

    // Make sure that the Desired Ratio is not too large.  This enforces the
    // requirement that the bit rate is larger than requested.

    if((sourceClock / desiredRatio) > bitRate)
    {
        desiredRatio += 1;
    }

    while(desiredRatio <= CAN_MAX_PRE_DIVISOR * CAN_MAX_BIT_DIVISOR) // Check all possible values to find a matching value.
    {
        //
        // Loop through all possible CAN bit divisors.
        //
        for(canBits = CAN_MAX_BIT_DIVISOR;
                canBits >= CAN_MIN_BIT_DIVISOR;
                canBits--)
        {

            preDivide = desiredRatio / canBits; // For a given CAN bit divisor save the pre divisor.

            // If the calculated divisors match the desired clock ratio then
            // return these bit rate and set the CAN bit timing.

            if((preDivide * canBits) == desiredRatio)
            {
                //
                // Start building the bit timing value by adding the bit timing
                // in time quanta.
                //
                regValue = canBitValues[canBits - CAN_MIN_BIT_DIVISOR];

                //
                // To set the bit timing register, the controller must be
                // placed
                // in init mode (if not already), and also configuration change
                // bit enabled.  The state of the register should be saved
                // so it can be restored.
                //
//                canControlValueA = CanaRegs.CAN_CTL.all;
//                CanaRegs.CAN_CTL.bit.Init = 1;
//                CanaRegs.CAN_CTL.bit.CCE = 1;

                // Add for CANB
                canControlValueB = CanbRegs.CAN_CTL.all;
                CanbRegs.CAN_CTL.bit.Init = 1;
                CanbRegs.CAN_CTL.bit.CCE = 1;

                //
                // Now add in the pre-scalar on the bit rate.
                //
                regValue |= ((preDivide - 1) & CAN_BTR_BRP_M) |
                            (((preDivide - 1) << 10) & CAN_BTR_BRPE_M);

                CanbRegs.CAN_BTR.all = regValue; // Set the clock bits in the and the bits of the pre-scalar.

                CanbRegs.CAN_CTL.all = canControlValueB; // Restore the saved CAN Control register.

                return(sourceClock / ( preDivide * canBits)); // Return the computed bit rate.
            }
        }

        //
        // Move the divisor up one and look again.  Only in rare cases are
        // more than 2 loops required to find the value.
        //
        desiredRatio++;
    }
    return 0;
}

// ******************************************* setCANABitRate ********************************************* //

// Set the CAN bit rate based on device clock (Hz) and desired bit rate (Hz)
uint32_t setCANABitRate(uint32_t sourceClock, uint32_t bitRate)
{
    uint32_t desiredRatio;
    uint32_t canBits;
    uint32_t preDivide;
    uint32_t regValue;
//    uint16_t canControlValueA;// originally just canControlValue;
    uint16_t canControlValueA;

    desiredRatio = sourceClock / bitRate; // Calculate the desired clock rate.

    // Make sure that the Desired Ratio is not too large.  This enforces the
    // requirement that the bit rate is larger than requested.

    if((sourceClock / desiredRatio) > bitRate)
    {
        desiredRatio += 1;
    }

    while(desiredRatio <= CAN_MAX_PRE_DIVISOR * CAN_MAX_BIT_DIVISOR) // Check all possible values to find a matching value.
    {
        //
        // Loop through all possible CAN bit divisors.
        //
        for(canBits = CAN_MAX_BIT_DIVISOR;
                canBits >= CAN_MIN_BIT_DIVISOR;
                canBits--)
        {

            preDivide = desiredRatio / canBits; // For a given CAN bit divisor save the pre divisor.

            // If the calculated divisors match the desired clock ratio then
            // return these bit rate and set the CAN bit timing.

            if((preDivide * canBits) == desiredRatio)
            {
                //
                // Start building the bit timing value by adding the bit timing
                // in time quanta.
                //
                regValue = canBitValues[canBits - CAN_MIN_BIT_DIVISOR];

                //
                // To set the bit timing register, the controller must be
                // placed
                // in init mode (if not already), and also configuration change
                // bit enabled.  The state of the register should be saved
                // so it can be restored.
                //
//                canControlValueA = CanaRegs.CAN_CTL.all;
//                CanaRegs.CAN_CTL.bit.Init = 1;
//                CanaRegs.CAN_CTL.bit.CCE = 1;

                // Add for CANB
                canControlValueA = CanaRegs.CAN_CTL.all;
                CanaRegs.CAN_CTL.bit.Init = 1;
                CanaRegs.CAN_CTL.bit.CCE = 1;

                //
                // Now add in the pre-scalar on the bit rate.
                //
                regValue |= ((preDivide - 1) & CAN_BTR_BRP_M) |
                            (((preDivide - 1) << 10) & CAN_BTR_BRPE_M);

                CanaRegs.CAN_BTR.all = regValue; // Set the clock bits in the and the bits of the pre-scalar.

                CanaRegs.CAN_CTL.all = canControlValueA; // Restore the saved CAN Control register.

                return(sourceClock / ( preDivide * canBits)); // Return the computed bit rate.
            }
        }

        //
        // Move the divisor up one and look again.  Only in rare cases are
        // more than 2 loops required to find the value.
        //
        desiredRatio++;
    }
    return 0;
}

// ****************************************** setupMessageObjectB ***************************************** //
void setupMessageObjectB(uint32_t objID, uint32_t msg_ID_offset, msgObjType msgType, Uint16 msg_size, bool u_mask)
{
    //
    // Use Shadow variable for IF1CMD. IF1CMD should be written to in single 32-bit write.
    //
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;

    uint32_t maskReg = CAN_MSG_ID_MASK;

    while(CanbRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    // Clear and Write out the registers to program the message object.

    CAN_IF1CMD_SHADOW.all = 0;
    CanbRegs.CAN_IF1MSK.all = 0;
    CanbRegs.CAN_IF1ARB.all = 0;
    CanbRegs.CAN_IF1MCTL.all = 0;


    // Set the Control, Mask, Arb, MB number so that they get transferred to the Message object.

    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.Arb = 1;
    CAN_IF1CMD_SHADOW.bit.Mask = 1;
    CAN_IF1CMD_SHADOW.bit.DIR = 1;
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer data to message object RAM

    // Set direction to transmit

    if(msgType == MSG_OBJ_TYPE_TRANSMIT || msgType == MSG_OBJ_TYPE_REMOTE_T)
    {
        CanbRegs.CAN_IF1ARB.bit.Dir = 1;
    }
    if(msgType == MSG_OBJ_TYPE_RECEIVE)
    {
//        CanbRegs.CAN_IF1MCTL.bit.RxIE = 1; // No more interrupt
        CanbRegs.CAN_IF1MCTL.bit.UMask = u_mask;
    }

    // Set the data length since this is set for all transfers.  This is
    // also a single transfer and not a FIFO transfer so set EOB bit.
    CanbRegs.CAN_IF1MCTL.bit.DLC = msg_size;
    CanbRegs.CAN_IF1MCTL.bit.EoB = 1;

    if(msgType == MSG_OBJ_TYPE_REMOTE_T)
    {
        CanbRegs.CAN_IF1MCTL.bit.RmtEn = 1;
        CanbRegs.CAN_IF1MCTL.bit.UMask = 1;
    }

    CanbRegs.CAN_IF1MSK.all = maskReg; // Set Mask filter

    // Set Message ID (for RX this is AND with MASK so only 3 MSB will associate with the MB number)
    CanbRegs.CAN_IF1ARB.bit.Xtd = 0; // not using extended addressing
    CanbRegs.CAN_IF1ARB.bit.ID = (msg_ID_offset << CAN_MSG_ID_SHIFT);
    CanbRegs.CAN_IF1ARB.bit.MsgVal = 1;


    CanbRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;
}

// ****************************************** setupMessageObjectA ***************************************** //
void setupMessageObjectA(uint32_t objID, uint32_t msg_ID_offset, msgObjType msgType, Uint16 msg_size, bool u_mask)
{
    //
    // Use Shadow variable for IF1CMD. IF1CMD should be written to in single 32-bit write.
    //
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;

    uint32_t maskReg = CAN_MSG_ID_MASK;

    while(CanaRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    // Clear and Write out the registers to program the message object.

    CAN_IF1CMD_SHADOW.all = 0;
    CanaRegs.CAN_IF1MSK.all = 0;
    CanaRegs.CAN_IF1ARB.all = 0;
    CanaRegs.CAN_IF1MCTL.all = 0;


    // Set the Control, Mask, Arb, MB number so that they get transferred to the Message object.

    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.Arb = 1;
    CAN_IF1CMD_SHADOW.bit.Mask = 1;
    CAN_IF1CMD_SHADOW.bit.DIR = 1;
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer data to message object RAM

    // Set direction to transmit

    if(msgType == MSG_OBJ_TYPE_TRANSMIT || msgType == MSG_OBJ_TYPE_REMOTE_T)
    {
        CanaRegs.CAN_IF1ARB.bit.Dir = 1;
    }
    if(msgType == MSG_OBJ_TYPE_RECEIVE)
    {
//        CanaRegs.CAN_IF1MCTL.bit.RxIE = 1; // No more interrupt
        CanaRegs.CAN_IF1MCTL.bit.UMask = u_mask;
    }

    // Set the data length since this is set for all transfers.  This is
    // also a single transfer and not a FIFO transfer so set EOB bit.
    CanaRegs.CAN_IF1MCTL.bit.DLC = msg_size;
    CanaRegs.CAN_IF1MCTL.bit.EoB = 1;

    if(msgType == MSG_OBJ_TYPE_REMOTE_T)
    {
        CanaRegs.CAN_IF1MCTL.bit.RmtEn = 1;
        CanaRegs.CAN_IF1MCTL.bit.UMask = 1;
    }

    CanaRegs.CAN_IF1MSK.all = maskReg; // Set Mask filter

    // Set Message ID (for RX this is AND with MASK so only 3 MSB will associate with the MB number)
    CanaRegs.CAN_IF1ARB.bit.Xtd = 0; // not using extended addressing
    CanaRegs.CAN_IF1ARB.bit.ID = (msg_ID_offset << CAN_MSG_ID_SHIFT);
    CanaRegs.CAN_IF1ARB.bit.MsgVal = 1;


    CanaRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;
}

// ************************************** CANB Mailbox Init ********************************************** //
void Init_CANB_Mailboxes(void){

    //  TX Mailboxes 1-2
    setupMessageObjectB(OUTPUT_TX_MB_ID, OUTPUT_TX_MSG_ID, MSG_OBJ_TYPE_TRANSMIT, 5, false);// MB2 for DC-DC communication (This is used for CAN B for Iout and Vout data)

    // RX Mailboxes 5-27
    setupMessageObjectB(UNFOLDER_MB_ID, UNFOLDER_MSG_ID, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB7 for DC-DC module 1 output info
    setupMessageObjectB(DCDC_MB_ID_1, DCDC_MSG_ID_1, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB8 for DC-DC module 1 output info
    setupMessageObjectB(DCDC_MB_ID_2, DCDC_MSG_ID_2, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB9 for DC-DC module 2 output info
    setupMessageObjectB(DCDC_MB_ID_3, DCDC_MSG_ID_3, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 3 output info
    setupMessageObjectB(DCDC_MB_ID_4, DCDC_MSG_ID_4, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 4 output info
    setupMessageObjectB(DCDC_MB_ID_5, DCDC_MSG_ID_5, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 5 output info
    setupMessageObjectB(DCDC_MB_ID_6, DCDC_MSG_ID_6, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 6 output info
    setupMessageObjectB(DCDC_MB_ID_7, DCDC_MSG_ID_7, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 7 output info
    setupMessageObjectB(DCDC_MB_ID_8, DCDC_MSG_ID_8, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 8 output info
    setupMessageObjectB(DCDC_MB_ID_9, DCDC_MSG_ID_9, MSG_OBJ_TYPE_RECEIVE, 5, false);   // MB for DC-DC module 9 output info
    setupMessageObjectB(DCDC_MB_ID_10, DCDC_MSG_ID_10, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 10 output info
    setupMessageObjectB(DCDC_MB_ID_11, DCDC_MSG_ID_11, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 11 output info
    setupMessageObjectB(DCDC_MB_ID_12, DCDC_MSG_ID_12, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 12 output info
    setupMessageObjectB(DCDC_MB_ID_13, DCDC_MSG_ID_13, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 13 output info
    setupMessageObjectB(DCDC_MB_ID_14, DCDC_MSG_ID_14, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 14 output info
    setupMessageObjectB(DCDC_MB_ID_15, DCDC_MSG_ID_15, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 15 output info
    setupMessageObjectB(DCDC_MB_ID_16, DCDC_MSG_ID_16, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB for DC-DC module 16 output info

}

// ************************************** CANA Mailbox Init ********************************************** //
void Init_CANA_Mailboxes(void){
    // TX Mailboxes 1-2
    setupMessageObjectA(FAULT_TX_MB_ID, FAULT_TX_MSG_ID, MSG_OBJ_TYPE_TRANSMIT, 8, false); // MB1 for DC-DC fault communication
    setupMessageObjectA(OUTPUT_TX_MB_ID, OUTPUT_TX_MSG_ID, MSG_OBJ_TYPE_TRANSMIT, 8, false);// MB3 for transmitting ADC Calibration Offset Info

    // RX Mailboxes 5-23
    setupMessageObjectA(MATLAB_RX_MB_ID, MATLAB_RX_MSG_ID, MSG_OBJ_TYPE_RECEIVE, 8, true); // MB5 From Matlab
    setupMessageObjectA(FAULT_RX_MB_ID, FAULT_CAN_MSG_OFFSET, MSG_OBJ_TYPE_RECEIVE, 8, true); // MB6 for DC-DC fault communication
    setupMessageObjectA(UNFOLDER_MB_ID, UNFOLDER_MSG_ID, MSG_OBJ_TYPE_RECEIVE, 5, false); // MB7 for Unfolder info
    setupMessageObjectA(DCDC_MB_ID_1, DCDC_MSG_ID_1, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_2, DCDC_MSG_ID_2, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_3, DCDC_MSG_ID_3, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_4, DCDC_MSG_ID_4, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_5, DCDC_MSG_ID_5, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_6, DCDC_MSG_ID_6, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_7, DCDC_MSG_ID_7, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_8, DCDC_MSG_ID_8, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_9, DCDC_MSG_ID_9, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_10, DCDC_MSG_ID_10, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_11, DCDC_MSG_ID_11, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_12, DCDC_MSG_ID_12, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_13, DCDC_MSG_ID_13, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_14, DCDC_MSG_ID_14, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_15, DCDC_MSG_ID_15, MSG_OBJ_TYPE_RECEIVE, 8, false);
    setupMessageObjectA(DCDC_MB_ID_16, DCDC_MSG_ID_16, MSG_OBJ_TYPE_RECEIVE, 8, false);
}





// ************************************** CAN_Send_Fault_MessagesA *************************************** //
bool CANA_Send_Fault_Message(uint32_t Obj_ID, struct FAULT_LOG fault_tx)
{
    Uint32 temp = (0x3F & fault_tx.fault_code) + (0xFFFFFFC0 & (fault_tx.time << 6L));
    Uint16 temp1 = 0xFFFF & temp;
    Uint16 temp2 = 0xFFFF & (temp >> 16L);
    TX_Data_CANA[0] = temp1; // send [5:0] fault code bits and [9:0] fault time bits
    TX_Data_CANA[1] = temp2; // send [25:10] fault time bits which gives about 24 min of time with 21.6 us resolution
    TX_Data_CANA[2] = fault_tx.int1;
    TX_Data_CANA[3] = fault_tx.int2;

    return CANA_Send_Message(Obj_ID, TX_Data_CANA);
}


// ************************************** CAN_Send_Calibration_MessagesA ********************************* //

bool CANA_Send_ADC_Message(uint32_t Obj_ID, int16 ID)
{

    if (ID == 0)
    {
        TX_Data_CANA[0] = (int16)(LPF1_out + ADC_Result.Iout_send_offset);
        TX_Data_CANA[1] = (int16)(LPF2_out + ADC_Result.Vout_send_offset);
        TX_Data_CANA[2] = (int16)(LPF4_out + ADC_Result.Ip_send_offset);
        TX_Data_CANA[3] = ID + (Flags.bit.fault << 1L) + (Flags.bit.ePWM << 2L);
    }
    else if (ID == 1)
    {
        TX_Data_CANA[0] = (int16)(LPF5_out + ADC_Result.In_send_offset);
        TX_Data_CANA[1] = (int16)(LPF6_out + ADC_Result.Vpo_send_offset);
        TX_Data_CANA[2] = (int16)(LPF7_out + ADC_Result.Von_send_offset);
        TX_Data_CANA[3] = ID + (Flags.bit.fault << 1L) + (Flags.bit.ePWM << 2L);
    }

    return CANA_Send_Message(Obj_ID, TX_Data_CANA);
}



// ****************************************** sendCANMessageA ********************************************* //
bool CANA_Send_Message(uint32_t objID, uint32_t *objData) // sendCANMessage - Transmit data from the specified message object
{
    //
    // Use Shadow variable for IF1CMD. IF1CMD should be written to in
    // single 32-bit write.
    //
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;

    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer the message object to the message object specified by objID.

    while(CanaRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    CanaRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;

    while(CanaRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    if(CanaRegs.CAN_IF1MCTL.bit.TxRqst){ // Previous data hasn't sent yet

#if CAN_COMM_PROT
        if(Fault.Counter.CANA_timer >= CANA_TIME_OUT){
            Stop_ePWM(); // Stop modulation by abruptly opening all switches simultaneously
            SET_INT_SW_FAULT();
            Fault.Fault.bit.CANA = 0;
            Fault.CANA_Protection.bit.CAN_TX = 0;

            // Hard Reset CAN Module
            DIS_CANA();
            Init_CANA();
            Init_CANA_Mailboxes();
            EN_CANA();

            // Add fault to log
            if(Fault.count<FAULT_LOG_SIZE){
                Fault.Log[Fault.count].fault_code = 37; // CANA_TX Fault
                Fault.Log[Fault.count].int1 = objID;
                Fault.Log[Fault.count].int2 = 0;
                Fault.Log[Fault.count].time = Fault.time;
                ++Fault.count;
            }

            Flags.bit.send_messageA = 0; // Clear send message bit
            Flags.bit.en_CAN = 0; // Stop enabling send message bit

        }
#endif
        return false;
    }

    //
    // Write data to transfer into DATA-A and DATA-B interface registers
    //
    CanaRegs.CAN_IF1DATA.all = objData[0];// | (objData[1] << 16);
    CanaRegs.CAN_IF1DATB.all = objData[1];

    //
    // Set Direction to write and set DATA-A/DATA-B to be transfered to message object
    //
    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.DIR = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_A = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_B = 1;

    CAN_IF1CMD_SHADOW.bit.TXRQST = 1; // Set Tx Request Bit

    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer the message object to the message object specified by objID.
    CanaRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;
    Fault.Counter.CANA_timer = 0;

    return true;
}



// ************************************** CAN_Send_Output_MessageB **************************************** //
bool CANB_Send_Output_Message(uint32_t Obj_ID, int16 Iout_ADC, int16 Vout_ADC)
{
    Uint16 temp = 0xFFFF&(Flags.all>>12L);
    TX_Data_CANB[0] = Iout_ADC+ADC_Result.Iout_send_offset;
    TX_Data_CANB[1] = Vout_ADC+ADC_Result.Vout_send_offset;
    TX_Data_CANB[2] = temp;

    Output_RX_Data[THIS_DCDC_ID - 1] = TX_Data_CANB[0]; // for current
    Output_RX_Data[THIS_DCDC_ID + 19] = TX_Data_CANB[1]; // for voltage

    return CANB_Send_Message(Obj_ID, TX_Data_CANB);
}

// ****************************************** sendCANMessageB ********************************************* //
bool CANB_Send_Message(uint32_t objID, uint32_t *objData) // sendCANMessage - Transmit data from the specified message object
{
    //
    // Use Shadow variable for IF1CMD. IF1CMD should be written to in
    // single 32-bit write.
    //
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;

    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer the message object to the message object specified by objID.

    while(CanbRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    CanbRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;

    while(CanbRegs.CAN_IF1CMD.bit.Busy){} // Wait for busy bit to clear.

    if(CanbRegs.CAN_IF1MCTL.bit.TxRqst){
#if CAN_COMM_PROT
        if(Fault.Counter.CANB_timer >= CANB_TIME_OUT){
            Stop_ePWM(); // Stop modulation by abruptly opening all switches simultaneously
            SET_INT_SW_FAULT();
            Fault.Fault.bit.CANB = 0;
            Fault.CANB_Protection.bit.CAN_TX = 0;
        }
#endif
        return false;
    }

    //
    // Write data to transfer into DATA-A and DATA-B interface registers
    //
    CanbRegs.CAN_IF1DATA.all = objData[0];// | (objData[1] << 16);
    CanbRegs.CAN_IF1DATB.all = objData[1];

    //
    // Set Direction to write and set DATA-A/DATA-B to be transfered to message object
    //
    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.DIR = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_A = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_B = 1;

    CAN_IF1CMD_SHADOW.bit.TXRQST = 1; // Set Tx Request Bit

    CAN_IF1CMD_SHADOW.bit.MSG_NUM = objID; // Transfer the message object to the message object specified by objID.
    CanbRegs.CAN_IF1CMD.all = CAN_IF1CMD_SHADOW.all;
    Fault.Counter.CANB_timer = 0;
    return true;
}






// **********************  CANB RX Polling - check receive mailboxes for new data  ************************ //
void poll_CAN_Mailboxes(void){
    Uint16 mailbox;

    // Check receive message Mailbox
    if(CanbRegs.CAN_NDAT_21 & CANB_RX_MB_MASK){
        for(mailbox = CANB_RX_MB_START; mailbox <= CANB_RX_MB_END; ++mailbox){
            // Check New Dat bit for each RX MB separately
            if((CanbRegs.CAN_NDAT_21>>(mailbox-1)) & 0x1){
                CANB_Get_Message(mailbox);
            }
        }
    }

    // Check receive message Mailbox
    if(CanaRegs.CAN_NDAT_21 & CANA_RX_MB_MASK){
        for(mailbox = CANA_RX_MB_START; mailbox <= CANA_RX_MB_END; ++mailbox){
            // Check New Dat bit for each RX MB separately
            if((CanaRegs.CAN_NDAT_21>>(mailbox-1)) & 0x1){
                CANA_Get_Message(mailbox);
            }
        }
    }





}


// **********************  CAN RX Message handler for CANB  ****************************** //
void CANB_Get_Message(Uint32 mailbox)
{
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;
    Uint16 module;
    Uint32 temp_module_mask;
    Uint16 msgID;
    Uint16 i, n_tot;
    float Vo_mod_avg,Vo_tot;

    // Set the Message Data A, Data B, and control values to be read on request for data from the message object.

    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.Arb = 1;
    CAN_IF1CMD_SHADOW.bit.Mask = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_A = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_B = 1;

    CAN_IF1CMD_SHADOW.bit.MSG_NUM = mailbox; // Transfer the message object to the message object IF register.

    while(CanbRegs.CAN_IF2CMD.bit.Busy){} // Wait for busy bit to clear.

    CanbRegs.CAN_IF2CMD.all = CAN_IF1CMD_SHADOW.all;

    while(CanbRegs.CAN_IF2CMD.bit.Busy){} // Wait for busy bit to clear.

    // Check for lost messages and initiate protection
    if(CanbRegs.CAN_IF2MCTL.bit.MsgLst){
#if CAN_COMM_PROT
        Stop_ePWM();    // Stop Modulation
        SET_INT_SW_FAULT();
        Fault.Fault.bit.CANB = 0;
#endif
        Fault.CANB_Protection.bit.CAN_MSG_LST = 0;
        Fault.CANB_Protection.bit.MB_ID_LST = mailbox;
        if(Fault.count<FAULT_LOG_SIZE){
            Fault.Log[Fault.count].fault_code = 36;
            Fault.Log[Fault.count].int1 = mailbox;
            Fault.Log[Fault.count].int2 = 0;
            Fault.Log[Fault.count].time = Fault.time;
            ++Fault.count;
        }
    }

    msgID = 0x7FF&(CanbRegs.CAN_IF2ARB.all >> CAN_MSG_ID_SHIFT);

    switch(mailbox)
    {
    case UNFOLDER_MB_ID:

        Unfolder_RX_Data[0] = CanbRegs.CAN_IF2DATA.all & 0xFFFF; // for f_grid
        Unfolder_RX_Data[1] = (CanbRegs.CAN_IF2DATA.all & 0xFFFF0000) >> 16; // for Vph_m

        break;

    case DCDC_MB_ID_1:
    case DCDC_MB_ID_2:
    case DCDC_MB_ID_3:
    case DCDC_MB_ID_4:
    case DCDC_MB_ID_5:
    case DCDC_MB_ID_6:
    case DCDC_MB_ID_7:
    case DCDC_MB_ID_8:
    case DCDC_MB_ID_9:
    case DCDC_MB_ID_10:
    case DCDC_MB_ID_11:
    case DCDC_MB_ID_12:
    case DCDC_MB_ID_13:
    case DCDC_MB_ID_14:
    case DCDC_MB_ID_15:
    case DCDC_MB_ID_16:
    case DCDC_MB_ID_17:
    case DCDC_MB_ID_18:
    case DCDC_MB_ID_19:
    case DCDC_MB_ID_20:

        module = (msgID & 0xFF);

        if((module == (THIS_DCDC_ID-1))||
          ((module == N_MODULES) && (THIS_DCDC_ID == 1))){
            Flags.bit.send_messageB = 1;
            Fault.Counter.CANB_timer = 0;
        }

        Output_RX_Data[module - 1] = CanbRegs.CAN_IF2DATA.all & 0xFFFF; // for current
        Output_RX_Data[module + 19] = (CanbRegs.CAN_IF2DATA.all & 0xFFFF0000) >> 16; // for voltage

        // First 20 bits of next 32 bit word 1 bit/module determine whether each module is switching or closed
        temp_module_mask = (0x000FFFFF & Matlab_RX_Data[1]);


//        if((module==N_MODULES)||((THIS_DCDC_ID==N_MODULES)&&(module==(N_MODULES-1U)))){
//            Vo_tot = 0;
//            for(i=0;i<S_SERIES;++i){
//                Vo_mod_avg = 0;
//                for(j=0;j<M_PARALLEL;++j){
//                    mod_index = j*M_PARALLEL + i;
//                    Vo_mod_avg += VO_K*(Output_RX_Data[mod_index + 20]-VO_0);
//                }
//                Vo_tot += Vo_mod_avg*INV_M_PARALLEL;
//            }
//            Vo_mod_avg = Vo_tot*INV_N_SERIES;
//            Vout_Reg.Vout_ref = Vo_mod_avg;
//        }


        if((module==N_MODULES)||((THIS_DCDC_ID==N_MODULES)&&(module==(N_MODULES-1U)))){
            Vo_tot = 0;
            n_tot = 0;
            for(i=0; i < N_MODULES; ++ i){
                if(!(0x1 & (temp_module_mask>>i))){ // Module i+1 is not closed
                    ++n_tot;
                    Vo_tot += VO_K*(Output_RX_Data[i + 20]-VO_0);
                }
            }
            Vo_mod_avg = Vo_tot/n_tot;
#if VOUT_REF_AVG_CALC
            Vout_Reg.Vout_ref = Vo_mod_avg;
#endif
        }

        break;

    default: // mailbox not recognized throw an error?

        break;
    }

    CAN_IF1CMD_SHADOW.all = CanbRegs.CAN_IF2CMD.all; // Populate Shadow Variable
    CAN_IF1CMD_SHADOW.bit.TXRQST = 1; // Clear New Data Flag
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = mailbox; // Transfer the message object to the message object IF register.
    CanbRegs.CAN_IF2CMD.all = CAN_IF1CMD_SHADOW.all;

}

// **********************  CAN RX Message handler for CANA  ****************************** //
void CANA_Get_Message(Uint32 mailbox)
{
    union CAN_IF1CMD_REG CAN_IF1CMD_SHADOW;
    //Uint16 module;
    Uint32 temp_module_mask;
    Uint16 msgID;
    Uint16 previous_CAN_state = Flags.bit.en_CAN;


    // Set the Message Data A, Data B, and control values to be read on request for data from the message object.

    CAN_IF1CMD_SHADOW.all = 0;
    CAN_IF1CMD_SHADOW.bit.Control = 1;
    CAN_IF1CMD_SHADOW.bit.Arb = 1;
    CAN_IF1CMD_SHADOW.bit.Mask = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_A = 1;
    CAN_IF1CMD_SHADOW.bit.DATA_B = 1;

    CAN_IF1CMD_SHADOW.bit.MSG_NUM = mailbox; // Transfer the message object to the message object IF register.

    while(CanaRegs.CAN_IF2CMD.bit.Busy){} // Wait for busy bit to clear.

    CanaRegs.CAN_IF2CMD.all = CAN_IF1CMD_SHADOW.all;

    while(CanaRegs.CAN_IF2CMD.bit.Busy){} // Wait for busy bit to clear.

    // Check for lost messages and initiate protection
    if(CanaRegs.CAN_IF2MCTL.bit.MsgLst){
#if CAN_COMM_PROT
        Stop_ePWM();    // Stop Modulation
        SET_INT_SW_FAULT();
        Fault.Fault.bit.CANA = 0;
#endif
        Fault.CANA_Protection.bit.CAN_MSG_LST = 0;
        Fault.CANA_Protection.bit.MB_ID_LST = mailbox;
        if(Fault.count<FAULT_LOG_SIZE){
            Fault.Log[Fault.count].fault_code = 36;
            Fault.Log[Fault.count].int1 = mailbox;
            Fault.Log[Fault.count].int2 = 0;
            Fault.Log[Fault.count].time = Fault.time;
            ++Fault.count;
        }
    }

    msgID = 0x7FF&(CanaRegs.CAN_IF2ARB.all >> CAN_MSG_ID_SHIFT);

    switch(mailbox)
    {
    case MATLAB_RX_MB_ID:
        Matlab_RX_Data[0] = CanaRegs.CAN_IF2DATA.all;
        Matlab_RX_Data[1] = CanaRegs.CAN_IF2DATB.all;

        Flags.all |= 0xFFF & Matlab_RX_Data[0];      // First 12 bits of Matlab Data directly into Flags Reg
        Flags.all &= 0xFFFFF000 | Matlab_RX_Data[0]; // First 12 bits of Matlab Data directly into Flags Reg

        // Next 20 bits 1 bit/module determine whether each module is switching or opened
        temp_module_mask = (0xFFFFF000 & Matlab_RX_Data[0]) >> 12U;
        Flags.bit.secondary_open = 0x1 & (temp_module_mask>>(THIS_DCDC_ID-1));

        // First 16 bits of next 32 bit word 1 bit/module determine whether each module is switching or closed
        temp_module_mask = (0x0000FFFF & Matlab_RX_Data[1]);
        Flags.bit.secondary_closed = 0x1 & (temp_module_mask>>(THIS_DCDC_ID-1));

        // Next 16 bits of next 32 bit word 1 bit/module determine whether each module is doing negative power
        temp_module_mask = (0xFFFF0000 & Matlab_RX_Data[1]) >> 16U;
        Flags.bit.negative_power = 0x1 & (temp_module_mask>>(THIS_DCDC_ID-1));

        if (Flags.bit.negative_power)
        {
            V1Q_VPH_M_SF_temp = -0.73656;
            Iout_Reg.Iout_ref_gain = -0.1683;
        }
        else
        {
            V1Q_VPH_M_SF_temp = 1.2276;
            Iout_Reg.Iout_ref_gain = 0.2805;
        }

        if(Flags.bit.en_CAN && (!previous_CAN_state)){
            Fault.Counter.CANA_timer = 0;
            if(THIS_DCDC_ID == 1){
                Flags.bit.send_messageB = 1;
                Fault.Counter.CANB_timer = 0;
            }
        }

#if CAN_COMM_PROT
        if(Flags.bit.secondary_open & Flags.bit.secondary_closed){
            // throw an error bc module should never be initialized this way
            Stop_ePWM();    // Stop Modulation
            SET_INT_SW_FAULT();
            Fault.CANA_Protection.bit.CAN_INIT = 0;
            Fault.Fault.bit.CANA = 0;
            Flags.bit.reset_faults = 0; // if reset faults was set make sure to reset it if theres a fault here
        }
#endif

        break;

    case FAULT_RX_MB_ID:
        // Do fault stuff here if needed

//        module = (msgID & 0xFF);

        Fault_RX_Data[0] = CanaRegs.CAN_IF2DATA.all;
        Fault_RX_Data[1] = CanaRegs.CAN_IF2DATB.all;

        break;

    case UNFOLDER_MB_ID:

        Unfolder_RX_Data[0] = CanbRegs.CAN_IF2DATA.all & 0xFFFF; // for f_grid
        Unfolder_RX_Data[1] = (CanbRegs.CAN_IF2DATA.all & 0xFFFF0000) >> 16; // for Vph_m

        break;

    case DCDC_MB_ID_1:
    case DCDC_MB_ID_2:
    case DCDC_MB_ID_3:
    case DCDC_MB_ID_4:
    case DCDC_MB_ID_5:
    case DCDC_MB_ID_6:
    case DCDC_MB_ID_7:
    case DCDC_MB_ID_8:
    case DCDC_MB_ID_9:
    case DCDC_MB_ID_10:
    case DCDC_MB_ID_11:
    case DCDC_MB_ID_12:
    case DCDC_MB_ID_13:
    case DCDC_MB_ID_14:
    case DCDC_MB_ID_15:
    case DCDC_MB_ID_16:
    case DCDC_MB_ID_17:
    case DCDC_MB_ID_18:
    case DCDC_MB_ID_19:
    case DCDC_MB_ID_20:

//        module = (msgID & 0xFF);

        break;

    default: // mailbox not recognized throw an error?

        break;
    }

    CAN_IF1CMD_SHADOW.all = CanaRegs.CAN_IF2CMD.all; // Populate Shadow Variable
    CAN_IF1CMD_SHADOW.bit.TXRQST = 1; // Clear New Data Flag
    CAN_IF1CMD_SHADOW.bit.MSG_NUM = mailbox; // Transfer the message object to the message object IF register.
    CanaRegs.CAN_IF2CMD.all = CAN_IF1CMD_SHADOW.all;

}
