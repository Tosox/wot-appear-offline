# Appear Offline

[![Downloads (All Time)](https://img.shields.io/github/downloads/Tosox/wot-appear-offline/total.svg?label=Downloads%20(All%20Time))](https://github.com/Tosox/wot-appear-offline/releases) [![Downloads (Latest Release)](https://img.shields.io/github/downloads/Tosox/wot-appear-offline/latest/total.svg?label=Downloads%20(Latest%20Release))](https://github.com/Tosox/wot-appear-offline/releases/latest)

## 📜 Description

Makes your account appear offline to friends and clanmates in the World of
Tanks client while you keep playing normally, optionally without losing your
own view of their online status. Everything is configured from a native panel
inside the game's Contacts window.

There are two modes:

* **Invisible** (*"Still see others' status" on*): you appear offline to everyone,
  but you still see your friends' and clanmates' live status. *Caveat:* a
  currently-online contact may see a brief online→offline flicker right after you
  log in.
* **Hard offline** (*"Still see others' status" off*): you go fully offline to the
  server. Simplest and flicker-free, but you also stop seeing others' status.

## 🎮 Usage

Open `Contacts → Settings` in the garage. There you'll find two checkboxes:

* **Appear offline** — master switch for the mod.
* **Still see others' status** — picks Invisible (on) vs Hard offline (off). Hover
  its ⚠ icon for details.

> [!NOTE]
> A change takes effect on your **next login**, not instantly

## 🔧 Installation

* Download the [latest release](https://github.com/Tosox/wot-appear-offline/releases/latest)
* Drop the `.wotmod` into your game's mods folder: `World_of_Tanks_EU\mods\<version>\`
* Launch the game and configure it from **Contacts → Settings**

## 📝 Changelog

You can check out the latest changes in [`CHANGELOG.md`](CHANGELOG.md).

## 🎥 Preview

<table>
  <tr>
    <th align="left">Your view</th>
    <th align="left">Their view</th>
  </tr>
  <tr>
    <td align="left"><img src="readme-res/your-view.png" alt="Your view" width="310"/></td>
    <td align="left"><img src="readme-res/their-view.png" alt="Their view" width="340"/></td>
  </tr>
  <tr>
    <td colspan="2" align="left"><img src="readme-res/settings.png" alt="Settings" width="310"/></td>
  </tr>
</table>

## 🛠️ Build from source

### Prerequisites

* [Python 2.7.18](https://www.python.org/downloads/release/python-2718/) — compiles the game bytecode
* A JDK such as [Eclipse Temurin 11](https://adoptium.net/temurin/releases/?version=11) — required by the Flex compiler
* [Apache Flex SDK 4.16.1](https://archive.apache.org/dist/flex/4.16.1/binaries/apache-flex-sdk-4.16.1-bin.zip) — compiles the UI SWF
* Adobe [`playerglobal32_0.swc`](https://fpdownload.macromedia.com/get/flashplayer/updaters/32/playerglobal32_0.swc) — not bundled with Flex, so it's a separate download

### Setup

1. Extract the Flex SDK somewhere, then drop `playerglobal32_0.swc` into it as
   `frameworks/libs/player/11.1/playerglobal.swc`.
2. Point the `FLEX_HOME` environment variable at that SDK folder.
3. Point the `PYTHON27` environment variable at your Python 2.7 executable
   (e.g. `C:\Python27\python.exe`). Skip this if you run `build.py` with Python 2.7 directly.
4. For `--install`, copy `build.local.example.json` to `build.local.json` and fill
   in your `game_dir` and `game_version`.

### Build

```bash
python build.py            # -> dist/<id>_<version>.wotmod
python build.py --install  # also copies it into the game's mods/<version> folder
```

The mod is configured through `mod.json`.

## ⚙️ How it works

Your online status is broadcast by your own client over XMPP, through
`messenger.proto.xmpp.contacts._UserPresence.sendPresence()`. gloox, the native
XMPP layer, doesn't broadcast on its own, so this one method fully drives it.

The mod installs a single patch over that method once at startup. The patch then
reads the current config every time the game sends presence, so your setting is
applied automatically at each login without any mid-session presence spam:

* **Invisible** — broadcast `AVAILABLE` once so the server keeps feeding you
  contacts' presence, then answer each contact with a directed `UNAVAILABLE` so
  they see you offline.
* **Hard offline** — broadcast a global `UNAVAILABLE`.

The native UI is a small Scaleform SWF loaded as a lobby view;
it injects the two checkboxes into the real `ContactsSettingsView`
using the game's own CLIK `CheckBox` component.

## 📄 License

Distributed under the GNU General Public License v3.0. See [`LICENSE`](LICENSE) for more information.
