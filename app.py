import streamlit as st
import re
import io

# Настройки страницы
st.set_page_config(
    page_title="🎾 Tennis Expert vs Market Analysis", 
    layout="wide",
    page_icon="🎾"
)

st.title("🎾 Tennis Expert vs Market --- Full Analysis")
st.markdown("---")

OUTCOMES = ['2:0', '2:1', '1:2', '0:2']
MIN_ODDS = 1.45  # Исключаем коэффициенты ≤ 1.45

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

def find_value_bets(match_totals, odds_data):
    candidates = []
    min_votes = 10
    min_value = 1.15

    for match_num in range(1, 15):
        if match_num not in odds_data:
            continue
            
        totals = match_totals[match_num]
        total_votes = sum(totals.values())
        if total_votes == 0:
            continue

        bk = odds_data[match_num]
        implied_total = 1/bk['p1'] + 1/bk['p2']

        # === Анализ П1 ===
        if bk['p1'] > MIN_ODDS:  # Только если коэффициент > 1.45
            p1_expert = (totals['2:0'] + totals['2:1']) / total_votes
            votes_p1 = totals['2:0'] + totals['2:1']
            fair_p1 = (1 / bk['p1']) / implied_total
            value_ratio_p1 = p1_expert / fair_p1

            if p1_expert > fair_p1 and value_ratio_p1 >= min_value and votes_p1 >= min_votes:
                candidates.append({
                    'match': match_num,
                    'side': 'П1',
                    'exp_prob': p1_expert,
                    'fair_prob': fair_p1,
                    'odd': bk['p1'],
                    'value': value_ratio_p1,
                    'votes': votes_p1,
                    'total': total_votes
                })

        # === Анализ П2 ===
        if bk['p2'] > MIN_ODDS:
            p2_expert = (totals['1:2'] + totals['0:2']) / total_votes
            votes_p2 = totals['1:2'] + totals['0:2']
            fair_p2 = (1 / bk['p2']) / implied_total
            value_ratio_p2 = p2_expert / fair_p2

            if p2_expert > fair_p2 and value_ratio_p2 >= min_value and votes_p2 >= min_votes:
                candidates.append({
                    'match': match_num,
                    'side': 'П2',
                    'exp_prob': p2_expert,
                    'fair_prob': fair_p2,
                    'odd': bk['p2'],
                    'value': value_ratio_p2,
                    'votes': votes_p2,
                    'total': total_votes
                })

    # Сортируем по value ratio (лучшие — первые)
    candidates.sort(key=lambda x: x['value'], reverse=True)
    return candidates

