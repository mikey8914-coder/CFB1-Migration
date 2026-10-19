"""Bounded, point-only Covers bridge; no handicapping or wager evaluation."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib import error, request
from zoneinfo import ZoneInfo
import argparse
import csv
import hashlib
import json
import math
import re
import threading

from cfb1.cfbd_schedule import CFBDAcquisitionError, acquire_cfbd_schedule
from cfb1.schedule import ScheduleValidation
from cfb1.team_identity import TEAM_ALIASES, normalize_team_name

BOARD_URL = 'https://www.covers.com/sport/football/ncaaf/odds'
ET = ZoneInfo('America/New_York')

class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []
    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node): yield from child.walk()
    def has(self, cls): return cls in self.attrs.get('class', '').split()
    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)
    def direct_text(self): return ''.join(c for c in self.children if isinstance(c, str))

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node(); self.stack = [self.root]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs); self.stack[-1].children.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)

def first(node, predicate): return next((n for n in node.walk() if predicate(n)), None)
def utc_text(value): return value.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
def point(cell, side, total=False):
    side_node = first(cell, lambda n: n.has(side+'-cell'))
    anchor = first(side_node, lambda n: n.tag == 'a') if side_node else None
    if anchor is None: return None
    # Prices are nested spans. Only point text directly inside the link counts.
    raw = unescape(anchor.direct_text()).strip()
    if total: raw = re.sub(r'^[ou]\s*', '', raw, flags=re.I)
    if raw.upper() in {'PK','PICK','PICKEM'} and not total: return 0.0
    if not re.fullmatch(r'[+-]?\d+(?:\.\d+)?', raw): return None
    value = float(raw)
    return value if math.isfinite(value) and (not total or value > 0) else None

def parse_board(text, target_date, retrieved_at):
    root = Document(text).root
    tables = {}
    for kind in ['spread','total']:
        table = first(root, lambda n: n.tag == 'table' and n.attrs.get('id') == kind+'-table')
        if table is None: raise ValueError('Missing dedicated '+kind+' table; source schema changed')
        tables[kind] = table
    totals = {}
    for row in tables['total'].walk():
        if row.tag != 'tr' or not row.has('oddsGameRow'): continue
        for cell in row.walk():
            if cell.tag == 'td' and cell.attrs.get('data-book') in {'DraftKings','FanDuel'}:
                key = (cell.attrs.get('data-game'), cell.attrs['data-book'])
                totals.setdefault(key, []).append(cell)
    records = []
    marker = target_date.strftime('%b')+' '+str(target_date.day)+','
    for row in tables['spread'].walk():
        if row.tag != 'tr' or not row.has('oddsGameRow'): continue
        when = first(row, lambda n: n.has('game-time'))
        if when is None or marker not in ' '.join(when.text().split()): continue
        cells = [n for n in row.walk() if n.tag == 'td' and 'data-book' in n.attrs]
        ids = {n.attrs.get('data-game') for n in cells if n.attrs.get('data-game')}
        if len(ids) != 1: raise ValueError('Target row has missing/conflicting source game IDs')
        gid = next(iter(ids))
        if not gid.isdigit(): raise ValueError('Invalid Covers game ID')
        record = {'game_id':None, 'covers_game_id':gid, 'market_date':target_date.isoformat(),
                  'away_team':None, 'home_team':None, 'away_team_raw':None, 'home_team_raw':None,
                  'kickoff_utc':None, 'source':'covers', 'source_url':BOARD_URL,
                  'retrieved_at':retrieved_at, 'opening_home_spread':None,
                  'opening_spread_status':'excluded_unverified_attribution',
                  'identity_status':'unresolved', 'schedule_join_status':'unverified',
                  'fbs_status':'not_independently_verified', 'issues':[], 'warnings':[], 'books':{}}
        for book, prefix in [('DraftKings','DK'),('FanDuel','FD')]:
            spread_cells = [n for n in cells if n.attrs['data-book']==book]
            total_cells = totals.get((gid,book), [])
            home = away = total = None
            side_status = 'missing'
            spread_epoch = total_epoch = None
            if len(spread_cells)==1:
                sc = spread_cells[0];home=point(sc,'home');away=point(sc,'away')
                spread_epoch=sc.attrs.get('data-date')
                sides = [[n for n in sc.walk() if n.has(side+'-cell')] for side in ['home', 'away']]
                ambiguous = any(len(nodes)>1 or any(
                    sum(n.tag=='a' for n in node.walk())>1 for node in nodes
                ) for nodes in sides)
                if ambiguous:
                    record['issues'].append(prefix+'_ambiguous_spread_sides')
                    home=away=None;side_status='ambiguous'
                elif home is not None and away is not None:
                    if abs(home+away)>1e-9:
                        record['issues'].append(prefix+'_spread_side_conflict');home=None
                        side_status='conflicting'
                    else:side_status='complete'
                elif home is not None or away is not None:
                    side_status='incomplete'
                    record['warnings'].append(prefix+'_incomplete_spread_sides')
            elif len(spread_cells)>1:
                record['issues'].append(prefix+'_ambiguous_spread_cells');side_status='ambiguous'
            if len(total_cells)==1:
                tc=total_cells[0];over=point(tc,'away',True);under=point(tc,'home',True)
                total_epoch=tc.attrs.get('data-date')
                if over is not None and under is not None and over==under:total=over
                elif over is not None or under is not None:record['issues'].append(prefix+'_total_side_conflict')
            elif len(total_cells)>1: record['issues'].append(prefix+'_ambiguous_total_cells')
            record[prefix+'_Spread']=home;record[prefix+'_Away_Spread']=away;record[prefix+'_Total']=total
            record['books'][book]={'spread_data_date_raw':spread_epoch,'total_data_date_raw':total_epoch,
                                   'spread_side_status':side_status,
                                   'source_timestamp_semantics':'unverified','retrieved_at':retrieved_at}
        # Explicit point-only selection: measured DK total first, FD if DK absent.
        record['current_total']=record['DK_Total'] if record['DK_Total'] is not None else record['FD_Total']
        record['total_source_book']='DraftKings' if record['DK_Total'] is not None else ('FanDuel' if record['FD_Total'] is not None else None)
        records.append(record)
    counts=Counter(r['covers_game_id'] for r in records)
    for r in records:
        if counts[r['covers_game_id']]>1:r['issues'].append('duplicate_source_game_id')
    return records

def parse_detail(text, expected_game_id=None):
    root=Document(text).root
    events=[]
    def visit(value):
        if isinstance(value,dict):
            typ=value.get('@type',[])
            if typ=='SportsEvent' or isinstance(typ,list) and 'SportsEvent' in typ:events.append(value)
            for child in value.values():visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    for node in root.walk():
        if node.tag=='script' and node.attrs.get('type')=='application/ld+json':
            try:
                raw=node.text().strip()
                value,end=json.JSONDecoder().raw_decode(raw)
                # Covers currently emits one extra terminal brace. Accept only
                # a fully decoded object plus this exact observed suffix.
                if raw[end:].strip() not in {'', '}'}:continue
                visit(value)
            except (ValueError,TypeError):continue
    candidates=[]
    for event in events:
        away=event.get('awayTeam',{});home=event.get('homeTeam',{})
        away=away.get('name') if isinstance(away,dict) else None
        home=home.get('name') if isinstance(home,dict) else None
        if expected_game_id is not None and str(event.get('identifier'))!=str(expected_game_id):continue
        start=event.get('startDate')
        if not all(isinstance(x,str) and x.strip() for x in [away,home,start]):continue
        start=unescape(start)
        try:when=datetime.fromisoformat(start)
        except ValueError:
            try:when=datetime.strptime(start,'%m/%d/%Y %H:%M:%S %z')
            except ValueError:continue
        if when.tzinfo is None:continue
        candidates.append((unescape(away).strip(),unescape(home).strip(),utc_text(when)))
    unique=set(candidates)
    if len(unique)!=1:raise ValueError('Missing or ambiguous structured matchup identity/kickoff')
    return next(iter(unique))

class CoversFetcher:
    """One board + capped detail reads; never retries or bypasses a denial."""
    def __init__(self, max_requests=61, timeout=20):
        self.max_requests=max_requests;self.timeout=timeout;self.count=0
        self.lock=threading.Lock();self.blocked=False;self.requests=[]
    def get(self,url):
        with self.lock:
            if self.blocked:raise RuntimeError('Covers access denied; remaining requests stopped')
            if self.count>=self.max_requests:raise RuntimeError('Covers request budget exhausted')
            self.count+=1
        meta={'url':url,'retrieved_at':utc_text(datetime.now(timezone.utc))}
        try:
            req=request.Request(url,headers={'User-Agent':'CFB1-market-bridge/1.0'})
            with request.urlopen(req,timeout=self.timeout) as response:
                meta['http_status']=response.status
                body=response.read(16000001)
                if len(body)>16000000:raise RuntimeError('Covers response exceeds size limit')
                if response.url.split('/')[2]!='www.covers.com':raise RuntimeError('Unexpected Covers redirect host')
                meta['sha256']=hashlib.sha256(body).hexdigest()
                return body.decode('utf-8'),meta
        except error.HTTPError as exc:
            meta['http_status']=exc.code
            if exc.code in {401,403,429}:
                with self.lock:self.blocked=True
            raise RuntimeError('Covers HTTP '+str(exc.code)) from None
        except (error.URLError,OSError):raise RuntimeError('Covers connection failure') from None
        finally:
            with self.lock:self.requests.append(meta)

def enrich(records,fetcher,target_date,resolver=None):
    known=set(TEAM_ALIASES.values())
    def run(record):
        if 'duplicate_source_game_id' in record['issues']:return
        url='https://www.covers.com/sport/football/ncaaf/matchup/'+record['covers_game_id']
        try:
            text,meta=fetcher.get(url)
            away,home,kickoff=parse_detail(text,record['covers_game_id'])
            record.update(away_team_raw=away,home_team_raw=home,kickoff_utc=kickoff,
                          detail_url=url,detail_retrieved_at=meta['retrieved_at'])
            if datetime.fromisoformat(kickoff).astimezone(ET).date()!=target_date:
                record['issues'].append('detail_date_conflict')
            names=[normalize_team_name(away),normalize_team_name(home)]
            record['away_team'],record['home_team']=names
            if resolver is not None:
                ids=[resolver.resolve_market_name(away),resolver.resolve_market_name(home)]
                ambiguous=any(raw.strip() in resolver.canonical_team_names and raw.strip()!=ident.normalized_name and ident.matched for raw,ident in zip([away,home],ids))
                if ambiguous:record['issues'].append('ambiguous_team_identity')
                elif all(i.matched for i in ids):record['identity_status']='cfbd_registry_matched'
                else:record['issues'].append('unresolved_team_identity')
            elif all(n in known for n in names):record['identity_status']='legacy_alias_resolved_not_live_verified'
            else:record['issues'].append('unresolved_team_identity')
            if names[0]==names[1]:record['issues'].append('same_home_away_team')
        except (RuntimeError,ValueError) as exc:record['issues'].append(str(exc))
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,records))
    matches=Counter((r['away_team'],r['home_team'],r['kickoff_utc']) for r in records if r['away_team'] and r['home_team'] and r['kickoff_utc'])
    for r in records:
        if matches.get((r['away_team'],r['home_team'],r['kickoff_utc']),0)>1:
            r['issues'].append('duplicate_market_matchup')

def aware_time(value):
    """Read an explicit offset; never infer a timezone or capture time."""
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        return None
    return result if result.tzinfo is not None and result.utcoffset() is not None else None


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_game_id(value):
    return (type(value) is int and value > 0 or
            isinstance(value, str) and bool(value) and value == value.strip())


def attach_schedule(records, schedule, target_date, *, season, week):
    """Associate only a valid batch from the committed schedule boundary.

    Scope is explicit. Alias matches alone never create this association.
    Invalidate any previous association before checking another batch.
    """
    if type(season) is not int or season < 1 or type(week) is not int or week < 0:
        raise ValueError('Explicit valid season/week are required')
    if not isinstance(schedule, ScheduleValidation):
        raise TypeError('Use ScheduleValidation from the committed schedule boundary')
    scoped = schedule.valid and bool(schedule.records) and all(
        g.source == 'cfbd' and g.season == season and g.week == week
        and valid_game_id(g.game_id) for g in schedule.records
    )
    for r in records:
        r.update(game_id=None, verified_schedule=None, requested_season=season,
                 requested_week=week, schedule_join_status='unverified')
        if not scoped:
            r['schedule_join_status'] = 'invalid_batch'
            r['issues'].append('invalid_schedule_batch_or_scope')
            continue
        matches = [g for g in schedule.records
                   if (g.away_team, g.home_team) == (r['away_team'], r['home_team'])
                   and g.kickoff_utc.astimezone(ET).date() == target_date]
        if len(matches) > 1:
            r['schedule_join_status'] = 'ambiguous'
            r['issues'].append('ambiguous_schedule_join')
        elif len(matches) == 1:
            g = matches[0]
            if (r['market_date'] != target_date.isoformat()
                    or aware_time(r['kickoff_utc']) != g.kickoff_utc):
                r['schedule_join_status'] = 'kickoff_conflict'
                r['issues'].append('schedule_kickoff_or_date_conflict')
            else:
                r['game_id'] = g.game_id
                r['verified_schedule'] = g.to_dict()
                r['schedule_join_status'] = 'verified'
        else:
            reversed_match = any(
                (g.home_team, g.away_team) == (r['away_team'], r['home_team'])
                and g.kickoff_utc.astimezone(ET).date() == target_date
                for g in schedule.records)
            if reversed_match:
                r['schedule_join_status'] = 'home_away_conflict'
                r['issues'].append('schedule_home_away_conflict')
            else:
                r['schedule_join_status'] = 'unmatched'


def manual_ready(record):
    """Complete point inputs for controlled inspection, not official verification."""
    kickoff = aware_time(record.get('kickoff_utc'))
    return (not record.get('issues') and record.get('identity_status') in {
                'legacy_alias_resolved_not_live_verified', 'cfbd_registry_matched'}
            and all(record.get(k) for k in ('away_team', 'home_team'))
            and record['away_team'] != record['home_team']
            and all(finite_number(record.get(k)) for k in ('DK_Spread', 'FD_Spread', 'current_total'))
            and record['current_total'] > 0 and kickoff is not None
            and kickoff.astimezone(ET).date().isoformat() == record.get('market_date'))


def production_blockers(record):
    """Current-market eligibility; deliberately independent of opening lines."""
    reasons = list(record.get('issues', []))
    if not manual_ready(record):
        reasons.append('manual_point_or_identity_requirements_not_met')
    proof = record.get('verified_schedule') or {}
    if record.get('schedule_join_status') != 'verified' or not proof:
        reasons.append('schedule_association_not_verified')
    if (not valid_game_id(record.get('game_id'))
            or type(record.get('game_id')) is not type(proof.get('game_id'))
            or record.get('game_id') != proof.get('game_id')):
        reasons.append('official_game_id_not_preserved')
    if (proof.get('source') != 'cfbd'
            or (proof.get('away_team'), proof.get('home_team')) !=
               (record.get('away_team'), record.get('home_team'))
            or aware_time(proof.get('kickoff_utc')) is None
            or aware_time(proof.get('kickoff_utc')) != aware_time(record.get('kickoff_utc'))
            or type(record.get('requested_season')) is not int
            or type(record.get('requested_week')) is not int
            or (proof.get('season'), proof.get('week')) !=
               (record.get('requested_season'), record.get('requested_week'))):
        reasons.append('schedule_identity_orientation_or_scope_not_confirmed')
    if aware_time(record.get('retrieved_at')) is None:
        reasons.append('capture_time_unknown')
    for book, prefix in [('DraftKings', 'DK'), ('FanDuel', 'FD')]:
        if record.get('books', {}).get(book, {}).get('spread_side_status') != 'complete':
            reasons.append(prefix+'_spread_sides_not_confirmed')
    total_field = {'DraftKings': 'DK_Total', 'FanDuel': 'FD_Total'}.get(record.get('total_source_book'))
    if (total_field is None or not finite_number(record.get(total_field))
            or record.get(total_field) != record.get('current_total')):
        reasons.append('selected_total_attribution_not_confirmed')
    return list(dict.fromkeys(reasons))


def production_ready(record):
    return not production_blockers(record)


def audit_ready(record):
    """A separately verified, same-book opener/current pair for this game.

    The scraper does not acquire/verify this optional object. A trusted audit
    input boundary must supply it; a displayed opening number alone is insufficient.
    """
    if not production_ready(record):
        return False
    audit = record.get('movement_audit') or {}
    if (audit.get('verified') is not True or audit.get('game_id') != record['game_id']
            or (audit.get('away_team'), audit.get('home_team')) !=
               (record['away_team'], record['home_team'])):
        return False
    opening, current = audit.get('opening', {}), audit.get('current', {})
    for obs in (opening, current):
        if (not finite_number(obs.get('home_spread')) or not obs.get('source')
                or obs.get('book') not in {'DraftKings', 'FanDuel'}
                or aware_time(obs.get('retrieved_at')) is None):
            return False
    return (bool(opening.get('definition')) and opening['book'] == current['book']
            and opening['source'] == current['source']
            and aware_time(opening['retrieved_at']) <= aware_time(current['retrieved_at'])
            and aware_time(record['retrieved_at']) <= aware_time(current['retrieved_at']))


def load_cached_board(path, metadata_path=None):
    """An explicitly supplied capture receipt is trusted only for its matching bytes."""
    body = path.read_bytes()
    meta = {'url': BOARD_URL, 'sha256': hashlib.sha256(body).hexdigest(),
            'retrieved_at': None, 'capture_time_provenance': 'unknown',
            'filesystem_mtime_utc': utc_text(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)),
            'status': 'cached_input'}
    if metadata_path is not None:
        receipt = json.loads(metadata_path.read_text(encoding='utf-8'))
        if (not isinstance(receipt, dict) or receipt.get('sha256') != meta['sha256']
                or receipt.get('url') != BOARD_URL):
            raise ValueError('Capture receipt must match board URL and SHA-256')
        timestamp = receipt.get('retrieved_at')
        if timestamp is not None and aware_time(timestamp) is None:
            raise ValueError('Capture receipt time must have an explicit UTC offset')
        meta['retrieved_at'] = timestamp
        if timestamp is not None:
            meta['capture_time_provenance'] = 'supplied_capture_receipt'
    return body.decode('utf-8'), meta


def summary(records, target_date=None, *, season=None, week=None):
    n=len(records);both=sum(r['DK_Spread'] is not None and r['FD_Spread'] is not None for r in records)
    return {'games_found':n,'games_with_both_spreads':both,
            'games_with_current_total':sum(r['current_total'] is not None for r in records),
            'manual_ready_records':sum(manual_ready(r) for r in records),
            'production_ready_records':sum(production_ready(r) for r in records),
            'audit_ready_records':sum(audit_ready(r) for r in records),
            'excluded_or_blocked_records':sum(not production_ready(r) for r in records),
            'blocking_conflict_records':sum(bool(r['issues']) for r in records),
            'verified_schedule_joins':sum(r['schedule_join_status']=='verified' for r in records),
            'unmatched_or_unverified_schedule':sum(r['schedule_join_status'] in {'unverified','unmatched'} for r in records),
            'ambiguous_or_conflicting_schedule':sum(r['schedule_join_status'] in {'ambiguous','kickoff_conflict','home_away_conflict'} for r in records),
            'missing_fields':{field:sum(r.get(field) is None for r in records) for field in ['DK_Spread','FD_Spread','current_total','away_team','home_team','kickoff_utc','game_id']},
            'unresolved_identity_games':sum(r['identity_status']=='unresolved' for r in records),
            'manual_ready_coverage_pct':round(100*sum(manual_ready(r) for r in records)/n,2) if n else None,
            'verified_full_fbs_schedule_coverage_pct':None,
            'both_spreads_coverage_pct':round(100*both/n,2) if n else None,
            'requested_date':target_date.isoformat() if target_date else None,
            'requested_season':season, 'requested_week':week,
            'coverage_denominator':f"Covers rows for {target_date.isoformat() if target_date else ', '.join(sorted({r['market_date'] for r in records}))}; not independently verified full FBS schedule",
            'coverage_denominator_games':n,
            'issues_by_code':dict(Counter(issue for r in records for issue in r['issues']))}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',type=date.fromisoformat,required=True)
    parser.add_argument('--season',type=int,required=True)
    parser.add_argument('--week',type=int,required=True)
    parser.add_argument('--max-requests',type=int,default=61)
    parser.add_argument('--output-dir',type=Path,default=Path('data/market'))
    parser.add_argument('--board-file',type=Path,help='Reuse a freshly captured board for this run')
    parser.add_argument('--board-metadata',type=Path,help='Trusted capture receipt with URL, SHA-256 and optional offset-aware retrieved_at')
    args=parser.parse_args(argv)
    if not 1<=args.max_requests<=70:parser.error('max-requests must be between 1 and 70')
    if args.season != args.date.year or args.week < 0:
        parser.error('Explicit regular-season year must match date year; week must be >= 0')
    if args.board_metadata and not args.board_file:
        parser.error('--board-metadata requires --board-file')
    fetcher=CoversFetcher(args.max_requests)
    if args.board_file:
        try:
            text,board_meta=load_cached_board(args.board_file,args.board_metadata)
        except (OSError,ValueError) as exc:
            parser.error(str(exc))
    else:
        text,board_meta=fetcher.get(BOARD_URL)
        board_meta['capture_time_provenance']='live_http_capture'
    retrieved=board_meta['retrieved_at']
    records=parse_board(text,args.date,retrieved)
    schedule=None;resolver=None;schedule_status={}
    try:
        live=acquire_cfbd_schedule(args.season,args.week)
        schedule_status=live.to_dict()
        if live.validation.valid:
            schedule=live.validation
            # Only verified canonical names in the independently acquired schedule.
            from cfb1.team_identity import TeamIdentityResolver
            resolver=TeamIdentityResolver(n for g in schedule.records for n in [g.away_team,g.home_team])
        else:schedule_status['blocker']='CFBD batch validation failed; no verified batch attached'
    except CFBDAcquisitionError as exc:schedule_status={'valid':False,'blocker':str(exc)}
    enrich(records,fetcher,args.date,resolver)
    if schedule is not None:
        attach_schedule(records,schedule,args.date,season=args.season,week=args.week)
    for r in records:
        r.update(manual_ready=manual_ready(r),production_ready=production_ready(r),
                 audit_ready=audit_ready(r),production_blockers=production_blockers(r))
    success=bool(records) and all(production_ready(r) for r in records)
    report={'provisional':not success,'production_validation_passed':success,
            'success_rule':'Nonempty fetched slate; every fetched record production-ready. No claim of full schedule/model coverage.',
            'market_date':args.date.isoformat(),'season':args.season,'week':args.week,'source':'covers',
            'board':board_meta,'requests':fetcher.requests,'request_limit':args.max_requests,
            'schedule':schedule_status,'summary':summary(records,args.date,season=args.season,week=args.week),
            'fbs_scope':'Source NCAA board; independent 2026 FBS schedule coverage unverified unless separately established',
            'opener_policy':'Not used: attribution/definition unverified',
            'freshness':'Capture time may be unknown for cached input; book data-date semantics unverified; no guaranteed quote-age threshold',
            'records':records}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    stem='covers_'+args.date.isoformat()+('_provisional' if report['provisional'] else '')
    # Exclusive creation preserves prior snapshots rather than overwriting them.
    with (args.output_dir/(stem+'.json')).open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    fields=['provisional','game_id','covers_game_id','Away_Team','Home_Team','away_team','home_team','Kickoff_UTC','Kickoff_ET','Game_Date_ET','DK_Spread','FD_Spread','DK_Away_Spread','FD_Away_Spread','DK_Total','FD_Total','current_total','total_source_book','source','retrieved_at','schedule_join_status','identity_status','manual_ready','production_ready','audit_ready','production_blockers','validation_issues','validation_warnings']
    csv_rows=[]
    for r in records:
        k=datetime.fromisoformat(r['kickoff_utc']) if r['kickoff_utc'] else None
        row={field:r.get(field) for field in fields}
        row.update(provisional=report['provisional'],Away_Team=r['away_team_raw'],Home_Team=r['home_team_raw'],Kickoff_UTC=r['kickoff_utc'],Kickoff_ET=k.astimezone(ET).isoformat() if k else None,Game_Date_ET=k.astimezone(ET).date().isoformat() if k else None,production_blockers=';'.join(r['production_blockers']),validation_issues=';'.join(r['issues']),validation_warnings=';'.join(r['warnings']))
        csv_rows.append(row)
    for suffix,selected in [('.csv',csv_rows),
                            ('_manual_ready.csv',[r for r in csv_rows if r['manual_ready']]),
                            ('_production_ready.csv',[r for r in csv_rows if r['production_ready']])]:
        with (args.output_dir/(stem+suffix)).open('x',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(selected)
    report.pop('records')
    with (args.output_dir/(stem+'_validation.json')).open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report['summary'],indent=2))
    return 0 if success else 1

if __name__=='__main__':raise SystemExit(main())
