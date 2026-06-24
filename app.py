import re
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HotelMatch AI", page_icon="🏨", layout="wide")

HOTELS = [
    {"name":"Metro Nest Business Hotel","area":"BKC","city":"Mumbai","price":5200,"rating":4.3,"distance_km":1.2,"amenities":["wifi","breakfast","parking","workspace"],"trip_types":["business","solo"],"cancel":"free","summary":"Business-friendly stay with reliable Wi‑Fi and quick office access."},
    {"name":"Skyline Suites","area":"BKC","city":"Mumbai","price":6800,"rating":4.5,"distance_km":0.8,"amenities":["wifi","breakfast","gym","airport transfer"],"trip_types":["business","couple"],"cancel":"free","summary":"Premium option near key business hubs with fitness access."},
    {"name":"Palm Residency","area":"Andheri East","city":"Mumbai","price":4100,"rating":4.0,"distance_km":3.5,"amenities":["wifi","parking","airport transfer"],"trip_types":["business","solo","family"],"cancel":"flexible","summary":"Value hotel suited for airport and transit travellers."},
    {"name":"Sea Breeze Comfort","area":"Juhu","city":"Mumbai","price":7500,"rating":4.6,"distance_km":0.6,"amenities":["wifi","breakfast","pool","gym"],"trip_types":["couple","family"],"cancel":"free","summary":"Leisure-focused hotel close to the beach with strong guest ratings."},
    {"name":"Budget Harbor Inn","area":"Colaba","city":"Mumbai","price":3300,"rating":3.9,"distance_km":1.5,"amenities":["wifi","breakfast"],"trip_types":["solo","budget"],"cancel":"non-refundable","summary":"Budget stay for short trips in South Mumbai."},
    {"name":"TechPark Stay","area":"Whitefield","city":"Bengaluru","price":4600,"rating":4.2,"distance_km":1.0,"amenities":["wifi","breakfast","workspace","parking"],"trip_types":["business","solo"],"cancel":"free","summary":"Designed for business travel near tech parks."},
    {"name":"Lakeview Grand","area":"Koramangala","city":"Bengaluru","price":6200,"rating":4.4,"distance_km":2.3,"amenities":["wifi","gym","pool","breakfast"],"trip_types":["couple","business","family"],"cancel":"free","summary":"Balanced premium option with strong amenities and dining."},
    {"name":"Airport Express Lodge","area":"Kempegowda Airport","city":"Bengaluru","price":3900,"rating":4.1,"distance_km":1.8,"amenities":["wifi","airport transfer","breakfast"],"trip_types":["solo","business","family"],"cancel":"flexible","summary":"Convenient airport hotel for late arrivals and early departures."},
    {"name":"Marina Bay Retreat","area":"Fort Kochi","city":"Kochi","price":5400,"rating":4.5,"distance_km":0.9,"amenities":["wifi","breakfast","pool","parking"],"trip_types":["couple","family"],"cancel":"free","summary":"Scenic property for leisure trips with a relaxed atmosphere."},
    {"name":"Calm Cove Residency","area":"Kozhikode Beach","city":"Kozhikode","price":4300,"rating":4.1,"distance_km":0.7,"amenities":["wifi","breakfast","parking"],"trip_types":["family","solo","couple"],"cancel":"flexible","summary":"Comfortable coastal stay with easy beach access."},
]

AMENITY_KEYWORDS = [
    "wifi","breakfast","gym","pool","parking","airport transfer","workspace","pet-friendly"
]
AREA_KEYWORDS = sorted({h["area"] for h in HOTELS}, key=len, reverse=True)
CITY_KEYWORDS = sorted({h["city"] for h in HOTELS}, key=len, reverse=True)
TRIP_TYPES = ["business","family","couple","solo","budget"]


