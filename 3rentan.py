import streamlit as st
import json
import os
import random

# --- データベース (JSONファイルで全員の状況を共有) ---
DATA_FILE = "sanrentan_final.json"

def load_data():
    # データファイルがない場合の初期設定
    default_data = {
        "phase": "setup",       # setup, lobby, round_input, betting, result, game_over
        "config": {
            "total_rounds": 3,
            "team_names": {"A": "チームA", "B": "チームB"} 
        },
        "status": {
            "current_round": 1,
        },
        "teams": { "A": [], "B": [] }, 
        "team_scores": { "A": 0, "B": 0 },
        "round_data": {
            "target_name": "",  
            "topic": "",        
            "correct_order": [], 
            "options": []       
        },
        "bets": {}, 
    }
    if not os.path.exists(DATA_FILE): return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 手動更新用の関数
def show_refresh_button(label="🔄 画面を更新"):
    if st.button(label):
        st.rerun()

# 得点計算ロジック
def calculate_score(user_bet, correct_order):
    if not user_bet or len(user_bet) < 3: return 0, "なし"
    user_set = set(user_bet)
    correct_set = set(correct_order)
    intersection = user_set & correct_set
    
    scores = []
    if user_bet == correct_order: scores.append((6, "🦄 サンレンタン"))
    if user_set == correct_set: scores.append((4, "🍀 サンレンプク"))
    if user_bet[0] == correct_order[0] and user_bet[1] == correct_order[1]: scores.append((3, "🥈 ニレンタン"))
    if len(intersection) >= 2: scores.append((2, "🍡 プクプク"))
    if user_bet[0] == correct_order[0]: scores.append((1, "☀️ タン"))
    
    return max(scores, key=lambda x: x[0]) if scores else (0, "ハズレ")

# データをロード
game_data = load_data()
tn_a = game_data["config"]["team_names"]["A"]
tn_b = game_data["config"]["team_names"]["B"]


# ==========================================
# 0. ログイン管理 (ここが個別の画面を分ける鍵)
# ==========================================
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None 
    st.session_state["user_name"] = ""
    st.session_state["user_team"] = ""

