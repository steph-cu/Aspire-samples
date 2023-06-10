#ifndef INIT_CAN_H_
#define INIT_CAN_H_

// ******************************************* CAN Constants ********************************************** //
/* CANA Mailboxes */

/* CANA Mailboxes - same as CANB*/
//// TX Mailboxes
//#define     FAULT_TX_MB_ID_A        1 // Send Fault info
//#define     ADC_TX_MB_ID_A          2 // Send ADC info
//
//// RX Mailboxes
//#define     MATLAB_RX_MB_ID_A       5 // Receive Matlab cmd
//#define     FAULT_RX_MB_ID_A        6 // Receive Fault Info
//
///* CANA Message IDs */
//#define     MATLAB_RX_MSG_ID_A      0x100L // CAN message ID to receive messages from MATLAB
//#define     FAULT_TX_MSG_ID_A       (FAULT_CAN_MSG_OFFSET_A+THIS_DCDC_ID) // CAN message ID associated with this DC-DC's Fault message
//#define     FAULT_CAN_MSG_OFFSET_A  0x200L  // Fault transmit CAN message ID to transmit faults
//#define     ADC_MSG_OFFSET_A        0x400L // ADC Calibration messages sent with this offset
//#define     ADC_TX_MSG_ID_A         (ADC_MSG_OFFSET_A+THIS_DCDC_ID) // CAN message ID associated with this ADC Calibration TX message

/* CANB Mailboxes */

// TX Mailboxes
#define     FAULT_TX_MB_ID          1 // Fault transmit message mailbox
#define     OUTPUT_TX_MB_ID         2 // mail box number associated with this DC-DC's TX message
#define     ADC_CAL_TX_MB_ID        3 // MB3 for transmitting ADC Calibration Offset Info

// RX Mailboxes
#define     MATLAB_RX_MB_ID         5 // mailbox number associated to incoming MATLAB messages (highest priority receive MB)
#define     FAULT_RX_MB_ID          6 // Fault receive message mailbox
#define     UNFOLDER_MB_ID          7 // Unfolder mailbox for f_grid and Vph_m
#define     DCDC_CAN_MB_OFFSET      8 // CAN mailboxes for DCDC output information shifted to make room for higher priority messages
#define     DCDC_MB_ID_1            (DCDC_CAN_MB_OFFSET)
#define     DCDC_MB_ID_2            (DCDC_CAN_MB_OFFSET+1)
#define     DCDC_MB_ID_3            (DCDC_CAN_MB_OFFSET+2)
#define     DCDC_MB_ID_4            (DCDC_CAN_MB_OFFSET+3)
#define     DCDC_MB_ID_5            (DCDC_CAN_MB_OFFSET+4)
#define     DCDC_MB_ID_6            (DCDC_CAN_MB_OFFSET+5)
#define     DCDC_MB_ID_7            (DCDC_CAN_MB_OFFSET+6)
#define     DCDC_MB_ID_8            (DCDC_CAN_MB_OFFSET+7)
#define     DCDC_MB_ID_9            (DCDC_CAN_MB_OFFSET+8)
#define     DCDC_MB_ID_10           (DCDC_CAN_MB_OFFSET+9)
#define     DCDC_MB_ID_11           (DCDC_CAN_MB_OFFSET+10)
#define     DCDC_MB_ID_12           (DCDC_CAN_MB_OFFSET+11)
#define     DCDC_MB_ID_13           (DCDC_CAN_MB_OFFSET+12)
#define     DCDC_MB_ID_14           (DCDC_CAN_MB_OFFSET+13)
#define     DCDC_MB_ID_15           (DCDC_CAN_MB_OFFSET+14)
#define     DCDC_MB_ID_16           (DCDC_CAN_MB_OFFSET+15)
#define     DCDC_MB_ID_17           (DCDC_CAN_MB_OFFSET+16)
#define     DCDC_MB_ID_18           (DCDC_CAN_MB_OFFSET+17)
#define     DCDC_MB_ID_19           (DCDC_CAN_MB_OFFSET+18)
#define     DCDC_MB_ID_20           (DCDC_CAN_MB_OFFSET+19)

