# -*- coding: utf-8 -*-
"""初始化一个新的获客工作目录（把 skill 复刻给其他人用）

用法
----
    python init_workspace.py "D:\\my-leadgen"
    python init_workspace.py "D:\\my-leadgen" --force   # 目标目录非空也继续（不覆盖已有文件）

会生成：
    <目标>/tools/            14 个脚本（从 skill 内权威副本复制）
    <目标>/tools/data/map_keywords.json
    <目标>/master-lead-pool.csv   仅表头（21 列）
    <目标>/market-plan.csv        47 个市场，全部 active、last_run 清空
    <目标>/leads|reports|outreach|logs|review/   空目录

不会生成：客户跟进表.xlsx（可选，见 README）（首次跑 `python tools/build_followup_html.py` 后按需用 Excel 建，
或直接改用跟进台 HTML）、任何客户数据。
"""
import argparse
import csv
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_TOOLS = os.path.join(HERE, "tools")
TPL_PLAN = os.path.join(HERE, "templates", "market-plan.template.csv")
TPL_POOL = os.path.join(HERE, "templates", "pool.template.csv")

DIRS = ["tools", "tools/data", "leads", "reports", "outreach", "logs", "review"]


def main():
    ap = argparse.ArgumentParser(description="初始化获客工作目录")
    ap.add_argument("target", help="目标目录，如 D:\\my-leadgen")
    ap.add_argument("--force", action="store_true", help="目标目录非空也继续")
    args = ap.parse_args()

    tgt = os.path.abspath(args.target)
    if os.path.isdir(tgt) and os.listdir(tgt) and not args.force:
        print(f"❌ 目标目录非空：{tgt}\n   换一个空目录，或加 --force 合并（不覆盖已有文件）")
        return 1

    for d in DIRS:
        os.makedirs(os.path.join(tgt, d), exist_ok=True)
    print(f"✅ 目录结构：{len(DIRS)} 个")

    # 1) 脚本
    n = 0
    for fn in os.listdir(SRC_TOOLS):
        sp = os.path.join(SRC_TOOLS, fn)
        if os.path.isfile(sp) and fn.endswith(".py"):
            shutil.copy2(sp, os.path.join(tgt, "tools", fn))
            n += 1
    # 工作台前端页面（workbench.html，配套 workbench.py）
    wb_html = os.path.join(SRC_TOOLS, "workbench.html")
    if os.path.exists(wb_html):
        shutil.copy2(wb_html, os.path.join(tgt, "tools", "workbench.html"))
    if os.path.isdir(os.path.join(SRC_TOOLS, "data")):
        for fn in os.listdir(os.path.join(SRC_TOOLS, "data")):
            shutil.copy2(os.path.join(SRC_TOOLS, "data", fn),
                         os.path.join(tgt, "tools", "data", fn))
    print(f"✅ 脚本：{n} 个 + 工作台前端 + 关键词数据")

    # 身份占位：复制成 profile.json，用户必须改
    ex = os.path.join(SRC_TOOLS, "profile.example.json")
    dst = os.path.join(tgt, "tools", "profile.json")
    if os.path.exists(ex) and not os.path.exists(dst):
        shutil.copy2(ex, dst)

    # SMTP 配置占位（发信才需要，默认不含任何真实密钥）
    smtp_ex = os.path.join(HERE, "smtp_config.example.json")
    smtp_dst = os.path.join(tgt, "smtp_config.json")
    if os.path.exists(smtp_ex) and not os.path.exists(smtp_dst):
        shutil.copy2(smtp_ex, smtp_dst)

    # 2) 市场计划（重置状态）
    with open(TPL_PLAN, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    for r in rows:
        r["status"] = "active"
        r["last_run"] = ""
    with open(os.path.join(tgt, "market-plan.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"✅ market-plan.csv：{len(rows)} 个市场，全部 active（priority 1 起跑）")

    # 3) 空线索池（仅表头）
    shutil.copy2(TPL_POOL, os.path.join(tgt, "master-lead-pool.csv"))
    print("✅ master-lead-pool.csv：21 列表头，0 条线索")

    print(f"""
下一步（顺序别换）：
  1. cd /d {tgt}
  2. 改 tools/profile.json（姓名/公司/城市/邮箱/WhatsApp）——不改就发出去会带上别人的签名
  3. 改 skill 目录下 references/company-profile.md 为自己的真实公司数据（产能、认证、年限）
  4. （可选）改 smtp_config.json 填入自己的发信邮箱与授权码（用于工作台发信）
  5. python tools/pick_market.py            确认今天跑哪个市场
  6. python tools/kwgen.py --country 德国 --tier all --cities 3 --cmd
  7. 之后按 references/automation-guide.md 第六节一键版提示词走

🖥️ 启动客户工作台（可视化跟进）：
  python tools/workbench.py    → 浏览器打开 http://127.0.0.1:8610
  （或双击仓库里的「启动工作台.bat」/「start-workbench.bat」）

⚠️ 工作目录换了位置后，脚本靠「MB_HOME 环境变量」或「脚本所在目录的上一级」定位数据，
   两者都没有时默认就是脚本上一级——所以 tools/ 必须和 master-lead-pool.csv 同级。
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
