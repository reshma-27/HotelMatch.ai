import streamlit as st
import re
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(page_title='HotelMatch.ai', page_icon='🏨', layout='wide')

st.markdown('''
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1180px;}
.stApp {background: linear-gradient(180deg, #f6f8fb 0%, #eef3f8 100%);} 
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0ea5a4 100%);
    border-radius: 24px; padding: 28px 32px; color: white; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
}
.hero h1 {margin: 0; font-size: 2.2rem;}
.hero p {margin: 0.45rem 0 0 0; color: rgba(255,255,255,0.85); font-size: 1rem;}
.section-title {font-size: 1.08rem; font-weight: 700; color: #0f172a; margin: 0.5rem 0 0.9rem 0;}
.soft-card {
    background: rgba(255,255,255,0.88); border: 1px solid rgba(15,23,42,0.07); border-radius: 20px;
    padding: 18px; box-shadow: 0 10px 25px rgba(15,23,42,0.06);
}
.metric-card {
    background: white; border-radius: 18px; padding: 16px; border: 1px solid rgba(15,23,42,0.06);
    box-shadow: 0 8px 20px rgba(15,23,42,0.05);
}
.hotel-card {
    background: white; border-radius: 22px; padding: 18px; border: 1px solid rgba(15,23,42,0.06);
    box-shadow: 0 10px 24px rgba(15,23,42,0.06); margin-bottom: 16px;
}
.badge {
    display: inline-block; padding: 0.28rem 0.65rem; border-radius: 999px; margin: 0.2rem 0.35rem 0.2rem 0;
    background: #e6f7f6; color: #0f766e; font-size: 0.83rem; font-weight: 600; border: 1px solid #bce9e5;
}
.match-pill {
    display: inline-block; padding: 0.32rem 0.75rem; border-radius: 999px; background: #ecfeff; color: #155e75;
    font-size: 0.82rem; font-weight: 700; border: 1px solid #bae6fd;
}
.why-box {background: #f8fafc; border-radius: 14px; padding: 12px 14px; border: 1px dashed #cbd5e1; color: #334155; font-size: 0.92rem;}
.small-muted {color: #64748b; font-size: 0.92rem;}
.prompt-chip {
    display:inline-block; padding:0.45rem 0.7rem; margin:0.25rem 0.35rem 0 0; border-radius:999px; background:#fff;
    border:1px solid #dbe4ee; color:#1e293b; font-size:0.83rem;
}
</style>
''', unsafe_allow_html=True)

hotels = [
    {
        'name': 'Marina Grand Hotel', 'area': 'Kozhikode Beach', 'price': 5200, 'rating': 4.5,
        'distance_km': 1.2, 'amenities': ['wifi', 'breakfast', 'parking', 'sea view'], 'trip_types': ['couple', 'family', 'solo'],
        'description': 'Comfortable premium stay close to the beach with quick city access.'
    },
    {
        'name': 'Metro Business Inn', 'area': 'Railway Station', 'price': 3900, 'rating': 4.2,
        'distance_km': 0.8, 'amenities': ['wifi', 'breakfast', 'workspace', 'airport transfer'], 'trip_types': ['business', 'solo'],
        'description': 'Business-friendly property for short stays, meetings, and easy transit.'
    },
    {
        'name': 'Palm Residency', 'area': 'Mavoor Road', 'price': 4600, 'rating': 4.1,
        'distance_km': 2.4, 'amenities': ['wifi', 'parking', 'gym'], 'trip_types': ['business', 'family'],
        'description': 'Well-located city hotel with practical amenities for work and family travel.'
    },
    {
        'name': 'Airport Comfort Suites', 'area': 'Airport Road', 'price': 6100, 'rating': 4.6,
        'distance_km': 1.5, 'amenities': ['wifi', 'breakfast', 'airport transfer', 'pool'], 'trip_types': ['business', 'family', 'couple'],
        'description': 'Great for travelers prioritizing airport convenience and smooth transfers.'
    },
    {
        'name': 'Budget Stay Express', 'area': 'SM Street', 'price': 2800, 'rating': 3.9,
        'distance_km': 1.0, 'amenities': ['wifi', 'parking'], 'trip_types': ['solo', 'budget', 'business'],
        'description': 'Value-focused option for quick trips and budget-conscious travelers.'
    },
]