#define     CANA_RX_MB_START        MATLAB_RX_MB_ID // 5th MB is first one used for receive
#define     CANA_RX_MB_END          DCDC_MB_ID_16 // 26th MB is the last one used for module 20 output info
#define     CANA_RX_MB_MASK         0x007FFFF0

#define     CANB_RX_MB_START        UNFOLDER_MB_ID
#define     CANB_RX_MB_END          DCDC_MB_ID_16
#define     CANB_RX_MB_MASK         0x007FFFC0


/* CANB Message IDs */
// Message Mask the 3 MSB to receive multiple messages in one MB
#define     CAN_MSG_ID_SHIFT        18U // shifts the ID if not using extended
#define     CAN_MSG_ID_MASK         (0x700L<<CAN_MSG_ID_SHIFT) // Look at 3 MSB of 11-bit CAN ID

// Matlab Message ID
#define     MATLAB_RX_MSG_ID        0x100L // CAN message ID to receive messages from MATLAB

// Fault Message ID
#define     FAULT_TX_MSG_ID         (FAULT_CAN_MSG_OFFSET+THIS_DCDC_ID) // CAN message ID associated with this DC-DC's Fault message
#define     FAULT_CAN_MSG_OFFSET    0x200L  // Fault transmit CAN message ID to transmit faults
#define     FAULT_CAN_MSG_SHIFT     (FAULT_TX_MB_ID<<CAN_MSG_ID_SHIFT)

// Output ADC Data Message ID
#define     UNFOLDER_MSG_ID         0x500L // Unfolder messages sent with this offset
#define     DCDC_CAN_MSG_OFFSET     0x400L // DCDC messages sent with this offset
#define     OUTPUT_TX_MSG_ID        (DCDC_CAN_MSG_OFFSET+THIS_DCDC_ID) // CAN message ID associated with this DC-DC's TX message
#define     DCDC_MSG_ID_1           (DCDC_CAN_MSG_OFFSET+1)
#define     DCDC_MSG_ID_2           (DCDC_CAN_MSG_OFFSET+2)
#define     DCDC_MSG_ID_3           (DCDC_CAN_MSG_OFFSET+3)
#define     DCDC_MSG_ID_4           (DCDC_CAN_MSG_OFFSET+4)
#define     DCDC_MSG_ID_5           (DCDC_CAN_MSG_OFFSET+5)
#define     DCDC_MSG_ID_6           (DCDC_CAN_MSG_OFFSET+6)
#define     DCDC_MSG_ID_7           (DCDC_CAN_MSG_OFFSET+7)
#define     DCDC_MSG_ID_8           (DCDC_CAN_MSG_OFFSET+8)
#define     DCDC_MSG_ID_9           (DCDC_CAN_MSG_OFFSET+9)
#define     DCDC_MSG_ID_10          (DCDC_CAN_MSG_OFFSET+10)
#define     DCDC_MSG_ID_11          (DCDC_CAN_MSG_OFFSET+11)
#define     DCDC_MSG_ID_12          (DCDC_CAN_MSG_OFFSET+12)
#define     DCDC_MSG_ID_13          (DCDC_CAN_MSG_OFFSET+13)
#define     DCDC_MSG_ID_14          (DCDC_CAN_MSG_OFFSET+14)
#define     DCDC_MSG_ID_15          (DCDC_CAN_MSG_OFFSET+15)
#define     DCDC_MSG_ID_16          (DCDC_CAN_MSG_OFFSET+16)
#define     DCDC_MSG_ID_17          (DCDC_CAN_MSG_OFFSET+17)
#define     DCDC_MSG_ID_18          (DCDC_CAN_MSG_OFFSET+18)
#define     DCDC_MSG_ID_19          (DCDC_CAN_MSG_OFFSET+19)
#define     DCDC_MSG_ID_20          (DCDC_CAN_MSG_OFFSET+20)


