import streamlit as st
import re
import pandas as pd
import os

# Настройки страницы
st.set_page_config(
    page_title="🎾 Tennis Expert vs Market Analysis", 
    layout="wide",
    page_icon="🎾"
)

# Заголовок
st.title("🎾 Tennis Expert vs Market --- Full Analysis")
st.markdown("---")

OUTCOMES = ['2:0', '2:1', '1:2', '0:2']

def extract_matches(line):
    """Извлекает все фрагменты вида '1-(...)'"""
    return re.findall(r'\d+-\([^)]+\)', line)

def parse_match_part(part):
    """Парсит '1-(2:0,1:2)' → (номер_матча, ['2:0', '1:2'])"""
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
    """Парсит коэффициенты: '1\t1.65\t2.24' → {1: {'p1': 1.65, 'p2': 2.24}}"""
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
    # Подсчёт паттернов
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

def show_pattern_streamlit(data, title):
    """Аналог show_pattern для Streamlit"""
    st.subheader(title)
    found_matches = []
    for m in range(1, 15):
        cnt = data[m]
        if cnt > 0:
            found_matches.append(f"Матч {m}: {cnt} эксперт{'ов' if cnt != 1 else ''}")
    
    if found_matches:
        for match_info in found_matches:
            st.write(match_info)
    else:
        st.write("Не найдено.")
    st.write("")

