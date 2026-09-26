# Escalation rules (applied by code; explain them, do not change them)

- URGENT: threat_type is incitement AND there is a real-world call to action (time/place to gather),
  OR CIB score >= 80 with severity >= 4.
- ALERT: organized_misinformation or targeted_harassment with CIB score >= 60.
- MONITOR: everything else, including benign_coordination.
