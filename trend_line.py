class DashBoard:
    def __init__(self):
        self.count = 0

    def operation(self, df, column1, column2):
        start_time = pd.to_datetime('10:00:00').time()
        end_time = pd.to_datetime('23:30:00').time()

        # Create a mask to filter rows within the time range
        mask = (df[column1].dt.time >= start_time) & (df[column1].dt.time <= end_time)

        # Use the mask to filter the DataFrame
        filtered_df = df[mask]
        filtered_df = filtered_df.dropna(subset=[column2])

        # Calculate Q1 and Q3 for the specific column
        q1 = filtered_df[column2].quantile(0.25)
        q3 = filtered_df[column2].quantile(0.75)

        # Calculate IQR for the specific column
        iqr = q3 - q1

        # Define lower and upper bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Remove outliers from the DataFrame
        df_no_outliers = filtered_df[(filtered_df[column2] >= lower_bound) & (
                    filtered_df[column2] <= upper_bound)]

        return df_no_outliers


    def data(self, start_date, end_date):
        READ_SQL_CXN.execute(f"""SET NOCOUNT ON;Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,CD.CaseID,ai.caution
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
         Inner JOIN TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) on CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id
         Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) = '{start_date}'
             AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
             AND CD.BrandID = 6954
         AND ISNULL(CD.IsCaseDeleted,0)=0""")
        df = READ_SQL_CXN.fetch_df()
        return df


    def data1(self, start_date, end_date):
        READ_SQL_CXN.execute(f"""SET NOCOUNT ON; Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,CD.CaseID,FirstlevelTAT_Datetime,FirstLevelTAT_Seconds
          ,CD.CaseStatus
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
         Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) = '{start_date}'
             AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
             AND CD.BrandID = 6954
         AND ISNULL(CD.IsCaseDeleted,0)=0 
         AND CD.CaseID in (Select Distinct ticket_id from 
         TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) 
         where CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id)""")
        df = READ_SQL_CXN.fetch_df()
        return df

    def data2(self,start_date, end_date):

        READ_SQL_CXN.execute(f"""SET NOCOUNT ON;Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,CaseID,TotalTAT_Datetime,TotalTAT_Seconds
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
         Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
         AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
         AND CD.BrandID = 6954
         AND CD.CaseStatus=3
              AND CD.CaseID in (Select Distinct ticket_id from 
         TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) 
         where CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id)
        """)
        df = READ_SQL_CXN.fetch_df()

        return df

    def data3(self,start_date, end_date):
        READ_SQL_CXN.execute(f"""SET NOCOUNT ON;
             Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,CD.CaseID,WorkStartTime,WorkEndTime,WorkingTATTime,TotalTATTime
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
         Inner JOIN TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) on CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id
         LEFT JOIN TataDigitalDb.Dbo.mstActualTicketTATdetails MATT WITH(NOLOCK) on MATT.CaseID =CD.CaseID
         Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
             AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}' 
             AND CD.BrandID = 6954
                    """)
        df = READ_SQL_CXN.fetch_df()
        return df
    def data4(self,start_date, end_date):
        READ_SQL_CXN.execute(f"""SET NOCOUNT ON;
             Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,Count(Distinct CD.CaseID) as TotalTickets
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
          Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
             AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
             AND CD.BrandID = 6954
         Group By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))
         Order By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))
                            """)
        df = READ_SQL_CXN.fetch_df()
        return df['TotalTickets'][0]

    def result(self, start_date, end_date):