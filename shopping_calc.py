import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from supabase import create_client, Client

# --- ページ設定 ---
st.set_page_config(page_title="価格比較ツール", layout="centered")

# ==========================================
# 🛡️ 法的規約エリア（サイドバーに格納）
# ==========================================
with st.sidebar:
    st.markdown("### 📋 規約・ポリシー")
    st.caption("本サービスをご利用の前に必ずご確認ください。")
    
    with st.sidebar.expander("🛡️ プライバシーポリシー"):
        st.write("""
        1. 個人情報の取得
        当サービス（以下、「本サービス」といいます）は、ユーザーがアカウント登録を行う際に、メールアドレスおよびパスワードを取得します。また、本サービスの利用に伴い, 入力された商品名、価格、店舗名、およびそれらに付随する比較・履歴データ（以下、「ユーザーデータ」といいます）を自動的に取得し、クラウド上に保存します。

        2. 利用目的
        取得した個人情報およびユーザーデータは、以下の目的の範囲内でのみ利用します。
        ・本サービスにおけるログイン認証および本人確認のため
        ・ユーザーごとに最適化されたクラウド保存機能および履歴管理機能を提供するため
        ・パスワードリセット等の、本サービスの運営上重要なお知らせを通知するため
        ・本サービスの不具合修正、維持管理、および品質向上のための統計的分析のため

        3. 第三者提供および委託
        本サービスは、法令に基づく場合を除き、ユーザーの同意なく個人情報を第三者に提供することはありません。ただし、本サービスは認証およびデータ保存のインフラ基盤として、外部のクラウドサービス（Supabase等）を利用しています。これらの外部サービスへのデータの蓄積は、本サービスの提供に必要な範囲内での委託であり、第三者提供には該当しません。

        4. 安全管理措置
        本サービスは、取得した個人情報の漏洩、滅失、または毀損の防止のために、外部クラウド基盤が提供する暗号化通信（SSL/TLS）およびセキュリティ機能を適切に利用し、安全管理に努めます。

        5. データの削除（退会）
        ユーザーがアカウントおよび保存された履歴データの完全な削除を希望する場合、本サービスのお問い合わせ窓口（shopping.calc.support@gmail.com）までご連絡いただくものとします。申請を受理後、合理的な期間内に、認証情報および関連するすべてのユーザーデータをデータベースから完全に抹消します。

        6. ポリシーの変更
        本サービスは、法令の改正や運営方針 of 変更に伴い、本ポリシーを事前の予告なく改定することがあります。改定後のポリシーは、本サービス上に掲載した時点から効力を生じるものとします。
        """)

    with st.sidebar.expander("📝 利用規約"):
        st.write("""
        第1条（適用）
        本規約は、本サービスの利用者（以下、「ユーザー」といいます）と、本サービスの運営者（以下、「運営者」といいます）との間の、本サービスの利用に関わる一切の関係に適用されます。ユーザーは、本サービスのアカウントを作成した時点で、本規約のすべての条項に同意したものとみなされます。

        第2条（サービスの無償提供と変更・終了）
        1. 本サービスは、原則として無償で提供されます。
        2. 運営者は、ユーザーに事前に通知することなく、本サービスの内容を変更し、または提供を終了・中止することができるものとします。これによりユーザーに生じた不利益や損害について、運営者は一切の責任を負いません。

        第3条（免責事項・損害賠償の制限）
        1. 本サービスは、提供する価格比較結果、割引計算結果、およびデータ保存の正確性、完全性、有用性、確実性について、明示的にも黙示的にもいかなる保証も行いません。
        2. 本サービスで表示されるデータはあくまで参考値であり、実際の店舗での販売価格や条件を保証するものではありません。ユーザーが本サービスの情報を元に購入判断を行い、万が一不利益が生じた場合であっても、運営者は一切の責任を負いません。
        3. 運営者は、システムのメンテナンス、サーバー障害、通信回線の混雑、または第三者（SupabaseやStreamlit等）の提供するインフラサービスの停止・仕様変更・不具合等により、本サービスが一時的に停止、または保存されていた履歴データが消失・毀損した場合であっても、これに起因する損害について一切の責任を負いません。重要なデータは、ユーザー自身の責任において別途管理（バックアップ）するものとします。
        4. 本サービスの利用、または利用不能に関連してユーザーに生じた直接的、間接的、付随的、特別、または結果的な損害（金銭的損失、データの喪失、端末の不具合等を含みますがこれらに限定されません）について、運営者はその予見可能性の有無を問わず、一切の賠償責任および法的責任を負わないものとします。

        第4条（禁止事項）
        ユーザーは、本サービスの利用にあたり、以下の行為を行ってはなりません。
        (1) 法令または公序良俗に違反する行為
        (2) 本サービスに対するリバースエンジニアリング、解析、改変、またはソースコードの複製行為
        (3) 自動化ツール、スクリプト、ロボット、マクロ等を用いて、本サービスまたはサーバーに対して過度な負荷をかける行為（不正な大量アクセスやスクレイピング等）
        (4) 他人のメールアドレスを無断で使用してアカウントを作成する行為、または不正にログインを試みる行為
        (5) 本サービスの運営、または他のユーザーによる利用を妨害する一切の行為

        第5条（利用制限およびアカウント削除）
        運営者は、ユーザーが本規約のいずれかの条項に違反した場合、または違反した恐れがあると判断した場合、事前の通知なく、該当ユーザーのアカウントを停止、または保存データを削除することができるものとします。

        第6条（準拠法・裁判管轄）
        1. 本規約の解釈にあたっては、日本法を準拠法とします。
        2. 本サービスに関して紛争が生じた場合には、運営者の居住地を管轄する地方裁判所または簡易裁判所を第一審の専属的合意管轄裁判所とします。

        第7条（お問い合わせ窓口）
        本規約または本サービスに関する苦情、ご要望、お問い合わせは、すべて以下のメールアドレス宛に行うものとします。
        連絡先: shopping.calc.support@gmail.com
        """)
    st.markdown("---")

