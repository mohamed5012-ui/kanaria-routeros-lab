#!/usr/bin/env python3
"""Cards lab: the panel's generated hotspot-card scripts (c1 add 150 + read + profiles, c2 disable 2 + remove 2, c3 the
same 5 adds again) imported on a real RouterOS, as the agent does; what the router sent back is kept for the panel's own
parser (run locally). usage: cardslab.py <chr.img> <label> <out>"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LAB_OUT'] = sys.argv[3]
from labvm import VM, note
img, label, out = sys.argv[1:4]
LOG = os.path.join(out, 'recv.log')
def got(): return [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
here = os.path.dirname(os.path.abspath(__file__))
vm = VM('r', img, 2222, 5555)
res = {'label': label}
try:
    note('boot; serial login: ' + str(vm.login()))
    for _ in range(20):
        v = vm.ros(':put [/system resource get version]')
        if v and v[0].isdigit(): break
        time.sleep(6)
    note('RouterOS ' + v); res['ros'] = v
    note('scp -> ' + vm.put(os.path.join(sys.argv[3], 'ca.crt'), *[os.path.join(here, f) for f in ('c1.rsc', 'c2.rsc', 'c3.rsc')]))
    vm.run([':delay 2s', '/certificate import file-name=ca.crt passphrase=""', '/certificate set [find] trusted=yes'])
    # The customer's own hotspot user with the same name as card 3: it must stay as it is.
    vm.run(['/ip hotspot user add name="ownuser3" password="mine" comment="customer"'])
    for n in ('c1', 'c2', 'c3'):
        before = len(got()); t = time.time()
        o = vm.ros(f'/import file-name={n}.rsc', 600); sec = round(time.time() - t, 1)
        time.sleep(2)
        pieces = got()[before:]
        res[n] = {'seconds': sec, 'import': o[-400:], 'pieces': pieces}
        note(f'{n}: import {sec} s -> {" ".join(o.split())[-200:]!r}; pieces received: {len(pieces)} ({sum(len(p["body"]) for p in pieces)} chars)')
        if n == 'c1':
            res['after_c1'] = {
                'kanaria_users': vm.ros(':put [:len [/ip hotspot user find where comment="Kanary_C"]]'),
                'own_user': vm.ros('/ip hotspot user print detail without-paging where name="ownuser3"'),
                'profile': vm.ros('/ip hotspot user profile print detail without-paging where name="Kanary_P7"'),
                'one_card': vm.ros('/ip hotspot user print detail without-paging where comment="Kanary_C" and limit-bytes-total>0'),
            }
            note('after c1: ' + json.dumps({k: ' '.join(v.split())[:300] for k, v in res['after_c1'].items()}, ensure_ascii=False))
        if n == 'c2':
            res['after_c2'] = {'kanaria_users': vm.ros(':put [:len [/ip hotspot user find where comment="Kanary_C"]]'),
                               'disabled': vm.ros(':put [:len [/ip hotspot user find where comment="Kanary_C" and disabled]]')}
            note('after c2: ' + json.dumps(res['after_c2']))
        if n == 'c3':
            res['after_c3'] = {'kanaria_users': vm.ros(':put [:len [/ip hotspot user find where comment="Kanary_C"]]')}
            note('after c3: ' + json.dumps(res['after_c3']))
    res['log'] = vm.ros('/log print without-paging where topics~"script|error|warning|fetch"')[-3000:]
    note('DONE')
finally:
    json.dump(res, open(os.path.join(out, 'cards-result.json'), 'w'), ensure_ascii=False, indent=1)
    for k in ('c1', 'c2', 'c3'):
        if k in res: print(f'::notice title={label} {k}::{res[k]["seconds"]} s, pieces {len(res[k]["pieces"])}, import tail: {" ".join(res[k]["import"].split())[-160:]}', flush=True)
    for k in ('after_c1', 'after_c2', 'after_c3'):
        if k in res: print(f'::notice title={label} {k}::' + json.dumps({a: " ".join(b.split())[:400] for a, b in res[k].items()}, ensure_ascii=False)[:1500], flush=True)
    vm.stop()
