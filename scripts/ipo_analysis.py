"""
IPO Analysis Engine for NSE/BSE
Evaluates IPO attractiveness: GMP, valuation vs peers, fundamentals,
promoter history, and listing gain probability.
"""


def analyze_ipo(ipo_data):
    """
    Complete IPO analysis.

    ipo_data: dict with keys:
        - name: Company name
        - price_band: tuple (low, high) or single price
        - lot_size: Minimum application lot
        - issue_size_cr: Issue size in crores
        - fresh_issue_cr: Fresh issue component
        - ofs_cr: Offer for sale component
        - gmp: Grey Market Premium in ₹
        - eps: Earnings per share (TTM)
        - revenue_cr: Annual revenue in crores
        - pat_cr: Profit after tax in crores
        - roe: Return on equity %
        - debt_equity: Debt to equity ratio
        - promoter_holding_post: Promoter holding post-issue %
        - peer_pe: Average P/E of listed peers
        - peer_names: list of peer company names
        - subscription_retail: Retail subscription (times)
        - subscription_hni: HNI subscription (times)
        - subscription_qib: QIB subscription (times)
        - sector: Industry sector
        - year_incorporated: Year of incorporation
        - objects: Purpose of issue (list)
    """
    valuation = analyze_valuation(ipo_data)
    fundamentals = analyze_fundamentals(ipo_data)
    demand = analyze_demand(ipo_data)
    gmp_analysis = analyze_gmp(ipo_data)
    risk_factors = identify_risks(ipo_data)
    score = calculate_ipo_score(valuation, fundamentals, demand, gmp_analysis, risk_factors)
    verdict = generate_ipo_verdict(score, valuation, demand, gmp_analysis)

    return {
        "company": ipo_data.get("name", "Unknown"),
        "price_band": ipo_data.get("price_band"),
        "lot_size": ipo_data.get("lot_size"),
        "investment_per_lot": calculate_investment(ipo_data),
        "valuation": valuation,
        "fundamentals": fundamentals,
        "demand": demand,
        "gmp": gmp_analysis,
        "risks": risk_factors,
        "score": score,
        "verdict": verdict,
    }


def analyze_valuation(data):
    """Compare IPO valuation with listed peers."""
    price = data.get("price_band", (0, 0))
    upper_price = price[1] if isinstance(price, (list, tuple)) else price
    eps = data.get("eps", 0)
    peer_pe = data.get("peer_pe", 0)

    if eps <= 0:
        ipo_pe = None
        pe_status = "LOSS-MAKING — no P/E comparison possible"
    else:
        ipo_pe = round(upper_price / eps, 2)
        if peer_pe > 0:
            discount = ((peer_pe - ipo_pe) / peer_pe) * 100
            if discount > 20:
                pe_status = f"CHEAP — {round(discount)}% discount to peers"
            elif discount > 0:
                pe_status = f"FAIR — {round(discount)}% discount to peers"
            elif discount > -20:
                pe_status = f"SLIGHTLY EXPENSIVE — {round(abs(discount))}% premium to peers"
            else:
                pe_status = f"EXPENSIVE — {round(abs(discount))}% premium to peers"
        else:
            pe_status = "No peer data for comparison"

    # Market cap at upper band
    pat = data.get("pat_cr", 0)
    issue_size = data.get("issue_size_cr", 0)
    market_cap_estimate = ipo_pe * pat if ipo_pe and pat else None

    # Revenue multiple
    revenue = data.get("revenue_cr", 0)
    price_to_sales = round(market_cap_estimate / revenue, 2) if market_cap_estimate and revenue else None

    return {
        "ipo_pe": ipo_pe,
        "peer_pe": peer_pe,
        "pe_status": pe_status,
        "market_cap_cr": round(market_cap_estimate, 0) if market_cap_estimate else None,
        "price_to_sales": price_to_sales,
        "peers": data.get("peer_names", []),
    }


