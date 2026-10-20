"""Shared lab helpers: RouterOS images in qemu, first login on the serial console, commands over SSH."""
import os, shutil, socket, subprocess, time
import pexpect
from pexpect import fdpexpect
OUT = os.environ.get('LAB_OUT', '/tmp/lab')
os.makedirs(OUT, exist_ok=True)
PW = 'lab12345'
SSHO = ['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-o', 'LogLevel=ERROR', '-o', 'ConnectTimeout=10',
        '-o', 'HostKeyAlgorithms=+ssh-rsa,ssh-dss', '-o', 'PubkeyAcceptedAlgorithms=+ssh-rsa',
        '-o', 'KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1,diffie-hellman-group-exchange-sha1', '-o', 'ServerAliveInterval=30']
STEPS = []
def note(s):
    line = f'[{time.strftime("%H:%M:%S")}] {s}'
    print(line, flush=True); open(f'{OUT}/lab.txt', 'a').write(line + '\n'); STEPS.append(s)
kvm = os.path.exists('/dev/kvm') and os.access('/dev/kvm', os.W_OK)

class VM:
    def __init__(self, name, img, ssh, serial, extra=''):
        self.name, self.ssh, self.serial = name, ssh, serial
        disk = f'{OUT}/{name}.img'; shutil.copy(img, disk)
        fwd = f'hostfwd=tcp:127.0.0.1:{ssh}-:22' + extra
        self.p = subprocess.Popen(['qemu-system-x86_64', *(['-enable-kvm', '-cpu', 'host'] if kvm else []), '-m', '768', '-smp', '1',
                                   '-drive', f'file={disk},format=raw,if=ide', '-netdev', f'user,id=n0,{fwd}', '-device', 'e1000,netdev=n0',
                                   '-display', 'none', '-serial', f'tcp:127.0.0.1:{serial},server,nowait'],
                                  stdout=open(f'{OUT}/{name}-qemu.log', 'w'), stderr=subprocess.STDOUT)
    def login(self):
        def sl(ch, t): ch.send(t + '\r')
        end = time.time() + 480
        while time.time() < end:
            try:
                sock = socket.create_connection(('127.0.0.1', self.serial), timeout=10)
                ch = fdpexpect.fdspawn(sock.fileno(), timeout=45, encoding='utf-8', codec_errors='ignore')
                ch.logfile_read = open(f'{OUT}/{self.name}-serial.log', 'a'); sl(ch, '')
                changed = False
                for _ in range(40):
                    i = ch.expect([r'Login: ?$', r'[Pp]assword: ?$', r'\[Y/n\]', r'new password>', r'repeat new password>', r'\] >', pexpect.EOF, pexpect.TIMEOUT])
                    if i == 0: sl(ch, 'admin')
                    elif i == 1: sl(ch, PW if changed else '')
                    elif i == 2: sl(ch, 'n')
                    elif i in (3, 4):
                        def typed(t):
                            for c in t: ch.send(c); time.sleep(0.06)
                            ch.send('\r')
                        typed(PW)
                        if i == 3 and ch.expect([r'repeat new password>', pexpect.TIMEOUT], timeout=20) == 0: typed(PW)
                        changed = True
                        ch.expect([r'\] >', r'[Pp]assword', r'Login', pexpect.TIMEOUT], timeout=30); sl(ch, '')
                    elif i == 5:
                        sl(ch, f'/user set admin password={PW}'); ch.expect(r'\] >')
                        sl(ch, '/ip service set ssh disabled=no'); ch.expect(r'\] >')
                        sock.close(); return True
                    elif i == 7: sl(ch, '')
                    else: break
                sock.close()
            except Exception as e: note(f'{self.name} serial: {str(e)[:120]}')
            time.sleep(8)
        return False
    def ros(self, cmd, timeout=120):
        # RouterOS sometimes refuses a login that comes right after another one ("Permission denied"): tried again.
        for i in range(6):
            try: r = subprocess.run(['sshpass', '-p', PW, 'ssh', '-p', str(self.ssh), *SSHO, 'admin@127.0.0.1', cmd], capture_output=True, text=True, timeout=timeout)
            except subprocess.TimeoutExpired: return 'TIMEOUT'
            out = (r.stdout + r.stderr).replace('\r', '').strip()
            if 'Permission denied' not in out or i == 5: return out
            time.sleep(3 + 2 * i)
    def put(self, *files):
        r = subprocess.run(['sshpass', '-p', PW, 'scp', '-O', '-P', str(self.ssh), *SSHO, *files, 'admin@127.0.0.1:'], capture_output=True, text=True, timeout=120)
        return (r.stdout + r.stderr).strip()[-200:]
    def run(self, cmds):
        for c in cmds:
            o = self.ros(c); note(f'{self.name}: {c[:110]} -> {" ".join(o.split())[:200]}')
    def stop(self):
        self.p.terminate()
        try: self.p.wait(20)
        except Exception: self.p.kill()