examples = [
    'Need a business hotel near airport under ₹6000 with Wi‑Fi and breakfast',
    'Looking for a family stay near Kozhikode Beach with parking and pool',
    'Want a budget hotel near railway station under ₹4000 with Wi‑Fi',
]


def parse_prompt(text: str):
    t = text.lower()
    prefs = {'budget': None, 'area': None, 'distance': None, 'amenities': [], 'trip_type': None, 'sort_by': 'best match'}
    budget_match = re.search(r'(?:under|below|less than|upto|up to)\s*[₹rs\.\s]*([0-9]{3,6})', t)
    if budget_match:
        prefs['budget'] = int(budget_match.group(1))

    distance_match = re.search(r'(?:within|under|less than)\s*([0-9]+(?:\.[0-9]+)?)\s*km', t)
    if distance_match:
        prefs['distance'] = float(distance_match.group(1))

    areas = ['kozhikode beach', 'railway station', 'mavoor road', 'airport road', 'airport', 'sm street']
    for a in areas:
        if a in t:
            prefs['area'] = a.title()
            break

    amenity_map = ['wifi', 'breakfast', 'parking', 'pool', 'gym', 'airport transfer', 'workspace', 'sea view']
    prefs['amenities'] = [a for a in amenity_map if a in t]

    for trip in ['business', 'family', 'couple', 'solo', 'budget']:
        if trip in t:
            prefs['trip_type'] = trip
            break

    if 'cheapest' in t or 'lowest price' in t:
        prefs['sort_by'] = 'price'
    elif 'closest' in t or 'nearest' in t:
        prefs['sort_by'] = 'distance'
    elif 'best rated' in t or 'highest rated' in t:
        prefs['sort_by'] = 'rating'

    return prefs


def score_hotel(hotel, prefs):
    score = 50
    reasons = []

    if prefs['budget']:
        if hotel['price'] <= prefs['budget']:
            score += 16
            reasons.append(f"Within budget at ₹{hotel['price']}")
        else:
            score -= min(18, (hotel['price'] - prefs['budget']) / 150)

    if prefs['area']:
        if prefs['area'].lower() in hotel['area'].lower():
            score += 18
            reasons.append(f"Located in preferred area: {hotel['area']}")

    if prefs['distance'] is not None:
        if hotel['distance_km'] <= prefs['distance']:
            score += 12
            reasons.append(f"Within preferred distance: {hotel['distance_km']} km")
        else:
            score -= 8

    if prefs['amenities']:
        matched = [a for a in prefs['amenities'] if a in hotel['amenities']]
        score += len(matched) * 5
        if matched:
            reasons.append('Matches amenities: ' + ', '.join(matched[:3]))

    if prefs['trip_type'] and prefs['trip_type'] in hotel['trip_types']:
        score += 10
        reasons.append(f"Good fit for {prefs['trip_type']} travel")

    score += (hotel['rating'] - 4.0) * 10
    return max(1, min(99, round(score))), reasons


def rank_hotels(prefs):
    ranked = []
    for h in hotels:
        s, reasons = score_hotel(h, prefs)
        ranked.append((s, reasons, h))

    if prefs['sort_by'] == 'price':
        ranked.sort(key=lambda x: (x[2]['price'], -x[0]))
    elif prefs['sort_by'] == 'distance':
        ranked.sort(key=lambda x: (x[2]['distance_km'], -x[0]))
    elif prefs['sort_by'] == 'rating':
        ranked.sort(key=lambda x: (-x[2]['rating'], -x[0]))
    else:
        ranked.sort(key=lambda x: (-x[0], x[2]['price']))
    return ranked


if 'prompt_text' not in st.session_state:
    st.session_state.prompt_text = examples[0]

st.markdown('''
<div class="hero">
  <h1>🏨 HotelMatch.ai</h1>
  <p>Describe your perfect stay in plain language. The assistant extracts preferences, ranks matching hotels, and explains every recommendation.</p>
</div>
''', unsafe_allow_html=True)

st.write('')
left, right = st.columns([1.55, 1])

