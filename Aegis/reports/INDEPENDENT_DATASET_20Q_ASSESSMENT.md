# Independent Series-7 HCS 20-Question Assessment

## Scope and method

The 20 questions and expected answers were prepared from the fictional Series-7 HCS dataset, independently of the application answer rules. The questions were then sent in order through the current local `answer_question()` path. The runtime used its ordinary rules, original curated knowledge catalog, source retrieval, and configured Groq/LiteLLM evidence-grounded fallback. No new facts or rules were added to fit these questions; the assessment-specific catalog edits from the earlier run were reverted before this run. The model received each question with the evidence retrieved by the application.

Every system answer below includes the status, route, and sources returned by the system. Judgments compare the answer to the dataset answer key and account for whether the returned sources support it. “Correct” means the requested point is answered accurately; “Partial” means a material requested detail is missing. A refusal/abstention when evidence supports the answer is counted as a miss. These are manual judgments on this 20-question sample, not a representative accuracy guarantee.

## Verdict

- Questions completed: **20/20**; execution errors: **0**.
- Fully correct: **15/20 (75%)**.
- Partial: **3/20 (15%)**.
- Abstained despite answerable evidence: **1/20 (5%)**.
- Incorrect due to an unsupported assumption: **1/20 (5%)**.
- The AI evidence fallback handled several unseen phrasings correctly, but this run does **not** establish that the system is reliable across the dataset. It still missed answerable A18 evidence (D05), omitted requested details (D01, D11, D19), and made an unsupported machine-specific firmware assumption for the field observation (D17). I would not call the assessment “fixed” or treat the system as production-validated based on this sample. The appropriate next step is to improve general evidence retrieval/selection and uncertainty handling, then rerun an independently designed assessment; do not add one-off rules for these misses.

## Results by question

### D01 — Partial

**Question:** For the current Operator Manual, what interlocks must be satisfied before startup, and what are the first two steps after that?

**Dataset-based expected answer:** Before startup, fluid must be in the normal sight-glass band, IV-21 open, E-stop reset, and access panel closed. Then turn POWER ON and press START; verify the firmware-appropriate pressure target.

**System answer** (`insufficient_evidence`, route `fallback_search`): The provided excerpts list the required interlocks (hydraulic fluid level, isolation valve IV-21 open, emergency stop reset, and maintenance panel closed) but do not contain information about the first two steps after startup.

**System sources:**
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3: “Hydraulic fluid level is within the normal band on the sight glass.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3: “Isolation valve IV-21 is OPEN.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3: “The emergency stop circuit is RESET.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3 warning: “Do not start the Hydraulic Power Unit with the maintenance access panel removed.”

**Dataset reference used for answer key:** manuals/operator_manual.pdf p.1 §4.3; configuration/configuration_export.json $.startup_interlocks

**Comparison:** Correctly lists four startup interlocks, but misses POWER ON and START, which the question explicitly asks for.

### D02 — Correct

**Question:** How do the normal HPU sensor and pressure target differ between firmware 3.1 and 3.2?

**Dataset-based expected answer:** Firmware 3.1 uses PS-04 with a 180 bar target. Firmware 3.2 and later use PS-04A with a 200 bar target.

**System answer** (`answered`, route `normal_pressure`): In firmware 3.2 and later the HPU’s normal discharge‑pressure setpoint is **200 bar**, measured with the **PS‑04A** sensor.
In firmware versions prior to 3.2 the normal discharge‑pressure setpoint is **180 bar**, measured with the original **PS‑04** sensor.