def show_distribution_streamlit(match_totals):
    """Аналог show_distribution для Streamlit"""
    st.subheader("🔢 РАСПРЕДЕЛЕНИЕ ПРОГНОЗОВ ПО КАЖДОМУ МАТЧУ (1-14)")
    
    dist_data = []
    for m in range(1, 15):
        t = match_totals[m]
        total = sum(t.values())
        if total > 0:
            dist_data.append({
                'Матч': m,
                '2:0': t['2:0'],
                '2:1': t['2:1'],
                '1:2': t['1:2'],
                '0:2': t['0:2'],
                'Всего': total
            })
    
    if dist_data:
        df = pd.DataFrame(dist_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Данные не найдены")
    st.write("")

def show_value_bets_streamlit(match_totals, odds_data):
    """Аналог show_value_bets для Streamlit"""
    candidates = []
    for match_num in range(1, 15):
        if match_num not in odds_data:
            continue
            
        totals = match_totals[match_num]
        total_votes = sum(totals.values())
        if total_votes == 0:
            continue
            
        p2_expert = (totals['1:2'] + totals['0:2']) / total_votes
        votes_p2 = totals['1:2'] + totals['0:2']
        
        bk = odds_data[match_num]
        implied_total = 1/bk['p1'] + 1/bk['p2']
        fair_p2 = (1 / bk['p2']) / implied_total
        
        value_ratio = p2_expert / fair_p2
        
        min_votes = 10
        min_value = 1.15
        
        if p2_expert > fair_p2 and value_ratio >= min_value and votes_p2 >= min_votes:
            candidates.append({
                'Матч': match_num,
                'Поддержка П2': f"{p2_expert:.1%}",
                'Коэффициент П2': bk['p2'],
                'Подразумеваемая вероятность': f"{fair_p2:.1%}",
                'Value ratio': f"{value_ratio:.2f}x",
                'Голосов за П2': votes_p2,
                'Всего голосов': total_votes
            })
    
    candidates.sort(key=lambda x: float(x['Value ratio'].replace('x', '')), reverse=True)
    
    st.subheader("🏆 ТОП-6: СТАВКИ ПРОТИВ РЫНКА (эксперты > рынок)")
    
    if not candidates:
        st.info("⚠️ Не найдено ни одной ставки против рынка.")
    else:
        df = pd.DataFrame(candidates[:6])
        st.dataframe(df, use_container_width=True)
    st.write("")

def show_contrarian_bets_streamlit(match_totals, odds_data):
    """Аналог show_contrarian_bets для Streamlit"""
    candidates = []
    for match_num in range(1, 15):
        if match_num not in odds_data:
            continue
            
        totals = match_totals[match_num]
        total_votes = sum(totals.values())
        if total_votes == 0:
            continue
            
        p1_expert = (totals['2:0'] + totals['2:1']) / total_votes
        p2_expert = (totals['1:2'] + totals['0:2']) / total_votes
        
        bk = odds_data[match_num]
        implied_total = 1/bk['p1'] + 1/bk['p2']
        fair_p2 = (1 / bk['p2']) / implied_total
        
        if p1_expert > 0.70 and fair_p2 > 0.45 and fair_p2 > p2_expert * 1.1:
            candidates.append({
                'Матч': match_num,
                'Эксперты за П1': f"{p1_expert:.1%}",
                'Рынок за П2': f"{fair_p2:.1%}",
                'Коэффициент П2': bk['p2'],
                'Разница': f"{fair_p2 - p2_expert:+.1%}",
                'Всего голосов': total_votes
            })
    
    candidates.sort(key=lambda x: float(x['Разница'].replace('%', '').replace('+', '')), reverse=True)
    
    st.subheader("🛡️ ТОП-3: СТАВКИ ПРОТИВ ЭКСПЕРТОВ, НО ПО РЫНКУ")
    
    if not candidates:
        st.info("⚠️ Не найдено ни одного случая переоценки фаворита.")
    else:
        df = pd.DataFrame(candidates[:3])
        st.dataframe(df, use_container_width=True)
    st.write("")

# Интерфейс приложения
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔹 Прогнозы экспертов")
    st.caption("Формат: 1-(2:0); 2-(1:2,0:2); ...")
    expert_text = st.text_area(
        "Введите прогнозы:", 
        height=200,
        placeholder="1-(2:0,2:1)\n2-(1:2,0:2)\n3-(2:0)\n4-(0:2)\n5-(2:0)"
    )

with col2:
    st.subheader("🔹 Коэффициенты")
    st.caption("Формат: 1\\t1.65\\t2.24")
    odds_text = st.text_area(
        "Введите коэффициенты:", 
        height=200,
        placeholder="1\t1.65\t2.24\n2\t1.85\t2.00\n3\t1.70\t2.15"
    )

# Кнопка анализа
if st.button("🚀 Анализировать", type="primary", use_container_width=True):
    if not expert_text.strip():
        st.error("⚠️ Введите прогнозы экспертов!")
    else:
        with st.spinner("🔍 Анализируем данные..."):
            patterns, triple_patterns, match_totals, total_experts = analyze_data(expert_text)
            odds_data = parse_odds(odds_text)
            
            # Основная информация
            st.success(f"✅ Обработано экспертов: {total_experts}")
            
            # 🔴 Полная неопределённость
            show_pattern_streamlit(patterns['full_uncertainty'], "🔴 ПОЛНАЯ НЕОПРЕДЕЛЁННОСТЬ: -(2:0,2:1,1:2,0:2)")
            
            # 🟠 Борьба, возможен третий сет
            show_pattern_streamlit(patterns['battle_3set'], "🟠 БОРЬБА, ВОЗМОЖЕН ТРЕТИЙ СЕТ: -(1:2,0:2)")
            
            # 🟡 Небольшое преимущество второму
            show_pattern_streamlit(patterns['slight_advantage_away'], "🟡 НЕБОЛЬШОЕ ПРЕИМУЩЕСТВО ВТОРОМУ: -(2:1,0:2)")
            
            # 🟢 Равные шансы
            show_pattern_streamlit(patterns['close_fight'], "🟢 РАВНЫЕ ШАНСЫ: -(2:1,1:2)")
            
            # 🟣 Чёткий разброс
            show_pattern_streamlit(patterns['split_fav_vs_underdog'], "🟣 ЧЁТКИЙ РАЗБРОС: -(2:0,0:2)")
            
            # 🔵 Уверенность в фаворите, но с борьбой
            show_pattern_streamlit(patterns['fav_with_battle'], "🔵 УВЕРЕННОСТЬ В ФАВОРИТЕ, НО С БОРЬБОЙ: -(2:0,2:1)")
            
            # 🔹 Тройные комбинации
            triples_map = [
                (triple_patterns['triple_20_21_12'], '🔹 Фаворит, но с риском: -(2:0,2:1,1:2)'),
                (triple_patterns['triple_20_21_02'], '🔹 Фаворит может проиграть: -(2:0,2:1,0:2)'),
                (triple_patterns['triple_20_12_02'], '🔹 Фаворит: лёгкая победа или поражение: -(2:0,1:2,0:2)'),
                (triple_patterns['triple_21_12_02'], '🔹 Аутсайдер может победить любым способом: -(2:1,1:2,0:2)')
            ]
            
            for data, title in triples_map:
                show_pattern_streamlit(data, title)
            
            # 🔢 Распределение
            show_distribution_streamlit(match_totals)
            
            if not odds_data:
                st.warning("⚠️ Коэффициенты не загружены --- анализ пропущен.")
            else:
                # 🏆 Value ставки
                show_value_bets_streamlit(match_totals, odds_data)
                
                # 🛡️ Контр-ставки
                show_contrarian_bets_streamlit(match_totals, odds_data)

# Боковая панель с инструкцией
st.sidebar.title("📖 Инструкция")
st.sidebar.markdown("""
### Как использовать:

1. **Введите прогнозы** в левом поле: