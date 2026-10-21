#!/usr/bin/env python3
"""Cards lab 3 (V2.11.58): the scripts exactly as the panel makes them, on a real RouterOS: pack profiles, MAC binding,
expiry written by the router, the clock set, unbind, remove, the pack profiles and the expiry scheduler taken away at the end;
nothing written again when nothing changed. usage: cards3lab.py <chr.img> <label> <out>"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LAB_OUT'] = sys.argv[3]
from labvm import VM, note
img, label, out = sys.argv[1:4]
LOG = os.environ.get('LAB_RECV') or os.path.join(out, 'recv.log')
def got(): return [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
here = os.path.dirname(os.path.abspath(__file__))
vm = VM('r', img, 2222, 5555)
res = {'label': label, 'steps': {}}
def users(): return vm.ros('/ip hotspot user print detail without-paging')
def hist(): return vm.ros(':put [:len [/system history find]]').strip()
def run(name, f):
    b = len(got()); o = vm.ros(f'/import file-name={f}', 600); time.sleep(2)
    res['steps'][name] = {'import': o[-400:], 'posted': [x['body'][:1500] for x in got()[b:]], 'users': users()}
try:
    note('boot; serial login: ' + str(vm.login()))
    for _ in range(20):
        v = vm.ros(':put [/system resource get version]')
        if v and v[0].isdigit(): break
        time.sleep(6)
    res['ros'] = v
    files = ['s1.rsc', 's2.rsc', 's3.rsc', 's4.rsc', 'login1.rsc', 'login2.rsc', 'login3.rsc']
    note('scp -> ' + vm.put(os.path.join(out, 'ca.crt'), *[os.path.join(here, f) for f in files]))
    vm.run([':delay 2s', '/certificate import file-name=ca.crt passphrase=""', '/certificate set [find] trusted=yes'])
    vm.run(['/ip hotspot profile add name="custprof" login-by=http-chap,cookie'])
    res['clock0'] = vm.ros(':put ([/system clock get date] . " " . [/system clock get time])').strip()
    run('s1', 's1.rsc')
    res['after_s1'] = {'profiles': vm.ros('/ip hotspot user profile print detail without-paging where name~"Lab"'), 'login_by': vm.ros('/ip hotspot profile print detail without-paging'),
                       'scheduler': vm.ros('/system scheduler print detail without-paging'), 'history': hist()}
    run('s1_again', 's1.rsc'); res['history_again'] = hist()
    for i in (1, 2, 3): run(f'login{i}', f'login{i}.rsc')
    run('s2', 's2.rsc'); res['clock1'] = vm.ros(':put ([/system clock get date] . " " . [/system clock get time])').strip()
    run('s3', 's3.rsc')
    run('s4', 's4.rsc')
    res['end'] = {'profiles': vm.ros('/ip hotspot user profile print terse without-paging'), 'scheduler': vm.ros('/system scheduler print terse without-paging'),
                  'files': vm.ros('/file print terse without-paging')}
    res['log'] = vm.ros('/log print without-paging where topics~"script|error|warning"')[-2500:]
    note('DONE')
finally:
    json.dump(res, open(os.path.join(out, 'cards-result.json'), 'w'), ensure_ascii=False, indent=1)
    vm.stop()
