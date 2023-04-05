import random
import openai
import arxiv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

#API設定
openai.api_key = 'openAIのAPIキー'
line_bot_api = LineBotApi('LINEアクセストークン')
handler = WebhookHandler('LINEチャネルシークレット')
receiver = 'LINEアカウントのID(dev tool サイトから確認)'

#得たい論文のクエリ
query ='ti:%22 bayesian modeling %22'

#ChatGPTを使った論文情報生成関数
def get_summary(result):
    system = """与えられた論文の要点を3点のみでまとめ、以下のフォーマットで日本語で出力してください。```
    タイトルの日本語訳
    ・要点1
    ・要点2
    ・要点3
    ```"""

    text = f"title: {result.title}\nbody: {result.summary}"
    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': text}
                ],
                temperature=0.25,
            )
    summary = response['choices'][0]['message']['content']
    title_en = result.title
    title, *body = summary.split('\n')
    body = '\n'.join(body)
    date_str = result.published.strftime("%Y-%m-%d %H:%M:%S")
    message = f"発行日: {date_str}\n{result.entry_id}\n{title_en}\n{title}\n{body}\n"
    
    return message

   #メッセージ送信関数
def send_message(message):
    try:
        line_bot_api.push_message(receiver, TextSendMessage(text=message))
    except LineBotApiError as e:
        print(f"Error sending message: {e}")


#GCPが動かす関数
def main(event, context):
    #arxiv APIで最新の論文情報を取得する
    search = arxiv.Search(
        query=query,  # 検索クエリ（
        max_results=20,  # 取得する論文数
        sort_by=arxiv.SortCriterion.SubmittedDate,  # 論文を投稿された日付でソートする
        sort_order=arxiv.SortOrder.Descending,  # 新しい論文から順に取得する
        )

    #searchの結果をリストに格納
    result_list = []
    for result in search.results():
        result_list.append(result)

        #ランダムにnum_papersの数だけ選ぶ
    num_papers = 3
    results = random.sample(result_list, k=num_papers)

    #論文情報をLINEに送信
    for i, result in enumerate(results):
        try:
            # LINE に送信するメッセージを組み立てる
            message = "今日の論文です！ " + str(i+1) + "本目\n" + get_summary(result)
            # LINE にメッセージを送信
            send_message(message)
        except LineBotApiError as e:
            print(f"Error sending message: {e}")