#!/usr/bin/env python3
"""Tests of ledger.py and items.py. Run: python3 -m unittest test_ledger.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LEDGER = Path(__file__).with_name("ledger.py")
ITEMS = Path(__file__).with_name("items.py")
EVIDENCE = [{"file": "lanes/edge/wave1-ips.tsv", "label": "wave 1 IPs"}]


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.incidents = root / "incidents"
        self.work = self.incidents / "2026-11-24-test-flood"
        self.config = root / "config"
        self.config.mkdir()
        self.incidents.mkdir()
        self.items("init", str(self.incidents))
        (self.config / "indicators.tsv").write_text(
            "type\tvalue\tverdict\tincident\tfirst_seen\tlast_seen\tnote\n"
            "ip\t1.2.3.4\tnot-actor\t2026-11-01-old\t2026-11-01\t2026-11-01\tmonitor\n")
        self.run_ok("init", "--title", "Test flood", "--class", "availability", "--profile", "standard",
                    "--from", "2026-11-22 17:00", "--config", str(self.config), "--budget", "6")
        (self.work / "lanes" / "edge").mkdir()
        (self.work / "lanes" / "edge" / "wave1-ips.tsv").write_text("ip\tn\n1.2.3.4\t5\n")
        (self.work / "lanes" / "edge" / "wave1-ips.sql").write_text("-- source: ch-aws\nSELECT 1\n")

    def tearDown(self):
        self.tmp.cleanup()

    def items(self, *args):
        done = subprocess.run([sys.executable, str(ITEMS), *args], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout

    def run_ledger(self, command, *args):
        return subprocess.run([sys.executable, str(LEDGER), command, str(self.work), *args],
                              capture_output=True, text=True)

    def run_ok(self, command, *args):
        done = self.run_ledger(command, *args)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout

    def merge(self, lane, result):
        (self.work / "lanes" / f"{lane}.json").write_text(json.dumps({"lane": lane, **result}))
        return self.run_ledger("merge", f"lanes/{lane}.json")

    def ledger(self):
        return json.loads((self.work / "ledger.json").read_text())

    def edge_result(self):
        return {
            "units": [{"id": "U2", "status": "answered", "answer": "1.18M GET / from 8,038 IPs",
                       "evidence": EVIDENCE,
                       "sources": [{"source": "ch-aws", "from": "2026-11-22", "to": "2026-11-23", "status": "done"},
                                   {"source": "athena", "from": "2026-10-01", "to": "2026-10-24",
                                    "status": "skipped"}]}],
            "indicators": [{"type": "ip", "value": "1.2.3.4", "verdict": "actor", "first_seen": "2026-11-22 17:20",
                            "last_seen": "2026-11-22 17:30", "evidence": EVIDENCE}],
            "findings": [{"section": "impact", "title": "Origin", "text": "712,333 x 504 | pipe",
                          "evidence": EVIDENCE},
                         {"section": "timeline", "time": "2026-11-22 17:20:11", "title": "wave 1",
                          "text": "Wave 1 starts", "key": True, "evidence": EVIDENCE}],
            "actions": [{"text": "Add rate rule", "owner": "infra", "priority": "P0", "list": "ops",
                         "scope": "incident", "file": "infra: waf.py"},
                        {"text": "Farm 331", "owner": "partner", "priority": "P0", "list": "ops",
                         "scope": "elsewhere"}],
            "new_units": [{"lane": "payments", "question": "Did callbacks fail?"}],
            "notes": [{"source": "ch-aws", "fact": "a pod restart cuts a result", "how": "count check"}],
        }

    def test_init_seeds_the_first_wave(self):
        lanes = [u["lane"] for u in self.ledger()["units"]]
        self.assertEqual(lanes, ["activity", "edge", "control", "impact", "changes", "history"])
        self.assertTrue((self.incidents / "incident-2026-11-24-test-flood.md").is_file())

    def test_merge_plans_follow_up_and_writes_the_report(self):
        self.run_ok("start", "edge", "sonnet", "U2")
        done = self.merge("edge", self.edge_result())
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("NEW-INDICATOR ip 1.2.3.4 actor", done.stdout)
        self.assertIn("KNOWN ip 1.2.3.4: not-actor in 2026-11-01-old", done.stdout)
        self.assertIn("gap: Finish athena", done.stdout)
        self.assertIn("payments: Did callbacks fail?", done.stdout)
        self.assertIn("VERIFY F1 I1", done.stdout)
        report = (self.incidents / "incident-2026-11-24-test-flood.md").read_text()
        self.assertIn("712,333 x 504 \\| pipe", report)
        self.assertIn("[wave 1 IPs](2026-11-24-test-flood/lanes/edge/wave1-ips.tsv)", report)
        self.assertIn("| A1 | Add rate rule (`infra: waf.py`)", report)
        self.assertNotIn("Farm 331", report)
        self.assertIn("[lanes/edge/wave1-ips.tsv](lanes/edge/wave1-ips.tsv)", (self.work / "README.md").read_text())

    def test_invalid_result_changes_nothing(self):
        self.run_ok("start", "edge", "sonnet", "U2")
        bad = self.edge_result()
        bad["findings"][0]["evidence"] = [{"file": "lanes/none.tsv", "label": "x"}]
        bad["bogus"] = 1
        del bad["units"]
        done = self.merge("edge", bad)
        self.assertEqual(done.returncode, 1)
        self.assertIn("INVALID unknown top-level field bogus", done.stdout)
        self.assertIn("INVALID unit U2: no result", done.stdout)
        self.assertIn("no file lanes/none.tsv", done.stdout)
        self.assertEqual(self.ledger()["findings"], [])

    def test_verdicts_conflicts_and_final_check(self):
        self.run_ok("start", "edge", "sonnet", "U2")
        self.merge("edge", self.edge_result())
        self.run_ok("start", "edge-2", "sonnet")
        own = self.merge("edge", {"verdicts": [{"id": "F1", "state": "confirmed"}]})
        self.assertIn("is not running", own.stdout)
        self.run_ok("start", "verify-1", "opus")
        done = self.merge("verify-1", {
            "verdicts": [{"id": "F1", "state": "confirmed"},
                         {"id": "I1", "state": "rejected", "verdict": "probable", "note": "shared proxy"}],
            "indicators": [{"type": "ip", "value": "1.2.3.4", "verdict": "not-actor", "first_seen": "2026-11-01",
                            "last_seen": "2026-11-23", "evidence": EVIDENCE}]})
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("CONFLICT ip 1.2.3.4", done.stdout)
        ledger = self.ledger()
        self.assertEqual(ledger["findings"][0]["state"], "confirmed")
        self.assertEqual(ledger["indicators"][0]["verdict"], "probable")
        self.assertEqual(ledger["units"][-1]["lane"], "verify")
        check = self.run_ledger("check")
        self.assertEqual(check.returncode, 1)
        for line in ("OPEN U1 activity", "RUNNING edge-2", "NO-FIELD summary"):
            self.assertIn(line, check.stdout)
        self.assertNotIn("UNVERIFIED", check.stdout)

    def test_a_lane_does_not_verify_its_own_record(self):
        self.run_ok("start", "edge", "sonnet", "U2")
        self.merge("edge", self.edge_result())
        self.run_ok("start", "impact", "opus", "U4")
        first = self.merge("impact", {"units": [{"id": "U4", "status": "blocked", "blocked_by": "owner",
                                                 "owner": "infra", "note": "AWS case"}],
                                      "findings": [{"section": "cause", "title": "cap", "text": "16.5K rps",
                                                    "evidence": EVIDENCE}]})
        self.assertEqual(first.returncode, 0, first.stdout)
        self.run_ok("start", "impact-2", "opus")
        (self.work / "lanes" / "x.json").write_text(json.dumps(
            {"lane": "impact-2", "verdicts": [{"id": "F3", "state": "confirmed"}]}))
        self.assertEqual(self.run_ledger("merge", "lanes/x.json").returncode, 0)
        self.run_ok("start", "edge-3", "sonnet")
        ledger = self.ledger()
        ledger["findings"][0]["lane"] = "edge-3"
        (self.work / "ledger.json").write_text(json.dumps(ledger))
        done = self.merge("edge-3", {"verdicts": [{"id": "F1", "state": "confirmed"}]})
        self.assertIn("a lane does not verify its own record", done.stdout)

    def test_quick_profile_defers_follow_up(self):
        ledger = self.ledger()
        ledger["incident"]["profile"] = "quick"
        (self.work / "ledger.json").write_text(json.dumps(ledger))
        self.run_ok("start", "edge", "sonnet", "U2")
        self.merge("edge", self.edge_result())
        self.assertEqual([u["status"] for u in self.ledger()["units"][-2:]], ["deferred", "deferred"])
        self.assertIn("Appendix E. Not checked",
                      (self.incidents / "incident-2026-11-24-test-flood.md").read_text())

    def test_budget_questions_resources_lists_and_registry(self):
        for n in range(6):
            self.run_ok("start", f"lane-{n}", "sonnet")
        self.assertIn("BUDGET", self.run_ledger("start", "lane-7", "sonnet").stdout)
        self.assertIn("WAITING U7", self.run_ok("ask", "Run the paid scan?"))
        self.run_ok("answer", "U7", "no")
        self.assertTrue(self.ledger()["units"][-1]["answer"].endswith("no"))
        self.run_ok("resource", "Grant wallet DB")
        self.assertIn("CLEANUP R1", self.run_ledger("check").stdout)
        self.run_ok("resource", "removed 21:15", "--id", "R1")
        self.assertNotIn("CLEANUP", self.run_ledger("check").stdout)

        ledger = self.ledger()
        ledger["indicators"] = [{"id": "I1", "type": "ip", "value": "1.2.3.4", "verdict": "actor",
                                 "first_seen": "a", "last_seen": "b", "lane": "edge", "evidence": []}]
        (self.work / "ledger.json").write_text(json.dumps(ledger))
        learn = self.run_ok("learn")
        self.assertIn("CONFLICT ip 1.2.3.4", learn)
        self.assertIn("REGISTRY 1 rows", learn)
        self.assertIn("REGISTRY 0 rows", self.run_ok("learn"))
        self.assertEqual(len((self.config / "indicators.tsv").read_text().splitlines()), 3)


    def test_open_items_and_prune(self):
        self.run_ok("start", "edge", "sonnet", "U2")
        self.merge("edge", self.edge_result())
        self.run_ok("ask", "Run the paid scan?")
        (self.work / "lanes" / "edge" / "scratch.tsv").write_text("x\n")
        self.assertIn("ITEMS 3 added, 0 linked", self.items("merge", str(self.work)))
        self.assertIn("ITEMS 0 added", self.items("merge", str(self.work)))
        ops = (self.incidents / "open-items-ops.md").read_text()
        self.assertIn("[2026-11-24-test-flood](incident-2026-11-24-test-flood.md) A1", ops)
        self.assertIn("Farm 331", ops)
        self.assertIn("Run the paid scan?", ops)

        body = self.incidents / "rule.md"
        body.write_text("**Rule.** One canonical path.")
        self.assertIn("GROUP G1", self.items("group", str(self.incidents), "One canonical path", str(body)))
        ledger = self.ledger()
        ledger["actions"].append({"id": "A2", "lane": "edge", "status": "OPEN", "text": "Normalise the path",
                                  "owner": "gateway", "priority": "P1", "list": "dev", "scope": "incident"})
        (self.work / "ledger.json").write_text(json.dumps(ledger))
        self.run_ok("start", "report", "opus")
        bad = self.merge("report", {"items": [{"action": "A2", "item": "O9"}]})
        self.assertIn("no open item O9", bad.stdout)
        done = self.merge("report", {"items": [{"action": "A2", "group": "G1"},
                                               {"item": "O1", "status": "DONE", "note": "rule live"}]})
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("ITEMS 1 added, 0 linked to an item, 1 updated", self.items("merge", str(self.work)))
        dev = (self.incidents / "open-items-dev.md").read_text()
        self.assertIn("## G1 One canonical path", dev)
        self.assertIn("Normalise the path", dev)
        self.assertIn("| O1 | Add rate rule (`infra: waf.py`) | DONE", (self.incidents / "open-items-ops.md").read_text())
        self.assertIn("O2\tops\tP0", self.items("list", str(self.incidents)))

        self.assertIn("INVALID prune needs a clean check", self.run_ledger("prune").stdout)
        ledger = self.ledger()
        ledger["units"] = [u for u in ledger["units"] if u["status"] == "answered"]
        ledger["indicators"] = []
        ledger["findings"] = [f for f in ledger["findings"] if f["section"] == "timeline"]
        ledger["incident"].update(severity="SEV4", summary="s", what_happened="w", detection="d", status="OPEN")
        (self.work / "ledger.json").write_text(json.dumps(ledger))
        self.assertIn("PRUNED 1 files", self.run_ok("prune"))
        self.assertFalse((self.work / "lanes" / "edge" / "scratch.tsv").exists())
        self.assertTrue((self.work / "lanes" / "edge" / "wave1-ips.sql").exists())


if __name__ == "__main__":
    unittest.main()
