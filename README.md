# Appear Offline — World of Tanks mod

Makes your account appear **offline** to friends and clanmates in the WoT
client while you keep playing normally — optionally **without** losing your own
view of *their* online status. Configurable from a native panel inside the
game's Contacts window.

## Two modes

- **Invisible** (*"Still see others' status" on*) — you appear offline to
  everyone, but you still see your friends' and clanmates' live status.
  *Caveat:* a currently-online contact may see a brief online→offline flicker
  right after you log in (their client gets the server's broadcast a moment
  before your directed "offline" reaches them). Inherent to a client-side
  approach. This is the **experimental** option (flagged in the UI).
- **Hard offline** (*"Still see others' status" off*) — you go fully offline to
  the server. Simplest and flicker-free, but you also stop seeing others' status.

## Using it (in-game)

Open **Contacts** in the garage → **Settings**. Below the native Apply/Cancel
bar you'll find two checkboxes:

- **Appear offline** — master switch for the mod.
- **Still see others' status** — picks Invisible (on) vs Hard offline (off).
  It carries a ⚠ warning icon; hover it for details.

> **Good to know:** a change you make here takes effect on your **next login**,
> not instantly — a small notification reminds you. Changing chat presence
> mid-session isn't reliable on Wargaming's server (global presence is
> rate-limited, and an in-session chat reconnect corrupts state), whereas a
> fresh login applies your choice cleanly every time. So: toggle, then relog.

Settings are stored in `res_mods/configs/appear_offline/config.json` and persist
across sessions. You can also edit that file directly (see below).

## How it works

Your online status is broadcast by your own client over XMPP. The client calls
`messenger.proto.xmpp.contacts._UserPresence.sendPresence()`, which publishes
`PRESENCE.AVAILABLE` in the garage (and `AVAILABLE`/`DND` in battle). gloox (the
native XMPP layer) does **not** broadcast on its own — this Python method fully
drives it.

The mod installs a single patch over that method **once at startup**; the patch
reads the current config every time the game sends presence, so your setting is
applied automatically at each login without any mid-session presence spam:

- **Invisible** — broadcast `AVAILABLE` once (so the server keeps feeding you
  contacts' presence), then answer each contact with a *directed* `UNAVAILABLE`
  (via the `onUserStatusUpdated` event) so *they* see you offline.
- **Hard offline** — broadcast a global `UNAVAILABLE`.

The native UI is a small Scaleform SWF (compiled from `as3/`) loaded as a lobby
view; it injects the two checkboxes into the real `ContactsSettingsView` using
the game's own CLIK `CheckBox` component. The patch is restored in `fini()`.
Verified against decompiled client scripts for **v2.3.0.1**.

### Scope & limitations

- Hides your **in-client** online indicator from friends and clanmates.
- Cannot lie selectively — presence is all-or-nothing at the connection level.
- Does **not** affect the external clan-portal website (that's server-side).
- Chat still works if you open it; only your status changes.
- A setting change applies on your next login, not mid-session (see above).
- Must comply with the [Wargaming Fair Play Policy](https://worldoftanks.eu/en/content/guide/fair_play/).

## Install (for players)

Copy the built mod into your game's mods folder:

```
dist/de.tosox.appear_offline_1.0.0.wotmod
        ->  C:\Games\World_of_Tanks_EU\mods\2.3.0.1\
```

Launch the game and configure it from **Contacts → Settings** (see above). On
first run the mod writes `res_mods/configs/appear_offline/config.json`:

```json
{
  "enabled": true,
  "see_others_status": false
}
```

- `enabled` — `false` appears online again (mod effectively off) without
  uninstalling.
- `see_others_status` — `true` = Invisible, `false` = Hard offline.

Restart the client after editing the file (same "applies on next login" rule).

## Build (for developers)

Two artifacts are produced: the Python mod (`.pyc`) and the native UI (`.swf`).
The compiled SWF is committed, so you only need to rebuild it if you change the
AS3.

**1. Mod + package** — requires **Python 2.7** (compiles the game bytecode) and
**Python 3** (runs the script). Paths are configured at the top of `build.py`.

```bash
python build.py            # -> dist/de.tosox.appear_offline_1.0.0.wotmod
python build.py --dev      # also drops the .pyc + .swf into res_mods (fast test loop)
python build.py --install  # also copies the .wotmod into mods/<version>
```

`build.py` packages the pre-built `as3/appear_offline_contacts_hook.swf`; it does
not compile it.

> When switching from `--dev` testing to a real `.wotmod` install, remove the
> dev copies from `res_mods/2.3.0.1/scripts/client/gui/mods/` and
> `res_mods/2.3.0.1/gui/flash/` so the mod isn't loaded twice.

**2. UI SWF** (only if you touched the AS3) — requires the **Apache Flex SDK**
(+ playerglobal) at `.work/tools/flex` (or set `FLEX_HOME`):

```bash
bash as3/build_swf.sh      # -> as3/appear_offline_contacts_hook.swf
```

It compiles minimal external signature stubs (`as3/stubs`) into a `.swc`, then
builds the hook with `mxmlc` at `-swf-version=17` (the game's SWFs are v17; GFx
rejects newer). The game's real `net.wg.*` classes are used at runtime and are
not embedded.

## Testing

There is no hot reload — recompile and restart the client for every change.
Watch `python.log` at the game root for the mod's output:

```
[appear_offline] config loaded: {...}
[appear_offline] presence patch armed (your setting applies at each login)
[appear_offline] UI hook registered
[appear_offline] loaded
[appear_offline] reconfigured: enabled=... see_others=... (applies on next login)
```

To confirm end-to-end, use a **second account** (or ask a friend): appear offline
on account A and verify account B sees you offline while you can still play — and,
in Invisible mode, that A still sees B's status changes.

## Project layout

```
src/mod_appear_offline.py          the mod (Python 2.7)
as3/src/                           AS3 sources for the UI hook SWF
as3/stubs/                         minimal net.wg.* signature stubs (compiled to a .swc)
as3/build_swf.sh                   mxmlc build for the SWF
as3/appear_offline_contacts_hook.swf   compiled UI hook (committed)
build.py                           compile + package + install helper (Python 3)
dist/                              built .wotmod output
```