**System sources:**
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3 and §5; p. 2: “This is the normal operating pressure for software revision 3.2 and later.”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1042.pdf` — p. 1, §1: “the normal HPU discharge pressure setpoint is revised from 180 bar to 200 bar.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 2, §5: “On revisions prior to 3.2, normal discharge pressure was 180 bar, measured by the original PS-04 sensor.”
- `aegis-dataset/aegis-dataset/manuals/legacy_manual_v1.html` — §5 Normal Operating Ranges: “Normal HPU discharge pressure is 180 bar, as measured by pressure sensor PS-04.”

**Dataset reference used for answer key:** manuals/operator_manual.pdf p.1 §2, §4.3; p.2 §5; engineering_bulletins/ECN-1042.pdf p.1 §1; reference/revision_history.xlsx Revision History row 4

**Comparison:** Correctly maps firmware 3.1 to PS-04/180 bar and 3.2+ to PS-04A/200 bar.

### D03 — Correct

**Question:** Does ECN-1058 retune A17, or only correct the sensor reference used to evaluate it? What stays unchanged?

**Dataset-based expected answer:** ECN-1058 corrects the active sensor reference by firmware and is documentation-only. Alarm thresholds (150 bar low and 220 bar high) and the normal operating setpoint remain unchanged.

**System answer** (`answered`, route `fallback_search`): ECN‑1058 does not retune Alarm A17; it only corrects the documentation so that the alarm’s low‑pressure condition is evaluated against whichever pressure sensor (PS‑04 or PS‑04A) is active for the installed software revision. The alarm’s threshold values (150 bar low‑pressure, 220 bar high‑pressure) and the underlying alarm logic remain unchanged, and no firmware or hardware changes are required.

**System sources:**
- `aegis-dataset/aegis-dataset/reference/revision_history.xlsx` — Revision History!A5:D5: “3.2.1 | 2025-11-18 | Documentation correction: Alarm A17 condition text no longer names a specific sensor (PS-04 or PS-04A) ... Alarm thresholds unchanged. See ECN-1058.”
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — p. 1, AEG-AL-700 Rev 5, sensor note: “The 150 bar and 220 bar thresholds shown above are unchanged by ECN-1058.”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1058.pdf` — Page 1: “Engineering Change Notice [ECN]-[1058] Engineering Change Notice [ECN]-[1058] [ECN] Number: [ECN]-[1058] Title: Alarm [A17] Threshold [Reference] Correction Effective: Immediately upon publication References: [ECN]-1042 Status: Released 1. Description of Change The Alarm [Reference] … ”
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — Page 1: “ … A19 Pressure [sensor] RED 1. [Sensor] wiring fault Replace [sensor] per signal invalid 2. [Sensor] drift beyond Maintenance Manual tolerance (see [ECN]-1042) Section 6. * Shutdown Procedure 4.7 applies [only] when [A17] persists beyond 10 … ”

**Dataset reference used for answer key:** engineering_bulletins/ECN-1058.pdf p.1 §1–2; reference/alarm_reference.pdf p.1 sensor-reference note

**Comparison:** Explains the sensor-reference correction and that the thresholds and alarm logic remain unchanged; cites ECN-1058 and the alarm reference.

### D04 — Correct

**Question:** Once A17 lasts past the 10-second point, what actions make up the required shutdown?

**Dataset-based expected answer:** Follow Shutdown Procedure 4.7: close IV-21, confirm pressure decay, switch POWER off, apply LOTO, and troubleshoot. Do not only silence the alarm.

**System answer** (`answered`, route `alarm_a17_persistent_action`): If alarm A17 remains active for more than 10 seconds, you must follow Shutdown Procedure 4.7. The required steps are:

1. Close valve IV‑21.
2. Verify that system pressure is decaying.
3. Set the POWER selector to OFF.
4. Apply the site lockout/tagout procedure.
5. After the shutdown, proceed with troubleshooting.

Simply silencing the alarm is not an acceptable response.

**System sources:**
- `aegis-dataset/aegis-dataset/manuals/maintenance_manual.pdf` — p. 1, §4 and Shutdown Procedure 4.7: “If alarm A17 persists for more than 10 seconds, execute Shutdown Procedure 4.7 ... close IV-21, confirm pressure decay, set POWER selector to OFF, tag out per site lockout/tagout procedure”
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — p. 1, A17 row and footnote: “If persistent > 10 s, run Shutdown Proc. 4.7. A transient A17 that clears on its own during normal valve transition does not require Procedure 4.7.”

**Dataset reference used for answer key:** manuals/maintenance_manual.pdf p.1 §4 and Shutdown Procedure 4.7; reference/alarm_reference.pdf p.1 A17 row and footnote

