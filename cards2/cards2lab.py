#!/usr/bin/env python3
"""Cards lab 2 (V2.11.58): the router-side card logic on a real RouterOS: profiles with on-login, «mac» added to the
hotspot sign-in ways, the expiry scheduler, emulated sign-ins (activation, MAC binding, the older card on the same device
switched off), the clock moved on and the expiry run, the report, unbind, cleanup, and nothing rewritten on a second run.
usage: cards2lab.py <chr.img> <label> <out>"""
import json, os, sys, time, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LAB_OUT'] = sys.argv[3]
from labvm import VM, note
img, label, out = sys.argv[1:4]
LOG = os.path.join(out, 'recv.log')
def got(): return [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
here = os.path.dirname(os.path.abspath(__file__))
vm = VM('r', img, 2222, 5555)
res = {'label': label, 'steps': {}}
def users(): return vm.ros('/ip hotspot user print detail without-paging')
def step(name, cmd, t=300):
    o = vm.ros(cmd, t); res['steps'][name] = {'import': o[-500:]}; time.sleep(1); return o
try:
    note('boot; serial login: ' + str(vm.login()))
    for _ in range(20):
        v = vm.ros(':put [/system resource get version]')
        if v and v[0].isdigit(): break
        time.sleep(6)
    res['ros'] = v; note('RouterOS ' + v)
    files = ['l1.rsc', 'rep.rsc', 'unbind.rsc', 'clean.rsc', 'expire.rsc'] + [f'login{i}.rsc' for i in range(1, 6)]
    note('scp -> ' + vm.put(os.path.join(out, 'ca.crt'), *[os.path.join(here, f) for f in files]))
    vm.run([':delay 2s', '/certificate import file-name=ca.crt passphrase=""', '/certificate set [find] trusted=yes'])
    vm.run(['/ip hotspot profile add name="custprof" login-by=http-chap,cookie', '/ip hotspot profile add name="emptyprof" login-by=""'])
    res['clock0'] = {'date': vm.ros(':put [/system clock get date]').strip(), 'time': vm.ros(':put [/system clock get time]').strip(),
                     'gmt': vm.ros(':put [/system clock get gmt-offset]').strip()}
    note('clock ' + json.dumps(res['clock0']))
    step('l1', '/import file-name=l1.rsc')
    res['after_l1'] = {'profiles': vm.ros('/ip hotspot user profile print detail without-paging where name~"Lab"'),
                       'onlogin_len': vm.ros(':put [:len [/ip hotspot user profile get [find where name~"MAC"] on-login]]').strip(),
                       'login_by': vm.ros('/ip hotspot profile print detail without-paging'),
                       'scheduler': vm.ros('/system scheduler print detail without-paging'),
                       'users': users(), 'history': vm.ros(':put [:len [/system history find]]').strip()}
    step('l1_again', '/import file-name=l1.rsc')
    res['history_again'] = vm.ros(':put [:len [/system history find]]').strip()
    note(f"history after l1 {res['after_l1']['history']} after second run {res['history_again']}")
    for i in range(1, 6):
        before = len(got())
        step(f'login{i}', f'/import file-name=login{i}.rsc'); time.sleep(2)
        res['steps'][f'login{i}']['users'] = users(); res['steps'][f'login{i}']['notified'] = got()[before:]
    # the clock moved on by 4 hours (the panel's clock line does the same), then the expiry run
    d, t, g = res['clock0']['date'], vm.ros(':put [/system clock get time]').strip(), res['clock0']['gmt']
    iso = len(d) >= 5 and d[4] == '-'
    cur = datetime.datetime.strptime(f'{d} {t}', '%Y-%m-%d %H:%M:%S' if iso else '%b/%d/%Y %H:%M:%S') + datetime.timedelta(hours=4)
    nd = cur.strftime('%Y-%m-%d') if iso else cur.strftime('%b/%d/%Y').lower()
    step('clock', f'/system clock set date="{nd}" time="{cur.strftime("%H:%M:%S")}"')
    res['clock1'] = {'date': vm.ros(':put [/system clock get date]').strip(), 'time': vm.ros(':put [/system clock get time]').strip()}
    step('expire', '/import file-name=expire.rsc')
    res['after_expire'] = users()
    before = len(got()); step('report', '/import file-name=rep.rsc'); time.sleep(2); res['report'] = got()[before:]
    step('unbind', '/import file-name=unbind.rsc'); res['after_unbind'] = users()
    step('clean', '/import file-name=clean.rsc')
    res['after_clean'] = {'users': users(), 'profiles': vm.ros('/ip hotspot user profile print terse without-paging'),
                          'scheduler': vm.ros('/system scheduler print terse without-paging')}
    res['log'] = vm.ros('/log print without-paging where topics~"script|error|warning|fetch"')[-3000:]
    note('DONE')
finally:
    json.dump(res, open(os.path.join(out, 'cards-result.json'), 'w'), ensure_ascii=False, indent=1)
    vm.stop()
