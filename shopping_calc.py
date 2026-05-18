import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
from streamlit_local_storage import LocalStorage
from supabase import create_client, Client # 追加：Supabaseライブラリ

# --- ページ設定 ---
st.set_page_config(page_title="価格比較ツール", layout="centered")

# ==========================================
# 🎨 デザインカスタマイズ用CSS
# ==========================================
st.markdown("""
<style>
/* タブのベースデザイン（丸みを持たせて独立したボタンのようにする） */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    background-color: #EDE9DF; /* 非選択時は薄いベージュ */
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: #698474; /* 文字色はグリーン */
    font-weight: bold;
}
/* 選択されているタブのデザイン（背景をグリーン、文字を白に） */
.stTabs [aria-selected="true"] {
    background-color: #698474 !important;
    color: #FFFFFF !important;
}

/* ボタンのデザイン（少し丸みを持たせ、押したくなる立体感を出す） */
.stButton>button {
    border-radius: 8px;
    border: none;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}
/* ボタンに触れたとき（ホバー時）に少し浮き上がるエフェクト */
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 Supabase 認証ロジック（ここを追加しました！）
# ==========================================
# Supabaseへの接続設定
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Supabaseの接続設定が見つかりません。secrets.tomlを確認してください。")
    st.stop()

# セッションにユーザー情報を保持する枠を作る
if "user" not in st.session_state:
    st.session_state.user = None

# ログイン画面を作る関数
def login_ui():
    st.title("🔒 ログイン")
    st.markdown("自分専用の価格比較ツールにアクセスするため、ログインしてください。")

    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        password = st.text_input("パスワード", type="password")
        col1, col2 = st.columns(2)
        with col1:
            submit_login = st.form_submit_button("ログイン", use_container_width=True)
        with col2:
            submit_signup = st.form_submit_button("新規登録", use_container_width=True)

    # 新規登録ボタンが押された時の処理
    if submit_signup:
        if not email or not password:
            st.warning("メールアドレスとパスワードを入力してください")
        else:
            try:
                # Supabaseにユーザーを作成
                response = supabase.auth.sign_up({"email": email, "password": password})
                st.success("登録が完了しました！そのまま「ログイン」ボタンを押して開始してください。")
            except Exception as e:
                st.error("登録に失敗しました。パスワードは6文字以上で設定してください。")

    # ログインボタンが押された時の処理
    if submit_login:
        if not email or not password:
            st.warning("メールアドレスとパスワードを入力してください")
        else:
            try:
                # Supabaseでログイン確認
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = response.user
                st.rerun() # 画面をリロードしてメイン画面へ進む
            except Exception as e:
                st.error("ログイン失敗：メールアドレスかパスワードが間違っています。")

# ⚠️ ログインしていない場合はここで処理をストップし、これより下（メイン機能）を隠す
if st.session_state.user is None:
    login_ui()
    st.stop()

# ==========================================
# 👤 ログイン中のヘッダー（ログアウト機能）
# ==========================================
col_user, col_logout = st.columns([4, 1])
with col_user:
    st.caption(f"ログイン中: {st.session_state.user.email}")
with col_logout:
    if st.button("ログアウト"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# ==========================================
# これ以降は既存のメイン機能
# ==========================================
localS = LocalStorage()

if "store_count" not in st.session_state:
    st.session_state.store_count = 2

if "edit_item_name" not in st.session_state:
    st.session_state.edit_item_name = ""

if "search_word" not in st.session_state:
    st.session_state.search_word = ""

if "history_changed" not in st.session_state:
    st.session_state.history_changed = False

for i in range(10): 
    if f"name_{i}" not in st.session_state: st.session_state[f"name_{i}"] = ""
    if f"price_{i}" not in st.session_state: st.session_state[f"price_{i}"] = None
    if f"amount_{i}" not in st.session_state: st.session_state[f"amount_{i}"] = None

history_str = localS.getItem("shopping_history")

if "history_loaded" not in st.session_state:
    if history_str is not None:
        try:
            raw_list = json.loads(history_str) if history_str != "null" else []
            for item in raw_list:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
            st.session_state.history_list = raw_list
        except:
            st.session_state.history_list = []
        st.session_state.history_loaded = True
    else:
        st.session_state.history_list = []

def load_target_to_compare(target):
    st.session_state.edit_item_name = target.get("商品名", "")
    saved_stores = target.get("raw_stores", [])
    st.session_state.store_count = max(2, len(saved_stores))
    
    for idx in range(10):
        st.session_state[f"name_{idx}"] = ""
        st.session_state[f"price_{idx}"] = None
        st.session_state[f"amount_{idx}"] = None
        
    for idx, s_data in enumerate(saved_stores):
        if idx < 10:
            st.session_state[f"name_{idx}"] = s_data.get("name", "")
            st.session_state[f"price_{idx}"] = s_data.get("price", None)
            st.session_state[f"amount_{idx}"] = s_data.get("amount", None)

def clear_all_inputs():
    st.session_state.edit_item_name = ""
    for idx in range(10):
        st.session_state[f"name_{idx}"] = ""
        st.session_state[f"price_{idx}"] = None
        st.session_state[f"amount_{idx}"] = None

st.title("価格比較ツール")

tab1, tab2, tab3 = st.tabs(["比較", "履歴", "割引"])

with tab1:
    st.text_input("商品名", key="edit_item_name", placeholder="例: 鶏胸肉、オムツなど")
    st.markdown("---")
    
    col_add, col_sub, col_clr = st.columns([2.5, 2.5, 3])
    with col_add:
        if st.button("＋ 店舗を追加"):
            if st.session_state.store_count < 10:
                st.session_state.store_count += 1
                st.rerun()
            else:
                st.warning("追加できるのは10店舗までです")
    with col_sub:
        if st.button("－ 店舗を減らす"):
            if st.session_state.store_count > 2:
                st.session_state.store_count -= 1
                st.rerun()
            else:
                st.warning("最低2店舗は必要です")
    with col_clr:
        if st.button("クリア", use_container_width=True, on_click=clear_all_inputs):
            st.toast("入力をクリアしました", icon="🧹")

    valid_stores = []
    
    for i in range(0, st.session_state.store_count, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < st.session_state.store_count:
                with cols[j]:
                    st.subheader(f"店舗 {idx + 1}")
                    s_name = st.text_input("店名", key=f"name_{idx}", placeholder=f"店舗{idx+1}の名前")
                    
                    s_price = st.number_input("価格(円)", min_value=0, value=None, placeholder="例: 498", step=10, key=f"price_{idx}")
                    s_amount = st.number_input("内容量", min_value=0, value=None, placeholder="例: 400", step=10, key=f"amount_{idx}")
                    
                    if s_amount is not None and s_price is not None and s_amount > 0 and s_price > 0:
                        valid_stores.append({
                            "id": idx,
                            "name": s_name or f"店舗{idx+1}",
                            "price": s_price,
                            "amount": s_amount,
                            "unit_price": s_price / s_amount
                        })

    st.markdown("---")
    
    if len(valid_stores) >= 2:
        min_unit_price = min(s["unit_price"] for s in valid_stores)
        winners = [s for s in valid_stores if s["unit_price"] == min_unit_price]
        
        if len(winners) == 1:
            winner = winners[0]
            st.error(f"🔥 【{winner['name']}】がお得！")
            
            other_stores = [s for s in valid_stores if s["id"] != winner["id"]]
            next_best = min(other_stores, key=lambda x: x["unit_price"])
            
            unit_diff = next_best["unit_price"] - winner["unit_price"]
            total_saved = unit_diff * winner["amount"]
            
            st.markdown(f"👉 【{winner['name']}】で **内容量 {winner['amount']}** 買った場合、【{next_best['name']}】より **約 {int(total_saved):,}円 お得** になります。（1単位あたり {unit_diff:.2f}円安）")
            
            save_name = winner["name"]
            save_price = winner["price"]
            save_amount = winner["amount"]
            save_unit = winner["unit_price"]
        else:
            names = " と ".join([w["name"] for w in winners])
            st.warning(f"🤝 【{names}】が同じ単価（1単位あたり {min_unit_price:.2f}円）で最安です！")
            save_name = names
            save_price = winners[0]["price"]
            save_amount = winners[0]["amount"]
            save_unit = winners[0]["unit_price"]
            
        compared_str = " vs ".join([s["name"] for s in valid_stores])
        
        if st.session_state.edit_item_name:
            if st.button("履歴に保存"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                store_data_to_save = []
                for idx in range(st.session_state.store_count):
                    p = st.session_state[f"price_{idx}"]
                    a = st.session_state[f"amount_{idx}"]
                    store_data_to_save.append({
                        "name": st.session_state[f"name_{idx}"],
                        "price": p if p is not None else 0,
                        "amount": a if a is not None else 0
                    })

                new_record = {
                    "id": str(uuid.uuid4()),
                    "日付": now,
                    "商品名": st.session_state.edit_item_name,
                    "最安店舗": save_name,
                    "価格": int(save_price),
                    "内容量": int(save_amount),
                    "グラム/個単価": round(save_unit, 2),
                    "比較対象": compared_str,
                    "raw_stores": store_data_to_save
                }
                st.session_state.history_list.insert(0, new_record)
                st.session_state.history_changed = True
                st.toast("保存しました！", icon="💾")
    elif len(valid_stores) == 1:
        st.warning("比較するため、もう1店舗入力してください")

with tab2:
    if st.session_state.history_list:
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1:
            temp_search = st.text_input("商品名や店舗名で検索", value=st.session_state.search_word)
        with col_s2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("検索", use_container_width=True):
                st.session_state.search_word = temp_search
                st.rerun()
        
        filtered_list = []
        for r in st.session_state.history_list:
            if st.session_state.search_word.lower() in r.get("商品名", "").lower() or st.session_state.search_word.lower() in r.get("最安店舗", "").lower() or st.session_state.search_word.lower() in r.get("比較対象", "").lower():
                filtered_list.append(r)
                
        if not filtered_list:
            st.info("該当する履歴がありません。")
        else:
            st.markdown("#### 履歴から再比較")
            
            load_options = ["(選択なし)"] + [r.get('id') for r in filtered_list]
            
            def format_label(x):
                if x == "(選択なし)": return x
                target = next((item for item in filtered_list if item.get('id') == x), None)
                if target:
                    return f"{target['商品名']} ({target['最安店舗']}が最安)"
                return ""
                
            selected_id = st.selectbox("再比較したい履歴を選んでください", load_options, format_func=format_label)
            
            if selected_id != "(選択なし)":
                target = next(item for item in filtered_list if item.get('id') == selected_id)
                if st.button("この履歴を「比較」タブにセットする", on_click=load_target_to_compare, args=(target,)):
                    st.toast("セットしました！「比較」タブを開いてください", icon="✅")

            st.markdown("---")
            
            st.markdown("#### 登録データ")
            df = pd.DataFrame(filtered_list)
            
            if "比較対象" not in df.columns:
                df["比較対象"] = "記録なし(旧データ)"
            else:
                df["比較対象"] = df["比較対象"].fillna("記録なし(旧データ)")
            
            df.insert(0, "削除", False)
            
            df_display = df.copy()
            df_display["登録日付"] = df_display["日付"].apply(lambda x: x[5:10].replace("-", "/"))
            df_display["価格"] = df_display["価格"].apply(lambda x: f"{x:,}円")
            df_display["内容量"] = df_display["内容量"].apply(lambda x: f"{x:,}")
            df_display["グラム/個単価"] = df_display["グラム/個単価"].apply(lambda x: f"{x:.2f}円")
            
            df_display_with_id = df_display.copy()
            
            cols_to_show = ["削除", "商品名", "最安店舗", "価格", "内容量", "グラム/個単価", "比較対象", "登録日付"]
            
            edited_df = st.data_editor(
                df_display[cols_to_show],
                hide_index=True,
                width="stretch",
                column_config={
                    "削除": st.column_config.CheckboxColumn("", default=False, width="small"),
                    "商品名": st.column_config.Column("商品名", width="medium", disabled=True),
                    "最安店舗": st.column_config.Column("最安店舗", width="medium", disabled=True),
                    "価格": st.column_config.Column("価格", width="small", disabled=True),
                    "内容量": st.column_config.Column("内容量", width="small", disabled=True),
                    "グラム/個単価": st.column_config.Column("単価", width="small", disabled=True),
                    "比較対象": st.column_config.Column("比較対象", width="large", disabled=True),
                    "登録日付": st.column_config.Column("登録日付", width="small", disabled=True)
                }
            )
            
            if st.button("チェックした履歴を削除"):
                drop_indices = edited_df[edited_df["削除"] == True].index.tolist()
                
                if drop_indices:
                    ids_to_delete = [df_display_with_id.iloc[i].get("id") for i in drop_indices if i < len(df_display_with_id)]
                    
                    new_history = [r for r in st.session_state.history_list if r.get("id") not in ids_to_delete]
                    st.session_state.history_list = new_history
                    st.session_state.history_changed = True
                    st.rerun()
                else:
                    st.warning("削除する履歴にチェックを入れてください")
    else:
        st.info("データがありません")

with tab3:
    base_price = st.number_input("元値(円)", min_value=0, value=None, placeholder="例: 3980", step=100)
    discount_type = st.radio("割引種別", ["%OFF", "円引き"], horizontal=True)

    final_price = None

    if discount_type == "%OFF":
        discount_val = st.number_input("割引率(%)", min_value=0, max_value=100, value=None, placeholder="例: 20", step=5)
        if base_price is not None and discount_val is not None:
            final_price = base_price * (1 - discount_val / 100)
    else:
        discount_val = st.number_input("値引(円)", min_value=0, value=None, placeholder="例: 500", step=100)
        if base_price is not None and discount_val is not None:
            final_price = base_price - discount_val

    st.markdown("---")
    
    if final_price is not None:
        st.metric(label="計算結果", value=f"{int(final_price):,} 円")
    else:
        st.caption("元値と割引額を入力すると計算結果が表示されます")

if st.session_state.get("history_changed", False):
    localS.setItem("shopping_history", json.dumps(st.session_state.history_list))
    st.session_state.history_changed = False
