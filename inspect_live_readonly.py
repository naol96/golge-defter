#!/usr/bin/env python3
"""Read-only SQLite diagnostic for a running Gölge Defter worker.

Does not write to the database, run migrations, start/stop workers, or change
positions. Works with older and newer schemas by inspecting present columns.
"""
import argparse
import datetime as dt
import sqlite3
from decimal import Decimal
from pathlib import Path

from contracts.models import ConstitutionRules

TZ = dt.timezone(dt.timedelta(hours=3))

def fmt_time(raw):
    if raw is None:
        return "—"
    try:
        return dt.datetime.fromtimestamp(int(raw), TZ).strftime('%Y-%m-%d %H:%M:%S TRT')
    except (TypeError, ValueError, OverflowError, OSError):
        return str(raw)

def columns(con, name):
    return [r[1] for r in con.execute(f'PRAGMA table_info("{name}")')]

def rows(con, name, cols, limit=5):
    pick = ','.join('"'+c+'"' for c in cols)
    return [dict(r) for r in con.execute(f'SELECT {pick} FROM "{name}" ORDER BY rowid DESC LIMIT ?', (limit,))]

def _paper_positions_table(tables: set[str]) -> str | None:
    if "paper_positions" in tables:
        return "paper_positions"
    if "positions" in tables:
        return "positions"
    return None


def _print_min_order_context(db: sqlite3.Connection, tables: set[str]) -> None:
    rules = ConstitutionRules()
    balance = None
    if "paper_state" in tables:
        row = db.execute("SELECT balance_usdt FROM paper_state WHERE id = 1").fetchone()
        if row:
            balance = Decimal(str(row[0]))
    if balance is None:
        print("  paper_state yok; anayasal tavan hesaplanamadı")
        return
    ceiling = balance * rules.max_position_fraction
    min_order = Decimal("10")
    open_n = 0
    pos_table = _paper_positions_table(tables)
    if pos_table:
        cs = columns(db, pos_table)
        if "status" in cs:
            open_n = db.execute(
                f'SELECT COUNT(*) FROM "{pos_table}" WHERE status = "OPEN"'
            ).fetchone()[0]
    print(f"  PAPER bakiye: {balance} USDT | anayasal tavan (%25): {ceiling} USDT")
    print(f"  Borsa min emir (adapter varsayılanı): {min_order} USDT")
    if ceiling < min_order:
        print(
            "  MIN_ORDER beklenen: tavan min emrin altında; yeni PAPER açılmaz "
            "(risk engeli değil, teknik blok)."
        )
    if open_n:
        print(f"  Açık PAPER pozisyon: {open_n} (bakiye düşük; demo analist hâlâ BUY verebilir).")
    if "shadow_evaluations" in tables:
        pending = db.execute(
            "SELECT COUNT(*) FROM shadow_evaluations WHERE status='PENDING'"
        ).fetchone()[0]
        if pending:
            print(
                f"  {pending} gölge değerlendirme PENDING; feed_source vade dolunca yazılır."
            )


def show_rows(con, table, preferred, limit=5):
    found = columns(con, table)
    if not found:
        print(f'  {table}: tablo yok (bu sürümde farklı ad kullanılabilir)')
        return
    present = [c for c in preferred if c in found]
    print(f'  {table} alanları: {", ".join(found)}')
    if present:
        for r in rows(con, table, present, limit):
            time_keys = (
                "ts",
                "created_at",
                "opened_at",
                "observed_ts",
                "target_ts",
                "target_15_ts",
                "target_60_ts",
            )
            print(
                '   ',
                ' | '.join(
                    f'{k}={fmt_time(v) if k in time_keys else v}' for k, v in r.items()
                ),
            )

def main():
    parser = argparse.ArgumentParser(description='Çalışan Gölge Defter için salt-okunur tanı')
    parser.add_argument('--db', default='data/golge.db')
    args = parser.parse_args()
    path = Path(args.db).resolve()
    if not path.is_file():
        parser.error(f'Dosya bulunamadı: {path} (boş DB oluşturulmadı)')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=3)
    db.row_factory = sqlite3.Row
    tables = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    print('DB:', path)
    print('Okuma modu: salt-okunur; worker üzerinde değişiklik YOK')
    print('Tablolar:', ', '.join(sorted(tables)))
    print('\n1. Karar sayıları / parite')
    if 'decisions' in tables:
        cs = columns(db, 'decisions')
        status = next((x for x in ['status', 'outcome', 'decision_status'] if x in cs), None)
        if 'symbol' in cs and status:
            for r in db.execute(f'SELECT symbol,"{status}" s,COUNT(*) n FROM decisions GROUP BY symbol,"{status}" ORDER BY symbol,s'):
                print(f'  {r[0]} / {r[1]}: {r[2]}')
        else:
            print('  Beklenen symbol/status alanları yok; örnek satırlar aşağıda')
    print('\n2. Son altı karar — min emir / tavan ilişkisi')
    if 'decisions' in tables:
        show_rows(db, 'decisions', [
            'id', 'ts', 'created_at', 'symbol', 'signal', 'status', 'outcome', 'rule',
            'balance_before', 'available_balance', 'notional', 'computed_notional',
            'min_order_usdt', 'min_order_evidence', 'spread_pct',
            'feed_source', 'market_source'], 6)
    print('\n3. PAPER açık pozisyonları')
    pos_table = _paper_positions_table(tables)
    if pos_table:
        cs = columns(db, pos_table)
        status = 'status' if 'status' in cs else None
        if status:
            print(
                '  Durumlar:',
                dict(
                    db.execute(
                        f'SELECT status,COUNT(*) FROM "{pos_table}" GROUP BY status'
                    ).fetchall()
                ),
            )
        show_rows(
            db,
            pos_table,
            [
                'id',
                'ts',
                'symbol',
                'notional_usdt',
                'notional',
                'entry_price',
                'entry_ask',
                'status',
                'opened_at',
                'feed_source',
                'market_source',
            ],
            3,
        )
    else:
        print('  positions / paper_positions tablosu yok')
    print('\n3b. Anayasa tavanı vs min emir')
    _print_min_order_context(db, tables)
    print('\n4. Gölge vade alanları ve değerlendirme örnekleri')
    for t in ('shadow_trades', 'shadow_evaluations', 'evaluations'):
        if t in tables:
            show_rows(db, t, ['id','trade_id','ts','symbol','category','status','horizon_min',
                              'target_ts','target_15_ts','target_60_ts','observed_ts',
                              'feed_source','market_source','validation_note','net_pnl'], 3)
    if 'shadow_trades' in tables:
        cs = columns(db, 'shadow_trades')
        for t in ('target_15_ts', 'target_60_ts'):
            if t in cs:
                found = db.execute(f'SELECT MIN("{t}") FROM shadow_trades WHERE "{t}" IS NOT NULL').fetchone()[0]
                print(f'  İlk {t}: {fmt_time(found)}')
    db.close()

if __name__ == '__main__':
    main()
