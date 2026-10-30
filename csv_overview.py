"""使用标准库统计 UTF-8 CSV 文件。"""
import argparse
import csv
import sys
from pathlib import Path


def summarize(path):
    """返回列名、数据行数和空值数；空白字符串也视为空值。"""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        columns = next((row for row in reader if row), [])
        counts = [0] * len(columns)
        rows = 0
        for row in reader:
            if not row:  # 忽略完全空白的物理行
                continue
            if len(row) > len(columns):
                raise ValueError(f"第 {reader.line_num} 行的字段数超过列名数量")
            rows += 1
            for index in range(len(columns)):
                if index >= len(row) or not row[index].strip():
                    counts[index] += 1
        return columns, rows, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description="显示 CSV 列名、数据行数和每列空值及非空值数量")
    parser.add_argument("path", help="UTF-8 编码的 CSV 文件路径")
    args = parser.parse_args(argv)
    try:
        columns, rows, counts = summarize(args.path)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1
    print("列名：" + ("、".join(columns) if columns else "（无）"))
    print(f"数据行数：{rows}")
    print("每列空值数量：")
    for column, count in zip(columns, counts):
        print(f"  {column}：{count}")
    print("每列非空值数量：")
    for column, count in zip(columns, counts):
        print(f"  {column}：{rows - count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
