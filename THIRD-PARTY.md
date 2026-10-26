# Third-party components and licenses

Æther's own code and documents are under the MIT license (`LICENSE`). The components below keep their own licenses. None of them is copied into this repository unless the table says so.

| Component | License | In this repository | How Æther uses it |
| --- | --- | --- | --- |
| Big Shoulders Display (subset) | SIL Open Font License 1.1 | Yes: `interfaces/shared/design/fonts/` with `OFL.txt` | Display typeface |
| NitroGen (code and model weights) | NVIDIA License: **non-commercial research use only**; excludes military, surveillance, nuclear and biometric purposes | **No.** Installed separately; weights are never committed | A separate server process PR-REX talks to over a local socket. Anyone running PR-REX with NitroGen is bound by NitroGen's license, so that configuration is research-only |

The MIT license covers only the code written for Æther. It does not relax any third-party license. A backend added later is listed here with its license before it is used.