def analyze_fundamentals(data):
    """Evaluate company fundamentals."""
    roe = data.get("roe", 0)
    debt_equity = data.get("debt_equity", 0)
    pat = data.get("pat_cr", 0)
    revenue = data.get("revenue_cr", 0)
    pat_margin = (pat / revenue * 100) if revenue > 0 else 0

    score = 0
    flags = []

    # ROE
    if roe > 20:
        score += 25
        flags.append(f"✅ Strong ROE: {roe}%")
    elif roe > 12:
        score += 15
        flags.append(f"⚠️ Moderate ROE: {roe}%")
    else:
        flags.append(f"❌ Weak ROE: {roe}%")

    # Debt
    if debt_equity < 0.5:
        score += 20
        flags.append(f"✅ Low debt: {debt_equity}x")
    elif debt_equity < 1.0:
        score += 10
        flags.append(f"⚠️ Moderate debt: {debt_equity}x")
    else:
        flags.append(f"❌ High debt: {debt_equity}x")

    # Profitability
    if pat > 0 and pat_margin > 15:
        score += 20
        flags.append(f"✅ Strong margin: {round(pat_margin, 1)}%")
    elif pat > 0:
        score += 10
        flags.append(f"⚠️ Thin margin: {round(pat_margin, 1)}%")
    else:
        flags.append("❌ Loss-making company")

    # Promoter holding
    promoter = data.get("promoter_holding_post", 0)
    if promoter > 60:
        score += 15
        flags.append(f"✅ High promoter holding: {promoter}%")
    elif promoter > 40:
        score += 10
        flags.append(f"⚠️ Moderate promoter: {promoter}%")
    else:
        flags.append(f"❌ Low promoter holding: {promoter}%")

    # Fresh issue vs OFS
    fresh = data.get("fresh_issue_cr", 0)
    ofs = data.get("ofs_cr", 0)
    total = fresh + ofs
    if total > 0:
        ofs_pct = (ofs / total) * 100
        if ofs_pct > 70:
            flags.append(f"❌ Mostly OFS ({round(ofs_pct)}%) — promoter exiting, not growth capital")
        elif ofs_pct > 40:
            flags.append(f"⚠️ Mixed ({round(ofs_pct)}% OFS)")
        else:
            score += 10
            flags.append(f"✅ Mostly fresh issue — growth capital")

    return {
        "score": min(100, score),
        "roe": roe,
        "debt_equity": debt_equity,
        "pat_margin": round(pat_margin, 1),
        "promoter_holding": promoter,
        "flags": flags,
    }


def analyze_demand(data):
    """Analyze subscription and demand indicators."""
    retail = data.get("subscription_retail", 0)
    hni = data.get("subscription_hni", 0)
    qib = data.get("subscription_qib", 0)

    if retail == 0 and hni == 0 and qib == 0:
        return {"status": "SUBSCRIPTION DATA NOT YET AVAILABLE"}

    total_weighted = retail * 0.2 + hni * 0.3 + qib * 0.5  # QIB matters most

    if qib > 10:
        demand_level = "BLOCKBUSTER"
    elif qib > 3:
        demand_level = "STRONG"
    elif qib > 1:
        demand_level = "MODERATE"
    else:
        demand_level = "WEAK"

    listing_probability = "HIGH" if total_weighted > 5 else "MODERATE" if total_weighted > 2 else "LOW"

    return {
        "retail": f"{retail}x",
        "hni": f"{hni}x",
        "qib": f"{qib}x",
        "demand_level": demand_level,
        "listing_gain_probability": listing_probability,
        "key_signal": "QIB" if qib > hni and qib > retail else "RETAIL" if retail > hni else "HNI",
        "interpretation": f"{'QIB leading — institutional confidence' if qib > 3 else 'Retail-driven — speculative demand' if retail > qib else 'Mixed demand'}",
    }


