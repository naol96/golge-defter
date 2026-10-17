"""Fully simulated examples; never actual market observations."""
from decimal import Decimal as D
from .risk import AnalystSignal, Constitution, MarketSnapshot, evaluate, tighten_position_limit


def main() -> None:
    print("[MOCK / SIMULATED] Gerçek OKX verisi veya emir icrası yoktur.")
    policy = Constitution()
    policy, warning = tighten_position_limit(policy, D("0.80"))
    print("Anayasa:", warning)
    t = 1_800_000_000
    scenarios = [
        ("Başarılı PAPER adayı", "AVAX-USDT", "BUY", "23.99", "24", "50", "10", "0"),
        ("Minimum lot engeli", "BTC-USDT", "BUY", "70000", "70050", "30", "10", "0"),
        ("Spread engeli", "ETH-USDT", "BUY", "2990", "3000", "80", "10", "0"),
        ("Pas gözlemi", "AVAX-USDT", "PASS", "23.99", "24", "50", "10", "0"),
    ]
    for label, pair, direction, bid, ask, balance, minimum, loss in scenarios:
        result = evaluate(constitution=policy,
                          signal=AnalystSignal(pair, direction, "MOCK teknik sinyal"),
                          market=MarketSnapshot(pair, D(bid), D(ask), t),
                          available_usdt=D(balance), min_order_usdt=D(minimum),
                          daily_realized_loss_usdt=D(loss), now=t)
        print(f"{label}: {result.status}, tutar={result.constitutional_amount_usdt} USDT, kural={result.rule}")


if __name__ == "__main__":
    main()
