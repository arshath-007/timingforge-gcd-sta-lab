"""Generate auditable single-RTL formal negative controls."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "formal"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one mutation anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    combined = (ROOT / "rtl/gcd_binary_combined.sv").read_text(encoding="utf-8")
    split = (ROOT / "rtl/gcd_binary_split.sv").read_text(encoding="utf-8")

    n1_combined = replace_once(combined, "x <= x - y;", "x <= x - y + 1;", "N1 combined subtraction")
    (OUT / "n1_combined.sv").write_text(n1_combined, encoding="utf-8")
    (OUT / "n1_split.sv").write_text(split, encoding="utf-8")

    n3_combined = replace_once(combined, "gcd_out <= b_in;", "gcd_out <= '0;", "N3 combined zero case")
    (OUT / "n3_combined.sv").write_text(n3_combined, encoding="utf-8")
    (OUT / "n3_split.sv").write_text(split, encoding="utf-8")

    n4_combined = replace_once(combined, "common_shift <= common_shift + 1'b1;", "common_shift <= common_shift;", "N4 combined shift")
    (OUT / "n4_combined.sv").write_text(n4_combined, encoding="utf-8")
    (OUT / "n4_split.sv").write_text(split, encoding="utf-8")

    n6_combined = replace_once(combined, "end else if (x > y) begin", "end else if (x[1:0] > y[1:0]) begin", "N6 comparator")
    (OUT / "n6_combined.sv").write_text(n6_combined, encoding="utf-8")
    (OUT / "n6_split.sv").write_text(split, encoding="utf-8")


if __name__ == "__main__":
    main()
