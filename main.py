import string
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, date
from database import MssqlHandler

READ_SQL_CXN = MssqlHandler("r")


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
        df = self.data(start_date, end_date)
        df1 = self.data1(start_date, end_date)
        df2 = self.data2(start_date, end_date)
        df3 = self.data3(start_date, end_date)

        total_ticket = self.data4(start_date,end_date)
        suggested_ticket = len(df1)
        per_sug_tic = f'{(suggested_ticket/total_ticket)*100:.1f}'

        total_sugg = len(df)
        true_caution = df['caution'].sum()
        out_of_kb = f'{(true_caution/total_sugg)*100:.1f}'

        df1_without_outlier = self.operation(df1, 'FirstlevelTAT_Datetime','FirstLevelTAT_Seconds')
        df2_without_outlier = self.operation(df2, 'TotalTAT_Datetime', 'TotalTAT_Seconds')
        df3_without_outlier = self.operation(df3, 'WorkStartTime', 'TotalTATTime')

        avg_flr = df1_without_outlier['FirstLevelTAT_Seconds'].mean()
        avg_tat = df2_without_outlier['TotalTAT_Seconds'].mean()
        aht = df3_without_outlier['TotalTATTime'].mean()
        flr_minutes, flr_seconds = divmod(avg_flr, 60)
        tat_minutes, tat_seconds = divmod(avg_tat, 60)
        aht_minutes, aht_seconds = divmod(aht, 60)
        company_flr = 2487
        company_tat = 6186
        company_aht = 24480
        cflr_minutes, cflr_seconds = divmod(2487, 60)
        ctat_minutes, ctat_seconds = divmod(6186, 60)
        caht_minutes, caht_seconds = divmod(24480, 60)

        flr_per = f'{((company_flr-avg_flr)/company_flr)*100:.1f}'
        tat_per = f'{((company_tat-avg_tat)/company_tat)*100:.1f}'
        aht_per = f'{((company_aht-aht)/company_aht)*100:.1f}'

        final_data = {
            'Total Tickets ': total_ticket,
            'Total Suggested Tickets': suggested_ticket,
            '% Suggestions vs Tickets': per_sug_tic,
            'Total Suggestions': total_sugg,
            '% of Suggestion Outside Knowledge Base': out_of_kb,
            'FLR (when suggestion were given)' : f"{round(flr_minutes)} min {round(flr_seconds)} sec",
            'Ticket Closure TAT (when suggestion were given)': f"{round(tat_minutes)} min {round(tat_seconds)} sec",
            'Avg Agent handlng time (when suggestion were given)': f"{round(aht_minutes)} min {round(aht_seconds)} sec",
            'Pre AI stats-FLR': f"{cflr_minutes} min {cflr_seconds} sec",
            'Pre AI stats-TAT': f"{ctat_minutes} min {ctat_seconds} sec",
            'Pre AI stats-AHT': f"{caht_minutes} min {caht_seconds} sec",
            '% difference FLR': flr_per,
            '% difference TAT': tat_per,
            '% difference AHT': aht_per,

        }

        final = pd.DataFrame(final_data, index=[0])

        return final

    def output(self):
        st.title("Tata Digital AI Impact Dashboard")

        # Calculate yesterday's date
        yesterday1 = (datetime.now() - timedelta(days=1)).date()
        yesterday2 = (datetime.now() - timedelta(days=1)).date()

        # Date selection widget with default value set to yesterday's date for start date
        start_date = st.date_input("Select Start Date", value=yesterday1)

        # Date selection widget with default value set to yesterday's date for end date
        end_date = st.date_input("Select End Date", value=yesterday2)
        # Check if the selected date is greater than yesterday
        if end_date > yesterday1 or start_date > yesterday1:
            st.write("No data available to show. Please select a date before today.")
        else:
            with st.spinner("Fetching Data.. "):
                kpi_df = self.result(start_date, end_date)
                # print(type(kpi_df))

                # Create a layout with three rows
                row1 = st.columns(3)
                row2 = st.columns(2)
                row3 = st.columns(3)
                row4 = st.columns(3)
                row5 = st.columns(3)

                # Display KPIs in styled boxes
                box_style = (
                    "background-color: #87CEEB; padding: 10px; margin: 10px; border-radius: 10px; "
                    "box-shadow: 5px 5px 10px #888888;"
                )
                box_style1 = (
                    "background-color: #90EE90; padding: 10px; margin: 10px; border-radius: 10px; "
                    "box-shadow: 5px 5px 10px #888888; width: 200px;"
                )

                box_style2 = (
                    "background-color: #FFFFED; padding: 10px; margin: 10px; border-radius: 10px; "
                    "box-shadow: 5px 5px 10px #888888;"
                )

                # Display KPIs in the first row
                for col in kpi_df.columns[:3]:
                    row1[kpi_df.columns.get_loc(col)].write(
                        f"<div style='{box_style1} text-align:center;'><div style='font-size:18px;'>{col}</div><div style='font-size:24px;'>{kpi_df[col][0]}</div></div>",
                        unsafe_allow_html=True,
                    )

                # Display KPIs in the second row
                for col in kpi_df.columns[3:5]:
                    row2[kpi_df.columns.get_loc(col) - 3].write(
                        f"<div style='{box_style2} text-align:center;'><div style='font-size:18px;'>{col}</div><div style='font-size:24px;'>{kpi_df[col][0]}</div></div>",
                        unsafe_allow_html=True,
                    )

                # Display KPIs in the third row
                for col in kpi_df.columns[5:8]:
                    row3[kpi_df.columns.get_loc(col) - 5].write(
                        f"<div style='{box_style} text-align:center;'><div style='font-size:18px;'>{col}</div><div style='font-size:24px;'>{kpi_df[col][0]}</div></div>",
                        unsafe_allow_html=True,
                    )

                # Display KPIs in the fourth row
                for col in kpi_df.columns[8:11]:
                    row4[kpi_df.columns.get_loc(col) - 8].write(
                        f"<div style='{box_style} text-align:center;'><div style='font-size:18px;'>{col}</div><div style='font-size:24px;'>{kpi_df[col][0]}</div></div>",
                        unsafe_allow_html=True,
                    )

                for col in kpi_df.columns[11:14]:
                    row4[kpi_df.columns.get_loc(col) - 11].write(
                        f"<div style='{box_style} text-align:center;'><div style='font-size:18px;'>{col}</div><div style='font-size:24px;'>{kpi_df[col][0]}</div></div>",
                        unsafe_allow_html=True,
                    )

                # Display an empty row for spacing
                row5[0].empty()

if __name__ == '__main__':
    controller = DashBoard()
    controller.output()
    # uvicorn.run("main:app", host="0.0.0.0", port=APP_MAIN_PORT, log_level="info", reload=True)