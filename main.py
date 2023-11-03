import string
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timedelta, date
from database import MssqlHandler
from agent import AgentReply

READ_SQL_CXN = MssqlHandler("r")
agent_reply = AgentReply()

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
        #  total sugegstions ai
        READ_SQL_CXN.execute(f""" --- Total Tickets created in that given Duration
        Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
        ,Count(Distinct CD.CaseID) as TotalTickets
        From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
        Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
        AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
        AND CD.BrandID = 6954
        Group By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))
        Order By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))""")
        df = READ_SQL_CXN.fetch_df()
        return df


    def data1(self, start_date, end_date):
        # flr and suggested tickets

        READ_SQL_CXN.execute(f"""SET NOCOUNT ON; Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
        ,CD.CaseID,FirstlevelTAT_Datetime,FirstLevelTAT_Seconds
        ,CD.CaseStatus
        From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
        Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
        AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}'
        AND CD.BrandID = 6954
        AND ISNULL(CD.IsCaseDeleted,0)=0 
        AND CD.CaseID in (Select Distinct ticket_id from 
        TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) 
        where CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id)""")
        df = READ_SQL_CXN.fetch_df()
        return df

    def data2(self,start_date, end_date):
        # avg tat
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
        #  aht
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
        #  total suggested tickets, no o suggestion , caution
        READ_SQL_CXN.execute(f""" Select CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) as Date
         ,Count(Distinct CD.CaseID) as TotalAisuggestedTickets
         ,Count(Distinct ai.ID) as NoofSuggestions
         ,Count(Distinct Case when  ISNULL(ai.Caution,0)=1 Then  ai.ID ELSE NULL END) as out_of_knowledge_base
         ,Count(Distinct Case when  ISNULL(ai.Caution,0)=0 Then  ai.ID ELSE NULL END) as from_knowledge_base
         From TataDigitalDb.dbo.MstCasedetails CD With(Nolock)
         Inner JOIN TataDigitalDb.Dbo.MstAIsuggestedTokendetails ai With(Nolock) on CD.BrandID=ai.BrandID and CD.CaseID = ai.ticket_id
         LEFT JOIN TataDigitalDb.Dbo.mstActualTicketTATdetails MATT WITH(NOLOCK) on MATT.CaseID =CD.CaseID
         Where   CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) >= '{start_date}'
         AND CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate)) <= '{end_date}' 
         AND CD.BrandID = 6954
         Group By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))
         Order By CONVERT(Date,Dateadd(Minute,330,CD.InsertedDate))
                            """)
        df = READ_SQL_CXN.fetch_df()
        return df

    def load_css(self):
        with open("dash.css", "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    def boxs(self, row_data, color1, color2,):
        # Define CSS styles for the boxes with text starting from the left
        box_style1 = (
            "border: 1px solid #ccc; "
            f"border-left: 5px solid {color1}; "  # Replace 'your-color' with the desired color
            "border-radius: 5px; "
            "box-shadow: 4px 4px 8px 0px rgba(0, 0, 0, 0.2); "
            "padding: 5px 10px; "
            "margin: 10px; "
        )
        box_style2= (
            "border: 1px solid #ccc; "
            f"border-left: 5px solid {color2}; "  # Replace 'your-color' with the desired color
            "border-radius: 5px; "
            "box-shadow: 4px 4px 8px 0px rgba(0, 0, 0, 0.2); "
            "padding: 5px 10px; "
            "margin: 10px; "
        )

        title_style = (
            "margin: 0 0 5px 0;"  # Adjust the margin to reduce space between title and value
        )

        value_style = (
            "margin: 0;"  # Remove margin to reduce space between title and value
        )
        self.load_css()

        col = st.columns(6)
        for i in range(6):
            if i <3:
                with col[i]:
                    st.markdown(
                        f'<div style="{box_style1}">'
                        f'<p style="{title_style}">'
                        f'{row_data[i][0]} <span title="{row_data[i][1]}">ℹ️</span>'
                        '</p>'
                        f'<h2 style="{value_style}">{row_data[i][2]}</h2>'
                        '</div>',
                        unsafe_allow_html=True
                    )
            else:
                with col[i]:
                    st.markdown(
                        f'<div style="{box_style2}">'
                        f'<p style="{title_style}">'
                        f'{row_data[i][0]} <span title="{row_data[i][1]}">ℹ️</span>'
                        '</p>'
                        f'<h2 style="{value_style}">{row_data[i][2]}</h2>'
                        '</div>',
                        unsafe_allow_html=True
                    )


    def output(self):

        st.set_page_config(layout="wide")  # Set the layout to wide
        # Define the custom CSS to change the background color
        st.markdown(
            """
            <style>
            .reportview-container {
                background-color: #EEF3FF; /* Specify the background color you want */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.title("Tata Digital AI Impact Dashboard")

        # Calculate yesterday's date
        yesterday1 = (datetime.now() - timedelta(days=10)).date()
        yesterday2 = (datetime.now() - timedelta(days=1)).date()

        # Move date selection widgets to the right sidebar
        # with st.sidebar:
        left_column1, right_column2 = st.columns(2)

        # Duplicate the entire dashboard code in both columns
        with left_column1:
            start_date = st.date_input("Select Start Date", value=yesterday1)
        with right_column2:
            end_date = st.date_input("Select End Date", value=yesterday2)

        # Check if the selected date is greater than yesterday
        if end_date > yesterday2 or start_date > yesterday2:
            st.write("No data available to show. Please select a date before today.")
        else:
            with st.spinner("Fetching Data.. "):
                total_ticket_df = self.data(start_date, end_date)
                ai_ticket_df = self.data4(start_date, end_date)
                ticket_df = pd.merge(total_ticket_df, ai_ticket_df, on='Date')
                ticket_df["% Suggested vs Total Ticket"] = ticket_df.apply(lambda row: f'{(row["TotalAisuggestedTickets"] / row["TotalTickets"]) * 100:.1f}', axis=1)
                ticket_df["% From Knowledge Base"] = ticket_df.apply(lambda row: f'{(row["from_knowledge_base"] / row["NoofSuggestions"]) * 100:.1f}', axis=1)

                ticket_df['Date'] = pd.to_datetime(ticket_df['Date'])

                # Split the screen into two equal-width columns
                left_column, right_column = st.columns(2)

                # Duplicate the entire dashboard code in both columns
                with left_column:
                    # Create a chart for Value1
                    c1 = alt.Chart(ticket_df).mark_line().encode(
                        x='Date:T',
                        y='% Suggested vs Total Ticket:Q',
                    ).properties(
                        width=400,
                        height=400
                    )
                    # Display the charts on the left side
                    st.write("## Coverage of Suggestions over Total Tickets ")
                    st.altair_chart(c1, use_container_width=True)
                with right_column:
                    # Create a chart for Value2
                    c2 = alt.Chart(ticket_df).mark_line().encode(
                        x='Date:T',
                        y='% From Knowledge Base:Q',
                    ).properties(
                        width=400,
                        height=400
                    )

                    st.write("## Coverage of Suggestions From knowledge Base ")
                    st.altair_chart(c2, use_container_width=True)

                ssre_df = agent_reply.ssre(start_date, end_date)
                ssre_count = ssre_df["SSREReplyCount"].sum()
                brand_reply_count = agent_reply.agent(start_date, end_date)
                agent_reply_count = brand_reply_count - ssre_count
                total_ticket = ticket_df["TotalTickets"].sum()
                suggested_ticket = ticket_df["TotalAisuggestedTickets"].sum()
                per_suggested_total_ticket = round((suggested_ticket/total_ticket)*100, 1)
                total_suggestion = ticket_df["NoofSuggestions"].sum()
                out_side_kb = ticket_df["out_of_knowledge_base"].sum()
                from_kb = ticket_df["from_knowledge_base"].sum()

                st.write("Key Performance Indicators")
                row1_data = [
                    ("Total Tickets", "The total number of tickets Created in the selected duration", total_ticket),
                    ("Total Suggested Tickets", "The count of unique tickets with suggestions made", suggested_ticket),
                    ("Suggestions Vs Ticket %", " % of Suggested tickets vs Total Tickets",f"{per_suggested_total_ticket} %"),
                    ("Total Brand Reply", "The number of replies made by the brand.", brand_reply_count),
                    ("SSRE Count", "Count of replies from the Automation feature, SSRE", ssre_count),
                    ("Total Agent Reply", "Total Count of replies sent by any agent", agent_reply_count)
                ]
                self.boxs(row1_data, "#337AFF", "#FF9C33")

                df1 = self.data1(start_date, end_date)
                df2 = self.data2(start_date, end_date)
                df3 = self.data3(start_date, end_date)

                df1_without_outlier = self.operation(df1, 'FirstlevelTAT_Datetime', 'FirstLevelTAT_Seconds')
                df2_without_outlier = self.operation(df2, 'TotalTAT_Datetime', 'TotalTAT_Seconds')
                df3_without_outlier = self.operation(df3, 'WorkStartTime', 'TotalTATTime')

                flr_minutes, flr_seconds = divmod(df1_without_outlier['FirstLevelTAT_Seconds'].mean(), 60)
                tat_minutes, tat_seconds = divmod(df2_without_outlier['TotalTAT_Seconds'].mean(), 60)
                aht_minutes, aht_seconds = divmod(df3_without_outlier['TotalTATTime'].mean(), 60)

                # Data for the boxes (titles and numerical values)
                row4_data = [
                    ("Total Suggestions", "total number of response suggestions offered", total_suggestion),
                    ("From Knowledge Base", "total number of suggestion given from Knowledge Base",
                     f"{from_kb}   ({round((from_kb / total_suggestion) * 100, 1)} %)"),
                    ("Outside Knowledge Base", "total number of suggestion given out of Knowledge Base",
                     f"{out_side_kb}   ({round((out_side_kb / total_suggestion) * 100, 1)} %)"),
                    ("FLR", "(when suggestion were given)", f"{round(flr_minutes)} min {round(flr_seconds)} sec"),
                    ("Ticket Closure TAT", "(when suggestion were given)",
                     f"{round(tat_minutes)} min {round(tat_seconds)} sec"),
                    ("Avg Agent handling time", "(when suggestion were given)",
                     f"{round(aht_minutes)} min {round(aht_seconds)} sec")
                ]
                self.boxs(row4_data, "#145A32", "#9C33FF")



if __name__ == '__main__':
    controller = DashBoard()
    controller.output()
    # uvicorn.run("main:app", host="0.0.0.0", port=APP_MAIN_PORT, log_level="info", reload=True)