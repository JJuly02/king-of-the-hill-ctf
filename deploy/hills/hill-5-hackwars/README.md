# hill-5 // HackWars Arena

A worked example hill, added by following "Add your own hill" in the wiki. It shows
the full contract a hill has to satisfy: a foothold vulnerability, a planned
privilege escalation to root, the `king.txt` ownership convention, and a `reset.sh`
that revives the vuln without touching ownership.

## Theme

A ranked ladder / match-telemetry console for a fictional arena game.

## Foothold: command injection (service user `arena`)

The "replay relay check" runs a reachability check against a host you supply, and
passes the value straight into a shell. Anything after the host is executed as
`arena`.

```
GET /replay?match=x; id
GET /replay?match=x; cat /home/arena/user.txt
```

User flag: `/home/arena/user.txt`.

## Privesc: sudo awk, GTFOBins (root)

`arena` may run `/usr/bin/awk` as root with no password (`/etc/sudoers.d/arena`).
awk can spawn a shell, so that is a direct path to root.

```
sudo awk 'BEGIN{system("id")}'
sudo awk 'BEGIN{system("cat /root/root.txt")}'
```

Root flag: `/root/root.txt`.

## Take the hill

Write your team token to `/root/king.txt` as root. The beacon agent on the host
reads it and reports your team to the scoreboard; the tick engine starts scoring
you for as long as you hold it.

```
sudo awk 'BEGIN{system("echo TOK-YOURTEAM > /root/king.txt")}'
```

## Defend and reset

`king.txt` is `root:root` mode 600, so only root writes it: an attacker has to root
the box to overwrite yours. `reset.sh` restores the sudoers rule and the service if
a defender removed them, but never touches `king.txt`, so a box cannot be patched
permanently shut.

## Ports

Local demo: the service listens on container port 80, published on `8085`.

Everything here is intentionally vulnerable and is meant to run only on an isolated
lab or CTF network.
