import pandas as pd
import plotly.express as px


db_path = "df_all.pk"


def download(path=None):
    import os
    import requests
    if os.path.exists(db_path):
        return
    print(f"Downloading file {path}")
    res = requests.get(path)
    if res.ok:
        with open(db_path, 'wb') as f:
            f.write(res.content)
    else:
        print(f"Could not download url: {path}")


def get_data(path):
    download(path)
    df = pd.read_pickle(db_path)
    df['manufacturer'] = df['manufacturer'].astype(str)
    df['model'] = df['model'].astype(str)
    return df


def get_counts(df):
    model_cnts = df.groupby(["manufacturer", "model"]).size().sort_values(ascending=False)
    # oem, model_s = model_cnts[:200].sample(1).index[0]
    return model_cnts


# New line for scatter info
sep = '</br>'


def add_newline(txt, every=15, limit=200):
    if txt is None:
        return None
    txt = txt if len(txt) < limit else txt[:limit] + "..."
    return ' '.join([x if i % every != every - 1 else x + sep for i, x in enumerate(txt.strip().split())])


def get_graph(df_q, model_s, color_by='year'):
    oem = df_q.sample(1)['manufacturer'].squeeze()
    df_q['link'] = df_q['id'].apply(lambda x: f'https://www.yad2.co.il/item/{x}')
    df_q['info_text_s'] = df_q['info_text'].apply(add_newline)
    df_q['hover_s'] = df_q.apply(lambda r: f"{r['year']} {'(סוחר$)' if r['merchant'] else ''} {r['sub_model']}", axis=1)
    df_q = df_q.sort_values('year', ascending=False)
    df_q['year'] = df_q['year'].astype(str)
    fig = px.scatter(df_q, x='price', y='kilometers', color=color_by, title=f'{oem}, {model_s}',
                     hover_name="hover_s",
                     # template="plotly_dark",
                     hover_data=["info_text_s", "link"])
    return fig