def analyze_gmp(data):
    """Analyze Grey Market Premium."""
    gmp = data.get("gmp", 0)
    price = data.get("price_band", (0, 0))
    upper_price = price[1] if isinstance(price, (list, tuple)) else price

    if upper_price == 0:
        return {"error": "No price data"}

    gmp_pct = (gmp / upper_price) * 100
    expected_listing = upper_price + gmp

    if gmp_pct > 50:
        outlook = "EXTREMELY POSITIVE — high listing expected"
    elif gmp_pct > 20:
        outlook = "POSITIVE — decent listing expected"
    elif gmp_pct > 5:
        outlook = "MODERATE — small listing gain expected"
    elif gmp_pct > 0:
        outlook = "MARGINAL — may list at par or slight premium"
    else:
        outlook = "NEGATIVE — listing below issue price likely"

    return {
        "gmp": gmp,
        "gmp_pct": round(gmp_pct, 1),
        "expected_listing_price": round(expected_listing, 2),
        "outlook": outlook,
        "reliability": "GMP is UNOFFICIAL — indicative only, can change rapidly before listing",
    }


def identify_risks(data):
    """Identify key risk factors."""
    risks = []

    # High valuation risk
    eps = data.get("eps", 0)
    price = data.get("price_band", (0, 0))
    upper_price = price[1] if isinstance(price, (list, tuple)) else price
    peer_pe = data.get("peer_pe", 0)

    if eps > 0 and peer_pe > 0:
        ipo_pe = upper_price / eps
        if ipo_pe > peer_pe * 1.3:
            risks.append({"risk": "VALUATION", "severity": "HIGH", "detail": f"IPO P/E ({round(ipo_pe)}) > Peer P/E ({peer_pe}) by {round((ipo_pe/peer_pe - 1)*100)}%"})

    # OFS heavy
    ofs = data.get("ofs_cr", 0)
    total = data.get("issue_size_cr", 0)
    if total > 0 and ofs / total > 0.7:
        risks.append({"risk": "PROMOTER EXIT", "severity": "HIGH", "detail": f"{round(ofs/total*100)}% is OFS — promoters cashing out"})

    # Debt
    if data.get("debt_equity", 0) > 2:
        risks.append({"risk": "HIGH DEBT", "severity": "MEDIUM", "detail": f"D/E ratio: {data['debt_equity']}"})

    # Loss-making
    if data.get("pat_cr", 0) <= 0:
        risks.append({"risk": "LOSS-MAKING", "severity": "HIGH", "detail": "Company not yet profitable"})

    # Low promoter holding
    if data.get("promoter_holding_post", 100) < 30:
        risks.append({"risk": "LOW PROMOTER SKIN", "severity": "MEDIUM", "detail": f"Only {data['promoter_holding_post']}% post-issue"})

    if not risks:
        risks.append({"risk": "NONE IDENTIFIED", "severity": "LOW", "detail": "No major red flags"})

    return risks


def calculate_ipo_score(valuation, fundamentals, demand, gmp, risks):
    """Composite IPO score (0-100)."""
    score = 0

    # Valuation (25)
    if valuation.get("ipo_pe") and valuation.get("peer_pe"):
        if valuation["ipo_pe"] < valuation["peer_pe"]:
            score += 25
        elif valuation["ipo_pe"] < valuation["peer_pe"] * 1.2:
            score += 15
        else:
            score += 5

    # Fundamentals (25)
    score += fundamentals.get("score", 0) * 0.25

    # Demand (25)
    demand_level = demand.get("demand_level", "")
    if demand_level == "BLOCKBUSTER":
        score += 25
    elif demand_level == "STRONG":
        score += 20
    elif demand_level == "MODERATE":
        score += 10

    # GMP (15)
    gmp_pct = gmp.get("gmp_pct", 0)
    if gmp_pct > 30:
        score += 15
    elif gmp_pct > 10:
        score += 10
    elif gmp_pct > 0:
        score += 5

    # Risk deduction (10)
    high_risks = sum(1 for r in risks if r["severity"] == "HIGH")
    score += max(0, 10 - high_risks * 5)

    return {
        "total": round(min(100, score)),
        "grade": "A+" if score >= 80 else "A" if score >= 65 else "B" if score >= 50 else "C" if score >= 35 else "D",
        "recommendation": "APPLY" if score >= 65 else "RISKY APPLY" if score >= 50 else "AVOID" if score < 35 else "WAIT & WATCH",
    }