**Comparison:** Gives the complete required shutdown sequence and warns against merely silencing the alarm.

### D05 — Miss — abstention

**Question:** For A18, what pressure condition and causes are listed, and what restart restriction follows?

**Dataset-based expected answer:** A18 indicates pressure above 220 bar; listed causes are a relief-valve fault or setpoint misconfiguration. Stop the HPU and do not restart until pressure relief is verified.

**System answer** (`insufficient_evidence`, route `fallback_search`): I could not find a matching supported claim for this question. Here are the closest indexed passages. Their presence does not by itself establish an answer.

**System sources:**
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — Page 1: “ … 4.7* signal invalid [A18] Hydraulic [pressure] AMBER 1. Relief valve fault Stop the HPU. Do not above 220 bar 2. Setpoint [restart] until [pressure] misconfiguration relief is verified. A19 [Pressure] sensor RED 1. Sensor wiring … ”
- `aegis-dataset/aegis-dataset/configuration/configuration_export.json` — $.alarms.A18.description: “$.alarms.[A18].description = "hydraulic_[pressure]_high"”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Sheet Components, row 9, cells A9:F9: “A9=[A18] | B9=Alarm: Hydraulic [Pressure] High | C9=— | D9=N/A (software alarm) | E9=Active | F9=See Alarm Reference AEG-AL-700.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — Page 2: “ … Alarms See the Aegis Alarm Reference (AEG-AL-700) for the full alarm list, including alarm A17 (Hydraulic [Pressure] Low), its possible [causes], and required operator actions. 7. Controller Reset Do not reset the PLC-03 … ”
- `aegis-dataset/aegis-dataset/screenshots/screen_02_alarms.png` — Alarm list and A17 timer: “ … A17 Hydraulic [Pressure] Low CLEARED at 08:14:02; A19 [Pressure] Sensor Signal Invalid CLEARED at 03-11 22:40; A17 Hydraulic [Pressure] Low ACTIVE at 08:14:57; [A18] Hydraulic [Pressure] High INACTIVE. Banner: Alarm … ”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1058.pdf` — Page 1: “ … Alarm A17's low-[pressure] [condition] is evaluated against whichever [pressure] sensor is active for the installed software revision (PS-04 prior to revision 3.2, PS-04A on revision 3.2 and later). The alarm … ”
- `aegis-dataset/aegis-dataset/configuration/configuration_export.json` — $.alarms.A18.persistence_before_shutdown_seconds: “$.alarms.[A18].persistence_before_shutdown_seconds = null”
- `aegis-dataset/aegis-dataset/reference/terminology_glossary.docx` — Table 1, row 7: “Alarm | A system-generated notification indicating an out-of-tolerance or fault [condition]. See the Alarm Reference for the current alarm list.”

**Dataset reference used for answer key:** reference/alarm_reference.pdf p.1 A18 row; configuration/configuration_export.json $.sensors.sensor_ps04a_alarm_high_bar

**Comparison:** The dataset supports the A18 threshold, listed causes, and restart restriction, but the system abstained after retrieving only weak/partial A18 evidence.

### D06 — Correct

**Question:** Is PS-04A a form-fit replacement for PS-04 on firmware 3.1?

**Dataset-based expected answer:** No. PS-04A is not a form-fit-function replacement and requires firmware 3.2 or later; PS-04 is used before 3.2.

**System answer** (`answered`, route `sensor_ps04_vs_ps04a`): No. PS‑04A is not a form‑fit‑function replacement for PS‑04, and it requires controller firmware revision 3.2 or later. Consequently, on firmware 3.1 it cannot serve as a direct replacement.

**System sources:**
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1042.pdf` — p. 1, §1: “pressure sensor PS-04 is replaced by pressure sensor PS-04A at the HPU discharge line.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Components!A4:F5: “PS-04 | Pressure Sensor 04 | ... | Superseded | Superseded by PS-04A effective software rev 3.2.”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1042.pdf` — p. 1, §1: “PS-04A uses an updated signal conditioning circuit and is not a form-fit-function replacement for PS-04; controller firmware must be at revision 3.2 or later to read PS-04A correctly.”

**Dataset reference used for answer key:** engineering_bulletins/ECN-1042.pdf p.1 §1; reference/component_register.xlsx Components rows 4–5

**Comparison:** Correctly says PS-04A is not form-fit-function and requires firmware 3.2+, so it cannot be a direct replacement on 3.1.

### D07 — Correct

**Question:** What faults can cause an A17 low-pressure event, and which sensor is checked on newer software?

**Dataset-based expected answer:** Causes include IV-21 being closed or partly closed, low fluid, or an invalid sensor signal. The active sensor is PS-04 before firmware 3.2 and PS-04A on 3.2 or later.

**System answer** (`answered`, route `fallback_search`): A17 can be triggered by a closed or partially closed IV-21 isolation valve, low hydraulic fluid level, or an invalid pressure‑sensor signal. On software revisions 3.2 and later the alarm checks the pressure reading from sensor PS‑04A (the active sensor for those revisions).

**System sources:**
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — p. 1, AEG-AL-700 Rev 5, A17 row and sensor note: “Hydraulic pressure below 150 bar ... whichever pressure sensor is active for the installed software revision (PS-04 or PS-04A).”
- `aegis-dataset/aegis-dataset/reference/alarm_reference.pdf` — p. 1, AEG-AL-700 Rev 5, A17 row: “1. IV-21 closed or partially closed; 2. Low hydraulic fluid; 3. Pressure sensor signal invalid”
- `aegis-dataset/aegis-dataset/reference/revision_history.xlsx` — Revision History!A5:D5: “3.2.1 | 2025-11-18 | Documentation correction: Alarm A17 condition text no longer names a specific sensor (PS-04 or PS-04A) ... Alarm thresholds unchanged. See ECN-1058.”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1058.pdf` — Page 1: “ … Alarm [A17]'s [low]-[pressure] condition is evaluated against whichever [pressure] [sensor] is active for the installed [software] revision (PS-04 prior to revision 3.2, PS-04A on revision 3.2 and later). The alarm … ”