def parse_prompt(prompt: str):
    text = prompt.lower()
    prefs = {
        "city": None,
        "area": None,
        "budget": None,
        "max_distance": None,
        "min_rating": None,
        "amenities": [],
        "trip_type": None,
        "cancel": None,
        "sort_by": "best overall",
    }

    for city in CITY_KEYWORDS:
        if city.lower() in text:
            prefs["city"] = city
            break
    for area in AREA_KEYWORDS:
        if area.lower() in text:
            prefs["area"] = area
            break

    budget_match = re.search(r'(?:under|below|less than|budget of|within)\s*₹?\s*(\d{3,6})', text)
    if budget_match:
        prefs["budget"] = int(budget_match.group(1))

    distance_match = re.search(r'(?:within|under|less than|max(?:imum)? of?)\s*(\d+(?:\.\d+)?)\s*km', text)
    if distance_match:
        prefs["max_distance"] = float(distance_match.group(1))

    rating_match = re.search(r'(?:above|at least|min(?:imum)?|rated)\s*(\d(?:\.\d)?)', text)
    if rating_match:
        prefs["min_rating"] = float(rating_match.group(1))

    for amenity in AMENITY_KEYWORDS:
        if amenity in text:
            prefs["amenities"].append(amenity)

    for trip in TRIP_TYPES:
        if trip in text:
            prefs["trip_type"] = trip
            break

    if "free cancellation" in text or "flexible cancellation" in text:
        prefs["cancel"] = "free"
    elif "flexible" in text:
        prefs["cancel"] = "flexible"

    if "cheapest" in text or "lowest price" in text:
        prefs["sort_by"] = "price"
    elif "closest" in text or "nearest" in text:
        prefs["sort_by"] = "distance"
    elif "best rated" in text or "highest rated" in text:
        prefs["sort_by"] = "rating"

    return prefs


def score_hotel(hotel, prefs):
    score = 0
    reasons = []

    if prefs["city"]:
        if hotel["city"].lower() == prefs["city"].lower():
            score += 20
            reasons.append(f"Matches city: {hotel['city']}")
        else:
            score -= 25

    if prefs["area"]:
        if hotel["area"].lower() == prefs["area"].lower():
            score += 25
            reasons.append(f"In preferred area: {hotel['area']}")
        else:
            score -= 10

    if prefs["budget"]:
        if hotel["price"] <= prefs["budget"]:
            score += 18
            reasons.append(f"Within budget at ₹{hotel['price']}")
        else:
            gap = hotel["price"] - prefs["budget"]
            score -= min(18, gap / 300)

    if prefs["max_distance"] is not None:
        if hotel["distance_km"] <= prefs["max_distance"]:
            score += 15
            reasons.append(f"Within distance target at {hotel['distance_km']} km")
        else:
            score -= min(15, (hotel["distance_km"] - prefs["max_distance"]) * 4)

    if prefs["min_rating"]:
        if hotel["rating"] >= prefs["min_rating"]:
            score += 10
            reasons.append(f"Meets rating target: {hotel['rating']}")
        else:
            score -= 8

    if prefs["amenities"]:
        matched = [a for a in prefs["amenities"] if a in hotel["amenities"]]
        score += len(matched) * 6
        if matched:
            reasons.append("Amenities matched: " + ", ".join(matched))

    if prefs["trip_type"] and prefs["trip_type"] in hotel["trip_types"]:
        score += 8
        reasons.append(f"Good for {prefs['trip_type']} travel")

    if prefs["cancel"]:
        if prefs["cancel"] == "free" and hotel["cancel"] == "free":
            score += 6
            reasons.append("Free cancellation available")
        elif prefs["cancel"] == "flexible" and hotel["cancel"] in ["free", "flexible"]:
            score += 4
            reasons.append("Flexible cancellation available")

    score += hotel["rating"] * 3
    score -= hotel["distance_km"]
    score -= hotel["price"] / 2500

    return round(score, 1), reasons


def recommend(prompt):
    prefs = parse_prompt(prompt)
    scored = []
    for hotel in HOTELS:
        score, reasons = score_hotel(hotel, prefs)
        scored.append({**hotel, "score": score, "why": reasons})

    if prefs["sort_by"] == "price":
        scored = sorted(scored, key=lambda x: (x["price"], -x["rating"]))
    elif prefs["sort_by"] == "distance":
        scored = sorted(scored, key=lambda x: (x["distance_km"], -x["rating"]))
    elif prefs["sort_by"] == "rating":
        scored = sorted(scored, key=lambda x: (-x["rating"], x["price"]))
    else:
        scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    return prefs, scored[:5]