with left:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Describe your stay</div>', unsafe_allow_html=True)
    prompt = st.text_area(
        'Enter your travel request',
        value=st.session_state.prompt_text,
        height=120,
        label_visibility='collapsed',
        placeholder='Example: Need a business hotel near airport under ₹6000 with Wi‑Fi and breakfast'
    )
    ex_cols = st.columns(3)
    for i, ex in enumerate(examples):
        if ex_cols[i].button(f'Use example {i+1}', use_container_width=True):
            st.session_state.prompt_text = ex
            st.rerun()
    search = st.button('Find best stays', type='primary', use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Why this feels better</div>', unsafe_allow_html=True)
    st.markdown('- Natural-language search instead of many filters')
    st.markdown('- Preference chips users can review quickly')
    st.markdown('- Transparent “why recommended” explanations')
    st.markdown('- Shortlist-style hotel cards with clear CTAs')
    st.markdown('<p class="small-muted">This prototype focuses on prompt → preference extraction → ranked recommendations.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

prefs = parse_prompt(prompt)
results = rank_hotels(prefs)

st.write('')
st.markdown('<div class="section-title">Extracted preferences</div>', unsafe_allow_html=True)
chip_html = []
if prefs['area']:
    chip_html.append(f'<span class="badge">📍 {prefs["area"]}</span>')
if prefs['budget']:
    chip_html.append(f'<span class="badge">💸 Under ₹{prefs["budget"]}</span>')
if prefs['distance'] is not None:
    chip_html.append(f'<span class="badge">📏 Within {prefs["distance"]} km</span>')
if prefs['trip_type']:
    chip_html.append(f'<span class="badge">🧳 {prefs["trip_type"].title()} trip</span>')
for a in prefs['amenities']:
    chip_html.append(f'<span class="badge">✅ {a.title()}</span>')
chip_html.append(f'<span class="badge">🔎 Sort: {prefs["sort_by"].title()}</span>')

st.markdown('<div class="soft-card">' + ''.join(chip_html if chip_html else ['<span class="small-muted">No clear filters detected yet. Try mentioning area, budget, amenities, or distance.</span>']) + '</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card"><div class="small-muted">Prompt understanding</div><h3>91%</h3></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><div class="small-muted">Recommendation relevance</div><h3>88%</h3></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="small-muted">Time to shortlist</div><h3>&lt;30 sec</h3></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><div class="small-muted">Expected abandonment reduction</div><h3>15–20%</h3></div>', unsafe_allow_html=True)

st.write('')
st.markdown('<div class="section-title">Recommended hotels</div>', unsafe_allow_html=True)

for idx, (score, reasons, hotel) in enumerate(results[:4], start=1):
    c1, c2 = st.columns([2.2, 1])
    with c1:
        amenities = ' · '.join([a.title() for a in hotel['amenities'][:4]])
        why = ' | '.join(reasons[:3]) if reasons else 'Strong overall fit based on rating, price, and convenience.'
        st.markdown(f'''
        <div class="hotel-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
                <div>
                    <div class="match-pill">Match score {score}%</div>
                    <h3 style="margin:10px 0 6px 0; color:#0f172a;">{idx}. {hotel['name']}</h3>
                    <div class="small-muted">{hotel['area']} · ⭐ {hotel['rating']} · {hotel['distance_km']} km away</div>
                    <p style="margin:10px 0 10px 0; color:#334155;">{hotel['description']}</p>
                    <div class="small-muted"><strong>Amenities:</strong> {amenities}</div>
                </div>
                <div style="text-align:right; min-width:120px;">
                    <div class="small-muted">Starting from</div>
                    <div style="font-size:1.5rem; font-weight:800; color:#0f172a;">₹{hotel['price']}</div>
                    <div class="small-muted">per night</div>
                </div>
            </div>
            <div class="why-box" style="margin-top:12px;"><strong>Why recommended:</strong> {why}</div>
        </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.markdown(f'**Quick actions**')
        st.button(f'Shortlist {idx}', key=f'short_{idx}', use_container_width=True)
        st.button(f'Compare {idx}', key=f'compare_{idx}', use_container_width=True)
        st.button(f'Book now {idx}', key=f'book_{idx}', type='primary', use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.write('')
st.markdown('<div class="soft-card"><div class="section-title">Prototype workflow</div><div class="small-muted">1. Traveler types request → 2. AI extracts budget, area, amenities, and travel intent → 3. Matching engine ranks hotels → 4. User reviews “why this match” → 5. User shortlists or books.</div></div>', unsafe_allow_html=True)