**Dataset reference used for answer key:** reference/alarm_reference.pdf p.1 A17 row and sensor note; engineering_bulletins/ECN-1058.pdf p.1 §1

**Comparison:** Gives all listed A17 causes and identifies PS-04A as the sensor on software 3.2+; the question only asks which sensor is checked on newer software.

### D08 — Correct

**Question:** What does the documentation say about resetting PLC-03 when pressure is exactly 50 bar?

**Dataset-based expected answer:** Reset is permitted only below 50 bar and forbidden above 50 bar. The supplied documentation does not specify what to do at exactly 50 bar.

**System answer** (`answered`, route `controller_reset`): The documentation permits resetting PLC‑03 only after the active pressure sensor reads **below 50 bar** and explicitly forbids resetting while pressure is **above 50 bar**. It does not specify what should be done when the pressure is exactly 50 bar.

**System sources:**
- `aegis-dataset/aegis-dataset/manuals/maintenance_manual.pdf` — p. 1, §3: “controller reset is only permitted when pressure ... reads below 50 bar.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 2, §7: “Do not reset the PLC-03 controller while hydraulic pressure is above 50 bar.”

**Dataset reference used for answer key:** manuals/maintenance_manual.pdf p.1 §3; manuals/operator_manual.pdf p.2 §7; configuration/configuration_export.json $.controller_reset

**Comparison:** Correctly preserves the strict below/above 50 bar limits and says exactly 50 bar is unspecified.

### D09 — Correct

**Question:** Which named assembly location does the Component Register assign to IV-21?

**Dataset-based expected answer:** IV-21 is located in the Hydraulic Module.

**System answer** (`answered`, route `valve_location`): The Component Register assigns IV‑21 to the **Hydraulic Module**.

**System sources:**
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Components!A3:D3: “IV-21 | Isolation Valve 21 | Isolation Valve; IV21 | Hydraulic Module”

**Dataset reference used for answer key:** reference/component_register.xlsx Components row 3

**Comparison:** Correctly identifies the Hydraulic Module as IV-21's registered location.

### D10 — Correct

**Question:** How does PS-40's documented location distinguish it from PS-04?

