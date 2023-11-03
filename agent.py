import datetime
import string
import pandas as pd
import numpy as np
from database import MssqlHandler

READ_SQL_CXN = MssqlHandler("r")


class AgentReply:
    def __init__(self):
        self.count = 0
        self.current_date = datetime.date.today()

    def ssre(self, start_date, end_date):
        READ_SQL_CXN.execute(f"""Select Convert(Date,DATEADD(Minute,330,CD.InsertedDate)) as Date, SUM(SSREReplyCount) as SSREReplyCount 
        FROM TataDigitalDb.dbo.Mstcasedetails CD WITH(Nolock)
        Inner Join TataDigitalDb.dbo.MstCaseDetails_MetaData MCM WITH(Nolock) on CD.CaseID=MCM.CaseID and CD.BrandID=MCM.BrandID
        where ( MCM.LatestSSREReply is not null AND MCM.LatestSSREReply<>'')
        AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
        AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
        AND CD.BrandID = 6954
        Group by Convert(Date,DATEADD(Minute,330,CD.InsertedDate))
        Order By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))""")

        df = READ_SQL_CXN.fetch_df()
        return df
    def agent(self, start_date, end_date):
        READ_SQL_CXN.execute(f"""SET NOCOUNT ON;
        EXEC LB3_Get_AllmentionCount_V41                 
        @CategoryName = 'TataDigitalDb',                 
        @BrandIDs = '6954',                 
        @StartDate = '{start_date - datetime.timedelta(days=1)} 18:30:00',                 
        @EndDate = '{end_date} 18:29:59',                 
        @StrWhereClause = ' ' 
                """)

        df = READ_SQL_CXN.fetch_df()

        return df.loc[0, "BrandReply"]


if __name__ == '__main__':
    # controller = DailyAccuracy()
    # controller.data()