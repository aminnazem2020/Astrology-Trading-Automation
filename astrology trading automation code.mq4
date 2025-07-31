//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
input string CSVFileName = "moon_saturn_squares.csv";  // CSV file name in MQL4 Files folder
input double Lots = 0.1;                                // Lot size for orders
input double StopLoss = 100;                            // Stop Loss in points
input double TakeProfit = 200;                          // Take Profit in points
input double Slippage = 3;                              // Max slippage
input int MagicNumber = 12345;                          // Unique magic number for orders

datetime lastProcessedTime = 0;                         // To track last processed event

// Convert CSV time string (ISO format) to datetime in UTC
datetime ParseCSVDateTime(string datetimeStr)
{
   // Expected format: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD HH:MM"
   string datePart, timePart;
   StringSplit(datetimeStr, ' ', datePart, timePart);
   string yearStr, monthStr, dayStr;
   string hourStr, minStr, secStr;
   StringSplit(datePart, '-', yearStr, monthStr, dayStr);
   StringSplit(timePart, ':', hourStr, minStr, secStr);
   if(secStr == "")
      secStr = "0";

   datetime dt = StructToTime(yearStr, monthStr, dayStr, hourStr, minStr, secStr);
   return dt;
}

// Helper to convert strings to datetime struct and then datetime value
datetime StructToTime(string y, string m, string d, string h, string min, string s)
{
   MqlDateTime dt;
   dt.year = (int)StringToInteger(y);
   dt.mon = (int)StringToInteger(m);
   dt.day = (int)StringToInteger(d);
   dt.hour = (int)StringToInteger(h);
   dt.min = (int)StringToInteger(min);
   dt.sec = (int)StringToInteger(s);
   return StructToTime(dt);
}

// Check if a position with the MagicNumber and Symbol already exists
bool PositionExists(string symbol, int magic, int cmd)
{
   for(int i=0; i<OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == symbol && OrderMagicNumber() == magic && OrderType() == cmd)
            return true;
      }
   }
   return false;
}

// Open a trade position
bool OpenPosition(int cmd)
{
   // Prevent opening duplicate positions
   if(PositionExists(Symbol(), MagicNumber, cmd))
   {
      Print("Position already exists, skipping new order.");
      return false;
   }

   double price = 0;
   if(cmd == OP_BUY)
      price = Ask;
   else if(cmd == OP_SELL)
      price = Bid;
   else
      return false;

   double sl = 0, tp = 0;

   // Calculate SL and TP prices depending on Buy or Sell
   if(cmd == OP_BUY)
   {
      sl = price - StopLoss * Point;
      tp = price + TakeProfit * Point;
   }
   else if(cmd == OP_SELL)
   {
      sl = price + StopLoss * Point;
      tp = price - TakeProfit * Point;
   }

   int ticket = OrderSend(Symbol(), cmd, Lots, price, Slippage, sl, tp, "Moon-Saturn EA", MagicNumber, 0, clrBlue);

   if(ticket < 0)
   {
      Print("OrderSend failed with error #", GetLastError());
      return false;
   }
   else
   {
      Print("Order opened successfully, ticket #", ticket);
      return true;
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastCheck = 0;

   if(TimeCurrent() - lastCheck < 60) // check once per minute
      return;

   lastCheck = TimeCurrent();

   // Do not trade on weekends
   MqlDateTime nowStruct;
   TimeToStruct(TimeCurrent(), nowStruct);
   if(nowStruct.day_of_week == 0 || nowStruct.day_of_week == 6) // Sunday or Saturday
   {
      Print("Weekend, no trading.");
      return;
   }

   string filepath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL4\\Files\\" + CSVFileName;
   int fileHandle = FileOpen(filepath, FILE_READ|FILE_CSV|FILE_ANSI);
   if(fileHandle == INVALID_HANDLE)
   {
      Print("Failed to open CSV file: ", filepath);
      return;
   }

   // Skip header line
   FileReadString(fileHandle);

   while(!FileIsEnding(fileHandle))
   {
      string dateTimeStr = FileReadString(fileHandle);
      string moonLonStr = FileReadString(fileHandle);
      string moonLatStr = FileReadString(fileHandle);
      string satLonStr = FileReadString(fileHandle);
      string satLatStr = FileReadString(fileHandle);
      string angleDiffStr = FileReadString(fileHandle);
      string distSqStr = FileReadString(fileHandle);

      datetime eventTime = ParseCSVDateTime(dateTimeStr);

      // Only consider future events, and avoid repeats
      if(eventTime <= lastProcessedTime || eventTime > TimeCurrent())
         continue;

      // Convert event time from UTC to local server time
      datetime eventTimeLocal = eventTime + (TimeLocal() - TimeGMT());

      // Check if event time is now or in past few minutes
      if(TimeCurrent() >= eventTimeLocal && TimeCurrent() <= eventTimeLocal + 60*5) // 5 minutes window
      {
         // Example: open SELL order on Moon-Saturn square event
         if(!PositionExists(Symbol(), MagicNumber, OP_SELL))
         {
            if(OpenPosition(OP_SELL))
            {
               lastProcessedTime = eventTime; // mark event as processed
               Print("Opened SELL position for Moon-Saturn square event at ", TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS));
            }
         }
      }
   }
   FileClose(fileHandle);
}
//+------------------------------------------------------------------+

   
  }
//+------------------------------------------------------------------+