**Dataset-based expected answer:** PS-40 is in the Coolant Loop, Skid B, and is unrelated to the HPU discharge pressure circuit served by PS-04/PS-04A.

**System answer** (`answered`, route `fallback_search`): PS-40 is documented as being installed in the Coolant Loop, Skid B, and explicitly noted as not part of the HPU discharge circuit, whereas PS‑04 (and PS‑04A) are located on the HPU discharge line.

**System sources:**
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Components!A4:F6: “PS-40 ... Coolant Loop, Skid B ... NOT related to the HPU discharge circuit. Do not confuse with PS-04 / PS-04A.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Sheet Components, row 6, cells A6:F6: “A6=PS-[40] | B6=Pressure Sensor [40] | C6=P40; PS40 | D6=Coolant Loop, Skid B | E6=Active | F6=NOT related to the HPU discharge circuit. Do not confuse with PS-[04] / PS-04A.”
- `aegis-dataset/aegis-dataset/scans/scanned_appendix_calibration.pdf` — Page 1; Calibration record and results: “ … This calibration record supersedes the field data sheet used prior to the PS-[04] to PS-04A sensor change (see ECN-1042). Span reference target is 200 bar, consistent with software revision 3.2 operating pressure … ”

**Dataset reference used for answer key:** reference/component_register.xlsx Components rows 4–6; configuration/configuration_export.json $.sensors.sensor_ps40_zone and sensor_ps40_note

**Comparison:** Correctly distinguishes PS-40 in the Coolant Loop, Skid B from the HPU discharge sensors.

### D11 — Partial

**Question:** Does the training slide deck introduce the Auxiliary Reservoir as a new component for every machine?

**Dataset-based expected answer:** No. It is present on most Line 4/5 configurations, where its small reservoir tops up the main reservoir during peak demand. It is absent from the standard Operator Manual.

**System answer** (`answered`, route `training_additions`): The training slide deck mentions the Auxiliary Reservoir only as a configuration detail for most Line 4/5 setups—it is not presented as a new component that appears on every machine.

**System sources:**
- `aegis-dataset/aegis-dataset/extra/training_slide_excerpt.pptx` — slide 2: “on most Line 4/5 configurations, tops up from a smaller Auxiliary Reservoir during peak demand. Note: Auxiliary Reservoir is a Line 4/5-specific configuration detail and is not covered in the standard Operator Manual.”
- `aegis-dataset/aegis-dataset/extra/training_slide_excerpt.pptx` — slides 1–3, all slide text and tables: “Reviewed slide titles, slide text, startup-check table, and speaker notes. No A-series alarm identifier occurs.”

**Dataset reference used for answer key:** training/maintenance_training_slides.pptx slide 2; manuals/operator_manual.pdf p.1

**Comparison:** Correctly rejects the claim that the Auxiliary Reservoir is on every machine and gives its Line 4/5 scope, but omits its top-up role and that it is absent from the standard Operator Manual.

### D12 — Correct

**Question:** What sensor tag appears in diagnostics and does it match a registered component?

**Dataset-based expected answer:** The screenshot shows P.S.04-A, which maps to registered PS-04A at the HPU discharge. It shows firmware 3.2.1, a 4–20 mA signal, 200.3 bar and in-tolerance status; it is a screenshot, not live telemetry.

**System answer** (`answered`, route `diagnostics_tag`): The diagnostics screenshot shows the sensor tag **P.S.04‑A** (firmware 3.2.1). This tag corresponds to the registered component **PS‑04A** in the component register (the pressure sensor for the HPU discharge line), so the tag displayed in diagnostics matches a registered component.

**System sources:**
- `aegis-dataset/aegis-dataset/screenshots/screen_03_diagnostics.png` — Sensor Diagnostics card, Tag and Firmware Rev. fields: “Tag P.S.04-A ... Firmware Rev. 3.2.1. Screen note: this screen displays the sensor tag as printed on the physical unit label.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Components!A5:F5: “PS-04A | Pressure Sensor 04A | P04A; PS04A | HPU discharge line | Active”

