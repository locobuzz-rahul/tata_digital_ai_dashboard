import datetime
import string
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from nltk.translate.bleu_score import sentence_bleu
from database import MssqlHandler
# from tools.gchat_logging import send_to_g_chat
# from sheet_link import create_editable_sheet

model = SentenceTransformer('all-MiniLM-L6-v2')
READ_SQL_CXN = MssqlHandler("r")


class DailyAccuracy:
    def __init__(self):
        self.count = 0

    def operations(self, df):
        # Drop duplicates
        df = df.drop_duplicates()
        # Drop NA from AgentReply and ResponseGenie
        df = df.dropna(subset=['AgentReply'])
        df = df.dropna(subset=['ResponseGenie'])

        # Check if there is a mode for 'AgentReply'
        if not df['AgentReply'].empty:
            common_ssre_reply = df['AgentReply'].mode()[0]
            # Remove rows containing the common "ssre reply"
            df = df[df['AgentReply'] != common_ssre_reply]

        # Drop NA from AgentReply and ResponseGenie
        df = df.dropna(subset=['AgentReply'])
        df = df.dropna(subset=['ResponseGenie'])

        # Remove Twitter handles and hashtags
        df['ResponseGenie'] = df['ResponseGenie'].str.replace(r'@\w+', '', regex=True)
        df['AgentReply'] = df['AgentReply'].str.replace(r'@\w+', '', regex=True)
        df['ResponseGenie'] = df['ResponseGenie'].str.replace(r'#\w+', '', regex=True)
        df['AgentReply'] = df['AgentReply'].str.replace(r'#\w+', '', regex=True)

        # Remove punctuation
        df['ResponseGenie'] = df['ResponseGenie'].str.replace(f'[{string.punctuation}]', '', regex=True)
        df['AgentReply'] = df['AgentReply'].str.replace(f'[{string.punctuation}]', '', regex=True)

        return df

    def calculate_sentence_similarity(self, sentence1, sentence2):
        # Encode the sentences into embeddings
        embedding1 = model.encode(sentence1, convert_to_tensor=True)
        embedding2 = model.encode(sentence2, convert_to_tensor=True)
        # Calculate cosine similarity
        cosine_similarity = util.pytorch_cos_sim(embedding1, embedding2)
        return cosine_similarity.item()

    def get_tag_info(self, tag_id, category_name):
        try:
            READ_SQL_CXN.execute(f"""
               SELECT ExistingTagID, channeltype, Brandid, Categoryid, authorid, Channelgroupid
               FROM {category_name}.dbo.tag_{category_name} WITH (NOLOCK)
               WHERE tagid = {tag_id};
               """)
            df_ = READ_SQL_CXN.fetch_df()
            if not df_.empty:
                return df_.iloc[0]
        except:
            pass
        return [None, None, None, None, None, None]

    def data(self, category_name, brand_name, brandid):
        READ_SQL_CXN.execute(f"""
                SELECT DATEADD(MINUTE, 330, InsertedDate) AS date,Response_Text as ResponseGenie, *
                FROM {category_name}.dbo.mstAISuggestedTokenDetails with (NOlock)
                WHERE CONVERT(DATE, DATEADD(MINUTE, 330, InsertedDate)) = '{self.previous_day}'
                and Brandid={brandid}
                ORDER BY date DESC;
                """
                             )

        df = READ_SQL_CXN.fetch_df()

        tag_info_columns = ["ExistingTagID", "channeltype", "Brandid", "Categoryid", "authorid", "Channelgroupid"]
        df[tag_info_columns] = df["TagID"].apply(lambda x: pd.Series(self.get_tag_info(x, category_name)))

        df["AgentReply"] = ""

        for i in df[(df["ai_feature_type"] == 2)].index:
            try:
                READ_SQL_CXN.execute(f"""EXEC LB3_GetUserCommunicationHistory_V51
                        @CategoryName = '{category_name}',
                        @BrandName = '{brand_name}',
                        @EndDate = '{self.current_date} 18:29:59',
                        @AuthorID = '{df["authorid"][i]}',
                        @ChannelGroupID = {int(df["Channelgroupid"][i])},
                        @TicketID = {int(df["ExistingTagID"][i])},
                        @From = 1,
                        @To = 50,
                        @IsActionableData = 0,
                        @CurrentUserID = NULL;""")
                # print(ticket_query)

                df_ = READ_SQL_CXN.fetch_df()
                df_sorted = df_.sort_values(by='CreatedDate', ascending=False)
                df_sorted = df_sorted.reset_index(drop=True)
                # Added assignment to the line below
                index = df_sorted[df_sorted["TagID"] == df["TagID"][i]].index[0] - 1
                df.loc[i, "AgentReply"] = df_sorted["Description"][index]
            except:
                df.loc[i, "AgentReply"] = None

        for i in df[(df["ai_feature_type"] == 0)].index:
            try:
                READ_SQL_CXN.execute(f"""EXEC LB3_GetUserCommunicationHistory_V51
                        @CategoryName = '{category_name}',
                        @BrandName = '{brand_name}',
                        @EndDate = '{self.current_date} 18:29:59',
                        @AuthorID = '{df["authorid"][i]}',
                        @ChannelGroupID = {int(df["Channelgroupid"][i])},
                        @TicketID = {int(df["ExistingTagID"][i])},
                        @From = 1,
                        @To = 50,
                        @IsActionableData = 0,
                        @CurrentUserID = NULL;""")
                # print(ticket_query)

                df_ = READ_SQL_CXN.fetch_df()
                df_sorted = df_.sort_values(by='CreatedDate', ascending=False)
                df_sorted = df_sorted.reset_index(drop=True)
                # Added assignment to the line below
                index = df_sorted[df_sorted["TagID"] == df["TagID"][i]].index[0]
                df.loc[i, "AgentReply"] = df_sorted["Description"][index]
            except:
                df.loc[i, "AgentReply"] = None
        return df


    def alert_formatting(self):
        try:
            # Initialize an empty DataFrame
            final = pd.DataFrame()

            # Load data from your source
            res1 = self.data("TataDigitalDb", "TataDigital", 6954)
            res1['Index'] = range(1, len(res1) + 1)
            res = self.operations(res1)
            responses = len(res)

            if responses > 0:
                score, in_kb = [], []

                for index, row in res.iterrows():
                    calculated_score = self.calculate_sentence_similarity(str(row["ResponseGenie"]),
                                                                          str(row["AgentReply"]))
                    score.append(calculated_score)

                    if not row["caution"]:
                        in_kb.append("Yes")
                    else:
                        in_kb.append("No")

                    res["Score"] = score
                    res["In KB"] = in_kb
                    # Filter rows in res1 to match the ones in res
                    res1 = res1[res1['Index'].isin(res['Index'])]

                    # Create the 'final' DataFrame
                    final["Mention Content"] = res1["Source_Text"]
                    final["AI Suggested Response"] = res1["ResponseGenie"]
                    final["Agent Response"] = res1["ResponseGenie"]
                    final["In KB"] = res["In KB"]
                    final["Score"] = res["Score"]

                    # Sort the final DataFrame
                    final_df = final.sort_values(by='Score', ascending=False)
                return final_df
            else:
                return None

        except Exception as e:
            print(f"Error: {str(e)}")




if __name__ == '__main__':
    controller = DailyAccuracy()
    controller.accuracy_update()