# app.py
import streamlit as st
import re
import pandas as pd

# Настройки страницы
st.set_page_config(page_title="🎾 Tennis Analysis", layout="wide")

# Заголовок
st.title("🎾 Tennis Expert vs Market Analysis")
st.markdown("---")

# Инициализация session state
if 'results' not in st.session_state:
    st.session_state.results = ""

OUTCOMES = ['2:0', '2:1', '1:2', '0:2']

def extract_matches(line):
    return re.findall(r'\d+-\([^)]+\)', line)

def parse_match_part(part):
    match = re.match(r'^(\d+)-\((.+)\)$', part.strip())
    if not match:
        return None, None
    num_str, outcome_str = match.groups()
    try:
        num = int(num_str)
        if 1 <= num <= 15:
            options = [o.strip() for o in outcome_str.split(',') if o.strip() in OUTCOMES]
            return num, options if options else None
        else:
            return None, None
    except:
        return None, None

def parse_odds(text):
    odds = {}
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or '\t' not in line:
            continue
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if len(parts) < 3:
            continue
        try:
            match_num = int(parts[0])
            p1 = float(parts[1])
            p2 = float(parts[2])
            odds[match_num] = {'p1': p1, 'p2': p2}
        except:
            continue
    return odds

def analyze_data(expert_text):
    patterns = {
        'full_uncertainty': {i: 0 for i in range(1, 16)},
        'battle_3set': {i: 0 for i in range(1, 16)},
        'slight_advantage_away': {i: 0 for i in range(1, 16)},
        'close_fight': {i: 0 for i in range(1, 16)},
        'split_fav_vs_underdog': {i: 0 for i in range(1, 16)},
        'fav_with_battle': {i: 0 for i in range(1, 16)}
    }
    
    triple_patterns = {
        'triple_20_21_12': {i: 0 for i in range(1, 16)},
        'triple_20_21_02': {i: 0 for i in range(1, 16)},
        'triple_20_12_02': {i: 0 for i in range(1, 16)},
        'triple_21_12_02': {i: 0 for i in range(1, 16)}
    }
    
    match_totals = {i: {'2:0': 0, '2:1': 0, '1:2': 0, '0:2': 0} for i in range(1, 16)}
    total_experts = 0
    
    lines = expert_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = extract_matches(line)
        if not parts:
            continue
            
        total_experts += 1
        
        for part in parts:
            match_num, options = parse_match_part(part)
            if match_num is None or options is None or match_num < 1 or match_num > 15:
                continue
                
            for outcome in options:
                if outcome in match_totals[match_num]:
                    match_totals[match_num][outcome] += 1
            
            s = set(options)
            if s == {'2:0', '2:1', '1:2', '0:2'}:
                patterns['full_uncertainty'][match_num] += 1
            elif s == {'1:2', '0:2'}:
                patterns['battle_3set'][match_num] += 1
            elif s == {'2:1', '0:2'}:
                patterns['slight_advantage_away'][match_num] += 1
            elif s == {'2:1', '1:2'}:
                patterns['close_fight'][match_num] += 1
            elif s == {'2:0', '0:2'}:
                patterns['split_fav_vs_underdog'][match_num] += 1
            elif s == {'2:0', '2:1'}:
                patterns['fav_with_battle'][match_num] += 1
            elif s == {'2:0', '2:1', '1:2'}:
                triple_patterns['triple_20_21_12'][match_num] += 1
            elif s == {'2:0', '2:1', '0:2'}:
                triple_patterns['triple_20_21_02'][match_num] += 1
            elif s == {'2:0', '1:2', '0:2'}:
                triple_patterns['triple_20_12_02'][match_num] += 1
            elif s == {'2:1', '1:2', '0:2'}:
                triple_patterns['triple_21_12_02'][match_num] += 1
    
    return patterns, triple_patterns, match_totals, total_experts

# Интерфейс
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔹 Прогнозы экспертов")
    st.caption("Формат: 1-(2:0); 2-(1:2,0:2); ...")
    expert_text = st.text_area("Введите прогнозы:", height=200, 
                              placeholder="1-(2:0,2:1)\n2-(1:2,0:2)\n3-(2:0)")

with col2:
    st.subheader("🔹 Коэффициенты")
    st.caption("Формат: 1\\t1.65\\t2.24")
    odds_text = st.text_area("Введите коэффициенты:", height=200,
                            placeholder="1\t1.65\t2.24\n2\t1.80\t2.00")

# Кнопка анализа
if st.button("🚀 Анализировать", type="primary"):
    if not expert_text.strip():
        st.error("Введите прогнозы экспертов!")
    else:
        with st.spinner("Анализируем данные..."):
            patterns, triple_patterns, match_totals, total_experts = analyze_data(expert_text)
            odds_data = parse_odds(odds_text)
            
            # Вывод результатов
            st.success(f"✅ Обработано экспертов: {total_experts}")
            
            # Таблица распределения
            st.subheader("📊 Распределение прогнозов")
            distribution_data = []
            for m in range(1, 15):
                t = match_totals[m]
                total = sum(t.values())
                if total > 0:
                    distribution_data.append({
                        'Матч': m,
                        '2:0': t['2:0'],
                        '2:1': t['2:1'],
                        '1:2': t['1:2'],
                        '0:2': t['0:2'],
                        'Всего': total
                    })
            
            if distribution_data:
                df = pd.DataFrame(distribution_data)
                st.dataframe(df, use_container_width=True)
            
            # Value bets
            if odds_data:
                st.subheader("🎯 Value ставки")
                candidates = []
                for match_num in range(1, 15):
                    if match_num not in odds_data:
                        continue
                    totals = match_totals[match_num]
                    total_votes = sum(totals.values())
                    if total_votes == 0:
                        continue
                    
                    p2_expert = (totals['1:2'] + totals['0:2']) / total_votes
                    bk = odds_data[match_num]
                    implied_total = 1/bk['p1'] + 1/bk['p2']
                    fair_p2 = (1 / bk['p2']) / implied_total
                    value_ratio = p2_expert / fair_p2
                    
                    if p2_expert > fair_p2 and value_ratio >= 1.15:
                        candidates.append({
                            'Матч': match_num,
                            'Поддержка П2': f"{p2_expert:.1%}",
                            'Коэф П2': bk['p2'],
                            'Value': f"{value_ratio:.2f}x"
                        })
                
                if candidates:
                    value_df = pd.DataFrame(candidates)
                    st.dataframe(value_df, use_container_width=True)
                else:
                    st.info("Value ставки не найдены")
            
            # Паттерны
            st.subheader("🔍 Паттерны")
            for pattern_name, pattern_data in patterns.items():
                pattern_matches = [m for m in range(1, 16) if pattern_data[m] > 0]
                if pattern_matches:
                    st.write(f"**{pattern_name}**: Матчи {pattern_matches}")

# requirements.txt для деплоя
st.sidebar.markdown("### 💡 Инструкция")
st.sidebar.info("""
1. Введите прогнозы экспертов в левом поле
2. Введите коэффициенты в правом поле  
3. Нажмите кнопку "Анализировать"
4. Получите результаты анализа
""")