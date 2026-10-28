# Æther / PR-REX research verification — drivers, NitroGen and local VLMs

**Retrieval date:** 2026-10-28  
**Scope:** Primary project repositories, project-maintainer documentation, model-card documentation and Microsoft Learn. No owner hardware was exercised. No driver was installed, no model was downloaded, and no live inference benchmark was run.

## 1. Virtual gamepad driver: ViGEmBus

**Status: VERIFIED — retired and archived.**

The official [Nefarius ViGEmBus repository](https://github.com/nefarius/ViGEmBus) states that the project is retired. GitHub reports the repository was archived on 2023-11-02; the latest repository commit shown in the retrieved page is 2023-09-08. The [Nefarius end-of-life statement](https://docs.nefarius.at/projects/ViGEm/End-of-Life/) says ViGEmBus and its client libraries will receive no further updates and are archived/retired. (Both retrieved 2026-10-28.)

**Signing/distribution:** the repository README says Nefarius supplied pre-built production-signed binaries for Windows 10/11 through its all-in-one setup/release channel. The same README says a self-built driver must be signed to load without test mode. This describes the historical official distribution path; it is not evidence that the retired driver remains an appropriate new dependency or receives security updates. [ViGEmBus README](https://github.com/nefarius/ViGEmBus) (retrieved 2026-10-28).

**Successor:** no official ViGEmBus successor or drop-in replacement is identified by the retrieved ViGEmBus EOL statement. Do not label any third-party product a Nefarius successor based on this evidence.

**Microsoft framework alternative (not a drop-in replacement):** Microsoft documents [Virtual HID Framework (VHF)](https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/virtual-hid-framework--vhf-) as a framework for writing a HID source driver using KMDF or WDM; the source driver is kernel-mode and uses Microsoft's in-box VHF driver to enumerate virtual HID devices. VHF is a driver-development framework, not a ready-made virtual XInput gamepad bus or an installed replacement for ViGEmBus. (Retrieved 2026-10-28.)

**Signing path for a future in-house driver:** Microsoft's [attestation signing procedure](https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-attestation) requires Windows Hardware Developer Program/Partner Center registration and an EV code-signing certificate for submission; Microsoft signs the driver package after submission. Microsoft's [driver signing tutorial](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/windows-driver-signing-tutorial) states that kernel-mode drivers must be digitally signed. This is a development/distribution path, not a recommendation to write a new driver in this pass. (Retrieved 2026-10-28.)

**Engineering conclusion:** keep ViGEmBus as a legacy compatibility reference only; do not install or newly recommend it as the default current foundation. No replacement is approved by this note. Any future driver work requires a separately scoped design, signing/distribution plan, recovery procedure and owner authorization.

## 2. Physical controller hiding: HidHide

**Status: PARTIALLY VERIFIED — current project documentation and a published release are available; owner-device behavior is untested.**

The [HidHide project documentation](https://docs.nefarius.at/projects/HidHide/) describes it as an input-device firewall that blocks selected applications from accessing HID/XInput devices. It links to the official [HidHide releases](https://github.com/nefarius/HidHide/releases). The release page lists **HidHide Drivers v1.5.230.0**, released **2024-05-11**, as the latest release displayed at retrieval. The documentation carries an actively-maintained badge; the release listing itself is dated 2024. Do not infer a later release date than the page displayed. (Retrieved 2026-10-28.)

The official [Simple Setup Guide](https://docs.nefarius.at/projects/HidHide/Simple-Setup-Guide/) documents these caveats:
- If both a physical controller and its emulated controller are visible to a game, the game can see two controllers, causing double-input or mis-input.
- HidHide is used to hide the physical device from selected clients while allowing explicitly whitelisted applications to see it.
- HidHide and HidGuardian **must not** be installed together; the guide identifies HidHide as HidGuardian's successor and warns coexistence can cause confusion or issues.
- After changing the hide configuration, reconnecting controllers is part of the documented procedure.
- The [HidHide overview](https://docs.nefarius.at/projects/HidHide/) notes that Kaspersky Anti-Virus can interfere with application-whitelisting detection.

The [ViGEm end-of-life page](https://docs.nefarius.at/projects/ViGEm/End-of-Life/) separately warns that older ViGEmBus/HidHide updater configurations may still contact the retired updates.vigem.org domain; it documents the affected old-version updater configuration and a migration to Nefarius' replacement update domain. This is a version-specific legacy concern, not a statement that all current HidHide installs are affected. (Retrieved 2026-10-28.)

**Engineering conclusion:** HidHide is not “passthrough”; it changes device visibility per application. No install, hide rule, or device-state change was performed. Before any owner-authorized trial, inventory existing HID filters (especially HidGuardian), record the exact device instance and whitelist, and have a tested disable/uninstall/recovery route. Physical controller behavior remains UNVERIFIED on the MSI.

## 3. NitroGen: exact upstream I/O and license

**Source of truth:** [MineDojo/NitroGen](https://github.com/MineDojo/NitroGen), linked by the [NVIDIA NitroGen model card](https://huggingface.co/nvidia/NitroGen). The actual code repository is **MineDojo/NitroGen**, not `NVIDIA/NitroGen`. (Retrieved 2026-10-28.)

### Model and frame/action shape

The model card states:
- Approximately (4.93 \times 10^8) parameters (about 493 million; repository README rounds this to 500M).
- Input: 256×256 RGB image.
- Output: a 21×16 action tensor, described as two 2D continuous joystick vectors plus 17 binary buttons across a 16-step action chunk.

The upstream `scripts/play.py` preprocesses the captured RGB image to 256×256 before inference. The upstream `nitrogen/inference_client.py` documents `ModelClient.predict(image)` as accepting a NumPy `(H, W, 3)` RGB array and returning a dictionary containing `j_left`, `j_right`, and `buttons`; the play script asserts equal action sequence lengths and checks that each button vector length equals the token set. [Model card](https://huggingface.co/nvidia/NitroGen), [play.py](https://github.com/MineDojo/NitroGen/blob/main/scripts/play.py), [inference_client.py](https://github.com/MineDojo/NitroGen/blob/main/nitrogen/inference_client.py) (retrieved 2026-10-28).

### Exact server request/reply

The upstream [scripts/serve.py](https://github.com/MineDojo/NitroGen/blob/main/scripts/serve.py) creates a ZeroMQ REP socket on port 5555 by default and deserializes incoming requests with Python `pickle.loads`. Supported request dictionaries:
- Predict: `{"type": "predict", "image": <numpy RGB image>}`; reply: `{"status": "ok", "pred": <prediction dict>}`.
- Reset: `{"type": "reset"}`; reply: `{"status": "ok"}`.
- Info: `{"type": "info"}`; reply: `{"status": "ok", "info": <session metadata>}`.
- Unknown type: `{"status": "error", "message": <description>}`.

The upstream [ModelClient](https://github.com/MineDojo/NitroGen/blob/main/nitrogen/inference_client.py) serializes those request dictionaries with `pickle.dumps`, sends them over a ZeroMQ REQ socket, unpickles the reply, checks `status == "ok"`, and returns `response["pred"]`. (Retrieved 2026-10-28.)

**Important transport exposure:** upstream `serve.py` binds `tcp://*:<port>`, not loopback-only. It also accepts pickle messages without an authentication layer. Do not run the upstream server on a trusted LAN or public interface as-is. The PR-REX adapter connects to `tcp://127.0.0.1:5555`, but that client-side loopback address does not constrain the server's wildcard bind. Any local deployment needs a verified loopback-only server bind or equivalent host isolation before use. This is a compatibility/security finding, not a claim that the current adapter itself binds a server.

### License

The upstream [LICENSE](https://github.com/MineDojo/NitroGen/blob/main/LICENSE) is the NVIDIA License. Section 3.3 limits the Work and derivative works to non-commercial use, defined as non-commercial research purposes only, and excludes military, surveillance, nuclear-technology service, and biometric-processing purposes. The [model card](https://huggingface.co/nvidia/NitroGen) links the NVIDIA OneWay Noncommercial License PDF. (Retrieved 2026-10-28.)

**Repository rule:** NitroGen code and weights remain out of Æther. Link-only reference is retained. The license terms are not replaced by the repository's MIT license.

### Adapter alignment checklist for Claude

Compare `src/prrex/backends/nitrogen_reflex.py` against this verified upstream contract:
1. Request must contain `type="predict"` and `image` as a 256×256 RGB NumPy array.
2. The ZMQ payload is pickle, not JSON; the response envelope is a dict with `status` and `pred`.
3. The prediction payload is a dict with `j_left`, `j_right`, and `buttons`; each sequence has the same 16-step length in the published model-card format, and each button vector has 17 entries.
4. Do not trust or unpickle replies from a non-local or otherwise untrusted server. Do not change the verified Governor/control layer as part of this adapter review.
5. Preserve the fact that the upstream model is described as a fast-reacting last-frame sensory policy, not a long-horizon planner. (See [upstream README](https://github.com/MineDojo/NitroGen) and [paper](https://arxiv.org/abs/2601.02427), retrieved 2026-10-28.)

## 4. Small local VLMs via Ollama: published size versus VRAM/latency

The official [Ollama Qwen2.5-VL library page](https://ollama.com/library/qwen2.5vl) lists `qwen2.5vl:3b` at **3.2 GB** and `qwen2.5vl:7b` at **6.0 GB**, both with image input and a 125K context listing. The page says Qwen2.5-VL requires Ollama 0.7.0. The official [Ollama Gemma 3 page](https://ollama.com/library/gemma3) lists `gemma3:4b` at **3.4 GB** and `gemma3:12b` at **8.2 GB**; it describes Gemma 3 4B as a vision model and states Ollama 0.6 or later is required. (Retrieved 2026-10-28.)

**Critical distinction:** these numbers are Ollama-displayed model package sizes, not measured GPU VRAM requirements. The retrieved official Ollama pages do not publish source-matched VRAM peaks or latency figures (cold start, time-to-first-token, tokens/s, or image-processing latency) with a stated GPU, quantization, context and image resolution for these models. Therefore:
- Do not call the 3.2 GB / 3.4 GB packages “VRAM fit”.
- Do not infer that a model will coexist with NitroGen in 8 GB.
- Do not publish latency figures without a hardware/configuration-matched source.
- Treat Qwen2.5-VL 3B and Gemma 3 4B only as candidate small vision models to measure locally; no model is recommended or selected here.

For owner-side measurements, record the exact Ollama model tag and quantization, Ollama version, GPU and driver, image dimensions, context settings, cold/warm latency samples, peak VRAM, and whether the reflex process is concurrently resident. Use the new inference bench only when it is implemented and reviewed; all actual GPU results remain UNVERIFIED until collected on the MSI.

## Sources and retrieval record

All items below were retrieved on **2026-10-28**:
- ViGEmBus repository and README: https://github.com/nefarius/ViGEmBus
- ViGEm end-of-life statement: https://docs.nefarius.at/projects/ViGEm/End-of-Life/
- HidHide overview: https://docs.nefarius.at/projects/HidHide/
- HidHide setup guide: https://docs.nefarius.at/projects/HidHide/Simple-Setup-Guide/
- HidHide release history: https://github.com/nefarius/HidHide/releases
- Microsoft VHF documentation: https://learn.microsoft.com/en-us/windows-hardware/drivers/hid/virtual-hid-framework--vhf-
- Microsoft driver attestation signing: https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-attestation
- Microsoft driver signing tutorial: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/windows-driver-signing-tutorial
- NitroGen code repository: https://github.com/MineDojo/NitroGen
- NitroGen server: https://github.com/MineDojo/NitroGen/blob/main/scripts/serve.py
- NitroGen client: https://github.com/MineDojo/NitroGen/blob/main/nitrogen/inference_client.py
- NitroGen play preprocessing/action mapping: https://github.com/MineDojo/NitroGen/blob/main/scripts/play.py
- NitroGen license: https://github.com/MineDojo/NitroGen/blob/main/LICENSE
- NitroGen model card: https://huggingface.co/nvidia/NitroGen
- Qwen2.5-VL Ollama listing: https://ollama.com/library/qwen2.5vl
- Gemma 3 Ollama listing: https://ollama.com/library/gemma3

## Firecrawl accounting

Successful calls in this research completion batch were charged by Firecrawl; the authenticated balance decreased from 855 to 829 credits during the batch, a net delta of **26 credits**. Some search results reported individual request costs and some scrape responses did not expose a per-call receipt in the returned content. The balance delta is therefore the auditable total; no per-source allocation is claimed. The rejected rate-limit attempts were not treated as successful retrievals.