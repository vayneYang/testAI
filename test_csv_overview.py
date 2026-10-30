import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from csv_overview import main, summarize


class OverviewTests(unittest.TestCase):
    def check_csv(self, content, expected):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "中文.csv"
            path.write_text(content, encoding="utf-8")
            self.assertEqual(summarize(path), expected)

    def test_chinese_bom_and_empty_values(self):
        self.check_csv("\ufeff姓名,城市\n张三,北京\n李四, \n王五\n\n",
                       (["姓名", "城市"], 3, [0, 2]))

    def test_empty(self):
        self.check_csv("", ([], 0, []))

    def test_header_only(self):
        self.check_csv("甲,乙\n", (["甲", "乙"], 0, [0, 0]))

    def test_quoted_fields(self):
        self.check_csv('甲,乙\n"含,逗号","跨\n行"\n,\n',
                       (["甲", "乙"], 2, [1, 1]))

    def test_extra_fields(self):
        with self.assertRaises(ValueError):
            self.check_csv("甲\n一,二\n", None)

    def test_missing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                self.assertEqual(main([str(Path(directory) / "missing.csv")]), 1)
            self.assertIn("错误", error.getvalue())

    def test_leading_blank_lines(self):
        self.check_csv("\n\n甲,乙\n一,\n", (["甲", "乙"], 1, [0, 1]))

    def test_blank_only(self):
        self.check_csv("\n\r\n", ([], 0, []))

    def test_cli_errors(self):
        script = Path(__file__).with_name("csv_overview.py")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "异常.csv"
            for content in (b'\xff', b'col\n"unclosed', b'col\na,b\n'):
                with self.subTest(content=content):
                    path.write_bytes(content)
                    result = subprocess.run(
                        [sys.executable, "-B", str(script), str(path)],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("错误", result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertNotIn("Traceback", result.stderr)

    def test_nonempty_cli_counts(self):
        cases = [
            ("", "列名：（无）\n数据行数：0\n每列空值数量：\n每列非空值数量：\n"),
            ("甲,乙\n", "每列非空值数量：\n  甲：0\n  乙：0\n"),
            ("甲,乙\n0,NULL\n ,\n值\n\n",
             "每列非空值数量：\n  甲：2\n  乙：1\n"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "中文.csv"
            for content, expected in cases:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(main([str(path)]), 0)
                    self.assertIn(expected, output.getvalue())

    def test_example_cli(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([str(Path(__file__).parent / "examples/sample.csv")]), 0)
        self.assertIn("数据行数：3", output.getvalue())
        self.assertIn("备注：2", output.getvalue())
        self.assertIn("每列非空值数量：\n  姓名：3\n  城市：2\n  备注：1\n",
                      output.getvalue())


if __name__ == "__main__":
    unittest.main()
