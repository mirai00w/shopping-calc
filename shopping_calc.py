import streamlit as st  # Streamlitライブラリをインポート（Web画面を構築するため）
import pandas as pd  # Pandasライブラリをインポート（履歴データを表形式で管理・表示するため）
import uuid  # UUIDライブラリをインポート（データの一意なIDを自動生成するため）
import time  # ★追加：時間待機ライブラリ（クッキーの保存完了を待つために使用）
from datetime import datetime  # 日時ライブラリをインポート（履歴の登録日時を取得するため）
from supabase import create_client, Client  # Supabase接続用の関数と型定義をインポート（データベースと認証のため）
from streamlit_cookies_controller import CookieController  # クッキー操作用ライブラリをインポート（自動ログインを実装するため）

# --- ページ設定 ---
st.set_page_config(page_title="価格比較ツール", layout="centered")  # アプリのブラウザタブ名と、画面を中央寄せにする設定

# ==========================================
# 🍪 クッキーコントローラーの初期化と自動ログインロジック
# ==========================================
controller = CookieController()  # ブラウザのクッキーを読み書きするためのインスタンス（コントローラー）を生成

# アプリ起動時に最初の一度だけクッキーをチェックするための初期設定
if "auth_attempted" not in st.session_state:  # セッション（一時メモリ）に「自動ログイン試行済みフラグ」がない場合
    st.session_state.auth_attempted = False  # まだ試していないので初期値としてFalseを設定

# まだログインしておらず、かつ自動ログインをまだ試みていない場合に実行
if st.session_state.get("user") is None and not st.session_state.auth_attempted:
    cookies = controller.getAll()  # ブラウザに保存されているすべてのクッキーを辞書型で取得
    access_token = cookies.get("sb_access_token")  # Supabaseの「アクセストークン（一時的な鍵）」を取り出す
    refresh_token = cookies.get("sb_refresh_token")  # Supabaseの「リフレッシュトークン（鍵を更新するための鍵）」を取り出す
    
    if access_token and refresh_token:  # クッキーに2つの鍵が安全に保存されていた場合
        try:
            # 保存されていた鍵をSupabaseに渡して、以前のログインセッションを完全に復元する
            response = supabase.auth.set_session(access_token, refresh_token) 
            st.session_state.user = response.user  # 復元に成功したら、ユーザー情報をセッション状態にセット
        except Exception:
            pass  # 鍵が期限切れなどの理由で復元に失敗した場合は、何もしないで通常のログイン画面へ流す
    st.session_state.auth_attempted = True  # 成功・失敗に関わらず「自動ログインは試行済み」にして無限ループを防止

# ==========================================
# 🛡️ 法的規約エリア（サイドバーに格納）
# ==========================================
with st.sidebar:  # 左側のサイドバー領域の中に以下の要素を配置する
    st.markdown("### 📋 規約・ポリシー")  # サイドバーにメニューのタイトルを表示
    st.caption("本サービスをご利用の前に必ずご確認ください。")  # 小さな文字で注意書きを表示
    
    with st.sidebar.expander("🛡️ プライバシーポリシー"):  # クリックすると開閉する「プライバシーポリシー」の枠を作成
        st.write("""
        1. 個人情報の取得
        当サービス（以下、「本サービス」といいます）は、ユーザーがアカウント登録を行う際に、メールアドレスおよびパスワードを取得します。また、本サービスの利用に伴い、入力された商品名、価格、店舗名、およびそれらに付随する比較・履歴データ（以下、「ユーザーデータ」といいます）を自動的に取得し、クラウド上に保存します。

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
        本サービスは、法令の改正や運営方針の変更に伴い、本ポリシーを事前の予告なく改定することがあります。改定後のポリシーは、本サービス上に掲載した時点から効力を生じるものとします。
        """)

    with st.sidebar.expander("📝 利用規約"):  # クリックすると開閉する「利用規約」の枠を作成
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
    st.markdown("---")  # サイドバー内に区切り線を表示

