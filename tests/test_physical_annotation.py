import tempfile
import unittest
from pathlib import Path

from tools.physical_annotation import classify_annotation


class PhysicalAnnotationTests(unittest.TestCase):
    def _fixture(self, root: Path, annotation: str):
        log = root / "postroute.log"
        netlist = root / "final.v"
        log.write_text(
            "=== POST-ROUTE PARASITIC ANNOTATION ===\n" + annotation +
            "\n=== TIMINGFORGE POST-ROUTE SETUP CHECK ===\n",
            encoding="utf-8",
        )
        netlist.write_text(
            "module top(input a, output y);\n"
            "wire dangling_net, loaded_net;\n"
            "BUF_X1 dangling (.A(a));\n"
            "BUF_X1 no_load (.A(a), .Z(dangling_net));\n"
            "BUF_X1 connected (.A(a), .Z(loaded_net));\n"
            "BUF_X1 sink (.A(loaded_net), .Z(y));\n"
            "endmodule\n",
            encoding="utf-8",
        )
        return log, netlist

    def test_dangling_output_drivers_are_not_misreported_as_unannotated_nets(self):
        with tempfile.TemporaryDirectory() as tmp:
            log, netlist = self._fixture(
                Path(tmp),
                "Found 2 unannotated drivers.\ndangling/Z\nno_load/Z\nFound 0 partially unannotated drivers.",
            )
            result = classify_annotation(log, netlist)
            self.assertEqual(result["reported_unannotated_driver_count"], 2)
            self.assertEqual(result["dangling_unannotated_driver_count"], 2)
            self.assertEqual(result["unannotated_connected_driver_count"], 0)

    def test_connected_unannotated_driver_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            log, netlist = self._fixture(
                Path(tmp),
                "Found 1 unannotated drivers.\nconnected/Z\nFound 0 partially unannotated drivers.",
            )
            with self.assertRaisesRegex(ValueError, "connected to routed nets"):
                classify_annotation(log, netlist)


    def test_direct_output_port_is_a_connected_net(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "postroute.log"
            netlist = root / "final.v"
            log.write_text(
                "=== POST-ROUTE PARASITIC ANNOTATION ===\n"
                "Found 1 unannotated drivers.\ndriver/Z\n"
                "Found 0 partially unannotated drivers.\n"
                "=== TIMINGFORGE POST-ROUTE SETUP CHECK ===\n",
                encoding="utf-8",
            )
            netlist.write_text(
                "module top(output out);\n"
                "BUF_X1 driver (.Z(out));\n"
                "endmodule\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "connected to routed nets"):
                classify_annotation(log, netlist)

    def test_partial_annotation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            log, netlist = self._fixture(
                Path(tmp),
                "Found 0 unannotated drivers.\nFound 1 partially unannotated drivers.",
            )
            with self.assertRaisesRegex(ValueError, "partially unannotated"):
                classify_annotation(log, netlist)


if __name__ == "__main__":
    unittest.main()
