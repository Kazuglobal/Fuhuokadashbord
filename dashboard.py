import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
import datetime
from collections import deque
import os

st.set_page_config(page_title="福岡高校同窓会 会報入金者ダッシュボード", layout="wide")

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stActionButton {display: none;}
    /* Manage app（左上）の非表示 */
    [data-testid="stSidebar"] > div:first-child {display: none !important;}
    div:has(> button[title="Manage app"]) {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
import datetime
from collections import deque
import os

# --- データファイルの絶対パス ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILES = {
    ("2023", "県別"): os.path.join(BASE_DIR, "2023pre(県別）.csv"),
    ("2023", "学年別"): os.path.join(BASE_DIR, "2023year（学年別）.csv"),
    ("2023", "市町村別"): os.path.join(BASE_DIR, "2023 vil（市町村別）.csv"),
    ("2024", "県別"): os.path.join(BASE_DIR, "2024会報独立採算県別.csv"),
    ("2024", "学年別"): os.path.join(BASE_DIR, "2024会報独立採算　学年別.csv"),
    ("2024", "市町村別"): os.path.join(BASE_DIR, "会報独立採算2024年市町村.csv"),
}

# --- セッション状態で履歴管理・自動保存 ---
if 'data_history' not in st.session_state:
    st.session_state['data_history'] = deque(maxlen=5)
if 'last_csv' not in st.session_state:
    st.session_state['last_csv'] = None
if 'last_filter' not in st.session_state:
    st.session_state['last_filter'] = {}
if 'last_filter_keys' not in st.session_state:
    st.session_state['last_filter_keys'] = None

def save_history(csv_content, filter_opts):
    st.session_state['data_history'].appendleft((csv_content, filter_opts, datetime.datetime.now()))
    st.session_state['last_csv'] = csv_content
    st.session_state['last_filter'] = filter_opts

def format_history(hist):
    return f"{hist[2].strftime('%Y-%m-%d %H:%M:%S')} | 条件: {hist[1]}"

# --- ページ設定・CSS ---
st.markdown("""
<style>
body, .stApp { font-family: 'IPAexGothic', 'Noto Sans JP', 'Meiryo', 'sans-serif'; }
.css-1d391kg, .stDataFrame { font-size: 1.05em; }
@media (max-width: 600px) {
  .block-container { padding: 0.5rem 0.5rem; }
}
</style>
""", unsafe_allow_html=True)

# --- スマホ最適化カスタムCSS ---
st.markdown('''
<style>
/* Streamlitメニュー・フッターのみ非表示（headerは表示） */
#MainMenu, footer { display: none !important; }

/* テーブル横スクロール */
[data-testid="stDataFrame"] { overflow-x: auto !important; }

/* タイトル装飾・スマホ最適化 */
h1, .stApp h1 {
  font-size: 2.0rem !important;
  font-weight: 900 !important;
  color: #2d3a4a !important;
  text-shadow: 1px 2px 8px #dbe7ff33;
  letter-spacing: 0.04em;
  margin-bottom: 0.2em !important;
  line-height: 1.05 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
@media (max-width: 600px) {
  h1, .stApp h1 {
    font-size: 1.05rem !important;
    padding: 0.1em 0.05em !important;
    margin-bottom: 0.08em !important;
    line-height: 1.05 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }
  h3, .stApp h3, h4, .stApp h4 {
    font-size: 1.00rem !important;
    margin-bottom: 0.12em !important;
  }
  p, .stMarkdown p, .stApp p {
    font-size: 0.95rem !important;
    line-height: 1.30 !important;
  }
}
/* サブタイトル装飾 */
h3, .stApp h3 {
  color: #1976d2 !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em;
}
/* メトリクスを縦並び・中央寄せ */
@media (max-width: 600px) {
  .element-container:has([data-testid="stMetric"]){
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 0.5rem !important;
  }
  [data-testid="stMetric"] {
    min-width: 0 !important;
    width: 100% !important;
    margin-bottom: 0.5rem !important;
    text-align: center !important;
  }
  /* グラフも横スクロール */
  .element-container:has(.js-plotly-plot) {
    overflow-x: auto !important;
  }
  /* サイドバー幅・フォント */
  section[data-testid="stSidebar"] {
    min-width: 120px !important;
    max-width: 90vw !important;
    font-size: 15px !important;
  }
  /* ボタン大きめ */
  button, .stButton>button {
    font-size: 18px !important;
    padding: 0.7em 1.2em !important;
  }
  /* タブのタッチ領域拡大 */
  .stTabs [role="tab"] {
    font-size: 17px !important;
    padding: 0.6em 0.8em !important;
  }
  /* 余白・改行削減 */
  .block-container { padding: 0.5rem 0.2rem !important; }
}
/* テーブルヘッダ折返し */
.stDataFrame th { white-space: pre-line !important; }
</style>
''', unsafe_allow_html=True)

st.title("福岡高校同窓会 会報入金者データ ダッシュボード")
st.markdown("""
#### データをサイドバーから選択してください。
""")

