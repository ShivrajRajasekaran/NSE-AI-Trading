"""
Options Greeks Calculator — Black-Scholes Model
Computes Delta, Gamma, Theta, Vega, Rho for NSE options.
"""

import math
from scipy.stats import norm


def black_scholes_greeks(S, K, T, r, sigma, option_type="call"):
    """
    Calculate all Greeks for a European option.

    S: Spot price
    K: Strike price
    T: Time to expiry in years (e.g., 5 days = 5/365)
    r: Risk-free rate (e.g., 0.07 for 7%)
    sigma: Implied Volatility (e.g., 0.15 for 15%)
    option_type: "call" or "put"
    """
    if T <= 0:
        T = 0.0001

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                 - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
        rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
    else:
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                 + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
        rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100

    gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
    vega = S * norm.pdf(d1) * math.sqrt(T) / 100

    return {
        "price": round(price, 2),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),
        "vega": round(vega, 2),
        "rho": round(rho, 4),
        "iv": sigma,
        "d1": round(d1, 4),
        "d2": round(d2, 4),
    }


def implied_volatility(S, K, T, r, market_price, option_type="call", tol=0.0001, max_iter=100):
    """
    Calculate IV from market price using Newton-Raphson.
    """
    sigma = 0.3
    for _ in range(max_iter):
        greeks = black_scholes_greeks(S, K, T, r, sigma, option_type)
        diff = greeks["price"] - market_price
        if abs(diff) < tol:
            return round(sigma, 4)
        vega_raw = greeks["vega"] * 100
        if vega_raw < 0.01:
            break
        sigma -= diff / vega_raw
        sigma = max(0.01, min(sigma, 5.0))
    return round(sigma, 4)


def option_chain_greeks(spot, strikes, T, r, iv_map, option_type="call"):
    """
    Calculate Greeks for entire option chain.
    strikes: list of strike prices
    iv_map: dict {strike: iv} or single float for flat IV
    """
    results = []
    for K in strikes:
        iv = iv_map.get(K, iv_map) if isinstance(iv_map, dict) else iv_map
        greeks = black_scholes_greeks(spot, K, T, r, iv, option_type)
        results.append({"strike": K, **greeks})
    return results


if __name__ == "__main__":
    print("=== NIFTY OPTIONS GREEKS ===")
    print()
    spot = 24500
    strike = 24500
    days_to_expiry = 3
    T = days_to_expiry / 365
    r = 0.07
    iv = 0.13

    call = black_scholes_greeks(spot, strike, T, r, iv, "call")
    put = black_scholes_greeks(spot, strike, T, r, iv, "put")

    print(f"Spot: {spot} | Strike: {strike} | DTE: {days_to_expiry} | IV: {iv*100}%")
    print()
    print(f"CALL: Price=₹{call['price']} | Delta={call['delta']} | Gamma={call['gamma']} | Theta=₹{call['theta']}/day | Vega=₹{call['vega']}")
    print(f"PUT:  Price=₹{put['price']} | Delta={put['delta']} | Gamma={put['gamma']} | Theta=₹{put['theta']}/day | Vega=₹{put['vega']}")