# ==========================================
# 🎨 デザインカスタマイズ用CSS
# ==========================================
st.markdown("""
<style>
/* タブ全体の並びに関するスタイル設定 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; /* タブとタブの間の隙間を8pxにする */
    background-color: transparent; /* 背景を透明にする */
}
/* 選択されていない状態の通常タブのスタイル */
.stTabs [data-baseweb="tab"] {
    background-color: #EDE9DF; /* 薄いベージュの背景色 */
    border-radius: 8px 8px 0 0; /* 上側の角だけを丸くする */
    padding: 10px 20px; /* タブ内の文字の上下左右に余白を作る */
    color: #698474; /* 文字色をくすんだグリーンにする */
    font-weight: bold; /* 文字を太字にする */
}
/* ユーザーが現在選択しているアクティブなタブのスタイル */
.stTabs [aria-selected="true"] {
    background-color: #698474 !important; /* 背景色を濃いグリーンに変える */
    color: #FFFFFF !important; /* 文字色を白に変える */
}
/* アプリ内のすべてのボタン共通のスタイル */
.stButton>button {
    border-radius: 8px; /* ボタンの角を丸くする */
    border: none; /* 外枠の線を消す */
    box-shadow: 0 2px 5px rgba(0,0,0,0.05); /* 下側に薄い影をつけて立体感を出す */
    transition: all 0.2s ease; /* マウスを乗せた時のアニメーションを滑らかにする */
}
/* ボタンにマウスが乗った時（ホバー時）のスタイル */
.stButton>button:hover {
    transform: translateY(-2px); /* ボタンを少しだけ上に浮かせる */
    box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* 影を少し濃くして浮遊感を強調する */
}
</style>
""", unsafe_allow_html=True)  # HTML/CSSをそのまま画面に反映させるための設定

# ==========================================
# 📱 スマホアプリ化（PWA全画面表示）用ハック
# ==========================================
st.markdown("""
<script>
    const head = document.getElementsByTagName('head')[0]; // HTMLの<head>タグを取得
    
    // iPhone（iOS）でPWAとして開いたときにアドレスバーを隠し、全画面アプリ化する設定
    const metaApple = document.createElement('meta');
    metaApple.name = 'apple-mobile-web-app-capable';
    metaApple.content = 'yes';
    head.appendChild(metaApple);

    // AndroidでPWAとして開いたときに全画面アプリ化する設定
    const metaAndroid = document.createElement('meta');
    metaAndroid.name = 'mobile-web-app-capable';
    metaAndroid.content = 'yes';
    head.appendChild(metaAndroid);

    // iPhoneでの全画面表示時、最上部のステータスバー（電波や電池の場所）の背景をデフォルト（白/黒）にする
    const metaStatus = document.createElement('meta');
    metaStatus.name = 'apple-mobile-web-app-status-bar-style';
    metaStatus.content = 'default';
    head.appendChild(metaStatus);
</script>
""", unsafe_allow_html=True)  # JavaScriptをページに埋め込んで実行させる設定

# ==========================================
# 🔐 Supabase 認証ロジック
# ==========================================
@st.cache_resource  # アプリが動いている間、この関数の実行結果（接続情報）をメモリにキャッシュして使い回す設定
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]  # 設定ファイル(secrets.toml)からURLを安全に取得
    key = st.secrets["SUPABASE_KEY"]  # 設定ファイルからAPIキーを安全に取得
    return create_client(url, key)  # Supabaseクライアントを作成して返す

try:
    supabase = init_supabase()  # データベースへの接続を開始
except Exception as e:
    st.error("Supabaseの接続設定が見つかりません。secrets.tomlを確認してください。")  # 接続に失敗した場合はエラーを表示
    st.stop()  # 処理を完全に停止

if "user" not in st.session_state:  # セッション状態に「ログインユーザー情報」の格納先がない場合
    st.session_state.user = None  # 初期値としてNone（未ログイン状態）をセット