# ==========================================
# 🎨 デザインカスタマイズ用CSS
# ==========================================
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    background-color: #EDE9DF;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: #698474;
    font-weight: bold;
}
.stTabs [aria-selected="true"] {
    background-color: #698474 !important;
    color: #FFFFFF !important;
}
.stButton>button {
    border-radius: 8px;
    border: none;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 📱 スマホアプリ化（PWA全画面表示）用ハック
# ==========================================
st.markdown("""
<script>
    const head = document.getElementsByTagName('head')[0];
    
    const metaApple = document.createElement('meta');
    metaApple.name = 'apple-mobile-web-app-capable';
    metaApple.content = 'yes';
    head.appendChild(metaApple);

    const metaAndroid = document.createElement('meta');
    metaAndroid.name = 'mobile-web-app-capable';
    metaAndroid.content = 'yes';
    head.appendChild(metaAndroid);

    const metaStatus = document.createElement('meta');
    metaStatus.name = 'apple-mobile-web-app-status-bar-style';
    metaStatus.content = 'default';
    head.appendChild(metaStatus);
</script>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 Supabase 認証ロジック
# ==========================================
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

if "user" not in st.session_state:
    st.session_state.user = None

def login_ui():
    st.title("🔒 ログイン")
    st.markdown("自分専用の価格比較ツールにアクセスするため、ログインしてください。")

    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        password = st.text_input("パスワード", type="password")
        submit_login = st.form_submit_button("ログイン", use_container_width=True)

    if submit_login:
        if not email or not password:
            st.warning("メールアドレスとパスワードを入力してください")
        else:
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = response.user
                st.rerun()
            except Exception as e:
                st.error("ログイン失敗：メールアドレスかパスワードが間違っているか、メール認証が未完了です。")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 新規登録の方はこちら"):
        with st.form("signup_form"):
            signup_email = st.text_input("登録するメールアドレス")
            signup_password = st.text_input("設定するパスワード（6文字以上）", type="password")
            submit_signup = st.form_submit_button("認証メールを送信して登録", use_container_width=True)

        if submit_signup:
            if not signup_email or not signup_password:
                st.warning("メールアドレスとパスワードを入力してください")
            elif len(signup_password) < 6:
                st.warning("パスワードは6文字以上で入力してください")
            else:
                try:
                    response = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                    st.success("登録メールを送信しました！届いたメール内のリンクをクリックして認証を完了させてから、上のフォームよりログインしてください。")
                except Exception as e:
                    st.error(f"登録に失敗しました。詳細エラー: {e}")

    with st.expander("❓ パスワードを忘れた場合はこちら"):
        reset_email = st.text_input("登録したメールアドレス", key="reset_email_input")
        if st.button("パスワード再設定メールを送信", use_container_width=True):
            if reset_email:
                try:
                    supabase.auth.reset_password_email(reset_email)
                    st.success("再設定用のメールを送信しました。メールの案内に従ってパスワードを変更してください。")
                except Exception as e:
                    st.error("メールの送信に失敗しました。アドレスを確認してください。")
            else:
                st.warning("メールアドレスを入力してください。")

if st.session_state.user is None:
    login_ui()
    st.stop()

# ==========================================
# 👤 ログイン中のヘッダー
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
# ☁️ クラウド連携用関数
# ==========================================
def load_from_cloud():
    try:
        response = supabase.table("user_data").select("history_list").eq("user_id", st.session_state.user.id).execute()
        if len(response.data) > 0:
            raw_list = response.data[0]["history_list"]
            for item in raw_list:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
            return raw_list
        return []
    except Exception as e:
        st.error("クラウドデータの読み込みに失敗しました")
        return []

def save_to_cloud(history_list):
    try:
        supabase.table("user_data").upsert({
            "user_id": st.session_state.user.id,
            "history_list": history_list
        }).execute()
    except Exception as e:
        st.error("クラウドデータへの保存に失敗しました")

# ==========================================
# メイン機能
# ==========================================
if "editing_record_id" not in st.session_state:
    st.session_state.editing_record_id = None

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

if "history_loaded" not in st.session_state:
    st.session_state.history_list = load_from_cloud()
    st.session_state.history_loaded = True

def load_target_to_compare(target):
    st.session_state.editing_record_id = target.get("id")
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
    st.session_state.editing_record_id = None
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
                    
                    s_price = st.number_input("価格(円)", min_value=0, placeholder="例: 498", step=10, key=f"price_{idx}")
                    s_amount = st.number_input("内容量", min_value=0, placeholder="例: 400", step=10, key=f"amount_{idx}")
                    
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
            btn_label = "履歴を上書き保存" if st.session_state.get("editing_record_id") else "履歴に新規保存"
            
            if st.button(btn_label):
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
                    "id": st.session_state.get("editing_record_id", str(uuid.uuid4())),
                    "日付": now,
                    "商品名": st.session_state.edit_item_name,
                    "最安店舗": save_name,
                    "価格": int(save_price),
                    "内容量": int(save_amount),
                    "グラム/個単価": round(save_unit, 2),
                    "比較対象": compared_str,
                    "raw_stores": store_data_to_save
                }
                
                if st.session_state.get("editing_record_id"):
                    for i, record in enumerate(st.session_state.history_list):
                        if record["id"] == st.session_state.editing_record_id:
                            st.session_state.history_list[i] = new_record
                            break
                    st.toast("上書き保存しました！", icon="🔄")
                    st.session_state.editing_record_id = None
                else:
                    st.session_state.history_list.insert(0, new_record)
                    st.toast("保存しました！", icon="💾")
                    
                st.session_state.history_changed = True
                
                # 保存・上書き完了時にフォームをお掃除して画面をリフレッシュ
                clear_all_inputs()
                st.rerun()
                
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

# ==========================================
# 💰 収益化（マネタイズ）エリア（※現在コメントアウト中）
# ==========================================
# st.markdown("<br>", unsafe_allow_html=True)
# st.caption("スポンサーリンク")
# st.markdown("""
# <div style="display: flex; gap: 10px; flex-direction: column;">
#     <a href="https://www.amazon.co.jp/" target="_blank" style="background-color: #232F3E; color: white; padding: 15px; border-radius: 8px; text-align: center; text-decoration: none; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
#         🛒 Amazon タイムセール会場をチェック
#     </a>
#     <a href="https://www.rakuten.co.jp/" target="_blank" style="background-color: #BF0000; color: white; padding: 15px; border-radius: 8px; text-align: center; text-decoration: none; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
#         🛍️ 楽天市場 24時間限定セールをチェック
#     </a>
# </div>
# """, unsafe_allow_html=True)
# st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.get("history_changed", False):
    save_to_cloud(st.session_state.history_list)
    st.session_state.history_changed = False
