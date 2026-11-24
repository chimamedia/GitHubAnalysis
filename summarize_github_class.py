#!/usr/bin/env python3
"""授業用: github_report/<班名>/<班名>_commits.csv を学生別に集計してCSV/HTMLを作成．標準ライブラリのみ．"""
import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import sys

max_size = sys.maxsize

while True:
    try:
        csv.field_size_limit(max_size)
        break
    except OverflowError:
        max_size //= 10
        

REQUIRED = {'開発者', 'メールアドレス', '日時', '作業メモ', '変更ファイル一覧', '追加行数', '削除行数'}


def read_csv(path):
    with path.open('r', encoding='utf-8-sig', newline='') as fp:
        reader = csv.DictReader(fp)
        if not reader.fieldnames or not REQUIRED.issubset(set(reader.fieldnames)):
            missing = sorted(REQUIRED - set(reader.fieldnames or []))
            raise ValueError(f'必要な列がありません: {missing}')
        return list(reader)

def write_csv(path, items, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(items)

def num(v):
    try: return int(float(str(v).replace(',', '').strip()))
    except (ValueError, TypeError): return 0

def date_of(raw):
    try: return datetime.fromisoformat(raw.replace('Z', '+00:00')).date().isoformat()
    except (ValueError, AttributeError): return str(raw)[:10]

def sample_memos(rows, limit):
    """同じ作業メモの重複を除いた，直近の代表例（AI再実行はしない）．"""
    memos = []
    seen = set()
    for c in sorted(rows, key=lambda c: c.get('日時', ''), reverse=True):
        memo = (c.get('作業メモ') or c.get('コミットメッセージ') or '').strip()
        if memo and memo not in seen:
            memos.append(memo.replace('\n', ' ')[:240]); seen.add(memo)
        if len(memos) >= limit: break
    return memos

def cell(s): return html.escape(str(s), quote=True)

def create_html(out, summary, all_rows, groups, memo_limit):
    by_team = defaultdict(list)
    for r in summary: by_team[r['班名']].append(r)
    blocks = []
    for team in sorted(by_team):
        students = sorted(by_team[team], key=lambda x: -x['コミット数'])
        max_count = max([s['コミット数'] for s in students] or [1]) or 1
        cards = []
        for s in students:
            percent = 100 * s['コミット数'] / max_count
            key = (team, s['識別子'])
            memos = sample_memos(groups[key], memo_limit)
            items = ''.join(f'<li>{cell(m)}</li>' for m in memos) or '<li>作業メモなし</li>'
            cards.append(f'''<article class="student"><div class="student-head"><b>{cell(s['開発者'])}</b><span>{cell(s['メールアドレス'])}</span></div>
              <div class="metrics"><span>コミット <strong>{s['コミット数']}</strong></span><span>活動日 <strong>{s['活動日数']}</strong></span><span>追加 <strong>+{s['追加行数']:,}</strong></span><span>削除 <strong>-{s['削除行数']:,}</strong></span><span>ファイル種類 <strong>{s['変更ファイル種類数']}</strong></span></div>
              <div class="bar"><div style="width:{percent:.2f}%"></div></div>
              <details><summary>作業メモ・直近{len(memos)}件</summary><ul>{items}</ul></details></article>''')
        total = sum(s['コミット数'] for s in students)
        blocks.append(f'<section class="team"><h2>{cell(team)} <small>{len(students)}名・{total}コミット</small></h2>{"".join(cards)}</section>')
    page = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GitHub 授業開発活動レポート</title>
<style>:root{font-family:system-ui,"Yu Gothic",sans-serif;color:#17243a;background:#f4f7fb}body{max-width:1150px;margin:30px auto;padding:0 18px}h1{margin-bottom:5px}p{color:#53647b}h2{margin-top:0}.team{background:white;border-radius:14px;padding:22px;margin:26px 0;box-shadow:0 4px 18px #18345713}.team small{color:#677b92;font-size:14px;font-weight:400}.student{padding:18px 0;border-top:1px solid #e6eaf0}.student-head{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.student-head span{color:#708096;font-size:12px}.metrics{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;margin-top:12px}.metrics strong{font-size:18px;margin-left:5px}.bar{height:11px;background:#e7edf6;border-radius:9px;margin:12px 0;overflow:hidden}.bar div{height:100%;background:linear-gradient(90deg,#2563eb,#39a9c6);border-radius:9px}details{font-size:13px;color:#354760}details summary{cursor:pointer;font-weight:600}li{margin:7px 0;line-height:1.55}#filter{font:inherit;padding:10px;border:1px solid #bac5d4;border-radius:8px;width:min(100%,380px)}</style></head><body>
<h1>GitHub 開発活動レポート</h1><p>コミット履歴ベースの活動量です．行数・コミット数だけで貢献度や成績を判定しないでください．</p>
<input id="filter" placeholder="班名・開発者名で絞り込み" oninput="filterRows()">
''' + ''.join(blocks) + '''<script>function filterRows(){let q=document.querySelector('#filter').value.toLowerCase();document.querySelectorAll('.team').forEach(t=>{let cards=[...t.querySelectorAll('.student')];let team=t.querySelector('h2').textContent.toLowerCase();cards.forEach(c=>c.hidden=!(team.includes(q)||c.querySelector('.student-head').textContent.toLowerCase().includes(q)));t.hidden=cards.every(c=>c.hidden);});}</script></body></html>'''
    out.write_text(page, encoding='utf-8')

def main():
    p = argparse.ArgumentParser(description='班ごとの *_commits.csv を開発者別に集計・可視化します')
    p.add_argument('--input', default='github_report', help='各班フォルダを含む親フォルダ')
    p.add_argument('--output', default=None, help='集計結果の保存先（省略時は input/_class_summary）')
    p.add_argument('--aliases', default=None, help='同一学生の複数メールアドレス等の名寄せJSON')
    p.add_argument('--since', help='集計開始日 YYYY-MM-DD')
    p.add_argument('--until', help='集計終了日 YYYY-MM-DD')
    p.add_argument('--memo-limit', type=int, default=8, help='HTMLに表示する学生別メモ数')
    args = p.parse_args()
    base = Path(args.input).expanduser().resolve()
    out = Path(args.output).expanduser().resolve() if args.output else base / '_class_summary'
    if not base.is_dir(): p.error(f'入力フォルダがありません: {base}')
    if args.since and args.until and args.since > args.until: p.error('開始日と終了日の順序が逆です')
    if args.memo_limit < 1: p.error('--memo-limit は1以上にしてください')
    aliases = {}
    if args.aliases:
        aliases = json.loads(Path(args.aliases).read_text(encoding='utf-8-sig'))
        if not isinstance(aliases, dict): p.error('aliasesは「メールアドレス: 学生名」のJSONオブジェクトにしてください')
        aliases = {str(k).strip().lower(): str(v).strip() for k,v in aliases.items()}
    files = sorted(base.rglob('*_commits.csv'))
    # 出力フォルダを指定した場所に再度入力しないための保険
    files = [f for f in files if out not in f.parents]
    if not files: p.error('対象の *_commits.csv が見つかりません')
    groups = defaultdict(list)
    unique = set()
    skipped = 0
    for path in files:
        team = path.name[:-len('_commits.csv')]  # フォルダ名と異なってもファイル名から班名を抽出
        try: rows = read_csv(path)
        except (ValueError, OSError) as ex:
            print(f'[警告] {path}: {ex}'); continue
        for row in rows:
            day = date_of(row.get('日時', ''))
            if args.since and day < args.since: continue
            if args.until and day > args.until: continue
            email = (row.get('メールアドレス') or '').strip().lower()
            name = (row.get('開発者') or '').strip()
            identity = aliases.get(email) or aliases.get(name.lower()) or email or name or '(不明)'
            # 班内で同一SHAの重複のみ除去（異なる班に同じSHAがある場合は別扱い）
            sha = (row.get('SHA') or '').strip()
            dedup = (team, sha) if sha else (team, str(path), row.get('日時'), name, row.get('コミットメッセージ'), row.get('変更ファイル一覧'))
            if dedup in unique: skipped += 1; continue
            unique.add(dedup)
            row = dict(row, _day=day, _identity=identity, _name=name, _email=email, _team=team)
            groups[(team, identity)].append(row)
    if not groups: p.error('有効なコミットがありません（列名・期間を確認してください）')
    summary = []
    detail = []
    for (team, identity), rows in sorted(groups.items()):
        names = Counter(r['_name'] for r in rows if r['_name'])
        emails = sorted({r['_email'] for r in rows if r['_email']})
        display = aliases.get(identity.lower()) or (identity if identity not in emails else (names.most_common(1)[0][0] if names else identity))
        dates = {r['_day'] for r in rows}
        changed = set()
        cats = Counter()
        for r in rows:
            changed.update(f.strip() for f in (r.get('変更ファイル一覧') or '').split(';') if f.strip())
            if r.get('分類（推定）'): cats[r['分類（推定）']] += 1
        summary.append({'班名': team, '識別子': identity, '開発者': display, 'メールアドレス': '; '.join(emails),
            'コミット数': len(rows), '活動日数': len(dates), '追加行数': sum(num(r.get('追加行数')) for r in rows),
            '削除行数': sum(num(r.get('削除行数')) for r in rows), '変更ファイル種類数': len(changed),
            '初回活動日': min(dates), '最終活動日': max(dates), '主な分類（推定）': cats.most_common(1)[0][0] if cats else '',
            '作業メモ抜粋': ' ／ '.join(sample_memos(rows, 3))})
        for r in rows:
            detail.append({'班名': team, '開発者': display, '識別子': identity, '日時': r.get('日時', ''),
                'SHA': r.get('SHA', ''), '分類（推定）': r.get('分類（推定）', ''), '作業メモ': r.get('作業メモ', ''),
                'コミットメッセージ': r.get('コミットメッセージ', ''), '変更ファイル一覧': r.get('変更ファイル一覧', ''),
                '追加行数': num(r.get('追加行数')), '削除行数': num(r.get('削除行数')),
                'メモ生成方法': r.get('メモ生成方法', ''), 'コミットURL': r.get('コミットURL', '')})
    summary.sort(key=lambda r: (r['班名'], -r['コミット数'], r['開発者']))
    detail.sort(key=lambda r: (r['班名'], r['開発者'], r['日時']))
    team_stats = []
    for team in sorted({s['班名'] for s in summary}):
        subset = [s for s in summary if s['班名'] == team]
        total = sum(s['コミット数'] for s in subset)
        team_stats.append({'班名': team, '開発者数': len(subset), 'コミット数': total,
            '追加行数': sum(s['追加行数'] for s in subset), '削除行数': sum(s['削除行数'] for s in subset),
            '最多コミット者の割合（参考）': round(max(s['コミット数'] for s in subset) / total * 100, 1) if total else 0})
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out/'students_summary.csv', summary, list(summary[0]))
    write_csv(out/'students_commits.csv', detail, list(detail[0]))
    write_csv(out/'teams_summary.csv', team_stats, list(team_stats[0]))
    create_html(out/'dashboard.html', summary, detail, groups, args.memo_limit)
    print(f'読み込み: {len(files)}ファイル / {len(team_stats)}班 / {len(summary)}班別開発者 / {len(detail)}コミット（重複{skipped}件除外）')
    print(f'出力先: {out}')
    for file in ['students_summary.csv', 'students_commits.csv', 'teams_summary.csv', 'dashboard.html']:
        print(' -', out / file)

if __name__ == '__main__':
    main()