def login_ui():  # ログイン画面を構築するための関数定義
    st.title("🔒 ログイン")  # ログイン画面のメイン見出しを表示
    st.markdown("自分専用の価格比較ツールにアクセスするため、ログインしてください。")  # 説明文を表示

    with st.form("login_form"):  # 入力欄のズレを防ぎ、ボタン押下時に一括送信するためのフォームを作成
        email = st.text_input("メールアドレス")  # メールアドレス用の文字列入力欄
        password = st.text_input("パスワード", type="password")  # 伏字（●●●）になるパスワード入力欄
        submit_login = st.form_submit_button("ログイン", use_container_width=True)  # 横幅いっぱいのログイン送信ボタン

    if submit_login:  # ログインボタンが押された場合
        if not email or not password:  # どちらかが空欄だった場合
            st.warning("メールアドレスとパスワードを入力してください")  # 注意を促す警告を表示
        else:
            try:
                # 入力されたアドレスとパスワードをSupabaseに送信して認証を行う
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = response.user  # 認証成功時、返ってきたユーザー情報を一時メモリに保存
                
                # ▼▼▼ 自動ログインのためのクッキー保存処理と待機ハック ▼▼▼
                if response.session:  # 正常にセッションが発行されている場合
                    # セッション復元に必要な2つの暗号鍵（トークン）をブラウザのクッキーに保存する
                    controller.set("sb_access_token", response.session.access_token)
                    controller.set("sb_refresh_token", response.session.refresh_token)
                    
                    # 【最重要】ブラウザがクッキーを保存し終える前にリロードが走らないよう、1秒間だけプログラムを一時停止して待つ
                    time.sleep(1)
                
                st.rerun()  # 画面を即座に再描画し、ログイン後のメイン画面へ切り替える
            except Exception as e:
                st.error("ログイン失敗：メールアドレスかパスワードが間違っているか、メール認証が未完了です。")  # 失敗時のエラーメッセージ

    st.markdown("<br>", unsafe_allow_html=True)  # 画面に見栄えのための改行を追加
    with st.expander("📝 新規登録の方はこちら"):  # クリックすると開く、アカウント新規作成用エリア
        with st.form("signup_form"):  # 新規登録用の入力フォームを作成
            signup_email = st.text_input("登録するメールアドレス")  # 登録用のアドレス入力欄
            signup_password = st.text_input("設定するパスワード（6文字以上）", type="password")  # 登録用のパスワード入力欄
            submit_signup = st.form_submit_button("認証メールを送信して登録", use_container_width=True)  # 新規登録ボタン

        if submit_signup:  # 登録ボタンが押された場合
            if not signup_email or not signup_password:  # 空欄チェック
                st.warning("メールアドレスとパスワードを入力してください")
            elif len(signup_password) < 6:  # パスワードの文字数チェック（Supabaseのセキュリティ仕様）
                st.warning("パスワードは6文字以上で入力してください")
            else:
                try:
                    # 入力された情報を元に、Supabaseに新規ユーザー登録を要求する（認証メールが自動送信される）
                    response = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                    st.success("登録メールを送信しました！届いたメール内のリンクをクリックして認証を完了させてから、上のフォームよりログインしてください。")
                except Exception as e:
                    st.error(f"登録に失敗しました。詳細エラー: {e}")

    with st.expander("❓ パスワードを忘れた場合はこちら"):  # パスワードリセット用のエリア
        reset_email = st.text_input("登録したメールアドレス", key="reset_email_input")  # 再設定用のアドレス入力欄
        if st.button("パスワード再設定メールを送信", use_container_width=True):  # 送信ボタンが押された場合
            if reset_email:
                try:
                    supabase.auth.reset_password_email(reset_email)  # Supabaseからリセットメールを送信させる
                    st.success("再設定用のメールを送信しました。メールの案内に従ってパスワードを変更してください。")
                except Exception as e:
                    st.error("メールの送信に失敗しました。アドレスを確認してください。")
            else:
                st.warning("メールアドレスを入力してください。")

if st.session_state.user is None:  # まだログインが完了していない（一時メモリもクッキー復元も空の）場合
    login_ui()  # ログイン画面のUIを表示する
    st.stop()  # これ以降のメイン機能のプログラムは一切実行せずにここで処理を打ち切る

# ==========================================
# 👤 ログイン中のヘッダー
# ==========================================
col_user, col_logout = st.columns([4, 1])  # 画面上部を「4対1」の比率で左右に分割する
with col_user:
    st.caption(f"ログイン中: {st.session_state.user.email}")  # 左側の広い方に、ログイン中のユーザーのアドレスを薄く表示
with col_logout:
    if st.button("ログアウト"):  # 右側の狭い方にログアウトボタンを配置し、押された場合
        supabase.auth.sign_out()  # Supabaseにログアウト（セッション破棄）を要求
        st.session_state.user = None  # 一時メモリのユーザー情報を空にする
        
        # ▼▼▼ ログアウト時にクッキーの鍵も完全に削除する処理と待機ハックを追加 ▼▼▼
        controller.remove("sb_access_token")  # クッキーからアクセストークンを削除
        controller.remove("sb_refresh_token")  # クッキーからリフレッシュトークンを削除
        
        # 【最重要】クッキーの削除指示がブラウザに伝わり切るまで1秒待つ
        time.sleep(1)
        
        st.rerun()  # 画面を再描画してログイン前の画面に戻す