# --- サイドバー (自分の情報表示) ---
if st.session_state["user_role"]:
    role = st.session_state["user_role"]
    name = st.session_state["user_name"]
    
    st.sidebar.markdown(f"## ログイン中: **{name}**")
    
    if role == "host":
        st.sidebar.warning("🔧 あなたはホストです")
        if st.sidebar.button("⚠️ データリセット"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()
    else:
        my_team_id = st.session_state["user_team"]
        t_label = tn_a if my_team_id == "A" else tn_b
        color = "🔴" if my_team_id == "A" else "🔵"
        st.sidebar.info(f"所属: {color} {t_label}")

    st.sidebar.markdown("---")
    if game_data["phase"] not in ["setup", "lobby"]:
        st.sidebar.markdown("### 🏆 現在のスコア")
        
        # チーム平均の計算
        team_a_size = len(game_data['teams']['A']) if len(game_data['teams']['A']) > 0 else 1
        team_b_size = len(game_data['teams']['B']) if len(game_data['teams']['B']) > 0 else 1
        
        avg_a = game_data['team_scores']['A'] / team_a_size
        avg_b = game_data['team_scores']['B'] / team_b_size
        
        st.sidebar.write(f"🔴 {tn_a}: {game_data['team_scores']['A']} pts (平均: {avg_a:.2f})")
        st.sidebar.write(f"🔵 {tn_b}: {game_data['team_scores']['B']} pts (平均: {avg_b:.2f})")
    else:
        st.sidebar.write(f"🔴 {tn_a}: {game_data['team_scores']['A']} pts")
        st.sidebar.write(f"🔵 {tn_b}: {game_data['team_scores']['B']} pts")
    
    if st.sidebar.button("ログアウト"):
        st.session_state.clear()
        st.rerun()

# --- ログイン画面 ---
if st.session_state["user_role"] is None:
    st.title("🐇 チーム対抗サンレンタン")
    st.info("名前を入力してログインしてください")
    
    tab1, tab2 = st.tabs(["👤 プレイヤーとして参加", "🔑 ホストとして管理"])
    
    with tab1:
        # 名前入力
        input_name = st.text_input("あなたの名前(ニックネーム)", key="p_name")
        
        # チーム選択
        st.write("所属チームを選んでください")
        c1, c2 = st.columns(2)
        with c1:
            is_a = st.button(f"🔴 {tn_a} で参加", use_container_width=True)
        with c2:
            is_b = st.button(f"🔵 {tn_b} で参加", use_container_width=True)
            
        if (is_a or is_b) and input_name:
            team_id = "A" if is_a else "B"
            # データの登録
            if input_name in game_data["teams"]["A"]: game_data["teams"]["A"].remove(input_name)
            if input_name in game_data["teams"]["B"]: game_data["teams"]["B"].remove(input_name)
            game_data["teams"][team_id].append(input_name)
            save_data(game_data)
            
            # ★ここでセッションに保存!「この画面はこの人のもの」と確定
            st.session_state["user_role"] = "player"
            st.session_state["user_name"] = input_name
            st.session_state["user_team"] = team_id
            st.rerun()
        elif (is_a or is_b) and not input_name:
            st.error("名前を入力してください!")

    with tab2:
        pwd = st.text_input("ホストパスワード", type="password")
        if st.button("管理者として入室", type="primary"):
            if pwd == "0000":
                st.session_state["user_role"] = "host"
                st.session_state["user_name"] = "HOST"
                st.rerun()
            else:
                st.error("パスワードが違います")
    st.stop()


# ==========================================
# メイン画面 (ロールによって表示を分岐)
# ==========================================
st.title("🐇 チーム対抗サンレンタン")
phase = game_data["phase"]
my_role = st.session_state["user_role"]
my_name = st.session_state["user_name"]

# ラウンド表示
if phase not in ["setup", "lobby", "game_over"]:
    curr = game_data["status"]["current_round"]
    total = game_data["config"]["total_rounds"]
    st.progress(curr/total, text=f"Round {curr} / {total}")

# ----------------------------------------
# 1. Setup (ホストのみ操作)
# ----------------------------------------
if phase == "setup":
    if my_role == "host":
        st.header("⚙️ 初期設定")
        col1, col2 = st.columns(2)
        na = col1.text_input("チームAの名前", value="赤組")
        nb = col2.text_input("チームBの名前", value="白組")
        rnd = st.number_input("ラウンド数", 1, 10, 3)
        
        if st.button("設定完了してロビーを開く", type="primary"):
            game_data["config"]["team_names"]["A"] = na
            game_data["config"]["team_names"]["B"] = nb
            game_data["config"]["total_rounds"] = rnd
            game_data["phase"] = "lobby"
            save_data(game_data)
            st.rerun()
    else:
        st.info("ホストが準備中です。しばらくお待ちください...")
        show_refresh_button()

# ----------------------------------------
# 2. Lobby (全員表示)
# ----------------------------------------
elif phase == "lobby":
    st.header("👥 参加者待機中")
    c1, c2 = st.columns(2)
    c1.success(f"🔴 {tn_a} ({len(game_data['teams']['A'])})")
    for p in game_data["teams"]["A"]: c1.write(f"- {p}")
    
    c2.info(f"🔵 {tn_b} ({len(game_data['teams']['B'])})")
    for p in game_data["teams"]["B"]: c2.write(f"- {p}")
    
    st.write("---")
    if my_role == "host":
        total_players = len(game_data['teams']['A']) + len(game_data['teams']['B'])
        st.metric("総参加者数", f"{total_players} 人")
        
        if st.button("🚀 ゲームスタート", type="primary"):
            game_data["phase"] = "round_input"
            save_data(game_data)
            st.rerun()
        
        st.caption("最新の参加状況を確認するには更新ボタンを押してください")
        show_refresh_button("🔄 参加者リストを更新")
    else:
        st.write("ホストの開始を待っています...")
        show_refresh_button()

# ----------------------------------------
# 3. Round Input (ホストだけが見える!)
# ----------------------------------------
elif phase == "round_input":
    r = game_data["status"]["current_round"]
    st.header(f"第 {r} ラウンド")
    
    if my_role == "host":
        # ▼▼▼ ホスト専用画面 ▼▼▼
        st.warning("⚠️ この画面は参加者に見せないでください")
        with st.form("input_form"):
            target = st.text_input("お題の人", placeholder="例: 佐藤部長")
            topic = st.text_input("お題テーマ", placeholder="例: 好きなランチメニュー")
            
            st.markdown("**正解の順番 (1位〜3位)**")
            c1, c2, c3 = st.columns(3)
            a1 = c1.text_input("🥇 1位")
            a2 = c2.text_input("🥈 2位")
            a3 = c3.text_input("🥉 3位")
            
            st.markdown("**ダミー選択肢 (4つ)**")
            c4, c5 = st.columns(2)
            d1 = c4.text_input("ダミー1")
            d2 = c5.text_input("ダミー2")
            d3 = c4.text_input("ダミー3")
            d4 = c5.text_input("ダミー4")
            
            if st.form_submit_button("出題スタート"):
                if all([target, topic, a1, a2, a3, d1, d2, d3, d4]):
                    opts = [a1, a2, a3, d1, d2, d3, d4]
                    random.shuffle(opts)
                    game_data["round_data"] = {
                        "target_name": target, "topic": topic,
                        "correct_order": [a1, a2, a3], "options": opts
                    }
                    game_data["bets"] = {}
                    game_data["phase"] = "betting"
                    save_data(game_data)
                    st.rerun()
                else:
                    st.error("全項目入力してください")
        # ▲▲▲ ホスト専用画面終わり ▲▲▲
    else:
        # ▼▼▼ プレイヤー画面 ▼▼▼
        st.info("ホストがお題を入力しています...")
        st.image("https://placehold.co/600x200?text=Waiting...", caption="待機中")
        show_refresh_button()

# ----------------------------------------
# 4. Betting (各プレイヤーが自分の予想を入力)
# ----------------------------------------
elif phase == "betting":
    rd = game_data["round_data"]
    st.subheader(f"お題: {rd['target_name']}さんの『{rd['topic']}』")
    
    if my_role == "player":
        # ▼▼▼ プレイヤー個人画面 ▼▼▼
        # 自分の過去の回答を確認
        my_bet = game_data["bets"].get(my_name)
        
        if my_bet:
            st.success("✅ 回答を受け付けました!")
            st.write("あなたの予想:")
            st.info(f"🥇{my_bet[0]} ➡ 🥈{my_bet[1]} ➡ 🥉{my_bet[2]}")
            st.write("他のメンバーを待っています...")
            show_refresh_button()
        else:
            st.write("選択肢から **1位・2位・3位** をそれぞれ選んでください")
            
            with st.form("betting_form"):
                st.markdown("### 順位を選択")
                col1, col2, col3 = st.columns(3)
                
                first = col1.selectbox("🥇 1位", [""] + rd["options"], key="first")
                second = col2.selectbox("🥈 2位", [""] + rd["options"], key="second")
                third = col3.selectbox("🥉 3位", [""] + rd["options"], key="third")
                
                submitted = st.form_submit_button("回答を確定する", type="primary")
                
                if submitted:
                    if first and second and third:
                        # 重複チェック
                        if len(set([first, second, third])) != 3:
                            st.error("❌ 同じ選択肢を複数回選ぶことはできません")
                        else:
                            # ★ここで「自分の名前」をキーにして保存する
                            game_data["bets"][my_name] = [first, second, third]
                            save_data(game_data)
                            st.rerun()
                    else:
                        st.error("❌ 1位、2位、3位をすべて選択してください")
        # ▲▲▲ プレイヤー個人画面終わり ▲▲▲
        
    elif my_role == "host":
        # ホストは全体の進捗だけ見る
        done = len(game_data["bets"])
        total = len(game_data["teams"]["A"]) + len(game_data["teams"]["B"])
        st.metric("回答済み人数", f"{done} / {total}")
        st.write("全員回答したら終了してください")
        if st.button("締め切って結果発表へ", type="primary"):
            game_data["phase"] = "result"
            save_data(game_data)
            st.rerun()
        
        st.caption("最新の回答状況を確認するには更新ボタンを押してください")
        show_refresh_button("🔄 回答状況を更新")

# ----------------------------------------
# 5. Result (全員で結果を見る)
# ----------------------------------------
elif phase == "result":
    st.header("🎉 結果発表")
    rd = game_data["round_data"]
    correct = rd["correct_order"]
    
    st.subheader("正解の順位")
    c1, c2, c3 = st.columns(3)
    c1.error(f"🥇 {correct[0]}")
    c2.warning(f"🥈 {correct[1]}")
    c3.success(f"🥉 {correct[2]}")
    
    st.write("---")
    
    # チーム別結果表示
    col_a, col_b = st.columns(2)
    scores_diff = {} # 今回の加算分
    
    for p in game_data["bets"]:
        s, l = calculate_score(game_data["bets"][p], correct)
        scores_diff[p] = (s, l)

    with col_a:
        st.markdown(f"### 🔴 {tn_a}")
        for p in game_data["teams"]["A"]:
            bet = game_data["bets"].get(p)
            if bet:
                s, l = scores_diff.get(p, (0, ""))
                res = f"{bet[0]}→{bet[1]}→{bet[2]}"
                if s > 0: st.success(f"**{p}**: +{s} ({l})\n\n{res}")
                else: st.write(f"**{p}**: 0\n\n{res}")
            else: st.write(f"**{p}**: 未回答")

    with col_b:
        st.markdown(f"### 🔵 {tn_b}")
        for p in game_data["teams"]["B"]:
            bet = game_data["bets"].get(p)
            if bet:
                s, l = scores_diff.get(p, (0, ""))
                res = f"{bet[0]}→{bet[1]}→{bet[2]}"
                if s > 0: st.success(f"**{p}**: +{s} ({l})\n\n{res}")
                else: st.write(f"**{p}**: 0\n\n{res}")
            else: st.write(f"**{p}**: 未回答")
            
    if my_role == "host":
        st.write("---")
        if st.button("得点を加算して次へ", type="primary"):
            for p, (s, l) in scores_diff.items():
                if p in game_data["teams"]["A"]: game_data["team_scores"]["A"] += s
                if p in game_data["teams"]["B"]: game_data["team_scores"]["B"] += s
            
            if game_data["status"]["current_round"] >= game_data["config"]["total_rounds"]:
                game_data["phase"] = "game_over"
            else:
                game_data["status"]["current_round"] += 1
                game_data["phase"] = "round_input"
            save_data(game_data)
            st.rerun()
    else:
        st.write("---")
        st.info("ホストの進行を待っています...")
        show_refresh_button()

# ----------------------------------------
# 6. Game Over
# ----------------------------------------
elif phase == "game_over":
    st.balloons()
    st.title("🏆 最終結果")
    sa = game_data["team_scores"]["A"]
    sb = game_data["team_scores"]["B"]
    
    # チーム平均の計算
    team_a_size = len(game_data['teams']['A']) if len(game_data['teams']['A']) > 0 else 1
    team_b_size = len(game_data['teams']['B']) if len(game_data['teams']['B']) > 0 else 1
    
    avg_a = sa / team_a_size
    avg_b = sb / team_b_size
    
    c1, c2 = st.columns(2)
    c1.metric(f"🔴 {tn_a}", f"{sa} pts", f"平均: {avg_a:.2f}")
    c2.metric(f"🔵 {tn_b}", f"{sb} pts", f"平均: {avg_b:.2f}")
    
    st.markdown("---")
    st.subheader("チーム平均点で判定")
    
    if avg_a > avg_b: 
        st.markdown(f"# 👑 {tn_a} の優勝!")
        st.success(f"{tn_a} の平均点 {avg_a:.2f} > {tn_b} の平均点 {avg_b:.2f}")
    elif avg_b > avg_a: 
        st.markdown(f"# 👑 {tn_b} の優勝!")
        st.success(f"{tn_b} の平均点 {avg_b:.2f} > {tn_a} の平均点 {avg_a:.2f}")
    else: 
        st.markdown("# 🤝 引き分け!")
        st.info(f"両チームの平均点: {avg_a:.2f}")
    
    if my_role == "host":
        st.write("---")
        if st.button("最初に戻る", type="primary"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()
    else:
        st.write("---")
        st.info("ゲーム終了です。お疲れ様でした!")