**Dataset reference used for answer key:** screenshots/screen_03_diagnostics_card.png; reference/component_register.xlsx Components row 5

**Comparison:** Identifies screenshot tag P.S.04-A and maps it to registered PS-04A at the HPU discharge. The other telemetry details were not required by the question.

### D13 — Correct

**Question:** What readings did the PS-04A calibration record show at its three reference points?

**Dataset-based expected answer:** On 2026-01-09, the record shows 0 bar reference → 0.1 bar, 100 → 99.6 bar, and 200 → 199.4 bar; all three passed. The record is an uncontrolled scan.

**System answer** (`answered`, route `fallback_search`): Zero (0%): reference 0 bar, reading 0.1 bar (PASS); Mid (50%): reference 100 bar, reading 99.6 bar (PASS); Span (100%): reference 200 bar, reading 199.4 bar (PASS).

**System sources:**
- `aegis-dataset/aegis-dataset/scans/scanned_appendix_calibration.pdf` — p. 1, Calibration Points table: “Zero (0%): 0 bar, 0.1 bar, PASS. Mid (50%): 100 bar, 99.6 bar, PASS. Span (100%): 200 bar, 199.4 bar, PASS.”
- `aegis-dataset/aegis-dataset/scans/scanned_appendix_calibration.pdf` — Page 1; Calibration record and results: “ … SENSOR [CALIBRATION] [RECORD]. Aegis Series-7 HCS (scanned from field service binder, uncontrolled copy). Sensor Tag: PS-[04A]. Location: HPU discharge line. [Calibration] Date: 2026-01-09. Technician: R. Okafor. [Calibration] [points]: Zero (0%), [reference] 0 … ”

**Dataset reference used for answer key:** scans/scanned_appendix_calibration.pdf p.1 Calibration Points table and header

**Comparison:** Reports all three calibration readings and PASS results. The question asks for the three reference points; date and scan status are additional context, not required to answer it.

### D14 — Correct

**Question:** What periodic recalibration frequency does the PS-04A record prescribe?

**Dataset-based expected answer:** It specifies no interval. It says to confirm recalibration frequency against the applicable maintenance schedule, which is not included in the binder.

**System answer** (`abstained`, route `calibration_interval_ps04a`): The scanned calibration record does not specify a periodic recalibration frequency for PS‑04A. It notes that the recalibration interval should be confirmed against the applicable maintenance schedule, which is not included in the provided documents.

**System sources:**
- `aegis-dataset/aegis-dataset/scans/scanned_appendix_calibration.pdf` — p. 1, note below calibration table: “No calibration interval is specified for PS-04A on this form; recalibration frequency should be confirmed against the applicable maintenance schedule, which is not included in this binder.”

**Dataset reference used for answer key:** scans/scanned_appendix_calibration.pdf p.1 note below table

**Comparison:** Correctly says no interval is specified and directs the reader to the maintenance schedule, which is not included.

### D15 — Correct

**Question:** Do the supplied drawings establish that a three-phase 400 V site supply is compatible?

**Dataset-based expected answer:** No. Compatibility is not established. The register lists a 480 V incoming disconnect and a 480:120 V transformer, but the package gives no phase count or 400 V compatibility statement.

**System answer** (`abstained`, route `power_compatibility`): The supplied drawings do not establish that a three‑phase 400 V site supply is compatible. The electrical diagram and component register only reference a 480 V incoming disconnect and a 480 : 120 V control transformer, with no mention of three‑phase 400 V compatibility. Consequently, the compatibility with a three‑phase 400 V supply is not demonstrated by the provided package.

**System sources:**
- `aegis-dataset/aegis-dataset/diagrams/system_diagram_electrical.png` — AEG-DWG-E02 labels: “The drawing labels a 480:120V control transformer and 24VDC supplies. It gives no three-phase 400V compatibility specification.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Components!A12:F13: “Q1 ... 480V incoming disconnect. T1 ... 480:120V control power.”

**Dataset reference used for answer key:** diagrams/system_diagram_electrical.png; reference/component_register.xlsx Components rows 12–13

**Comparison:** Correctly states compatibility is not established, cites the 480 V and 480:120 V ratings, and avoids inferring phase count.