# ==========================================
# ☁️ クラウド連携用関数
# ==========================================
def load_from_cloud():  # クラウド上のデータベースから履歴データを読み込む関数
    try:
        # Supabaseの「user_data」テーブルから、現在ログイン中のユーザーIDに一致するレコードの「history_list」列を取得
        response = supabase.table("user_data").select("history_list").eq("user_id", st.session_state.user.id).execute()
        if len(response.data) > 0:  # もしデータが1件以上見つかった場合
            raw_list = response.data[0]["history_list"]  # 生のリストデータを取り出す
            for item in raw_list:
                if "id" not in item:  # もし古いデータでIDが付与されていないレコードがあれば
                    item["id"] = str(uuid.uuid4())  # その場で新しく固有のUUIDを発行して割り当てる（バグ防止）
            return raw_list  # 綺麗になった履歴リストを返す
        return []  # データが登録されていなければ空のリストを返す
    except Exception as e:
        st.error("クラウドデータの読み込みに失敗しました")  # エラー発生時の警告
        return []  # 安全のために空のリストを返す

def save_to_cloud(history_list):  # クラウド上のデータベースへ履歴データを保存（同期）する関数
    try:
        # ログイン中のユーザーIDを主キーとして、履歴リストを丸ごとデータベースに上書き保存（Upsert）する
        supabase.table("user_data").upsert({
            "user_id": st.session_state.user.id,
            "history_list": history_list
        }).execute()
    except Exception as e:
        st.error("クラウドデータへの保存に失敗しました")  # エラー発生時の警告

# ==========================================
# メイン機能
# ==========================================
# アプリの動作状態を管理するための各種セッション（一時メモリ）の初期設定
if "editing_record_id" not in st.session_state:
    st.session_state.editing_record_id = None  # 履歴から読み込んだ「編集中のレコードID」を記憶する場所（初期値は空）

if "should_clear" not in st.session_state:
    st.session_state.should_clear = False  # 保存完了直後に「入力欄をすべて消去する」ための予約フラグ（初期値はFalse）

if "store_count" not in st.session_state:
    st.session_state.store_count = 2  # 比較する店舗数の初期値（最初は2店舗からスタート）

if "edit_item_name" not in st.session_state:
    st.session_state.edit_item_name = ""  # 商品名入力欄の初期状態（空っぽ）

if "search_word" not in st.session_state:
    st.session_state.search_word = ""  # 履歴タブでの検索キーワードの初期状態（空っぽ）

if "history_changed" not in st.session_state:
    st.session_state.history_changed = False  # 履歴に変更（追加や削除）があったかを検知するフラグ（初期値はFalse）

# 最大10店舗分の入力欄（店名、価格、内容量）の状態をあらかじめ一時メモリに確保するループ処理
for i in range(10): 
    if f"name_{i}" not in st.session_state: st.session_state[f"name_{i}"] = ""  # 店名の初期値（空文字列）
    if f"price_{i}" not in st.session_state: st.session_state[f"price_{i}"] = None  # 価格の初期値（空）
    if f"amount_{i}" not in st.session_state: st.session_state[f"amount_{i}"] = None  # 内容量の初期値（空）

# アプリ起動時に最初の一度だけクラウドからデータを読み込んでメモリに展開する
if "history_loaded" not in st.session_state:
    st.session_state.history_list = load_from_cloud()  # クラウドからデータを取得してリストに格納
    st.session_state.history_loaded = True  # 「読み込み完了フラグ」をTrueにする

def load_target_to_compare(target):  # 履歴タブで選んだ過去データを、比較タブの入力欄にセットする関数
    st.session_state.editing_record_id = target.get("id")  # 選んだ過去データの「固有ID」を編集用に記憶
    st.session_state.edit_item_name = target.get("商品名", "")  # 商品名をセット
    saved_stores = target.get("raw_stores", [])  # 保存されていた各店舗のデータを取得
    st.session_state.store_count = max(2, len(saved_stores))  # 店舗数入力欄の数を、保存されていた店舗数に合わせる（最低2）
    
    # 一度すべての入力欄（10店舗分）を綺麗に初期化する
    for idx in range(10):
        st.session_state[f"name_{idx}"] = ""
        st.session_state[f"price_{idx}"] = None
        st.session_state[f"amount_{idx}"] = None
        
    # 過去データに保存されていた店舗の情報を、対応する入力欄のメモリへ順番にセットしていく
    for idx, s_data in enumerate(saved_stores):
        if idx < 10:  # 最大10店舗を超えないようにガード
            st.session_state[f"name_{idx}"] = s_data.get("name", "")
            st.session_state[f"price_{idx}"] = s_data.get("price", None)
            st.session_state[f"amount_{idx}"] = s_data.get("amount", None)