def generate_ipo_verdict(score, valuation, demand, gmp):
    """One-line verdict."""
    grade = score["grade"]
    rec = score["recommendation"]
    gmp_pct = gmp.get("gmp_pct", 0)

    if grade in ("A+", "A"):
        return f"{rec} — Strong fundamentals + {demand.get('demand_level', 'good')} demand + GMP {gmp_pct}%"
    elif grade == "B":
        return f"{rec} — Moderate conviction, apply only if allocation likely"
    elif grade == "C":
        return f"{rec} — Weak case, better opportunities elsewhere"
    else:
        return f"{rec} — Multiple red flags, capital preservation first"


def calculate_investment(data):
    """Calculate investment per lot."""
    price = data.get("price_band", (0, 0))
    upper_price = price[1] if isinstance(price, (list, tuple)) else price
    lot_size = data.get("lot_size", 0)
    return round(upper_price * lot_size, 2)


if __name__ == "__main__":
    print("=== IPO ANALYSIS ENGINE ===\n")

    sample_ipo = {
        "name": "XYZ Technologies Ltd",
        "price_band": (450, 480),
        "lot_size": 31,
        "issue_size_cr": 1200,
        "fresh_issue_cr": 800,
        "ofs_cr": 400,
        "gmp": 120,
        "eps": 18.5,
        "revenue_cr": 3500,
        "pat_cr": 420,
        "roe": 22,
        "debt_equity": 0.4,
        "promoter_holding_post": 58,
        "peer_pe": 32,
        "peer_names": ["Infosys", "TCS", "HCL Tech"],
        "subscription_retail": 8.5,
        "subscription_hni": 25.3,
        "subscription_qib": 42.0,
        "sector": "IT Services",
        "objects": ["Expansion", "Working Capital", "Acquisitions"],
    }

    result = analyze_ipo(sample_ipo)

    print(f"Company: {result['company']}")
    print(f"Price Band: ₹{result['price_band'][0]}-{result['price_band'][1]} | Lot: {result['lot_size']} shares")
    print(f"Investment/Lot: ₹{result['investment_per_lot']:,.0f}")
    print(f"\n--- Valuation ---")
    print(f"IPO P/E: {result['valuation']['ipo_pe']} vs Peer P/E: {result['valuation']['peer_pe']}")
    print(f"Status: {result['valuation']['pe_status']}")
    print(f"\n--- Fundamentals (Score: {result['fundamentals']['score']}/100) ---")
    for f in result['fundamentals']['flags']:
        print(f"  {f}")
    print(f"\n--- Demand ---")
    print(f"  Retail: {result['demand']['retail']} | HNI: {result['demand']['hni']} | QIB: {result['demand']['qib']}")
    print(f"  Level: {result['demand']['demand_level']}")
    print(f"\n--- GMP ---")
    print(f"  GMP: ₹{result['gmp']['gmp']} ({result['gmp']['gmp_pct']}%)")
    print(f"  Expected Listing: ₹{result['gmp']['expected_listing_price']}")
    print(f"  Outlook: {result['gmp']['outlook']}")
    print(f"\n--- Risks ---")
    for r in result['risks']:
        print(f"  [{r['severity']}] {r['risk']}: {r['detail']}")
    print(f"\n{'='*50}")
    print(f"SCORE: {result['score']['total']}/100 (Grade: {result['score']['grade']})")
    print(f"VERDICT: {result['verdict']}")
    print(f"{'='*50}")
