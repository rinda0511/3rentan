import streamlit as st
import pandas as pd  # <-- 追加: データ集計・グラフ化用
import json
import os
import random

# --- データベース ---
DATA_FILE = "sanrentan_final.json"

def load_data():
    default_data = {
        "phase": "setup",       
        "config": {
            "total_rounds": 3,  
        },
        "status": {
            "current_round": 1,
        },
        "players": [],          
        "player_scores": {},    
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

def show_refresh_button(label="🔄 画面を更新"):
    if st.button(label):
        st.rerun()

def calculate_score(user_bet, correct_order):
    if not user_bet or isinstance(user_bet, str) or len(user_bet) < 3: 
        return 0, "なし"
    
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

game_data = load_data()


# ==========================================
# 0. ログイン管理
# ==========================================
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None 
    st.session_state["user_name"] = ""

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
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🗑️ プレイヤー管理")
        st.sidebar.caption("通信切断等で残ってしまったプレイヤーを削除できます")
        player_to_remove = st.sidebar.selectbox("削除するプレイヤーを選択", [""] + game_data["players"])
        if st.sidebar.button("プレイヤーを削除"):
            if player_to_remove in game_data["players"]:
                game_data["players"].remove(player_to_remove)
                if player_to_remove in game_data["player_scores"]:
                    del game_data["player_scores"][player_to_remove]
                if player_to_remove in game_data["bets"]:
                    del game_data["bets"][player_to_remove]
                save_data(game_data)
                st.sidebar.success(f"{player_to_remove} を削除しました")
                st.rerun()
                
    else:
        my_score = game_data["player_scores"].get(name, 0)
        st.sidebar.info(f"あなたの得点: **{my_score} pts**")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏆 現在のスコアランキング")
    
    sorted_scores = sorted(game_data["player_scores"].items(), key=lambda x: x[1], reverse=True)
    for i, (p_name, p_score) in enumerate(sorted_scores):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
        if p_score == 0 and i > 2: medal = "👤"
        st.sidebar.write(f"{medal} {p_name}: {p_score} pts")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("ログアウト"):
        st.session_state.clear()
        st.rerun()

# --- ログイン画面 ---
if st.session_state["user_role"] is None:
    st.title("🐇 サンレンタン (個人戦)")
    st.info("名前を入力してログインしてください")
    
    tab1, tab2 = st.tabs(["👤 プレイヤーとして参加", "🔑 ホストとして管理"])
    
    with tab1:
        input_name = st.text_input("あなたの名前(ニックネーム)", key="p_name")
        st.caption("※通信が切れた場合は、同じ名前を入力すれば元のスコアで復帰できます。")
        
        if st.button("ゲームに参加する", type="primary"):
            if input_name:
                if input_name not in game_data["players"]:
                    game_data["players"].append(input_name)
                    game_data["player_scores"][input_name] = 0
                    save_data(game_data)
                
                st.session_state["user_role"] = "player"
                st.session_state["user_name"] = input_name
                st.rerun()
            else:
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
# メイン画面
# ==========================================
st.title("🐇 サンレンタン (個人戦)")
phase = game_data["phase"]
my_role = st.session_state["user_role"]
my_name = st.session_state["user_name"]
current_round_num = game_data["status"]["current_round"]

if phase not in ["setup", "lobby", "game_over"]:
    curr = current_round_num
    total = game_data["config"]["total_rounds"]
    st.progress(curr/total, text=f"Round {curr} / {total}")


if phase == "setup":
    if my_role == "host":
        st.header("⚙️ 初期設定")
        rnd = st.number_input("ゲームの総ラウンド数", min_value=1, max_value=20, value=3)
        
        if st.button("設定完了してロビーを開く", type="primary"):
            game_data["config"]["total_rounds"] = rnd
            game_data["phase"] = "lobby"
            save_data(game_data)
            st.rerun()
    else:
        st.info("ホストが初期設定中です。しばらくお待ちください...")
        show_refresh_button()


elif phase == "lobby":
    st.header(f"👥 参加者待機中 ({len(game_data['players'])}人)")
    
    cols = st.columns(3)
    for idx, p in enumerate(game_data["players"]):
        cols[idx % 3].success(f"👤 {p}")
    
    st.write("---")
    if my_role == "host":
        st.write(f"予定ラウンド数: {game_data['config']['total_rounds']} 回戦")
        if st.button("🚀 ゲームスタート", type="primary"):
            game_data["phase"] = "round_input"
            save_data(game_data)
            st.rerun()
        
        st.caption("最新の参加状況を確認するには更新ボタンを押してください")
        show_refresh_button("🔄 参加者リストを更新")
    else:
        st.write("ホストの開始を待っています...")
        show_refresh_button()


elif phase == "round_input":
    r = current_round_num
    st.header(f"第 {r} ラウンド - お題入力")
    
    if my_role == "host":
        st.warning("⚠️ この画面は参加者に見せないでください")
        with st.form("input_form"):
            target = st.text_input("お題の人", placeholder="例: 佐藤さん")
            topic = st.text_input("お題テーマ", placeholder="例: 好きなランチメニュー")
            
            c1, c2, c3 = st.columns(3)
            a1 = c1.text_input("🥇 1位")
            a2 = c2.text_input("🥈 2位")
            a3 = c3.text_input("🥉 3位")
            
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
    else:
        st.info("ホストがお題を入力しています...")
        st.image("https://placehold.co/600x200?text=Waiting...", caption="待機中")
        show_refresh_button()


elif phase == "betting":
    rd = game_data["round_data"]
    st.subheader(f"お題: {rd['target_name']}さんの『{rd['topic']}』")
    
    if my_role == "player":
        my_bet = game_data["bets"].get(my_name)
        
        if my_bet:
            st.success("✅ 回答を受け付けました!")
            if my_bet == "SKIP":
                st.info("あなたはこのお題の対象者としてスキップしました。")
            else:
                st.write("あなたの予想:")
                st.info(f"🥇{my_bet[0]} ➡ 🥈{my_bet[1]} ➡ 🥉{my_bet[2]}")
            st.write("他のメンバーを待っています...")
            show_refresh_button()
        else:
            skip_key = f"skip_{current_round_num}"
            is_target = st.checkbox("🙋‍♀️ 私はこのお題の対象者です（回答をスキップ）", key=skip_key)
            
            with st.form(f"betting_form_{current_round_num}"):
                if is_target:
                    st.warning("お題の対象者は予想を行いません。「確定する」を押して待機してください。")
                    submitted = st.form_submit_button("スキップを確定する", type="primary")
                    if submitted:
                        game_data["bets"][my_name] = "SKIP"
                        save_data(game_data)
                        st.rerun()
                else:
                    st.write("選択肢から **1位・2位・3位** をそれぞれ選んでください")
                    col1, col2, col3 = st.columns(3)
                    
                    first = col1.selectbox("🥇 1位", [""] + rd["options"], key=f"first_{current_round_num}")
                    second = col2.selectbox("🥈 2位", [""] + rd["options"], key=f"second_{current_round_num}")
                    third = col3.selectbox("🥉 3位", [""] + rd["options"], key=f"third_{current_round_num}")
                    
                    submitted = st.form_submit_button("回答を確定する", type="primary")
                    
                    if submitted:
                        if first and second and third:
                            if len(set([first, second, third])) != 3:
                                st.error("❌ 同じ選択肢を複数回選ぶことはできません")
                            else:
                                game_data["bets"][my_name] = [first, second, third]
                                save_data(game_data)
                                st.rerun()
                        else:
                            st.error("❌ 1位、2位、3位をすべて選択してください")
                            
    elif my_role == "host":
        done = len(game_data["bets"])
        total = len(game_data["players"])
        st.metric("回答済み人数 (スキップ含む)", f"{done} / {total}")
        st.write("全員回答したら終了してください")
        
        if st.button("締め切って結果発表へ", type="primary"):
            game_data["phase"] = "result"
            save_data(game_data)
            st.rerun()
        
        st.caption("最新の回答状況を確認するには更新ボタンを押してください")
        show_refresh_button("🔄 回答状況を更新")


elif phase == "result":
    st.header("🎉 結果発表")
    rd = game_data["round_data"]
    correct = rd["correct_order"]
    
    st.subheader(f"お題: {rd['target_name']}さんの『{rd['topic']}』")
    c1, c2, c3 = st.columns(3)
    c1.error(f"🥇 正解 1位: {correct[0]}")
    c2.warning(f"🥈 正解 2位: {correct[1]}")
    c3.success(f"🥉 正解 3位: {correct[2]}")
    
    st.write("---")
    
    # --- 追加: 投票分布のグラフ表示 ---
    st.markdown("### 📊 みんなの予想分布")
    
    # 全選択肢ごとの投票数をカウントする辞書を作成
    vote_data = {opt: {"🥇 1位予想": 0, "🥈 2位予想": 0, "🥉 3位予想": 0} for opt in rd["options"]}
    
    for p, bet in game_data["bets"].items():
        if bet != "SKIP" and isinstance(bet, list) and len(bet) == 3:
            # 投票があった選択肢のカウントを増やす
            if bet[0] in vote_data: vote_data[bet[0]]["🥇 1位予想"] += 1
            if bet[1] in vote_data: vote_data[bet[1]]["🥈 2位予想"] += 1
            if bet[2] in vote_data: vote_data[bet[2]]["🥉 3位予想"] += 1
            
    # pandasのDataFrameに変換して、グラフを描画
    df_votes = pd.DataFrame(vote_data).T # 行を選択肢、列を順位にするために転置(T)
    st.bar_chart(df_votes)
    # ---------------------------------
    
    st.write("---")
    st.markdown("### 👤 個人の予想結果")
    
    scores_diff = {} 
    cols = st.columns(3) 
    for idx, p in enumerate(game_data["players"]):
        with cols[idx % 3]:
            bet = game_data["bets"].get(p)
            if bet == "SKIP":
                st.info(f"**{p}**\n\n🎯 お題の人 (スキップ)")
                scores_diff[p] = (0, "スキップ")
            elif bet:
                s, l = calculate_score(bet, correct)
                scores_diff[p] = (s, l)
                res = f"{bet[0]}→{bet[1]}→{bet[2]}"
                if s > 0: 
                    st.success(f"**{p}**: +{s} ({l})\n\n{res}")
                else: 
                    st.write(f"**{p}**: 0 pts\n\n{res}")
            else: 
                st.write(f"**{p}**: 未回答")
                scores_diff[p] = (0, "未回答")
            
    if my_role == "host":
        st.write("---")
        if st.button("得点を加算して次へ", type="primary"):
            for p, (s, l) in scores_diff.items():
                if p in game_data["player_scores"]:
                    game_data["player_scores"][p] += s
            
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


elif phase == "game_over":
    st.balloons()
    st.title("🏆 最終結果発表")
    
    final_ranking = sorted(game_data["player_scores"].items(), key=lambda x: x[1], reverse=True)
    
    if final_ranking:
        st.markdown(f"## 🥇 優勝: {final_ranking[0][0]} ({final_ranking[0][1]} pts)")
    
    st.markdown("### 総合ランキング")
    for i, (p_name, p_score) in enumerate(final_ranking):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}位"
        st.markdown(f"**{medal} : {p_name}** - {p_score} pts")
    
    if my_role == "host":
        st.write("---")
        if st.button("ゲームをリセットして最初に戻る", type="primary"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()
    else:
        st.write("---")
        st.info("ゲーム終了です。お疲れ様でした!")
        if st.button("ログアウトしてトップに戻る"):
            st.session_state.clear()
            st.rerun()