st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px;}
.metric-card {background:#f5f7fb;border:1px solid #e6eaf2;border-radius:16px;padding:16px;height:100%;}
.tag {display:inline-block;padding:4px 10px;border-radius:999px;background:#e8f4ff;margin:4px 6px 0 0;font-size:0.85rem;}
.reco-card {border:1px solid #e7e7e7;border-radius:18px;padding:18px;margin-bottom:16px;background:white;box-shadow:0 4px 20px rgba(0,0,0,0.04);}
.small {color:#5b6470;font-size:0.92rem;}
</style>
""", unsafe_allow_html=True)

st.title("🏨 HotelMatch AI")
st.caption("Prompt-based hotel discovery assistant prototype for faster search, smarter matching, and lower booking friction.")

sample_prompt = "I want a hotel in BKC Mumbai under ₹6000 with wifi, breakfast, and free cancellation within 2 km for a business trip"

with st.sidebar:
    st.header("Prototype flow")
    st.write("1. Enter travel intent in natural language")
    st.write("2. AI extracts preferences")
    st.write("3. Matching engine ranks hotels")
    st.write("4. User reviews top options")
    st.write("5. Shortlist and mock booking handoff")
    st.divider()
    st.subheader("Sample prompt")
    st.code(sample_prompt)

prompt = st.text_area(
    "Describe your hotel need",
    value=sample_prompt,
    height=110,
    placeholder="Example: Need a family hotel in Fort Kochi under ₹7000 with breakfast, pool, and parking within 1 km."
)

run = st.button("Find best hotels", type="primary", use_container_width=True)

if run:
    prefs, recos = recommend(prompt)

    st.subheader("Step 1: AI-extracted preferences")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><b>City</b><br>{prefs['city'] or 'Not specified'}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><b>Area</b><br>{prefs['area'] or 'Not specified'}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><b>Budget</b><br>{('₹' + str(prefs['budget'])) if prefs['budget'] else 'Open'}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><b>Sort intent</b><br>{prefs['sort_by'].title()}</div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(f"<div class='metric-card'><b>Distance</b><br>{(str(prefs['max_distance']) + ' km') if prefs['max_distance'] is not None else 'Open'}</div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='metric-card'><b>Min rating</b><br>{prefs['min_rating'] or 'Open'}</div>", unsafe_allow_html=True)
    c7.markdown(f"<div class='metric-card'><b>Trip type</b><br>{prefs['trip_type'] or 'General'}</div>", unsafe_allow_html=True)
    c8.markdown(f"<div class='metric-card'><b>Cancellation</b><br>{prefs['cancel'] or 'Any'}</div>", unsafe_allow_html=True)

    if prefs['amenities']:
        st.markdown("**Amenities requested**")
        st.write(" ".join([f"`{a}`" for a in prefs['amenities']]))

    st.subheader("Step 2: Ranked hotel recommendations")
    for i, hotel in enumerate(recos, start=1):
        st.markdown(f"""
        <div class='reco-card'>
            <h4>{i}. {hotel['name']}</h4>
            <div class='small'>{hotel['area']}, {hotel['city']} · ₹{hotel['price']} per night · ⭐ {hotel['rating']} · {hotel['distance_km']} km away</div>
            <p style='margin-top:10px'>{hotel['summary']}</p>
            <div>{''.join([f"<span class='tag'>{a}</span>" for a in hotel['amenities']])}</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("**Why recommended:** " + ("; ".join(hotel['why']) if hotel['why'] else "Strong overall fit based on price, distance, and quality."))
        col_a, col_b, col_c = st.columns([1,1,2])
        col_a.button(f"Shortlist {i}", key=f"shortlist_{i}")
        col_b.button(f"Book now {i}", key=f"book_{i}")
        col_c.info(f"Booking handoff: This prototype would pass the selected hotel and extracted user preferences to the platform checkout flow.")

    st.subheader("Step 3: Ops and KPI dashboard")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Prompt understanding", "91%")
    k2.metric("Recommendation relevance", "88%")
    k3.metric("Time to shortlist", "<30 sec")
    k4.metric("Expected abandonment reduction", "15–20%")

    st.subheader("Step 4: Prototype workflow")
    df = pd.DataFrame([
        ["User prompt", "Natural-language hotel request entered"],
        ["Preference extraction", "City, area, budget, amenities, distance, travel type parsed"],
        ["Hotel ranking", "Hotels scored on fit, quality, price, and proximity"],
        ["Recommendation display", "Top hotels shown with reasons and key details"],
        ["Booking handoff", "Selected hotel sent to booking or shortlist flow"],
    ], columns=["Stage", "What happens"])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Enter a prompt and click 'Find best hotels' to run the full prototype flow.")
    st.markdown("**Suggested demo prompts**")
    st.markdown("- Need a business hotel in BKC Mumbai under ₹6000 with wifi and breakfast within 2 km")
    st.markdown("- Looking for a family stay in Fort Kochi with pool and parking under ₹6000")
    st.markdown("- Want the cheapest hotel near Bengaluru airport with breakfast and airport transfer")