### D16 — Correct

**Question:** What incoming voltage and transformer ratio are actually listed for the electrical assembly?

**Dataset-based expected answer:** The Component Register lists Q1 as a 480 V incoming disconnect and T1 as a 480:120 V control transformer. The drawing also shows 24 VDC PLC and sensor-loop components; no phase count is given.

**System answer** (`answered`, route `fallback_search`): The drawing lists a 480 V incoming supply and a control transformer with a 480:120 V ratio.

**System sources:**
- `aegis-dataset/aegis-dataset/diagrams/system_diagram_electrical.png` — diagram labels and topology: “MAIN DISCONNECT Q1; CONTROL XFMR T1 480:120V; PLC-03 24VDC POWER SUPPLY; SENSOR LOOP POWER 24VDC.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Sheet Components, row 12, cells A12:F12: “A12=Q1 | B12=Main Disconnect | C12=— | D12=Control Cabinet 1 | E12=Active | F12=480V [incoming] disconnect.”
- `aegis-dataset/aegis-dataset/reference/component_register.xlsx` — Sheet Components, row 13, cells A13:F13: “A13=T1 | B13=Control [Transformer] | C13=— | D13=Control Cabinet 1 | E13=Active | F13=480:120V control power.”

**Dataset reference used for answer key:** reference/component_register.xlsx Components rows 12–13; diagrams/system_diagram_electrical.png

**Comparison:** Correctly returns the requested 480 V supply and 480:120 V transformer ratio with register citations.

### D17 — Incorrect — unsupported assumption

**Question:** Can the field note's roughly 175 bar reading be treated as the controlled normal setpoint?

**Dataset-based expected answer:** No. It is an approximate reading from an uncalibrated gauge, with firmware unknown and no HMI cross-check. The note recommends checking with a calibrated gauge, so it is a low-trust observation rather than the controlled setpoint.

**System answer** (`answered`, route `fallback_search`): No, the approximately 175 bar reading in the field note should not be treated as the controlled normal setpoint; the documented normal discharge pressure setpoint for the applicable software revision (3.2) is 200 bar.

**System sources:**
- `aegis-dataset/aegis-dataset/low_trust/site_survey_notes.docx` — paragraphs 3 and 7: “gauge on the local panel ... about 175 bar during a normal run ... Could be the gauge is a little off, didn't have a calibrated reference ... didn't get a chance to check what software revision the controller is running.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §4.3 and §5; p. 2: “This is the normal operating pressure for software revision 3.2 and later.”
- `aegis-dataset/aegis-dataset/reference/revision_history.xlsx` — Revision History!A4:D4: “3.2 | 2025-09-30 | Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar to 200 bar. See ECN-1042.”
- `aegis-dataset/aegis-dataset/configuration/configuration_export.json` — $.sensors.sensor_ps04a_threshold_bar and $.revision_applicability.sensor_ps04a_threshold_bar: “sensor_ps04a_threshold_bar = 200; applies_from_firmware = "3.2"”
- `aegis-dataset/aegis-dataset/engineering_bulletins/ECN-1042.pdf` — Page 1: “ … Alongside the sensor change, the [normal] HPU discharge pressure [setpoint] is revised from 180 [bar] to 200 [bar]. This is a deliberate process change, not a sensor calibration artifact: the higher [setpoint] improves press cycle time … ”
- `aegis-dataset/aegis-dataset/scans/scanned_appendix_calibration.pdf` — Page 1; Calibration record and results: “ … Zero (0%), reference 0 [bar], [reading] 0.1 [bar], PASS; Mid (50%), reference 100 [bar], [reading] 99.6 [bar], PASS; Span (100%), reference 200 [bar], [reading] 199.4 [bar], PASS. This calibration record supersedes the [field] … ”

**Dataset reference used for answer key:** low_trust/site_survey_notes.docx paragraphs 3, 4, 7

**Comparison:** It correctly rejects the field note as a setpoint, but then asserts the applicable revision is 3.2 and the target is 200 bar even though the field note says firmware is unknown. That machine-specific setpoint is not established.

### D18 — Correct