# --- サイドバー: データ選択 ---
st.sidebar.header("データ選択")
year = st.sidebar.selectbox("年度", options=["2024", "2023"], index=0)
type_disp = st.sidebar.selectbox("集計単位", options=["県別", "学年別", "市町村別"], index=0)

# --- ファイル存在チェック ---
def get_file_content(year, type_disp):
    fpath = DATA_FILES.get((year, type_disp))
    if not fpath:
        return None, "該当データファイルがありません"
    if not os.path.exists(fpath):
        return None, f"ファイルが見つかりません: {os.path.basename(fpath)}"
    try:
        with open(fpath, encoding="utf-8-sig") as f:
            return f.read(), None
    except Exception as e:
        return None, f"ファイル読込エラー: {e}"

csv_content, file_err = get_file_content(year, type_disp)

# --- サイドバー: 履歴呼び出し ---
st.sidebar.header("データ履歴・設定")
if st.session_state['data_history']:
    idx = st.sidebar.selectbox("過去データを呼び出し", options=list(range(len(st.session_state['data_history']))),
        format_func=lambda i: format_history(st.session_state['data_history'][i]), key='hist_sel')
    if st.sidebar.button("履歴データで復元", key='restore_hist'):
        csv_content_hist, filter_opts, _ = st.session_state['data_history'][idx]
        st.session_state['last_csv'] = csv_content_hist
        st.session_state['last_filter'] = filter_opts
        st.experimental_rerun()

# --- データ取得 ---
# サイドバー選択のcsv_contentのみ使用
if not csv_content:
    st.info("サイドバーから年度・集計単位を選択してください。例: 都道府県別/学年別/市町村別のいずれか")
    st.stop()
if file_err:
    st.warning(file_err)

# --- データ形式判別 ---
header_line = csv_content.splitlines()[0]
if "卒業年" in header_line:
    data_type = "year"
elif "都道府県" in header_line:
    data_type = "pref"
elif "市町村" in header_line or "key" in header_line:
    data_type = "vil"
else:
    data_type = "unknown"

# --- データフレーム化 ---
try:
    df = pd.read_csv(io.StringIO(csv_content), encoding="utf-8-sig")
except Exception:
    df = pd.read_csv(io.StringIO(csv_content), encoding="utf-8")
if df.columns[0] in ["key", "都道府県", "市町村", "卒業年"]:
    df = df.dropna(subset=[df.columns[0]])
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

if df is None or df.empty:
    st.error("データが空です。正しいCSVを選択してください。")
    st.stop()

# --- サイドバー: フィルタ ---
st.sidebar.subheader("フィルタ")
# 年度や集計単位が切り替わったときはフィルタをリセット
if st.session_state['last_filter_keys'] != (year, type_disp):
    st.session_state['last_filter'] = {}
    st.session_state['last_filter_keys'] = (year, type_disp)
filter_opts = {}
if data_type == "year":
    years = df[df.columns[0]].unique().tolist()
    sel_years = st.sidebar.multiselect("卒業年で絞り込み", years, default=years)
    filter_opts['years'] = sel_years
    df = df[df[df.columns[0]].isin(sel_years)]
elif data_type == "pref":
    prefs = df[df.columns[0]].unique().tolist()
    sel_prefs = st.sidebar.multiselect("都道府県で絞り込み", prefs, default=prefs)
    filter_opts['prefs'] = sel_prefs
    df = df[df[df.columns[0]].isin(sel_prefs)]
elif data_type == "vil":
    vils = df[df.columns[0]].unique().tolist()
    sel_vils = st.sidebar.multiselect("市町村で絞り込み", vils, default=vils)
    filter_opts['vils'] = sel_vils
    df = df[df[df.columns[0]].isin(sel_vils)]

# --- 集計 ---
def show_stats(df, label):
    st.markdown(f"##### {label} 集計")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("合計件数", int(df['入金件数'].sum()))
    with col2: st.metric("合計金額", int(df['入金額'].sum()))
    with col3: st.metric("最大金額", int(df['入金額'].max()))
    with col4: st.metric("平均金額", round(df['入金額'].mean(),1))

