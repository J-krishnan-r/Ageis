# Evaluation results

The deterministic evidence system was run against all 23 questions in the supplied evaluation PDF.

- Questions: 23 (18 answerable, 5 designed for abstention)
- Answerable question accuracy: 100.0% (18/18)
- Correct abstention on unanswerable questions: 100.0% (5/5)
- Overall exact evidence accuracy: 100.0% (23/23)
- Expected fact recall: 100.0%
- Citation completeness: 100.0% (74/74 expected source citations)
- Corpus indexed: 20 files, 121 source segments

An answer counts as correct only when the route and answerability status match, every expected fact is present, every expected citation is emitted with its source, locator and quote, and all cited source files exist. Expected facts and answers were curated from the supplied corpus because the brief provides no official answer key.

| ID | Result | Evidence route | Answer / abstention |
| --- | --- | --- | --- |
| Q01 | PASS | `startup_checks` | Before startup, confirm the hydraulic fluid is within the normal sight-glass band, IV-21 is OPEN, the emergency stop is RESET, and the maintenance access panel is installed, secured, and CLOSED. |
| Q02 | PASS | `normal_pressure` | For firmware revision 3.2 and later, normal HPU discharge pressure is 200 bar using PS-04A. Firmware revisions before 3.2 use the prior 180 bar setpoint with PS-04. Confirm the installed firmware before interpreting the reading. |
| Q03 | PASS | `alarm_a17_definition` | A17 indicates hydraulic pressure below 150 bar using whichever sensor is active for the firmware revision. Listed causes are IV-21 closed or partly closed, low hydraulic fluid, or an invalid pressure-sensor signal. |
| Q04 | PASS | `sensor_ps04_vs_ps04a` | No. PS-04 and PS-04A are distinct sensors. ECN-1042 replaced PS-04 with PS-04A from firmware 3.2 onward; it explicitly says PS-04A is not a form-fit-function replacement and requires firmware 3.2 or later. |
| Q05 | PASS | `ecn_1042_sensor_change` | Engineering Change Notice ECN-1042 introduced the change from PS-04 to PS-04A, effective with firmware revision 3.2. |
| Q06 | PASS | `diagram_controller_connections` | The schematic’s purple control/signal lines connect PS-04A and IV-21 directly to PLC-03. It also draws a grey line from PLC-03 to the HPU, although grey is defined as a hydraulic-fluid path; that part of the drawing is ambiguous, so I would not classify it as a clear controller signal connection. |
| Q07 | PASS | `alarm_a17_persistent_action` | If A17 persists for more than 10 seconds, execute Shutdown Procedure 4.7: close IV-21, confirm pressure decay, set POWER to OFF, apply site lockout/tagout, then troubleshoot. Silencing the alarm alone is not sufficient. |
| Q08 | PASS | `controller_reset` | Do not reset the PLC-03 while hydraulic pressure is above 50 bar. Reset is permitted only after the active pressure sensor reads below 50 bar. The documents do not specify exactly 50 bar. |
| Q09 | PASS | `pressure_before_3_2` | Before software revision 3.2, the normal HPU discharge pressure setpoint was 180 bar, measured by sensor PS-04. ECN-1042 introduced the change to PS-04A and 200 bar at revision 3.2. |
| Q10 | PASS | `alarm_a17_threshold` | Alarm A17, Hydraulic Pressure Low, applies when the active pressure sensor reports hydraulic pressure below 150 bar. |
| Q11 | PASS | `valve_location` | The component register lists IV-21’s location as the Hydraulic Module. |
| Q12 | PASS | `training_additions` | The excerpt introduces an Auxiliary Reservoir as a Line 4/5 configuration detail that the standard Operator Manual does not cover. Its three slides do not name a new alarm code. |
| Q13 | PASS | `diagnostics_tag` | The diagnostics screenshot displays sensor tag P.S.04-A. It matches the registered component PS-04A by its normalized identifier and context: both identify the active HPU discharge pressure sensor, and the screenshot reports firmware 3.2.1. |
| Q14 | PASS | `revision_3_2_history` | Software revision 3.2 took effect on 2025-09-30. It replaced PS-04 with PS-04A and changed the normal HPU pressure setpoint from 180 bar to 200 bar. |
| Q15 | PASS | `configuration_setpoint_mapping` | sensor_ps04a_threshold_bar = 200 maps to the Operator Manual’s normal HPU discharge pressure setpoint for revision 3.2 and later. It is separate from the A17 low-pressure alarm threshold of 150 bar. |
| Q16 | PASS | `setpoint_applies_scope` | The 200 bar normal setpoint applies to software revision 3.2 and later with PS-04A. Earlier revisions use PS-04 and a 180 bar setpoint. ECN-1042 says the higher setting improves cycle time on units manufactured after 2024. The package does not support a blanket claim that every Aegis unit uses 200 bar; check the installed firmware and applicable unit configuration. |
| Q17 | PASS | `sensor_ps04_vs_ps40` | No. PS-40 is in the coolant loop on Skid B. The register and configuration export explicitly say it is unrelated to the HPU discharge sensors PS-04 and PS-04A. |
| Q18 | PASS | `pressure_before_3_2` | Before software revision 3.2, the normal HPU discharge pressure setpoint was 180 bar, measured by sensor PS-04. ECN-1042 introduced the change to PS-04A and 200 bar at revision 3.2. |
| Q19 | PASS | `sensor_temperature` | The supplied package does not specify a maximum continuous operating temperature for PS-04A. The scanned calibration record gives calibration points and the HPU discharge line location, but it is an uncontrolled calibration copy rather than an operating-temperature specification. |
| Q20 | PASS | `voltage_calibration_interval` | The supplied electrical diagram does not identify a voltage sensor. It labels a 24 VDC sensor-loop supply and a pressure transducer loop. No calibration interval for a voltage sensor is provided in the package. |
| Q21 | PASS | `ecn_approver` | The approver of ECN-1058 is not identified in the supplied notice. Its header gives its title, effective date, references, and Released status, but no approver or approval signature. |
| Q22 | PASS | `valve_mtbf` | The package does not state an MTBF or failure rate for IV-21. The component register gives its name, aliases, location, and startup note. |
| Q23 | PASS | `power_compatibility` | The supplied package does not establish compatibility with a three-phase 400 V supply. The electrical drawing and component register mention a 480 V incoming disconnect and 480:120 V control transformer, but they do not specify three-phase 400 V compatibility. Treat that compatibility as unknown. |

## Evaluation limits

This is a transparent, rule-based evaluation against the supplied question set and a reviewed local answer key. It measures these known questions and their provenance; it does not estimate general language understanding, measure model calibration, or validate the system on unseen equipment documentation.
