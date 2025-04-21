import pandas as pd
import dash
from dash import dcc, html, Output, Input
import plotly.express as px
import matplotlib.pyplot as plt
import dash_bootstrap_components as dbc


#import data
df = pd.read_csv("all_musk_posts.csv")

#clean
df = df[df["isRetweet"].notna()]
df = df[df["isReply"].notna()]
df["createdAt"] = pd.to_datetime(df["createdAt"])
df["year"] = df["createdAt"].dt.year
df["cleanText"] = (
    df["fullText"]
    .fillna("")     
    .str.lower()                           
    .str.replace(r"http\S+", "", regex=True)
    .str.replace(r"[^a-z\s]", "", regex=True) 
)

texts_by_year = df.groupby("year")["cleanText"].apply(lambda x: " ".join(x)).reset_index()
texts_by_year.columns = ["year", "allText"]


#app

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN]) 

app.layout = html.Div([
    html.H1("Elon Tweet Comparison"),

    html.Div([
        html.Div([
            html.Label("Select Year A"),
            dcc.Dropdown(
                id="year-a",
                options=[{"label": str(year), "value": year} for year in sorted(df["year"].unique())],
                value=2020
            )
        ], style={"width": "48%", "display": "inline-block"}),

        html.Div([
            html.Label("Select Year B"),
            dcc.Dropdown(
                id="year-b",
                options=[{"label": str(year), "value": year} for year in sorted(df["year"].unique())],
                value=2022
            )
        ], style={"width": "48%", "display": "inline-block", "float": "right"}),

        html.Div([
            html.Label("Select Month"),
            dcc.Slider(
                id="month-slider",
                min=1,
                max=12,
                value=1,
                marks={i: m for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)},
                step=None
            )
        ], style={"marginTop": "20px"})
    ]),

    html.Div(id="comparison-output")
])

@app.callback(
    Output("comparison-output", "children"),
    Input("year-a", "value"),
    Input("year-b", "value"),
    Input("month-slider", "value")
)

def update_output(year_a, year_b, selected_month):

    #filter year
    df_a = df[df["year"] == year_a]
    df_b = df[df["year"] == year_b]

    #filter month
    df_a_month = df_a[df_a["createdAt"].dt.month == selected_month]
    df_b_month = df_b[df_b["createdAt"].dt.month == selected_month]

    keywords = ["tesla", "spacex", "starlink", "doge", "trump", "twitter"]

    #consistent axises
    max_y = max(
        df_a.resample("ME", on="createdAt")["likeCount"].sum().max(),
        df_b.resample("ME", on="createdAt")["likeCount"].sum().max()
    )

    #like count tracker
    def engagement_summary(data):
        return html.Ul([
            html.Li(f"Tweets: {len(data)}"),
            html.Li(f"Total Likes: {data['likeCount'].sum()}"),
            html.Li(f"Total Retweets: {data['retweetCount'].sum()}")
        ])

    def plot_engagement(data, title):
        monthly = data.resample("ME", on="createdAt")["likeCount"].sum().reset_index()

        tickvals = monthly["createdAt"]
        ticktext = monthly["createdAt"].dt.strftime("%b").str[0]

        fig = px.line(monthly, x="createdAt", y="likeCount", title=title)
        fig.update_yaxes(range=[0, max_y])
        fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
        return dcc.Graph(figure=fig)
    
    #get the top tweet of the month
    def show_top_tweet(data):
        top_row = data.loc[data["likeCount"].idxmax()]
        return html.Div([
            html.P(top_row["fullText"]),
            html.P(f"Likes: {top_row['likeCount']} | Retweets: {top_row['retweetCount']}"),
        ], style={"marginTop": "10px"})
    
    #count key words for bar chart
    def count_keywords(text, keywords, total_tweets):
        raw_counts = {kw: text.count(kw) for kw in keywords}
        normalized_counts = {kw: round((count / total_tweets) * 100, 2) for kw, count in raw_counts.items()}
        return normalized_counts
    
    def keyword_bar_chart(counts):
        df_kw = pd.DataFrame(list(counts.items()), columns=["Keyword", "Count"])
        fig = px.bar(df_kw, x="Keyword", y="Count")
        return dcc.Graph(figure=fig)
    
    text_a = " ".join(df_a_month["cleanText"])
    text_b = " ".join(df_b_month["cleanText"])

    counts_a = count_keywords(text_a, keywords, len(df_a))
    counts_b = count_keywords(text_b, keywords, len(df_b)) 


    return html.Div([
        html.Div([
            html.H2(f"Year {year_a}"),
            engagement_summary(df_a),
            plot_engagement(df_a, f"Likes by Month ({year_a})"),
            html.H4("Top Tweet of the Month"),
            show_top_tweet(df_a_month),
            html.H4(f"Keyword Mentions in {selected_month}/{year_a}"),
            keyword_bar_chart(counts_a),
        ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            html.H2(f"Year {year_b}"),
            engagement_summary(df_b),
            plot_engagement(df_b, f"Likes by Month ({year_b})"),
            html.H4("___________ "),
            show_top_tweet(df_b_month),
            html.H4("___________ "),
            keyword_bar_chart(counts_b),
        ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "float": "right"})
    ])

if __name__ == "__main__":
    app.run(debug=True)