def format_output(patterns, triple_patterns, match_totals, total_experts, odds_data):
    output = io.StringIO()
    output.write(f"Обработано экспертов: {total_experts}\n\n")

    # === Паттерны (без изменений) ===
    pattern_list = [
        ('full_uncertainty', "🔴 ПОЛНАЯ НЕОПРЕДЕЛЁННОСТЬ: -(2:0,2:1,1:2,0:2)"),
        ('battle_3set', "🟠 БОРЬБА, ВОЗМОЖЕН ТРЕТИЙ СЕТ: -(1:2,0:2)"),
        ('slight_advantage_away', "🟡 НЕБОЛЬШОЕ ПРЕИМУЩЕСТВО ВТОРОМУ: -(2:1,0:2)"),
        ('close_fight', "🟢 РАВНЫЕ ШАНСЫ: -(2:1,1:2)"),
        ('split_fav_vs_underdog', "🟣 ЧЁТКИЙ РАЗБРОС: -(2:0,0:2)"),
        ('fav_with_battle', "🔵 УВЕРЕННОСТЬ В ФАВОРИТЕ, НО С БОРЬБОЙ: -(2:0,2:1)")
    ]

    for key, title in pattern_list:
        output.write(f"{title}\n")
        output.write("=" * 80 + "\n")
        found = False
        for m in range(1, 15):
            cnt = patterns[key][m]
            if cnt > 0:
                output.write(f"Матч {m}: {cnt} эксперт{'ов' if cnt != 1 else ''}\n")
                found = True
        if not found:
            output.write("Не найдено.\n")
        output.write("\n")

    # === Тройные комбинации ===
    triples_map = [
        (triple_patterns['triple_20_21_12'], '🔹 Фаворит, но с риском: -(2:0,2:1,1:2)'),
        (triple_patterns['triple_20_21_02'], '🔹 Фаворит может проиграть: -(2:0,2:1,0:2)'),
        (triple_patterns['triple_20_12_02'], '🔹 Фаворит: лёгкая победа или поражение: -(2:0,1:2,0:2)'),
        (triple_patterns['triple_21_12_02'], '🔹 Аутсайдер может победить любым способом: -(2:1,1:2,0:2)')
    ]
    
    for data, title in triples_map:
        output.write(f"{title}\n")
        output.write("=" * 80 + "\n")
        found = False
        for m in range(1, 15):
            cnt = data[m]
            if cnt > 0:
                output.write(f"Матч {m}: {cnt} эксперт{'ов' if cnt != 1 else ''}\n")
                found = True
        if not found:
            output.write("Не найдено.\n")
        output.write("\n")

    # === Распределение ===
    output.write("🔢 РАСПРЕДЕЛЕНИЕ ПРОГНОЗОВ ПО КАЖДОМУ МАТЧУ (1--14)\n")
    output.write("=" * 80 + "\n")
    header = f"{'№':<3} {'2:0':<6} {'2:1':<6} {'1:2':<6} {'0:2':<6} {'Σ':<6}"
    output.write(header + "\n")
    output.write("-" * 80 + "\n")
    for m in range(1, 15):
        t = match_totals[m]
        total = sum(t.values())
        if total > 0:
            line = f"{m:<3} {t['2:0']:<6} {t['2:1']:<6} {t['1:2']:<6} {t['0:2']:<6} {total:<6}"
            output.write(line + "\n")
    output.write("\n")

    # === ОСНОВНОЙ ВЫВОД: ТОП-6 ВАЛУЙНЫХ СТАВОК ===
    if not odds_data:
        output.write("⚠️ Коэффициенты не загружены --- анализ пропущен.\n\n")
    else:
        candidates = find_value_bets(match_totals, odds_data)
        output.write("🏆 ТОП-6: ЛУЧШИЕ ВАЛУЙНЫЕ СТАВКИ (П1 и П2, коэф. > 1.45)\n")
        output.write("=" * 80 + "\n")
        
        if not candidates:
            output.write("⚠️ Не найдено ни одной валуйной ставки.\n\n")
        else:
            for i, c in enumerate(candidates[:6], 1):
                output.write(f"{i}. МАТЧ {c['match']} → СТАВКА НА {c['side']}:\n")
                output.write(f" 📊 Поддержка: {c['votes']}/{c['total']} ({c['exp_prob']:.1%})\n")
                output.write(f" 📈 Коэффициент: {c['odd']} → подразумевает {c['fair_prob']:.1%}\n")
                output.write(f" 🎯 Value ratio: {c['value']:.2f}x\n\n")

    return output.getvalue()

# === Интерфейс ===
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔹 Прогнозы экспертов")
    st.caption("Формат: 1-(2:0); 2-(1:2,0:2); ...")
    expert_text = st.text_area(
        "Введите прогнозы:", 
        height=200,
        placeholder="1-(2:0,2:1)\n2-(1:2,0:2)\n3-(2:0)\n4-(0:2)"
    )

with col2:
    st.subheader("🔹 Коэффициенты")
    st.caption("Формат: 1\\t1.65\\t2.24")
    odds_text = st.text_area(
        "Введите коэффициенты:", 
        height=200,
        placeholder="1\t1.65\t2.24\n2\t1.85\t2.00"
    )

if st.button("🚀 Анализировать", type="primary", use_container_width=True):
    if not expert_text.strip():
        st.error("⚠️ Введите прогнозы экспертов!")
    else:
        with st.spinner("🔍 Анализируем данные..."):
            patterns, triple_patterns, match_totals, total_experts = analyze_data(expert_text)
            odds_data = parse_odds(odds_text)
            result_text = format_output(patterns, triple_patterns, match_totals, total_experts, odds_data)
            
            st.success(f"✅ Анализ завершён! Обработано экспертов: {total_experts}")
            st.subheader("📋 Результаты анализа")
            st.text_area("Результат:", value=result_text, height=600, key="results")
            
            st.download_button(
                label="📥 Скачать отчёт",
                data=result_text,
                file_name="tennis_analysis_report.txt",
                mime="text/plain"
            )

# === Инструкция ===
st.sidebar.title("📖 Инструкция")
st.sidebar.markdown("""
### Как использовать:
1. Введите прогнозы экспертов (слева)
2. Введите коэффициенты через **табуляцию** (справа)
3. Нажмите **«Анализировать»**
4. Получите **ТОП-6 рекомендаций** с чётким указанием: **П1 или П2**

💡 Алгоритм:
- Исключает коэффициенты ≤ 1.45 (низкая эффективность),
- Ищет расхождения между экспертами и рынком,
- Выбирает **6 лучших ставок из 14 матчей**.
""")
