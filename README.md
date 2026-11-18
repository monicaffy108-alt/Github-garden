# GitHub Garden

Automatically generated GitHub contribution graph records — **not genuine development activity**. Historical date entries preserve their actual generation timestamp, and commit messages are explicitly labeled *synthetic*. Not intended for papers, projects, or proof-of-work.

Target account: **monicaffy108-alt**. Dedicated repository: **monicaffy108-alt/Github-garden**.

---

## Behavior

- Generates **1–12 synthetic records per day** from a fixed seed, with weekly clustering, daily jitter, lower weekend counts, and occasional small bursts. Repeated runs never infinitely inflate commits.
- `--days 365` fills in the target count for the previous 365 calendar days from today. It creates synthetic commits with historical dates and **never rewrites existing history**.
- Existing daily base records are preserved; additional color-level records are placed under `entries/<date>/`. Appends only — original contributions are never deleted.
- Timezone is fixed to **Asia/Shanghai / UTC+8**.
- Only the `main` branch of the dedicated repository is allowed; if the worktree has uncommitted changes, the script stops.
- No force-push, no touching research repositories, no tokens or private keys stored in source code.
- Scheduled in the background by a **VPS systemd timer**; push failures can be retried.

---

## How It Works

The repository is already created. The following commands are for first-time deployment examples only — do not re-run them on an existing repository:

```sh
gh repo create monicaffy108-alt/Github-garden --public --description 'Explicitly synthetic contribution garden; not genuine development activity' --source . --remote origin --push
```

The VPS needs Python 3, Git, and a dedicated **deploy key** with write access to this repository only. Do not copy your local `gh` token or personal SSH private key to the server.

Install the source code to `/opt/github-garden`, clone the dedicated repository to `/var/lib/github-garden/repo`, and confirm it has a `main` branch. Then:

```sh
python3 /opt/github-garden/garden.py --worktree /var/lib/github-garden/repo --days 365
install -m 644 /opt/github-garden/github-garden.service /etc/systemd/system/github-garden.service
install -m 644 /opt/github-garden/github-garden.timer /etc/systemd/system/github-garden.timer
systemctl daemon-reload
systemctl enable --now github-garden.timer
systemctl list-timers github-garden.timer
```

Git commits use the account's noreply address `285931751+monicaffy108-alt@users.noreply.github.com`. The GitHub contribution graph may update with a delay — the script finishing does not mean the graph has updated.

To pause: `systemctl disable --now github-garden.timer`.

---

## Disclaimer

This repository exists solely to generate synthetic contribution records. All commits are produced by an automated script and do not reflect real software engineering work.