def clear_all_inputs():  # すべての入力欄を完全に空っぽにするお掃除関数
    st.session_state.editing_record_id = None  # 編集モード（上書き状態）を解除して通常モードに戻す
    st.session_state.edit_item_name = ""  # 商品名入力欄をクリア
    for idx in range(10):  # 10店舗分の入力値をすべてクリア
        st.session_state[f"name_{idx}"] = ""
        st.session_state[f"price_{idx}"] = None
        st.session_state[f"amount_{idx}"] = None

# ▼ 画面が描画される前に「クリア予約フラグ」をチェックし、立っていたらここでお掃除を実行する（Streamlitのバグ回避） ▼
if st.session_state.get("should_clear"):
    clear_all_inputs()  # 入力欄をクリア
    st.session_state.should_clear = False  # 掃除が終わったのでフラグを下げておく

st.title("価格比較ツール")  # アプリのメインタイトルを画面上に大きく表示

tab1, tab2, tab3 = st.tabs(["比較", "履歴", "割引"])  # 画面を「比較」「履歴」「割引」の3つのタブに分割

# ------------------------------------------
# 比較タブの処理
# ------------------------------------------
with tab1:
    # 商品名の入力欄を作成。key="edit_item_name"でセッションメモリと同期させている
    st.text_input("商品名", key="edit_item_name", placeholder="例: 鶏胸肉、オムツなど")
    st.markdown("---")  # 横の区切り線を表示
    
    col_add, col_sub, col_clr = st.columns([2.5, 2.5, 3])  # ボタンを並べるために横に3つの列を作成
    with col_add:
        if st.button("＋ 店舗を追加"):  # 店舗追加ボタンが押された場合
            if st.session_state.store_count < 10:  # 10店舗未満なら
                st.session_state.store_count += 1  # カウントを1増やす
                st.rerun()  # 画面を再描画して入力欄を増やす
            else:
                st.warning("追加できるのは10店舗までです")
    with col_sub:
        if st.button("－ 店舗を減らす"):  # 店舗減少ボタンが押された場合
            if st.session_state.store_count > 2:  # 2店舗より多ければ
                st.session_state.store_count -= 1  # カウントを1減らす
                st.rerun()  # 画面を再描画して入力欄を減らす
            else:
                st.warning("最低2店舗は必要です")
    with col_clr:
        # クリアボタン。on_clickにクリア関数を紐付けることで、安全に入力欄をリセットする
        if st.button("クリア", use_container_width=True, on_click=clear_all_inputs):
            st.toast("入力をクリアしました", icon="🧹")  # 画面右下に小さなお知らせ（トースト）を表示

    valid_stores = []  # 正しく「価格」と「内容量」が入力された店舗のデータを格納する一時リスト
    
    # store_countの数だけ、2列並びで店舗の入力カードを動的に生成していくループ
    for i in range(0, st.session_state.store_count, 2):
        cols = st.columns(2)  # 左右に2分割の列を作成
        for j in range(2):
            idx = i + j  # 現在処理している店舗のインデックス番号（0〜9）を計算
            if idx < st.session_state.store_count:  # 設定された店舗数を超えていなければ描画
                with cols[j]:  # 左右どちらかの列の中に配置
                    st.subheader(f"店舗 {idx + 1}")  # 「店舗 1」のような小見出しを表示
                    # 各店舗の店名入力欄。keyを分けることでそれぞれの値を独立してメモリ保持する
                    s_name = st.text_input("店名", key=f"name_{idx}", placeholder=f"店舗{idx+1}の名前")
                    
                    # 数値入力欄（価格と内容量）。ユーザーが未入力の時はプレースホルダーを表示
                    s_price = st.number_input("価格(円)", min_value=0, placeholder="例: 498", step=10, key=f"price_{idx}")
                    s_amount = st.number_input("内容量", min_value=0, placeholder="例: 400", step=10, key=f"amount_{idx}")
                    
                    # 計算が可能なように、価格と内容量の両方に0より大きい有効な数値が入っているかチェック
                    if s_amount is not None and s_price is not None and s_amount > 0 and s_price > 0:
                        valid_stores.append({
                            "id": idx,
                            "name": s_name or f"店舗{idx+1}",  # 店名が空欄なら自動で「店舗1」等にする
                            "price": s_price,
                            "amount": s_amount,
                            "unit_price": s_price / s_amount  # 1単位（グラムや個）あたりの単価を計算して格納
                        })

    st.markdown("---")  # 入力欄の下に区切り線を表示
    
    # 有効に入力された店舗が2店舗以上あれば、最安値の計算と結果表示を行う
    if len(valid_stores) >= 2:
        min_unit_price = min(s["unit_price"] for s in valid_stores)  # 全店舗の中から一番低い単価（最安値）を見つける
        winners = [s for s in valid_stores if s["unit_price"] == min_unit_price]  # 最安値を持つ店舗のリストを作成（同率1位を考慮）
        
        if len(winners) == 1:  # 最安値の店舗が1つだけ（単独1位）の場合
            winner = winners[0]
            st.error(f"🔥 【{winner['name']}】がお得！")  # 目立つ赤色の枠で最安店舗の名前を表示
            
            # 最安店舗以外の店舗リストを作成
            other_stores = [s for s in valid_stores if s["id"] != winner["id"]]
            next_best = min(other_stores, key=lambda x: x["unit_price"])  # 2番目にお得な店舗を見つける
            
            unit_diff = next_best["unit_price"] - winner["unit_price"]  # 1単位あたりの単価の差額を計算
            total_saved = unit_diff * winner["amount"]  # 最安店舗の内容量と同じ分だけ買った場合に、いくら得するかを計算
            
            # 具体的にいくら節約できるかを分かりやすい文章にして表示
            st.markdown(f"👉 【{winner['name']}】で **内容量 {winner['amount']}** 買った場合、【{next_best['name']}】より **約 {int(total_saved):,}円 お得** になります。（1単位あたり {unit_diff:.2f}円安）")
            
            # 履歴保存用に、最安店舗のデータを変数に代入しておく
            save_name = winner["name"]
            save_price = winner["price"]
            save_amount = winner["amount"]
            save_unit = winner["unit_price"]
        else:  # 複数の店舗がまったく同じ単価で最安（同率1位）だった場合
            names = " と ".join([w["name"] for w in winners])  # 同率の店舗名を「と」で繋ぐ
            st.warning(f"🤝 【{names}】が同じ単価（1単位あたり {min_unit_price:.2f}円）で最安です！")  # オレンジ色の枠で表示
            
            # 履歴保存用に、同率店舗の情報を用意する
            save_name = names
            save_price = winners[0]["price"]
            save_amount = winners[0]["amount"]
            save_unit = winners[0]["unit_price"]
            
        compared_str = " vs ".join([s["name"] for s in valid_stores])  # 履歴に表示するための「店舗A vs 店舗B」という比較構図の文字列を作成
        
        if st.session_state.edit_item_name:  # 商品名が入力されている場合のみ、保存ボタンを表示する
            current_edit_id = st.session_state.get("editing_record_id")  # 現在編集モード中（過去履歴を読み込み済み）か確認
            # 編集モード中ならボタンの文字を「上書き保存」に、通常時なら「新規保存」にする
            btn_label = "履歴を上書き保存" if current_edit_id else "履歴に新規保存"
            
            if st.button(btn_label):  # 保存ボタンが押された場合
                now = datetime.now().strftime("%Y-%m-%d %H:%M")  # 現在の「年-月-日 時:分」を取得
                
                store_data_to_save = []  # 入力されていた全店舗の生データを保存するためのリスト
                for idx in range(st.session_state.store_count):  # 現在開いている入力欄の数だけループしてデータを回収
                    p = st.session_state[f"price_{idx}"]
                    a = st.session_state[f"amount_{idx}"]
                    store_data_to_save.append({
                        "name": st.session_state[f"name_{idx}"],
                        "price": p if p is not None else 0,
                        "amount": a if a is not None else 0
                    })

                # 保存するレコードの辞書を作成
                new_record = {
                    "id": current_edit_id if current_edit_id else str(uuid.uuid4()),  # 編集中のIDがあれば引き継ぎ、なければ新規発行
                    "日付": now,
                    "商品名": st.session_state.edit_item_name,
                    "最安店舗": save_name,
                    "価格": int(save_price),
                    "内容量": int(save_amount),
                    "グラム/個単価": round(save_unit, 2),
                    "比較対象": compared_str,
                    "raw_stores": store_data_to_save
                }
                
                if current_edit_id:  # 上書き保存モードの場合
                    for i, record in enumerate(st.session_state.history_list):  # 既存の履歴リストをループで回して探す
                        if record["id"] == current_edit_id:  # IDが一致する古いレコードを見つけたら
                            st.session_state.history_list[i] = new_record  # 新しいレコードで中身を丸ごと差し替える
                            break
                    st.toast("上書き保存しました！", icon="🔄")  # 上書き完了の通知
                else:  # 新規保存モードの場合
                    st.session_state.history_list.insert(0, new_record)  # 履歴リストの先頭（一番上）に新しいレコードを挿入
                    st.toast("保存しました！", icon="💾")  # 新規保存完了の通知
                    
                st.session_state.history_changed = True  # 「履歴に変化があったよ」というフラグをTrueにする
                
                # 保存完了後、入力欄をすべて空にするためにクリア予約フラグをTrueにして画面をリロードする
                st.session_state.should_clear = True
                st.rerun()  # これにより画面が一番上から再実行され、上の「お掃除処理」が綺麗に実行される
                
    elif len(valid_stores) == 1:  # 1店舗しか入力がない場合
        st.warning("比較するため、もう1店舗入力してください")  # 比較対象を入力するように促す警告