# --- メイン処理 ---
if data_type == "year":
    st.subheader(f"{year}年 学年別データ")
    def convert_jp_year(y):
        if pd.isna(y): return None
        y = str(y).strip()
        m = re.match(r'(\w+?)(\d+?)年', y)
        if not m: return None
        era, n = m.groups()
        n = int(n)
        if era == '明治': return 1867 + n
        if era == '大正': return 1911 + n
        if era == '昭和': return 1925 + n
        if era == '平成': return 1988 + n
        if era == '令和': return 2018 + n
        return None
    df['西暦'] = df[df.columns[0]].apply(convert_jp_year)
    df_plot = df.dropna(subset=['西暦'])
    show_stats(df_plot, "学年別")
    tab1, tab2 = st.tabs(["入金件数推移", "入金額推移"])
    with tab1:
        fig = px.line(df_plot, x='西暦', y='入金件数', markers=True, title=f"{year}年 学年別 入金件数推移",
                      template='plotly_white', color_discrete_sequence=['#1976d2'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig = px.line(df_plot, x='西暦', y='入金額', markers=True, title=f"{year}年 学年別 入金額推移",
                      template='plotly_white', color_discrete_sequence=['#43a047'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### 件数順テーブル")
    df_件数 = df_plot.sort_values('入金件数', ascending=False).reset_index(drop=True)
    df_件数.insert(0, '順位', range(1, len(df_件数)+1))
    st.dataframe(df_件数, use_container_width=True, hide_index=True)
    st.markdown("#### 金額順テーブル")
    df_金額 = df_plot.sort_values('入金額', ascending=False).reset_index(drop=True)
    df_金額.insert(0, '順位', range(1, len(df_金額)+1))
    st.dataframe(df_金額, use_container_width=True, hide_index=True)
    st.markdown("#### 上位10件 (件数)")
    df件数 = df_plot.sort_values('入金件数', ascending=False).head(10).reset_index(drop=True)
    df件数.insert(0, '順位', range(1, len(df件数)+1))
    st.dataframe(df件数, use_container_width=True, hide_index=True)
    st.markdown("#### 上位10件 (金額)")
    df金額 = df_plot.sort_values('入金額', ascending=False).head(10).reset_index(drop=True)
    df金額.insert(0, '順位', range(1, len(df金額)+1))
    st.dataframe(df金額, use_container_width=True, hide_index=True)
    st.markdown("#### 全件テーブル（学年別）")
    df_all = df_plot.sort_values('西暦').reset_index(drop=True)
    df_all.insert(0, '順位', range(1, len(df_all)+1))
    st.dataframe(df_all, use_container_width=True, hide_index=True)

elif data_type == "pref":
    st.subheader(f"{year}年 都道府県別データ")
    show_stats(df, "都道府県別")
    top_n = 15
    st.markdown(f"上位{top_n}件を表示")
    df_件数 = df.sort_values('入金件数', ascending=False).head(top_n).reset_index(drop=True)
    df_件数.insert(0, '順位', range(1, len(df_件数)+1))
    df_金額 = df.sort_values('入金額', ascending=False).head(top_n).reset_index(drop=True)
    df_金額.insert(0, '順位', range(1, len(df_金額)+1))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_件数, x=df_件数.columns[1], y='入金件数', title=f"{year}年 都道府県別 入金件数",
                     template='plotly_white', color_discrete_sequence=['#1976d2'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_金額, x=df_金額.columns[1], y='入金額', title=f"{year}年 都道府県別 入金額",
                     template='plotly_white', color_discrete_sequence=['#43a047'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### 件数順テーブル")
    st.dataframe(df_件数, use_container_width=True, hide_index=True)
    st.markdown("#### 金額順テーブル")
    st.dataframe(df_金額, use_container_width=True, hide_index=True)
    st.markdown("#### 全件テーブル（都道府県別）")
    df_all = df.sort_values(df.columns[1], ascending=False).reset_index(drop=True)
    df_all.insert(0, '順位', range(1, len(df_all)+1))
    st.dataframe(df_all, use_container_width=True, hide_index=True)

elif data_type == "vil":
    st.subheader(f"{year}年 市町村別データ")
    show_stats(df, "市町村別")
    top_n = 20
    st.markdown(f"上位{top_n}件を表示")
    df_件数 = df.sort_values('入金件数', ascending=False).head(top_n).reset_index(drop=True)
    df_件数.insert(0, '順位', range(1, len(df_件数)+1))
    df_金額 = df.sort_values('入金額', ascending=False).head(top_n).reset_index(drop=True)
    df_金額.insert(0, '順位', range(1, len(df_金額)+1))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_件数, x=df_件数.columns[1], y='入金件数', title=f"{year}年 市町村別 入金件数",
                     template='plotly_white', color_discrete_sequence=['#1976d2'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_金額, x=df_金額.columns[1], y='入金額', title=f"{year}年 市町村別 入金額",
                     template='plotly_white', color_discrete_sequence=['#43a047'])
        fig.update_layout(font_family="IPAexGothic", font_size=15)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### 件数順テーブル")
    st.dataframe(df_件数, use_container_width=True, hide_index=True)
    st.markdown("#### 金額順テーブル")
    st.dataframe(df_金額, use_container_width=True, hide_index=True)
    st.markdown("#### 全件テーブル（市町村別）")
    df_all = df.sort_values(df.columns[1], ascending=False).reset_index(drop=True)
    df_all.insert(0, '順位', range(1, len(df_all)+1))
    st.dataframe(df_all, use_container_width=True, hide_index=True)
else:
    st.warning("データ形式が認識できません。ヘッダー行をご確認ください。")

# --- CSVダウンロード ---
st.sidebar.markdown("---")
st.sidebar.subheader("データ出力")
st.sidebar.download_button("フィルタ済みデータCSVダウンロード", df.to_csv(index=False, encoding="utf-8-sig"),
                         file_name="filtered_data.csv", mime="text/csv")

# --- 履歴保存 ---
save_history(csv_content, filter_opts)
