from cat.mad_hatter.decorators import tool
import yfinance as yf


@tool
def buffett_analysis(ticker, cat):
    """Analyzes a publicly traded company using Warren Buffett's value investing principles. Input: ticker symbol (e.g., AAPL)."""

    # Fetch company data from Yahoo Finance
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow

    # Step 1: Profitability (ROE calculation)
    try:
        net_income = financials.loc["Net Income"].iloc[0] if "Net Income" in financials.index else \
        financials.loc["Net Income Common Stockholders"].iloc[0]
        equity = balance_sheet.loc["Total Stockholder Equity"].iloc[
            0] if "Total Stockholder Equity" in balance_sheet.index else balance_sheet.loc["Common Stock Equity"].iloc[
            0]
        roe = (net_income / equity) * 100
        roe_comment = f"ROE: {roe:.2f}% - " + (
            "solid, aligns with Buffett's standards." if roe > 15 else "low, below Buffett's target.")
    except Exception as e:
        roe_comment = f"Error calculating ROE: {str(e)}."

    # Step 2: Intrinsic Value (Simplified DCF)
    try:
        # Ensure Free Cash Flow is positive and available
        free_cash_flow = cash_flow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cash_flow.index else 0
        if free_cash_flow <= 0:
            raise ValueError(f"Free Cash Flow is non-positive ({free_cash_flow}), invalid for DCF.")

        # Dynamic growth rate, capped conservatively
        fcf_history = cash_flow.loc["Free Cash Flow"].iloc[:3].dropna()
        growth_rate = (fcf_history.pct_change().mean() + 1) if len(fcf_history) > 1 else 0.07
        discount_rate = 0.09  # 9% discount rate
        growth_rate = min(max(growth_rate, 0.03), 0.07)  # Cap at 7% for realism

        # Debug: Print key inputs
        print(f"FCF: {free_cash_flow}, Growth Rate: {growth_rate}, Discount Rate: {discount_rate}")

        # Calculate intrinsic value over 10 years
        intrinsic_value = 0
        for year in range(1, 11):
            intrinsic_value += free_cash_flow * (1 + growth_rate) ** year / (1 + discount_rate) ** year

        # Terminal value using perpetuity growth
        terminal_value = (free_cash_flow * (1 + growth_rate) ** 10) / (discount_rate - growth_rate)
        intrinsic_value += terminal_value / (1 + discount_rate) ** 10

        # Per-share value and margin of safety
        shares_outstanding = info.get("sharesOutstanding", 1)
        intrinsic_per_share = intrinsic_value / shares_outstanding
        current_price = info.get("currentPrice", 0)

        # Sanity check
        if intrinsic_per_share < 0:
            raise ValueError(f"Negative intrinsic value (${intrinsic_per_share:.2f}) detected.")
        if intrinsic_per_share > current_price * 5:  # Unrealistically high?
            print(f"Warning: Intrinsic value (${intrinsic_per_share:.2f}) seems unusually high.")

        margin_of_safety = (intrinsic_per_share - current_price) / intrinsic_per_share * 100
        price_comment = (
            f"Intrinsic value: ${intrinsic_per_share:.2f}/share (estimated growth: {growth_rate * 100:.1f}%). "
            f"Current price: ${current_price:.2f}. Margin: {margin_of_safety:.2f}%."
        )
    except Exception as e:
        price_comment = f"Error calculating intrinsic value: {str(e)}."

    # Step 3: Economic Moat (Profit margins and debt check)
    moat_comment = "Moat evaluation: "
    profit_margin = info.get("profitMargins", 0)
    debt_to_equity = info.get("debtToEquity", 1000)
    if profit_margin > 0.20 and debt_to_equity < 50:
        moat_comment += "High margins and low debt suggest a strong competitive advantage."
    elif profit_margin > 0.20:
        moat_comment += "High margins, but debt needs further evaluation."
    else:
        moat_comment += "Low margins or high debt, weak moat."

    # Final result
    result = (
        f"{ticker} according to Buffett:\n"
        f"1. Profitability: {roe_comment}\n"
        f"2. Valuation: {price_comment}\n"
        f"3. Economic Moat: {moat_comment}\n"
        f"Conclusion: "
    )
    if "Error" not in roe_comment and "Error" not in price_comment:
        if margin_of_safety > 25 and roe > 15:
            result += "Undervalued - great opportunity!"
        elif margin_of_safety < -10:
            result += "Overvalued - avoid."
        else:
            result += "Fairly priced - further evaluation needed."
    else:
        result += "Insufficient data for a reliable conclusion."

    return result