// Misc CAN Variables
#define     CAN_MAX_BIT_DIVISOR     (13)   // The maximum CAN bit timing divisor
#define     CAN_MIN_BIT_DIVISOR     (5)    // The minimum CAN bit timing divisor
#define     CAN_MAX_PRE_DIVISOR     (1024) // The maximum CAN pre-divisor
#define     CAN_MIN_PRE_DIVISOR     (1)    // The minimum CAN pre-divisor
#define     CAN_BTR_BRP_M           (0x3F) // bit rate prescaler mask
#define     CAN_BTR_BRPE_M          (0xF0000) // bit rate extended mask



//#define         CAN_OUTPUT_FREQ         125.0f  // Frequency (Hz) of sending out Vout / Iout Info (20 Modules 250 k baud)
#define         CANA_OUTPUT_FREQ         2.0f  // Frequency (Hz) of sending out Vout / Iout Info
#define         CANA_OUTPUT_TIME         (round(1.0f/CANA_OUTPUT_FREQ/REG_TS))
#define         CANA_TIME_OUT_S          5.0f   // Time (s) of waiting for Tx ok until comm fault
#define         CANA_TIME_OUT            (round(CANA_TIME_OUT_S/REG_TS))


#define         CANB_OUTPUT_FREQ         10.0f  // Frequency (Hz) of sending out Vout / Iout Info
#define         CANB_OUTPUT_TIME         (round(1.0f/CANB_OUTPUT_FREQ/REG_TS))
#define         CANB_TIME_OUT_S          2.0f   // Time (s) of waiting for Tx ok until comm fault
#define         CANB_TIME_OUT            (round(CANB_TIME_OUT_S/REG_TS))



// ******************************************* CAN Functions ********************************************** //

#define EN_CANB()   CanbRegs.CAN_CTL.bit.Init = 0;
#define EN_CANA()   CanaRegs.CAN_CTL.bit.Init = 0;

#define DIS_CANB()   CanbRegs.CAN_CTL.bit.Init = 1;
#define DIS_CANA()   CanaRegs.CAN_CTL.bit.Init = 1;

// Peripheral and GPIO Init
extern void Init_GPIO_CANA(void);
extern void Init_GPIO_CANB(void);

extern void Init_CANA(void);
extern void Init_CANB(void);

extern uint32_t setCANBBitRate(uint32_t sourceClock, uint32_t bitRate);
extern uint32_t setCANABitRate(uint32_t sourceClock, uint32_t bitRate);

// Mailbox Init
extern void setupMessageObjectB(uint32_t objID, uint32_t msg_ID_offset, msgObjType msgType, Uint16 msg_size, bool u_mask);
extern void setupMessageObjectA(uint32_t objID, uint32_t msg_ID_offset, msgObjType msgType, Uint16 msg_size, bool u_mask);
extern void Init_CANB_Mailboxes(void);
extern void Init_CANA_Mailboxes(void);

// TX Messaging A
extern bool CANA_Send_Fault_Message(uint32_t Obj_ID, struct FAULT_LOG fault_tx);// send Fault Log message
extern bool CANA_Send_ADC_Message(uint32_t Obj_ID, int16 ID);
extern bool CANA_Send_Message(uint32_t objID, uint32_t *objData);


// TX Messaging B
extern bool CANB_Send_Output_Message(uint32_t Obj_ID, int16 Iout_ADC, int16 Vout_ADC);// send output data messages
extern bool CANB_Send_Message(uint32_t objID, uint32_t *objData);

// RX Messaging
extern void poll_CAN_Mailboxes(void);
extern void CANA_Get_Message(Uint32 mailbox); // RX Message Handler
extern void CANB_Get_Message(Uint32 mailbox); // RX Message Handler


#endif /* INIT_CAN_H_ */