# ------------------------------------------
# 履歴タブの処理
# ------------------------------------------
with tab2:
    if st.session_state.history_list:  # 履歴データが1件以上存在する場合のみ処理を行う
        col_s1, col_s2 = st.columns([4, 1])  # 検索バーと検索ボタンのために横に列を分割
        with col_s1:
            # 検索キーワード入力欄。入力された文字を一旦一時的な変数(temp_search)で受ける
            temp_search = st.text_input("商品名や店舗名で検索", value=st.session_state.search_word)
        with col_s2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)  # ボタンの縦位置を入力欄と揃えるための余白
            if st.button("検索", use_container_width=True):  # 検索ボタンが押された場合
                st.session_state.search_word = temp_search  # 確定したキーワードを正式な変数にコピー
                st.rerun()  # 画面を再描画してリストを絞り込む
        
        filtered_list = []  # 検索条件に合致したレコードだけを入れるためのリスト
        for r in st.session_state.history_list:  # すべての履歴を1件ずつループでチェック
            # 商品名、最安店舗名、または比較対象の文字列の中に、検索キーワード（小文字に統一）が含まれているか判定
            if st.session_state.search_word.lower() in r.get("商品名", "").lower() or st.session_state.search_word.lower() in r.get("最安店舗", "").lower() or st.session_state.search_word.lower() in r.get("比較対象", "").lower():
                filtered_list.append(r)  # 合致していれば絞り込みリストに追加
                
        if not filtered_list:  # 検索結果が0件だった場合
            st.info("該当する履歴がありません。")  # インフォメーション表示
        else:
            st.markdown("#### 履歴から再比較")  # 小見出しを表示
            
            # ドロップダウンメニュー（セレクトボックス）の選択肢を作成。「選択なし」を先頭にする
            load_options = ["(選択なし)"] + [r.get('id') for r in filtered_list]
            
            def format_label(x):  # IDだけの無機質な選択肢を、人間が見て分かりやすいテキストに変換する関数
                if x == "(選択なし)": return x  # 選択なしの場合はそのまま表示
                target = next((item for item in filtered_list if item.get('id') == x), None)  # IDが一致するデータを検索
                if target:
                    return f"{target['商品名']} ({target['最安店舗']}が最安)"  # 「商品名 (〇〇店が最安)」という見栄えにする
                return ""
                
            # 分かりやすい名前がついたドロップダウンを表示し、選ばれたIDを取得
            selected_id = st.selectbox("再比較したい履歴を選んでください", load_options, format_func=format_label)
            
            if selected_id != "(選択なし)":  # ユーザーが具体的な過去の履歴を選んだ場合
                target = next(item for item in filtered_list if item.get('id') == selected_id)  # 選ばれたIDのレコードを特定
                # ボタンを配置し、押されたら「比較タブにセットする関数」を呼び出す
                if st.button("この履歴を「比較」タブにセットする", on_click=load_target_to_compare, args=(target,)):
                    st.toast("セットしました！「比較」タブを開いてください", icon="✅")  # 成功の通知

            st.markdown("---")  # 区切り線
            
            st.markdown("#### 登録データ")  # 一覧表の小見出し
            df = pd.DataFrame(filtered_list)  # 絞り込まれたリストを、Pandasのデータフレーム（表形式）に変換
            
            if "比較対象" not in df.columns:  # 古いデータ構造の救済措置（列が存在しない場合）
                df["比較対象"] = "記録なし(旧データ)"  # 初期値で埋める
            else:
                df["比較対象"] = df["比較対象"].fillna("記録なし(旧データ)")  # 空白（NaN）があれば文字で埋める
            
            df.insert(0, "削除", False)  # 一覧表の一番左側に、一括削除チェックボックス用の「削除」列をすべてFalseで挿入
            
            df_display = df.copy()  # 画面表示用に見た目を整形するため、データのコピーを作成
            df_display["登録日付"] = df_display["日付"].apply(lambda x: x[5:10].replace("-", "/"))  # 日付を「05/19」のような短い形式に変換
            df_display["価格"] = df_display["価格"].apply(lambda x: f"{x:,}円")  # 桁区切りのカンマをつけて「円」を付与
            df_display["内容量"] = df_display["内容量"].apply(lambda x: f"{x:,}")  # 内容量に桁区切りのカンマを付与
            df_display["グラム/個単価"] = df_display["グラム/個単価"].apply(lambda x: f"{x:.2f}円")  # 小数点2桁までの表示にして「円」を付与
            
            df_display_with_id = df_display.copy()  # 削除処理で内部IDを参照するために、さらにコピーを保持
            
            # ユーザーの画面に見せる必要のある列だけを指定
            cols_to_show = ["削除", "商品名", "最安店舗", "価格", "内容量", "グラム/個単価", "比較対象", "登録日付"]
            
            # インタラクティブなデータ編集テーブル（チェックボックスが扱える特殊な表）を画面に表示
            edited_df = st.data_editor(
                df_display[cols_to_show],
                hide_index=True,  # 行番号（0, 1, 2...）を非表示にする
                width="stretch",  # 横幅いっぱいに広げる
                column_config={  # 各列の細かな見た目や編集権限（disabled）の設定
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
            
            if st.button("チェックした履歴を削除"):  # 削除ボタンが押された場合
                drop_indices = edited_df[edited_df["削除"] == True].index.tolist()  # チェックボックスにチェックが入っている行番号を取得
                
                if drop_indices:  # 1件以上チェックが入っていた場合
                    # 画面上の行番号から、対応する本物の「固有データID」をリストとして抽出
                    ids_to_delete = [df_display_with_id.iloc[i].get("id") for i in drop_indices if i < len(df_display_with_id)]
                    
                    # 削除対象のIDを持たないレコードだけで、新しい履歴リストを再構成する（フィルタリング削除）
                    new_history = [r for r in st.session_state.history_list if r.get("id") not in ids_to_delete]
                    st.session_state.history_list = new_history  # 全体履歴を新しいリストで上書き
                    st.session_state.history_changed = True  # 「履歴が変わったよ」というフラグをTrueにする
                    st.rerun()  # 画面を再描画して一覧表から消し去る
                else:
                    st.warning("削除する履歴にチェックを入れてください")  # チェックがない場合の注意
    else:
        st.info("データがありません")  # 履歴が1件も登録されていない場合の表示

# ------------------------------------------
# 割引タブの処理
# ------------------------------------------
with tab3:
    # 元値（商品の定価など）を入力する欄。100円刻みで調整可能
    base_price = st.number_input("元値(円)", min_value=0, value=None, placeholder="例: 3980", step=100)
    # 割引の計算方法を、パーセント引きか金額値引きかラジオボタンで選ぶ（横並び配置）
    discount_type = st.radio("割引種別", ["%OFF", "円引き"], horizontal=True)

    final_price = None  # 計算後の最終価格を入れる変数（初期値は空）

    if discount_type == "%OFF":  # パーセント引きが選ばれている場合
        # 割引率（％）を入力する欄。0〜100%の間で、5%刻みで入力可能
        discount_val = st.number_input("割引率(%)", min_value=0, max_value=100, value=None, placeholder="例: 20", step=5)
        if base_price is not None and discount_val is not None:  # 両方入力があれば計算
            final_price = base_price * (1 - discount_val / 100)  # 例：3000円の20%OFF = 3000 * 0.8 を計算
    else:  # 円引きが選ばれている場合
        # 値引き金額（円）を入力する欄。100円刻みで入力可能
        discount_val = st.number_input("値引(円)", min_value=0, value=None, placeholder="例: 500", step=100)
        if base_price is not None and discount_val is not None:  # 両方入力があれば計算
            final_price = base_price - discount_val  # 元値から値引き額をそのまま引き算

    st.markdown("---")  # 区切り線
    
    if final_price is not None:  # 計算結果が正常に算出されている場合
        st.metric(label="計算結果", value=f"{int(final_price):,} 円")  # 大きな数字でカンマ区切りの計算結果を表示
    else:
        st.caption("元値と割引額を入力すると計算結果が表示されます")  # 未入力時の説明用キャプション

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

# ==========================================
# 🔄 最終データ同期処理（全処理の締めくくり）
# ==========================================
# アプリの処理の最後に、履歴データに何か変化（追加、上書き、削除）があったか確認
if st.session_state.get("history_changed", False):
    save_to_cloud(st.session_state.history_list)  # 変化があれば、最新の履歴リストをクラウド上のSupabaseへ自動保存
    st.session_state.history_changed = False  # 同期が完了したのでフラグをFalseに戻す