**Question:** What does the supplied revision history say about software 3.3, and does the package show a released change?

**Dataset-based expected answer:** The revision history lists 3.3 as planned for 2026-04-07 for extended diagnostics logging, with no sensor or setpoint change planned, and says it is not yet published. The supplied package does not establish that it was later released.

**System answer** (`answered`, route `fallback_search`): The revision history entry for software version 3.3 indicates it is scheduled for 2026‑04‑07, with the change described as “extended diagnostics logging” and notes that it is not yet published. No released change for version 3.3 appears in the supplied package.

**System sources:**
- `aegis-dataset/aegis-dataset/reference/revision_history.xlsx` — Sheet Revision History, row 6, cells A6:D6: “A6=[3.3] | B6=2026-04-07 (planned) | C6=Scheduled: extended diagnostics logging. No sensor or setpoint changes currently planned. | D6=Not yet published”

**Dataset reference used for answer key:** reference/revision_history.xlsx Revision History row 6

**Comparison:** Correctly reports 3.3 as planned for 2026-04-07, extended diagnostics logging, and not yet published in the supplied package.

### D19 — Partial

**Question:** Which alternate names in the documentation refer to the HPU assembly?

**Dataset-based expected answer:** The documentation also calls it the Hydraulic Unit, HP unit, Hydraulic Power Pack, hydraulic pack, or simply the unit.

**System answer** (`answered`, route `fallback_search`): Hydraulic Unit, HP unit, Hydraulic Power Pack, Hydraulic Power Unit

**System sources:**
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — p. 1, §1: “the Hydraulic Power Unit may also be referred to as the Hydraulic Unit or the HP unit ... All three terms refer to the same physical assembly.”
- `aegis-dataset/aegis-dataset/manuals/operator_manual.pdf` — Page 1: “ … All three terms [refer] to the same physical [assembly]. 2. Key Components Reference Component Function [HPU] Hydraulic Power Unit Generates and regulates hydraulic pressure IV-21 Isolation Valve 21 Isolates the [HPU] from the press circuit … ”

**Dataset reference used for answer key:** manuals/operator_manual.pdf p.1 §1; reference/component_register.xlsx Components row 2; training/maintenance_training_slides.pptx slide 2

**Comparison:** Supplies several documented aliases but omits “hydraulic pack” and “the unit”.

### D20 — Correct

**Question:** In the wiring diagram, what devices are associated with TB-7's J-14 and J-15 branches?

**Dataset-based expected answer:** TB-7 branch J-14 goes to the pressure transducer (identified as HPU discharge PS-04A); J-15 goes to the IV-21 solenoid.

**System answer** (`answered`, route `fallback_search`): J-14 branch connects the HPU discharge pressure transducer (PS‑04A) and J-15 branch connects the IV‑21 solenoid valve.

**System sources:**
- `aegis-dataset/aegis-dataset/diagrams/wiring_diagram.pdf` — Page 1: “Aegis Series-[7] HCS — Instrumentation [Wiring] [Diagram] (AEG-DWG-W03) Terminal block and connector references are local to this drawing. PLC-03 Terminal Block TB-[7] Connector Connector J-[14] J-[15] PRESSURE XDCR IV-21 … ”

**Dataset reference used for answer key:** diagrams/wiring_diagram.pdf p.1 diagram and note; reference/component_register.xlsx Components rows 5 and 11

**Comparison:** Correctly maps TB-7 J-14 to the PS-04A pressure transducer and J-15 to the IV-21 solenoid.

## Summary of misses

- **D01:** The source search returned startup interlocks but not the following POWER ON / START sequence in the model context.
- **D05:** The A18 evidence retrieval did not supply enough usable context to the model, leading to a non-answer.
- **D17:** The system rejected the low-trust observation but then assumed revision 3.2 despite the note saying the installed revision was unknown.
- **D11 and D19:** The answer was directionally right but incomplete for the asked scope.

## Artifact and raw run

The raw machine-readable result, including each question, expected answer, system response, route, status, and citations, is saved at `reports/INDEPENDENT_DATASET_20Q_ASSESSMENT_RESULTS.json`. The assessment runner completed without execution errors.
