# -*- coding: utf-8 -*-
"""对外素材库：WhatsApp 两句钩子 + 完整开发信（主题 / 正文 / 签名）

设计原则
--------
1. WhatsApp = **两句**，第一句自报身份+能给你什么，第二句戳痛点+轻 CTA。超过三行没人看。
2. 邮件 = **完整可寄**：Subject 独立成行、正文分 4 段（锚点→身份→能力→CTA）、真实签名。
3. 邮件比 WhatsApp 重三倍信息量：WhatsApp 负责让ta回一句，邮件负责让ta认真评估。
4. 示例文案里的 {NAME} / {公司名} / {EMAIL} / {WHATSAPP} / {Your Company Co., Ltd.}
   都是**占位符**，实际运行时从 tools/profile.json 动态读取真实签名（见下方 SIG_EN/SIG_ZH）。
   「{YEAR} 年 / {AREA}㎡ / 18 条线 / {CAPACITY} 万吨 / {CERT} / SGS」等实力数据是**示例**，
   复刻给他人时请改成自己公司 references/company-profile.md 里的真实数据。

用法
----
from outreach_copy import pick
c = pick(rank=1, name="{CUSTOMER}", industry="PET包装", city="{CITY_DEMO}",
         country="{COUNTRY_DEMO}", contact="{CONTACT_FULL}", grade="A", prod="")
c["wa_en"], c["wa_zh"], c["sj_en"], c["sj_zh"], c["m_en"], c["m_zh"]
"""

SIG_EN = (
    "Best regards,\n"
    "{NAME}\n"
    "{Your Company Co., Ltd.}\n"
    "Email: {EMAIL} | WhatsApp: {WHATSAPP}"
)

SIG_ZH = (
    "顺祝商祺\n"
    "{公司名}\n"
    "{公司全称}\n"
    "邮箱：{EMAIL} | WhatsApp：{WHATSAPP}"
)

# ---- 可替换身份：复刻给他人用时，改 tools/profile.json 即可，无需改代码 ----
import json as _json
import os as _os

_PROFILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "profile.json")
if not _os.path.exists(_PROFILE):
    print("⚠️ 未找到 tools/profile.json —— 正在使用内置签名。复刻给他人时必须先填 profile.json")
elif True:
    try:
        _p = _json.load(open(_PROFILE, encoding="utf-8"))
        SIG_EN = ("Best regards,\n" + _p["name"] + "\n" + _p["company"] + "\n"
                  + "Email: " + _p["email"] + " | WhatsApp: " + _p["whatsapp"])
        SIG_ZH = ("顺祝商祺\n" + _p.get("name_cn", _p["name"]) + "\n"
                  + _p.get("company_cn", _p["company"]) + "\n"
                  + "邮箱：" + _p["email"] + " | WhatsApp：" + _p["whatsapp"])
        if "example.com" in _p.get("email", "") or "Your Company" in _p.get("company", ""):
            print("⚠️ tools/profile.json 仍是占位内容（example.com / Your Company）——发信前必须改成真实公司信息")
    except Exception as _e:
        print(f"⚠️ tools/profile.json 读取失败（{_e}），已回退到内置签名")

# 身份段：多套表述轮换，避免 34 封读起来像同一封群发
WHO = {
    "plant": ("We are {NAME}, a masterbatch plant in {CITY} since {YEAR} — {AREA} m², "
              "{LINES} imported production lines, {CAPACITY} t/year, {CERT}, and SGS test data "
              "with every lot."),
    "factory": ("{NAME} has been making colour masterbatch in {CITY} since {YEAR}. "
                "We run {LINES} imported lines in a {AREA} m² plant, {CAPACITY} t/year, {CERT}, "
                "and every shipment carries SGS data."),
    "three": ("Three things about us that matter here: we are a factory, not a trader "
              "({CITY}, since {YEAR}); we run {CAPACITY} t/year on {LINES} imported lines with "
              "{CERT}; and 26 colour engineers handle matching and on-site trials."),
    "old": ("We have been compounding colour in {CITY} since {YEAR} — {YEARS}+ years, {AREA} m², "
            "{LINES} imported lines, {CAPACITY} t/year, {CERT}, SGS data per lot."),
}

CTA = {
    "sample": ("Would a free colour match help? Send me the resin grade and the target "
               "shade — matched sample plus SGS report back in 3-5 working days, DHL at our cost."),
    "sample2": ("If it is useful, I can run a free match on one of your current grades: "
                "you send resin plus target, we return a sample and its SGS report in 3-5 "
                "working days, freight on us."),
    "talk": ("Worth a short technical call? I can also send a matched sample first — resin "
             "grade plus target shade is all I need, 3-5 working days, DHL at our cost."),
}

A_COPY = {}

A_COPY[1] = dict(
    wa_en=("Hi {CONTACT}, {NAME} here from {CITY} — we make colour masterbatch for PET sheet "
           "and injection, {CAPACITY} t/yr since {YEAR}."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——我们做 PET 片材与注塑用色母粒，"
           "{YEAR} 年起，年产 {CAPACITY} 万吨。"),
    wa2_en=("Export orders usually die on batch-to-batch colour drift, not on the shade itself "
            "— we ship SGS data with every lot. Can I free-match one of your sheet grades?"),
    wa2_zh=("出口订单栽的通常不是颜色本身，而是批间色差——我们每批附 SGS 数据。"
            "能否给您一个片材料牌号做免费打样？"),
    sj_en="Colour drift on PET sheet — free match for {CUSTOMER}",
    sj_zh="PET 片材的批间色差——给 {CUSTOMER} 的免费打样",
    m_en=(
        "Hi {CONTACT},\n\n"
        "I saw that {CUSTOMER} runs PET rigid packaging alongside injection and blow moulding "
        "across Ho Chi {CONTACT} and Tay Ninh, and ships to more than 60 export markets. In that "
        "mix the complaint we hear most is not the shade itself but drift: lot 1 matches the "
        "standard, lot 5 is visibly off on the shelf, and the buyer sees it before your QC does.\n\n"
        + WHO["plant"] + "\n\n"
        "For PET sheet and food-grade packaging we work on dispersion consistency first, "
        "because that is what holds delta-E across a long run and through regrind. We match "
        "against your existing shade card or a physical sample, and we can quote a "
        "PCR-compatible version if your buyers are asking for recycled content.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "看到 {CUSTOMER} 在本土与周边省份同时做 PET 硬质包装、注塑和吹塑，出口 60 多个国家。"
        "这种结构下，我们听到最多的投诉不是颜色本身对不上，而是漂移：第 1 批对标准，"
        "第 5 批在货架上肉眼可见偏了，客户比你们的 QC 先发现。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口生产线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批随附 SGS 检测数据。\n\n"
        "针对 PET 片材与食品级包装，我们首先解决分散稳定性——这才是长周期生产和回料掺混下"
        "守住 ΔE 的关键。可以按你们现有色卡或实物样对色；如果你们的买家在要再生含量，"
        "我们也能做兼容 PCR 的版本。\n\n"
        "要不要先做一次免费配色打样？把树脂牌号和目标色号给我，3-5 个工作日出匹配样 + SGS 报告，"
        "DHL 到付我们承担。\n\n" + SIG_ZH),
)

A_COPY[2] = dict(
    wa_en=("Merhaba {CONTACT}, {NAME} from {CITY} — colour masterbatch for IML film and "
           "thin-wall food packaging."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做 IML 膜与薄壁食品包装用色母粒。"),
    wa2_en=("IML colour usually breaks at high speed on thin walls, and that is exactly where "
            "suppliers get replaced. Can I send a free match on your IML grade?"),
    wa2_zh=("IML 的颜色通常是在薄壁高速成型时崩的，供应商也往往是在这一步被换掉。"
            "能否给您 IML 牌号寄一次免费打样？"),
    sj_en="IML film colour at high speed — sample for Teknika Plast",
    sj_zh="IML 膜高速成型的颜色稳定——给 Teknika Plast 的样品",
    m_en=(
        "Merhaba {CONTACT},\n\n"
        "Teknika Plast runs IML food packaging together with appliance and automotive moulding "
        "out of Manisa, and exports a large share of it. IML is the hard case: the film has to "
        "hold colour on a thin wall at high cavity speed, and any hesitation in dispersion shows "
        "up as mottling on the printed surface, not as a colour number on a report.\n\n"
        + WHO["factory"] + "\n\n"
        "For IML and thin-wall work we control three things together — pigment dispersion, "
        "let-down consistency, and the carrier matching your PP or PS. That combination is what "
        "keeps a run stable from the first shot to the last, and it is also what keeps your "
        "food-contact documentation clean, since we supply SGS data per lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Teknika Plast 在马尼萨做 IML 食品包装，同时做家电与汽车注塑，出口占比很高。"
        "IML 是最难的一类：膜要在薄壁上、高腔数高速成型下守住颜色，分散稍有迟疑，"
        "表现出来的不是报告上的色号偏差，而是印刷面的麻点。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起。{AREA} ㎡ 厂房、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批出货附 SGS 数据。\n\n"
        "针对 IML 与薄壁件，我们同时管三件事——颜料分散、添加比一致性、载体与你们 PP/PS 的匹配。"
        "这三项合起来才决定从第一模到最后一模是否稳定，也决定你们的食品接触文件是否干净，"
        "因为我们每批都提供 SGS 数据。\n\n"
        "要不要做一次免费打样？把树脂牌号和目标色给我，3-5 个工作日出样 + SGS 报告，"
        "DHL 费用我们承担。\n\n" + SIG_ZH),
)

A_COPY[3] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — colour masterbatch for heavy-wall, two-shot and "
           "insert moulding."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做重壁、双色与嵌件注塑用色母粒。"),
    wa2_en=("Long cycles and regrind are where colour shifts; we quote against your resin and "
            "cycle, not a shade card. Free match on one engineering grade?"),
    wa2_zh=("颜色最容易在长周期和回料里漂——我们按你的树脂和成型周期报价，不套通用色卡。"
            "拿一个工程料牌号免费打样？"),
    sj_en="Colour in long-cycle, two-shot moulding — sample for Automation Plastics",
    sj_zh="长周期双色注塑的颜色稳定——给 Automation Plastics 的样品",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Automation Plastics does heavy-wall, two-shot and insert moulding in Aurora, which puts "
        "colour under two stresses at once: a long residence time in the barrel, and regrind "
        "folded back into the next run. Most colour complaints in that setup are not about the "
        "shade on day one — they are about the shade after the third regrind cycle.\n\n"
        + WHO["three"] + "\n\n"
        "So we quote against your resin and your cycle rather than a generic shade card: carrier "
        "selected for your processing temperature, pigment loading set so the let-down stays "
        "inside tolerance at your screw, and a regrind-stability check before we ship. "
        "SGS data comes with each lot, which also covers the paperwork side when a customer audits you.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Automation Plastics 在 Aurora 做重壁、双色和嵌件注塑，这会让颜色同时承受两种压力："
        "料筒里的长停留时间，以及回料被掺回下一批。这种场景下的颜色投诉，绝大多数不是"
        "第一天的色相不对，而是第三次回料之后的色相跑了。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色和现场试模。\n\n"
        "所以我们按你的树脂和成型周期报价，而不是拿通用色卡套：载体按你的加工温度选，"
        "颜料含量设在你们螺杆添加比下仍在公差内的水平，出货前做一次回料稳定性验证。"
        "每批附 SGS 数据，客户来审厂时这部分文件也是齐的。\n\n"
        "要不要先做一个工程料牌号的免费打样？树脂牌号 + 目标色给我即可，3-5 个工作日出样，"
        "DHL 费用我们承担。\n\n" + SIG_ZH),
)

A_COPY[4] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — colour masterbatch for blow-moulded bottles and "
           "jars, food, pharma and chemical."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做吹塑瓶罐用色母粒，食品、医药、化工。"),
    wa2_en=("Bottle colour gets audited like the resin, so we ship SGS data per lot and do "
            "PCR-compatible matching. Free sample on one bottle grade?"),
    wa2_zh=("瓶子的颜色和树脂一样要过合规审查，所以我们每批附 SGS 数据，也做兼容 PCR 的配色。"
            "给您一个瓶料牌号寄免费样品？"),
    sj_en="Bottle colour with the compliance paperwork attached",
    sj_zh="瓶罐配色，连同合规文件一起给你",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Hub Plastics blow moulds bottles and jars for food, pharma and chemical customers, where "
        "colour is not a cosmetic choice — it goes through the same compliance review as the resin. "
        "That changes what a supplier has to bring: not just a match, but a match you can put in "
        "front of a customer's QA without chasing documents for two weeks.\n\n"
        + WHO["plant"] + "\n\n"
        "Practically, that means: SGS test data issued per lot, carrier and pigment selected to "
        "stay inside food-contact requirements, and a PCR-compatible colour route if a brand owner "
        "is pushing recycled content on you. We match from your physical sample or a Pantone, and "
        "we keep the master on file so reorders do not drift.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Hub Plastics 为食品、医药和化工客户吹塑瓶罐，颜色在这里不是外观选择——它和树脂走"
        "同一套合规审查。这就改变了供应商要交付的东西：不只是对得上色，而是你拿到就能直接"
        "放在客户 QA 面前的、不用追两周文件的对色。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批随附 SGS 检测数据。\n\n"
        "具体来说就是：按批出具 SGS 数据；载体与颜料选型保证落在食品接触要求内；如果品牌方"
        "在压再生含量，我们有兼容 PCR 的配色路线。可按实物样或 Pantone 对色，色板留档，"
        "返单不会漂。\n\n"
        "要不要给您一个瓶料牌号做免费样品？树脂 + 目标色给我，3-5 个工作日出样加 SGS 报告，"
        "DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[5] = dict(
    wa_en=("Hi, {NAME} from {CITY} — low delta-E colour for Class A and FDA-grade medical "
           "moulding."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 Class A 表面与 FDA 级医疗件用的低 ΔE 配色。"),
    wa2_en=("70 presses to 1900T and Class A work means colour tolerance is the whole job — "
            "we ship SGS data per lot. Free match on a current shade?"),
    wa2_zh=("70 台机、最大 1900 吨还做 Class A，色差控制就是全部——我们每批附 SGS 数据。"
            "拿一个在做的颜色免费打样？"),
    sj_en="Low delta-E on Class A and FDA medical parts",
    sj_zh="Class A 与 FDA 医疗件的低 ΔE 控制",
    m_en=(
        "Hello,\n\n"
        "Sturgis runs 70 presses up to 1900 tonnes with Class A surfaces and FDA-grade medical "
        "work in the same building. That combination sets a hard bar: on a Class A part the eye "
        "finds a 0.5 delta-E miss under showroom lighting, and on a medical part the same miss "
        "turns into a documentation question.\n\n"
        + WHO["old"] + "\n\n"
        "We handle both cases with the same discipline — low-delta-E engineering colour, "
        "tight pigment-loading control so the let-down is repeatable at your press, and SGS data "
        "issued per lot for the medical side. Where a part is colour-critical we will ask for the "
        "resin lot and the wall thickness before quoting, because both move the result.\n\n"
        "Two questions so I can be specific: which colour approval route do you use for automotive "
        "interior work, and who signs off medical colour? I can send a free matched sample on one "
        "current shade in the meantime — 3-5 working days, DHL at our cost.\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Sturgis 有 70 台注塑机、最大 1900 吨，同一厂区里既做 Class A 表面，也做 FDA 级医疗件。"
        "这个组合的门槛很硬：Class A 件上，0.5 的 ΔE 偏差在展厅灯光下肉眼就能看出来；"
        "医疗件上，同样的偏差会变成一个文件问题。\n\n"
        "我们有 {YEARS} 多年配色积累——{YEAR} 年建厂，{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "两类件我们用同一套纪律处理：低 ΔE 工程配色、严格控制颜料含量以保证你们机台上的添加比"
        "可重复、医疗侧按批出 SGS 数据。颜色关键的件，我们报价前会先问树脂批号和壁厚，"
        "因为这两个变量都会改变结果。\n\n"
        "两个问题，方便我讲得更具体：汽车内饰这块你们走哪条配色审批路径？医疗件的颜色由谁签核？"
        "同时我可以先拿一个在做的颜色做免费打样，3-5 个工作日，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[6] = dict(
    wa_en=("Hi, {NAME} from {CITY} — interior grain colour matching for automotive, plus "
           "medical grades."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做汽车内饰皮纹配色，也做医疗级牌号。"),
    wa2_en=("85 to 1000T across three states means the same shade has to land on every press. "
            "Free match on an interior colour you run now?"),
    wa2_zh=("跨三个州、85 到 1000 吨的机台，意味着同一个色要在每台机上落得住。"
            "拿一个在做的内饰色免费打样？"),
    sj_en="Interior grain colour matching for Summit",
    sj_zh="给 Summit 的内饰皮纹配色",
    m_en=(
        "Hello,\n\n"
        "Summit moulds automotive interior and medical parts across Michigan, Texas and China on "
        "presses from 85 to 1000 tonnes. The interior side is where colour gets difficult: a "
        "grained surface reads colour differently from a polished one, so a shade that passes on "
        "a test plaque can still fail on the production tool.\n\n"
        + WHO["factory"] + "\n\n"
        "That is the job we do most — interior grain colour, matched on the actual texture rather "
        "than on a flat chip, with the carrier chosen so the shade holds across your range of press "
        "sizes. For the medical side we supply SGS data per lot and keep the master on file so "
        "reorders do not drift.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Summit 在密歇根、德州和中国多地，用 85 到 1000 吨的机台做汽车内饰件与医疗件。"
        "内饰这边颜色最难：皮纹面读色的方式和光面不一样，所以一块试板上过的颜色，"
        "上了量产模具仍可能不过。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "内饰皮纹配色正是我们做最多的一类：按真实纹理对色而不是按平面色板，载体按你们"
        "跨机台吨位的工艺选，保证同一个色在大小机上都能落住。医疗侧我们按批提供 SGS 数据，"
        "色板留档，返单不漂。\n\n"
        "要不要拿一个你们现在在做的内饰色做免费打样？树脂 + 纹理样 + 目标色给我，"
        "3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[7] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — UV-stable colour and FR grades for automotive "
           "parts that live outdoors."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做长期户外汽车件的抗 UV 配色与阻燃牌号。"),
    wa2_en=("As a VinFast Tier 1 your parts sit in the sun for years — colour and UV have to be "
            "designed together. Free match and sample for your next programme?"),
    wa2_zh=("作为 VinFast 一级供应商，你们的件要在太阳下晒好几年——颜色和抗 UV 必须一起设计。"
            "下一个项目给您免费打样寄样？"),
    sj_en="UV-stable interior colour for a VinFast Tier 1",
    sj_zh="给 VinFast 一级供应商的抗 UV 内饰配色",
    m_en=(
        "Chào anh {CONTACT},\n\n"
        "As a VinFast Tier 1, Y Chi Viet ships parts that spend their life outdoors, so colour and "
        "UV performance cannot be specified separately — a shade that matches at PPAP and fades in "
        "the second summer is a warranty claim, not a colour issue.\n\n"
        + WHO["plant"] + "\n\n"
        "For outdoor automotive work we build the package as one system: UV-stabilised pigment "
        "selection, HALS level set to your expected service life, and a carrier that keeps both "
        "stable through your regrind ratio. We also do UL 94 FR grades if a programme moves toward "
        "flame-retardant interior parts. Every lot ships with SGS data, which is what your customer's "
        "audit will ask for.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 先生，您好：\n\n"
        "作为 VinFast 的一级供应商，Y Chi Viet 交付的零件终年在户外，所以颜色和抗 UV 性能"
        "不能分开定——一个在 PPAP 时对得上、到第二个夏天就褪色的色，不是颜色问题，是保修索赔。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "户外汽车件我们按一个系统来做：抗 UV 颜料选型、按你们目标使用寿命设定 HALS 用量、"
        "载体保证这两项在你们的回料比例下仍然稳定。如果项目往阻燃内饰件走，我们也有 UL 94 牌号。"
        "每批随附 SGS 数据——这正是你们客户审厂时会要的东西。\n\n"
        "下一个项目给您免费打样寄样？把树脂、目标色和 Outdoor 使用年限给我，3-5 个工作日"
        "出样加耐候数据。\n\n" + SIG_ZH),
)

A_COPY[8] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — high-dispersion colour for colour multilayer film."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做彩色多层膜用高分散色母粒。"),
    wa2_en=("On multilayer film, let-down ratio decides whether film and print match. Free match on "
            "one of your structures?"),
    wa2_zh=("多层膜上，添加比直接决定膜和印刷能不能对上。拿一个多层结构免费打样？"),
    sj_en="Let-down ratio and film-to-print match",
    sj_zh="添加比，与膜色和印刷色的对位",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Versa Pak runs colour multilayer film, where the same masterbatch has to do two jobs at "
        "once: survive a thin skin layer at high let-down, and land close enough to the print that "
        "the finished pack reads as one colour. When those two drift apart you get a film that "
        "passes QC on its own and still looks wrong next to the printed panel.\n\n"
        + WHO["old"] + "\n\n"
        "We work on dispersion first and on let-down consistency second, because that pair is what "
        "holds the film-to-print relationship across a long run. Practically: we ask for your "
        "structure and your target let-down before quoting, then verify the match at that ratio "
        "rather than at a convenient one. SGS data with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Versa Pak 做彩色多层膜，同一支色母粒要同时干两件事：在高添加比下过得了薄表层，"
        "同时和印刷色对得足够近，让成品包装看上去是一个色。这两件事一旦分开漂，"
        "就会出现膜自己过 QC、但摆在印刷面板旁边就是不对的情况。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们先解决分散，再解决添加比一致性，因为这两项合起来才守得住膜色与印刷色的关系。"
        "具体做法：报价前先要你们的结构和实际添加比，然后就在那个比例下验证对色，"
        "而不是挑一个好做的比例验。每批附 SGS 数据。\n\n"
        "要不要拿一个多层结构做免费打样？3-5 个工作日出样，DHL 费用我们承担。\n\n" + SIG_ZH),
)

A_COPY[9] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — low delta-E engineering colour and UL-listed FR grades."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做低 ΔE 工程配色与 UL 认证阻燃牌号。"),
    wa2_en=("Under IATF 16949 a colour miss is a PPAP issue, not a cosmetic one. Free match on one "
            "part?"),
    wa2_zh=("在 IATF 16949 体系里，色差是 PPAP 问题，不是外观问题。拿一个零件免费打样？"),
    sj_en="Colour deviation as a PPAP item",
    sj_zh="当色差成为 PPAP 项",
    m_en=(
        "Hi {CONTACT},\n\n"
        "BMI is IATF 16949 and moulds plus assembles for Tier 1 and Tier 2 programmes, so colour "
        "deviation here is not a cosmetic note on an inspection sheet — it is a PPAP submission "
        "that can hold up a launch.\n\n"
        + WHO["three"] + "\n\n"
        "That is the frame we quote in. Low-delta-E engineering colour with the pigment loading set "
        "for repeatability at your press, carrier matched to the resin so shrinkage and flow stay in "
        "the window your tool was cut for, and SGS data per lot to sit behind the PPAP file. "
        "For programmes moving to flame-retardant parts we hold UL-listed FR grades, which shortens "
        "the qualification loop considerably.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "BMI 通过 IATF 16949，为一级和二级供应商做注塑与组装，所以这里的色差不是检验单上"
        "一条外观备注，而是一份可能卡住量产启动的 PPAP 文件。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色与现场试模。\n\n"
        "我们就按这个框架报价：低 ΔE 工程配色，颜料含量设在你们机台上可重复的水平；"
        "载体与树脂匹配，让收缩率和流动性仍落在模具设计窗口内；每批附 SGS 数据，"
        "垫在 PPAP 文件后面。项目若转向阻燃件，我们有 UL 认证牌号，能把认证周期缩短不少。\n\n"
        "要不要拿一个零件做免费打样试试？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[10] = dict(
    wa_en=("Hi, {NAME} from {CITY} — UV-stabilised colour for outdoor HVAC and agricultural parts."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做户外 HVAC 与农机件的抗 UV 配色。"),
    wa2_en=("80 years of moulding plus thermoforming means your parts get judged after a season in "
            "the sun. Free match on one grade?"),
    wa2_zh=("做了 80 年注塑和热成型，你们的件是在晒过一季之后才被检验的。拿一个牌号免费打样？"),
    sj_en="UV-stabilised colour for HVAC and ag parts",
    sj_zh="HVAC 与农机件的抗 UV 配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Cary has been moulding and thermoforming for 80 years, and a lot of that output — HVAC "
        "housings, agricultural parts — sits outdoors for years. On those parts, weather resistance "
        "matters as much as the shade on the day of shipment: the failure mode is fading and "
        "chalking in the second season, long after the colour was approved.\n\n"
        + WHO["plant"] + "\n\n"
        "So we treat UV and colour as one specification: pigment chosen for lightfastness first, "
        "HALS level set to your service life rather than to a generic loading, and the pair verified "
        "against your resin before we ship. For thermoformed sheet we also check the colour after "
        "the forming stretch, because draw ratio changes what the surface reads.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Cary 做注塑和热成型已经 80 年，其中很大一部分产出——HVAC 外壳、农机件——在户外一放就是几年。"
        "这类件上，耐候性和出货当天的颜色一样重要：失效方式是第二个季节的褪色和粉化，"
        "而那时候颜色早就审批通过了。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "所以我们把抗 UV 和颜色当一个指标来做：颜料先按耐光性选，HALS 用量按你们的实际使用年限"
        "而不是通用添加量设定，出货前在你们的树脂上验证这一对组合。热成型片材我们还会检查"
        "拉伸成型之后的颜色，因为拉伸比会改变表面读色。\n\n"
        "要不要寄一次免费打样？树脂 + 目标色 + 户外使用年限给我即可。\n\n" + SIG_ZH),
)

A_COPY[11] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — small-lot custom colour, which is what "
           "metal-to-plastic conversion usually needs."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做小批量定制配色，金属转塑料通常正好需要这个。"),
    wa2_en=("Conversions mean low volume and tight colour targets — the opposite of a commodity "
            "order. Free match on one project?"),
    wa2_zh=("替代项目意味着量小、色差目标紧——正好和大宗订单相反。拿一个项目免费打样？"),
    sj_en="Small-lot colour for metal-to-plastic conversions",
    sj_zh="金属转塑料的小批量配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Reliant converts metal parts to plastic, which means the volumes are modest and the colour "
        "targets are tight — usually because the plastic part has to match a finish the customer "
        "already approved in metal. That is the opposite of a commodity masterbatch order, and it "
        "is where most suppliers get expensive: minimum order quantities, tooling charges, long "
        "leads.\n\n"
        + WHO["old"] + "\n\n"
        "We run small-lot custom colour as normal business rather than as an exception: low minimums, "
        "matching from a physical part or a Pantone, and a master kept on file so the second order "
        "matches the first without a new approval cycle. SGS data with each lot when the end customer "
        "asks for it.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Reliant 做金属转塑料，这意味着量不大、但色差目标很紧——通常是因为塑料件必须对上"
        "客户已经在金属件上批过的表面效果。这和大宗色母粒订单正好相反，也是多数供应商开始"
        "变贵的地方：起订量、模具费、长交期。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们把小批量定制配色当常规业务，不当特例：起订量低、可按实物件或 Pantone 对色、"
        "色板留档，所以第二批不需要再走一轮审批就能对上第一批。终端客户要文件时，每批附 SGS 数据。\n\n"
        "要不要拿一个替代项目做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[12] = dict(
    wa_en=("Hi, {NAME} from {CITY} — colour masterbatch including PCR-compatible grades, "
           "{CAPACITY} t/yr."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做色母粒，含兼容 PCR 的牌号，年产 {CAPACITY} 万吨。"),
    wa2_en=("22 plants and FSSC 22000 in scope means supply has to scale and stay compliant. "
            "Who owns colour and PCR sourcing?"),
    wa2_zh=("22 个厂、FSSC 22000 在范围内，意味着供应既要上量又要合规。配色和 PCR 采购由谁负责？"),
    sj_en="PCR-compatible colour across 22 plants",
    sj_zh="22 个厂一致的 PCR 兼容配色",
    m_en=(
        "Hello,\n\n"
        "Axium runs 22 plants and around 3,500 people across North American packaging, on HDPE and "
        "PET with FSSC 22000 in scope. At that scale two things decide whether a masterbatch supplier "
        "is usable: can they hold the same shade across sites, and can they support the PCR content "
        "your brand owners are demanding without the colour falling apart.\n\n"
        + WHO["factory"] + "\n\n"
        "Both are answerable. Cross-site consistency comes from keeping one master per shade and "
        "issuing the same SGS data to every plant, rather than letting each site match locally. "
        "PCR support comes from carriers and pigment systems that tolerate the colour shift recycled "
        "feedstock brings, so a 30% PCR let-down still reads as the approved shade.\n\n"
        "Two questions: who owns colour specification centrally, and who is driving PCR sourcing? "
        "I can send a free matched sample against one of your current shades in the meantime — "
        "3-5 working days, DHL at our cost.\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Axium 在北美包装有 22 个厂、约 3,500 人，做 HDPE 和 PET，FSSC 22000 在范围内。"
        "这个体量下，决定一家色母粒供应商能不能用只有两件事：能不能跨厂守住同一个色；"
        "以及能不能支撑品牌方要求的 PCR 含量而颜色不散。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "这两件都答得上来。跨厂一致性靠的是每个色只留一块标准板、同一份 SGS 数据发给各厂，"
        "而不是让每个厂自己去对色。PCR 支持靠的是能容忍再生料带来的色偏的载体与颜料体系，"
        "30% PCR 添加下仍然读作批过的那个色。\n\n"
        "两个问题：配色规格在总部由谁负责？PCR 采购由谁在推？同时我可以先按你们现有色号"
        "做一次免费打样，3-5 个工作日，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[13] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — interior colour that survives heat and regrind."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做能扛住高温和回料的内饰配色。"),
    wa2_en=("Insert moulding for automotive since 1973 means the shade has to hold through both. "
            "Free match on a current programme?"),
    wa2_zh=("1973 年起做汽车嵌件注塑，意味着颜色要同时扛住这两样。拿一个在做的项目免费打样？"),
    sj_en="Interior colour that survives heat and regrind",
    sj_zh="扛得住高温与回料的内饰配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Agapé has supplied GM-tier work since 1973, and insert moulding for automotive and "
        "appliance parts puts colour under two loads: the metal insert holds heat longer than the "
        "polymer around it, and the regrind goes back in. A shade that passes on a first-shot plaque "
        "often drifts once those two are in play.\n\n"
        + WHO["three"] + "\n\n"
        "For interior work we set pigment loading for repeatability at your press, choose the carrier "
        "to suit the temperature the insert creates, and verify the shade after a regrind cycle rather "
        "than only on virgin resin. Low delta-E is the target, and SGS data per lot keeps the "
        "documentation side clean when your customer audits.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Agapé 从 1973 年起供通用体系，汽车与家电嵌件注塑会让颜色同时承受两种负荷："
        "金属嵌件的余热比周围聚合物保持更久，回料又要掺回去。一块在首模试板上过的颜色，"
        "这两件事一进来往往就漂了。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色与现场试模。\n\n"
        "内饰件上，我们把颜料含量设在你们机台可重复的水平，载体按嵌件造成的实际温度选，"
        "并且在走过一轮回料之后再验证色相，而不是只在新料上验。目标是低 ΔE；每批附 SGS 数据，"
        "客户审厂时文件这块是齐的。\n\n"
        "要不要拿一个在做的项目做免费打样？3-5 个工作日出样，DHL 费用我们承担。\n\n" + SIG_ZH),
)

A_COPY[14] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — masterbatch that won't move your shrinkage or flow."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做不会动你收缩率和流动性的色母粒。"),
    wa2_en=("At ±0.001 in ABS, nylon and PPS a bad carrier costs you scrap, not just colour. "
            "Free sample on one engineering grade?"),
    wa2_zh=("在 ABS、尼龙、PPS 上做到 ±0.001，载体选错损失的是报废而不只是颜色。"
            "拿一个工程料牌号免费寄样？"),
    sj_en="Masterbatch that won't move your ±0.001",
    sj_zh="不动你 ±0.001 的色母粒",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Camcar holds ±0.001 in ABS, nylon and PPS. At that tolerance a masterbatch is not a colour "
        "purchase, it is a process variable: the wrong carrier shifts shrinkage, changes flow, and "
        "the colour problem you were solving turns into a dimensional one that costs scrap.\n\n"
        + WHO["old"] + "\n\n"
        "So we start from the carrier, not the pigment: matched to your resin family so shrinkage and "
        "flow stay inside the window your tool was cut for, with pigment loading kept low enough that "
        "the let-down does not disturb the balance. We will ask for your resin grade and current "
        "processing window before quoting, and we verify dimensional impact on a trial shot rather "
        "than claiming neutrality on paper.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Camcar 在 ABS、尼龙和 PPS 上做到 ±0.001。在这个公差下，色母粒不是一次“买颜色”，"
        "而是一个工艺变量：载体选错会改变收缩率、改变流动性，你要解决的颜色问题就变成"
        "要付出报废代价的尺寸问题。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "所以我们从载体入手而不是从颜料入手：按你的树脂体系配，让收缩率和流动性仍落在模具"
        "设计窗口内；颜料含量压到不扰动这个平衡的水平。报价前我们会先要树脂牌号和当前工艺窗口，"
        "并且在试模件上验证尺寸影响——不在纸面上声称“中性”。\n\n"
        "要不要拿一个工程料牌号做免费寄样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[15] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — FR masterbatch for FR-ABS, PC and PA, UL 94 V-0."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做 FR-ABS、PC、PA 用阻燃母粒，UL 94 V-0。"),
    wa2_en=("V-0 depends on wall thickness — we quote to yours rather than to a generic data sheet. "
            "Free V-0 sample for your next build?"),
    wa2_zh=("V-0 取决于壁厚——我们按你的壁厚报价，而不是套通用数据表。下一个案子寄个 V-0 免费样品？"),
    sj_en="UL 94 V-0 at your wall thickness — FR sample for JATCO",
    sj_zh="按你的壁厚做 UL 94 V-0——给 JATCO 的阻燃样品",
    m_en=(
        "Hi {CONTACT},\n\n"
        "JATCO moulds FR-ABS, PC and PA for EV, electronics and medical housings, where UL 94 V-0 is "
        "the entry ticket rather than a selling point. The catch is that V-0 is a function of wall "
        "thickness and of how the part is gated — a grade that passes at 1.6 mm can fail at 0.8 mm, "
        "and that is usually discovered late.\n\n"
        + WHO["plant"] + "\n\n"
        "We quote FR grades against your actual wall thickness and resin, not against a generic data "
        "sheet, and we will tell you when a flame-retardant route is going to cost you impact strength "
        "— better to hear that before tooling than after. For EV and electronics work we also consider "
        "halogen-free routes where the end customer's specification calls for it. SGS data per lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "JATCO 做 FR-ABS、PC、PA 的注塑，用于 EV、电子和医疗外壳，UL 94 V-0 在这里是入场券，"
        "不是卖点。问题在于 V-0 是壁厚和进胶方式的函数：一个在 1.6 mm 过的牌号，"
        "到 0.8 mm 可能就不过，而这通常发现得很晚。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "我们的阻燃牌号按你们实际的壁厚和树脂报价，不按通用数据表；如果某条阻燃路线会牺牲冲击强度，"
        "我们会直接说——这话在开模前听到比开模后听到好。EV 与电子件上，如果终端规格要求无卤，"
        "我们也有对应路线。每批附 SGS 数据。\n\n"
        "下一个案子寄个 V-0 免费样品？壁厚和树脂牌号给我即可。\n\n" + SIG_ZH),
)

A_COPY[16] = dict(
    wa_en=("Hi, {NAME} from {CITY} — sheath colour and FR grades for PVC and XLPE cable."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 PVC 与 XLPE 电缆的护套配色和阻燃牌号。"),
    wa2_en=("You compound PVC and XLPE in-house, so sheath colour is the part still bought in. "
            "Free sheath match plus FR sample?"),
    wa2_zh=("你们自己做 PVC 和 XLPE 料，护套颜色仍是外购的部分。做一次护套配色打样加阻燃样品？"),
    sj_en="Sheath colour and FR grades for CADIVI",
    sj_zh="给 CADIVI 的护套配色与阻燃牌号",
    m_en=(
        "Hello,\n\n"
        "CADIVI compounds PVC and XLPE in-house, which means the part you still buy from outside is "
        "narrower than for most cable makers: sheath colour, and the flame-retardant or fire-resistant "
        "grades where local supply tends to be thin and lead times unpredictable.\n\n"
        + WHO["factory"] + "\n\n"
        "On the colour side we match sheath shades for PVC and XLPE against your compound, with "
        "dispersion set for the extrusion speeds you run and lightfastness checked for outdoor "
        "installation. On the FR side we supply halogen-free and fire-resistant masterbatch routes "
        "and will be straight with you about what each one does to tensile strength and elongation, "
        "since those are the numbers your standard actually tests. SGS data with every lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "CADIVI 自己做 PVC 和 XLPE 料，所以你们还需要外购的部分，比多数电缆厂要窄：护套颜色，"
        "以及阻燃/耐火牌号——后者本地供应通常很薄、交期不稳。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "颜色这边，我们按你们的料对 PVC 与 XLPE 护套色，分散度按你们的挤出速度设定，"
        "耐光性按户外敷设条件核。阻燃这边，我们提供无卤与耐火母粒路线，并且会直说每条路线"
        "对拉伸强度和断裂伸长率的影响——因为那才是你们标准里真正测的数。每批附 SGS 数据。\n\n"
        "要不要做一次护套配色打样加阻燃样品？料号与目标色给我即可，3-5 个工作日出样。\n\n" + SIG_ZH),
)

A_COPY[17] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — brand-exact colour, matched in 3-5 days."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——品牌精确配色，3-5 天出样。"),
    wa2_en=("Brand-exact colour is what you sell, so it is your bottleneck and your differentiator. "
            "Free match on a live brand shade?"),
    wa2_zh=("品牌精确配色就是你们卖的东西，所以它既是瓶颈也是差异点。拿一个在做的品牌色免费打样？"),
    sj_en="Brand-exact colour, matched in 3-5 days",
    sj_zh="品牌精确配色，3-5 天出样",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Brand-exact colour is what Texas Injection Molding sells, which makes matching both your "
        "bottleneck and your differentiator. The cost of a slow or approximate match is not the "
        "masterbatch — it is the days a mould sits waiting and the risk that the customer's brand "
        "team rejects the first article.\n\n"
        + WHO["three"] + "\n\n"
        "We work to a 3-5 working day match cycle on a physical sample or a Pantone, with 26 colour "
        "engineers on the bench, and we keep the master on file so the second and fifth order land on "
        "the same shade without a new round of approval. Low delta-E targets are normal for us rather "
        "than a special request, and SGS data ships with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Texas Injection Molding 卖的就是品牌精确配色，所以配色既是你们的瓶颈，也是差异点。"
        "一次慢的或“差不多”的对色，成本不在色母粒本身——而在于模具等着的那几天，"
        "以及客户品牌团队否掉首件的风险。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师在配色室。\n\n"
        "我们按实物样或 Pantone 走 3-5 个工作日的对色周期，色板留档，所以第 2 批、第 5 批"
        "都落在同一个色上，不用再走一轮审批。低 ΔE 目标对我们是常态而非特殊要求，每批随附 SGS 数据。\n\n"
        "要不要拿一个在做的品牌色做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[18] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — UV-stabilised and high-dispersion colour for pipe "
           "and profile."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做管材型材用抗 UV 与高分散配色。"),
    wa2_en=("On outdoor pipe, UV and dispersion show up as fading and streaks after one season. "
            "Free match on one pipe grade?"),
    wa2_zh=("户外管材上，UV 和分散问题会在一个季节后以褪色和条纹暴露出来。拿一个管材料牌号免费打样？"),
    sj_en="Fading and streaks on outdoor pipe — UV grade",
    sj_zh="户外管材的褪色与条纹——抗 UV 牌号",
    m_en=(
        "Hi {CONTACT},\n\n"
        "OSI extrudes PVC and HDPE pipe and profile, where two colour failures show up late: fading "
        "from UV exposure, and streaking from poor dispersion at high output. Both are invisible on "
        "the day of shipment and obvious after a season outdoors — which means they get found by the "
        "installer, not by your line.\n\n"
        + WHO["old"] + "\n\n"
        "We address them as one package: lightfast pigment selection with HALS set for the exposure "
        "your market actually sees, and dispersion quality controlled so a high-output line does not "
        "produce streaked pipe. For HDPE we also supply carbon black grades where UV resistance is "
        "specified by standard rather than by preference. SGS data with each lot, including the "
        "weathering data where it is relevant.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "OSI 挤 PVC 和 HDPE 管材型材，两种颜色失效都暴露得很晚：UV 暴露造成的褪色，"
        "以及高产量下分散不良造成的条纹。这两样在出货当天都看不出来，一个户外季节之后就很明显"
        "——也就是说，发现它们的是安装商，不是你们的产线。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们把这两件当一个问题解决：耐光颜料选型，HALS 按你们市场实际暴露量设定；"
        "分散质量受控，让高产线也不出条纹管。HDPE 上如果抗 UV 是由标准而不是偏好规定的，"
        "我们也供炭黑牌号。每批附 SGS 数据，必要时包含老化数据。\n\n"
        "要不要拿一个管材料牌号做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[19] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — high-gloss, low delta-E colour for Class A IML film."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做 Class A 级 IML 膜用高光低 ΔE 配色。"),
    wa2_en=("At 0.5 delta-E the showroom sees it, so the film has to be right the first time. "
            "Free match on a current film shade?"),
    wa2_zh=("0.5 的 ΔE 在展厅里就能看出来，所以膜必须一次做对。拿一个在做的膜色免费打样？"),
    sj_en="0.5 delta-E on Class A IML film",
    sj_zh="Class A 级 IML 膜的 0.5 ΔE",
    m_en=(
        "Hi {CONTACT},\n\n"
        "DT does Class A IML, where a 0.5 delta-E miss is visible on the showroom floor rather than "
        "buried in an inspection report. Film colour is also the hardest place to fix late, because "
        "the surface is glossy and the eye picks up both hue shift and any dispersion defect at once.\n\n"
        + WHO["factory"] + "\n\n"
        "For IML film we work on three things: pigment dispersion fine enough that gloss does not "
        "reveal specks, carrier matched to your film grade so the draw does not shift the shade, and "
        "a master kept on file so reorders hold. We verify on a finished film sample where possible "
        "rather than on a moulded chip, since the two read differently. SGS data with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "DT 做 Class A 级 IML，0.5 的 ΔE 偏差是在展厅地面上就能看出来的，不是埋在检验报告里。"
        "膜色也是最难补救的一环：表面是高光的，色相偏移和分散缺陷会同时被眼睛抓到。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "IML 膜上我们抓三件事：颜料分散细到高光下不露颗粒；载体与你们膜料牌号匹配，"
        "拉伸后色相不偏；色板留档，返单稳。条件允许时我们在成品膜样上验证，而不是只在注塑片上验，"
        "因为两者读色不一样。每批附 SGS 数据。\n\n"
        "要不要拿一个在做的膜色做免费打样？膜料牌号 + 目标色给我即可。\n\n" + SIG_ZH),
)

A_COPY[20] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — high-temperature engineering colour for hot-runner parts."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做热流道件用耐高温工程配色。"),
    wa2_en=("Six GM Supplier of the Year awards means colour and heat are already audited. Free sample "
            "on a hot-runner grade?"),
    wa2_zh=("六次通用年度供应商，说明颜色和耐热本来就在审核范围内。热流道牌号寄个免费样品？"),
    sj_en="High-temperature colour for hot-runner parts",
    sj_zh="热流道件的耐高温配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "GTP has taken GM Supplier of the Year six times, which tells me colour and heat performance on "
        "functional parts are already inside somebody's audit rather than being a matter of taste. "
        "Hot-runner work raises the bar again: longer residence time, higher melt temperature, and "
        "colour that must not degrade while it waits.\n\n"
        + WHO["three"] + "\n\n"
        "For high-temperature engineering parts we select the carrier for the melt temperature first "
        "and the pigment for heat stability second, then verify both after a residence-time test that "
        "mimics a hot runner rather than a short shot. Where a colour is near the limit we will say so "
        "and propose an alternative rather than ship something that passes on paper. SGS data per lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "GTP 六次拿到通用年度供应商，说明功能件上的颜色和耐热性能早就在别人的审核范围里，"
        "而不是审美问题。热流道又把门槛抬高一档：停留时间更长、熔温更高，颜色在等待期间不能降解。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色与试模。\n\n"
        "耐高温工程件上，我们先按熔温选载体，再按热稳定性选颜料，然后用模拟热流道的停留时间试验"
        "验证这两项，而不是用一个短射件验证。若某个颜色已经贴着极限，我们会直说并提替代方案，"
        "而不是发一批“纸面上过”的货。每批附 SGS 数据。\n\n"
        "热流道牌号要不要寄个免费样品？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[21] = dict(
    wa_en=("Hello, {NAME} from {CITY} — colouring Torlon and PEEK, where most masterbatch houses "
           "decline."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 Torlon 与 PEEK 着色，多数色母粒厂不接这类活。"),
    wa2_en=("Colouring those resins needs a carrier that survives 400 °C. Worth a short technical "
            "conversation?"),
    wa2_zh=("给这类树脂着色需要能扛 400℃ 的载体。要不要简短聊一次技术？"),
    sj_en="Colouring Torlon and PEEK at 400 °C",
    sj_zh="400℃ 下的 Torlon 与 PEEK 着色",
    m_en=(
        "Hello,\n\n"
        "Drake is the largest Torlon and PEEK processor, and colouring those resins is the request most "
        "masterbatch houses simply decline: the carrier has to survive a melt temperature around 400 °C "
        "without degrading, and the pigment has to hold colour through a process window that would "
        "destroy a standard masterbatch.\n\n"
        + WHO["old"] + "\n\n"
        "We take this on as small-lot high-temperature work rather than as a catalogue item. That means "
        "a carrier selected for the actual melt temperature, pigment chemistry chosen for heat stability "
        "rather than for cost, and a trial before any commitment on colour depth — because at these "
        "temperatures the achievable shade range narrows and it is better to agree on that early. "
        "SGS data with each lot.\n\n"
        "Would a short technical call be useful? I would rather discuss your melt profile and the target "
        "shade than send a generic brochure, and I can follow up with a small trial sample.\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Drake 是全球最大的 Torlon 与 PEEK 加工厂，而给这类树脂着色，是多数色母粒厂直接推掉的请求："
        "载体要在 400℃ 左右的熔温下不降解，颜料要在这个会把标准色母粒毁掉的工艺窗口里守住颜色。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们把这类活当小批量高温业务接，而不是当成目录产品：载体按实际熔温选，颜料化学按热稳定性"
        "而不是按成本选，并且在承诺色深之前先做试验——因为这个温度区间里可实现的色域会收窄，"
        "早点把这点谈清楚对双方都好。每批附 SGS 数据。\n\n"
        "要不要简短聊一次技术？我更愿意讨论你们的熔体曲线和目标色，而不是发一份通用资料，"
        "之后可以跟一个小批量试验样。\n\n" + SIG_ZH),
)

A_COPY[22] = dict(
    wa_en=("Hi, {NAME} from {CITY} — automotive interior colour plus UL 94 FR grades."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做汽车内饰配色与 UL 94 阻燃牌号。"),
    wa2_en=("With IATF 16949 and ITAR in scope, supplier documentation is part of the deal. Free match "
            "on one programme?"),
    wa2_zh=("IATF 16949 与 ITAR 在范围内，供应商的文件本来就是交易的一部分。拿一个项目免费打样？"),
    sj_en="Supplier documentation plus interior colour",
    sj_zh="供应商文件，加上内饰配色",
    m_en=(
        "Hello,\n\n"
        "EFI has been running since 1976 with IATF 16949 and ITAR in scope, so a supplier's paperwork "
        "is part of the commercial conversation rather than an afterthought. For a masterbatch supplier "
        "that narrows the field quickly: lots of plants can match a shade, fewer can put SGS data "
        "behind every shipment without being chased.\n\n"
        + WHO["plant"] + "\n\n"
        "What we bring is interior colour at low delta-E, pigment loading set for repeatability on your "
        "presses, and UL 94 FR grades where a programme needs them — with SGS test data issued per lot "
        "as standard rather than on request. We also keep the colour master on file so a reorder years "
        "later still matches the approved first article.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "EFI 自 1976 年运营，持 IATF 16949 与 ITAR，所以供应商的文件是商务谈判的一部分，不是事后补的。"
        "对色母粒供应商来说，这一条会迅速缩小候选范围：能对色的厂很多，能每批主动给 SGS 数据、"
        "不用催的厂少。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们提供的是：低 ΔE 内饰配色、颜料含量按你们机台可重复的水平设定、项目需要时提供 UL 94 "
        "阻燃牌号；SGS 检测数据按批出具是标配而不是“按要求提供”。色板留档，所以几年后返单"
        "仍对得上当年批过的首件。\n\n"
        "要不要拿一个项目做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[23] = dict(
    wa_en=("Merhaba, {NAME} from {CITY} — food-contact colour for IML and blow-moulded packaging."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 IML 与吹塑包装用食品接触级配色。"),
    wa2_en=("Colour on food and cosmetic packaging clears the same review as the resin. Free match on "
            "your IML or bottle grade?"),
    wa2_zh=("食品与化妆品包装的颜色要过和树脂同样的审查。给您 IML 或瓶料牌号做免费打样？"),
    sj_en="Food-contact colour for Sistem Ambalaj",
    sj_zh="给 Sistem Ambalaj 的食品接触级配色",
    m_en=(
        "Merhaba,\n\n"
        "Sistem Ambalaj moulds and blow moulds packaging for food, cosmetic and chemical customers, so "
        "colour on those parts clears the same food-contact review as the resin. That is the point where "
        "a cheap masterbatch becomes expensive: the shade matches, but the documentation does not.\n\n"
        + WHO["factory"] + "\n\n"
        "So we supply food-contact compliant colour with SGS test data per lot, carriers and pigments "
        "selected to stay inside the relevant requirements rather than at the edge of them, and colour "
        "matched from your physical sample or a Pantone. For cosmetic packaging we pay attention to "
        "gloss and surface appearance, since a defect that is tolerable on an industrial part is a "
        "rejection on a shelf.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Sistem Ambalaj 为食品、化妆品和化工客户做注塑与吹塑包装，这些件上的颜色要和树脂走"
        "同一套食品接触审查。这正是便宜色母粒变贵的地方：颜色对上了，文件对不上。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "我们提供符合食品接触要求的配色，每批附 SGS 检测数据；载体与颜料选型保证落在要求之内"
        "而不是贴着边界；可按实物样或 Pantone 对色。化妆品包装上我们会额外关注光泽与表面外观——"
        "在工业件上可以接受的瑕疵，摆在货架上就是退货。\n\n"
        "要不要给您 IML 或瓶料牌号做免费打样？3-5 个工作日出样，DHL 费用我们承担。\n\n" + SIG_ZH),
)

A_COPY[24] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — medical and FR masterbatch with SGS data on every lot."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——医疗级与阻燃母粒，每批附 SGS 数据。"),
    wa2_en=("Under ISO 13485 and ITAR, a supplier without paperwork is a non-starter. Free sample with "
            "full documentation?"),
    wa2_zh=("在 ISO 13485 与 ITAR 体系下，文件不全的供应商根本进不来。寄一份带完整文件的免费样品？"),
    sj_en="Masterbatch with the paperwork attached",
    sj_zh="把文件一起寄过来的色母粒",
    m_en=(
        "Hi {CONTACT},\n\n"
        "DEM works to ISO 13485 and ITAR, so a masterbatch supplier without documentation is not a "
        "cheap option — it is a non-starter. The usual failure here is not colour quality, it is a "
        "supplier who can match the shade but cannot produce traceable test data when the auditor asks.\n\n"
        + WHO["old"] + "\n\n"
        "We ship SGS test data with every medical and flame-retardant lot as standard, keep the colour "
        "master on file for traceability across reorders, and will tell you plainly which of our grades "
        "carry which documentation before you spend time on a trial. Where a specification needs a test "
        "we do not run, we say so rather than substitute a similar-looking report.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "DEM 按 ISO 13485 和 ITAR 运作，所以文件不齐的色母粒供应商不是一个“便宜的选项”，"
        "而是根本进不来。这里最常见的失败不是颜色质量，而是供应商能对上色，"
        "但审核员要文件时拿不出可追溯的检测数据。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们的医疗级与阻燃批次按标配随附 SGS 检测数据；色板留档，返单可追溯；"
        "在你们花时间做试验之前，我们会先明确说清哪个牌号带哪类文件。"
        "如果某项规格需要一项我们做不了的检测，我们会直说，而不是拿一份看起来差不多的报告替代。\n\n"
        "要不要寄一份带完整文件的免费样品？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[25] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — predictable colour at large shot weights, including "
           "PCR-compatible grades."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——大注射量下的稳定配色，也做兼容 PCR 的牌号。"),
    wa2_en=("At 9,000 tonnes a colour change costs real scrap, so the masterbatch has to be predictable. "
            "Free match on a large-part shade?"),
    wa2_zh=("9000 吨的机台上换色就是实打实的废料，所以色母粒必须可预测。拿一个大件颜色免费打样？"),
    sj_en="Predictable colour at 9,000 tonnes clamping force",
    sj_zh="9000 吨锁模力下的可预测配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "Cascade runs 37 presses up to 9,000 tonnes, and at that shot weight a colour change is not a "
        "cosmetic adjustment — it is kilos of scrap and hours of machine time. So the requirement on a "
        "masterbatch shifts from \"does it match\" to \"does it behave the same way every time\".\n\n"
        + WHO["three"] + "\n\n"
        "For large-part work we control pigment loading and dispersion so the let-down repeats at high "
        "shot weights, and we verify on a part of comparable mass rather than on a small test piece, "
        "because that is where the two diverge. We also supply PCR-compatible and sustainable colour "
        "routes where a programme needs recycled content without losing the approved shade. SGS data "
        "with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "Cascade 有 37 台机、最大 9000 吨，在这个注射量下，换色不是外观微调——是几十公斤废料"
        "加几小时机时。所以对色母粒的要求会从“能不能对上”变成“每次行为是否完全一致”。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色与试模。\n\n"
        "大件上我们控制颜料含量与分散度，让添加比在大注射量下可重复；并且在同等质量的件上验证，"
        "而不是在小试片上验——两者的偏差方向不一样。如果项目要再生含量又不丢批过的色，"
        "我们也有兼容 PCR 与可持续路线。每批附 SGS 数据。\n\n"
        "要不要拿一个大件颜色做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[26] = dict(
    wa_en=("Hi, {NAME} from {CITY} — FR sheath masterbatch for control, robotic and high-temp cable."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做控制、机器人、高温线缆用阻燃护套母粒。"),
    wa2_en=("Jacket colour and flame performance are both specified — we do them as one grade. Free "
            "sample on one jacket compound?"),
    wa2_zh=("护套颜色和阻燃性能都是明确指标——我们做成一个牌号。拿一个护套料免费寄样？"),
    sj_en="Jacket colour plus flame performance",
    sj_zh="护套颜色与阻燃性能，一起做",
    m_en=(
        "Hello,\n\n"
        "TPC builds control, robotic and high-temperature cable, where jacket colour and flame "
        "performance are both written into the specification. That combination is where single-purpose "
        "masterbatch fails: a colour grade that ignores flame retardancy forces you to add a second "
        "package, and the two then fight each other on elongation and surface finish.\n\n"
        + WHO["plant"] + "\n\n"
        "We supply FR sheath masterbatch as one grade — colour and flame performance designed together, "
        "with the impact on tensile strength and elongation stated up front because that is what your "
        "standard tests. For high-temperature cable we select carriers that tolerate the service "
        "temperature rather than only the extrusion temperature. SGS data with every lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "TPC 做控制、机器人和高温线缆，护套颜色和阻燃性能都写进了规格。这个组合正是单一功能色母粒"
        "失败的地方：只管颜色的牌号不管阻燃，逼你再加一套阻燃体系，然后两者在断裂伸长率和表面"
        "上互相打架。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "我们的阻燃护套母粒是一个牌号做完两件事：颜色和阻燃一起设计，并且提前告知对拉伸强度和"
        "断裂伸长率的影响——因为那才是你们标准里测的数。高温线缆上，我们选的载体能耐受使用温度，"
        "而不只是耐受挤出温度。每批附 SGS 数据。\n\n"
        "要不要拿一个护套料做免费样品？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[27] = dict(
    wa_en=("Hi, {NAME} from {CITY} — PVC insulation and nylon jacket colour, high-volume repeat work."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 PVC 绝缘与尼龙护套配色，高量重复采购那类。"),
    wa2_en=("Running from copper rod to finished wire means colour is a repeat consumable — consistency "
            "beats novelty. Free match on your PVC insulation shade?"),
    wa2_zh=("从铜杆做到成品线，颜色就是持续消耗品——一致性比新意重要。给您 PVC 绝缘色免费打样？"),
    sj_en="PVC insulation colour, high-volume repeat",
    sj_zh="PVC 绝缘配色，高量重复",
    m_en=(
        "Hello,\n\n"
        "Encore runs the whole chain from copper rod to finished wire, so PVC insulation and nylon "
        "jacket colour is a repeat consumable rather than a one-off project. On that kind of item, "
        "consistency matters more than novelty: the same shade, on the same line, year after year, "
        "with no adjustment calls in between.\n\n"
        + WHO["old"] + "\n\n"
        "That is a supply discipline question as much as a colour question — one master kept on file, "
        "the same pigment source, and SGS data per lot so the receiving inspection does not become the "
        "place where variation is discovered. We also supply FR and fire-resistant sheath grades where "
        "a cable family needs them, so you are not buying from two houses.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Encore 从铜杆一直做到成品线，所以 PVC 绝缘和尼龙护套的颜色是持续消耗品，不是一次性项目。"
        "这类物料上，一致性比新意重要：同一个色、同一条线、一年接一年，中间不要有调整电话。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "这既是配色问题，也是供应纪律问题：一个色只留一块标准板，颜料来源固定，每批附 SGS 数据，"
        "所以“发现波动”的地方不会是你们的来料检验。如果某个线缆系列需要阻燃或耐火护套牌号，"
        "我们也供，你们不用从两家买。\n\n"
        "要不要给您 PVC 绝缘色做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[28] = dict(
    wa_en=("Hi, {NAME} from {CITY} — the same colour across four plants, with SGS data per lot."),
    wa_zh=("您好，我是{公司名}的 {NAME}——四个厂同一个色，每批附 SGS 数据。"),
    wa2_en=("120 presses across four sites plus ISO 13485 cleanroom work means cross-site consistency is "
            "the requirement. Free match on one grade?"),
    wa2_zh=("四个厂 120 台机，还有 ISO 13485 洁净室业务，跨厂一致性就是硬要求。拿一个牌号免费打样？"),
    sj_en="Same colour across four plants",
    sj_zh="四个厂，同一个色",
    m_en=(
        "Hello,\n\n"
        "PMM runs around 120 presses across four plants, including ISO 13485 cleanroom work. At that "
        "structure the colour problem is not matching a shade once — it is making the same shade land "
        "identically at four sites, on different presses, with different operators running them.\n\n"
        + WHO["factory"] + "\n\n"
        "Cross-site consistency is a system, not a promise: one master per shade held on file, one "
        "pigment source, and the same SGS data issued to every plant so each site's QA starts from the "
        "same reference. For the medical side we keep lot traceability intact through reorders. If a "
        "site needs a local adjustment we would rather reissue the grade than let it drift.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "PMM 四个厂约 120 台注塑机，其中包含 ISO 13485 洁净室业务。这个结构下，颜色问题不是"
        "把某个色对上一次——而是让同一个色在四个不同的厂、不同的机台、不同的操作工手里落成一样。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        "跨厂一致性是体系而不是承诺：一个色只留一块标准板、颜料来源固定、同一份 SGS 数据发给各厂，"
        "让每个厂的 QA 从同一个基准出发。医疗侧我们保持批次可追溯，返单不断链。"
        "如果某个厂需要本地调整，我们宁可重新出一个牌号，也不让它自己漂。\n\n"
        "要不要拿一个牌号做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[29] = dict(
    wa_en=("Hi, {NAME} from {CITY} — carbon black and pipe colour for HDPE, PPR and uPVC lines."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 HDPE、PPR、uPVC 管线的炭黑与管材配色。"),
    wa2_en=("Close to 20 extrusion lines to European standards means colour is a continuous consumable. "
            "Free match on your PE100 or uPVC grade?"),
    wa2_zh=("近 20 条欧标挤出线，配色是持续消耗品。给您 PE100 或 uPVC 牌号免费打样？"),
    sj_en="Carbon black and pipe colour on 20 extrusion lines",
    sj_zh="20 条挤出线上的炭黑与管材配色",
    m_en=(
        "Hello,\n\n"
        "EUROPIPE runs close to 20 extrusion lines on HDPE, PPR and uPVC to European standards, so "
        "carbon black and pipe colour are continuous consumables rather than project purchases. Two "
        "things matter on a line like that: carbon black dispersion, because agglomerates become the "
        "failure point in a pressure test, and colour consistency, because a pipe run that changes "
        "shade between deliveries is a visible problem on site.\n\n"
        + WHO["old"] + "\n\n"
        "We supply carbon black and colour masterbatch with dispersion controlled and verified, SGS "
        "data per lot, and UV-stabilised grades for above-ground installation. We also match to the "
        "colour standards your market specifies rather than to a local reference, which matters when "
        "the same pipe is sold into several countries.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "EUROPIPE 有近 20 条挤出线，做欧标 HDPE、PPR 和 uPVC，所以炭黑和管材配色是持续消耗品，"
        "不是项目型采购。这种产线上两件事最关键：炭黑分散——因为团聚体就是压力试验的失效点；"
        "以及颜色一致性——因为管子在不同批次之间变色，在工地上是看得见的问题。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们供炭黑母粒与管材配色母粒，分散度受控并验证，每批附 SGS 数据；地上面敷设用的抗 UV "
        "牌号也有。对色按你们市场规定的色标走，而不是按某个本地参考——同一个管子卖到几个国家时，"
        "这一点很关键。\n\n"
        "要不要给您 PE100 或 uPVC 牌号做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[30] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — sheath colour and FR masterbatch for PVC and XLPE cable."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做 PVC 与 XLPE 电缆用护套配色与阻燃母粒。"),
    wa2_en=("Supplying Samsung, LG and Honda programmes means the documentation has to be as solid as "
            "the colour. Free sheath match plus FR sample?"),
    wa2_zh=("供三星、LG、本田的项目，文件要和颜色一样硬。做一次护套配色加阻燃样品？"),
    sj_en="Sheath colour and FR for CADI-SUN",
    sj_zh="给 CADI-SUN 的护套配色与阻燃",
    m_en=(
        "Chào anh {CONTACT},\n\n"
        "CADI-SUN supplies Samsung, LG and Honda programmes and compounds PVC and XLPE in-house, so the "
        "gap we can fill is narrow and specific: sheath colour, and the flame-retardant grades where "
        "local supply is thin. Working with that customer base also means documentation has to be as "
        "solid as the shade itself.\n\n"
        + WHO["plant"] + "\n\n"
        "On sheath colour we match against your compound for both PVC and XLPE, with dispersion set for "
        "your extrusion speed and lightfastness checked for the installation environment. On FR we "
        "supply halogen-free and fire-resistant routes and state the effect on tensile strength and "
        "elongation before you trial, so the qualification does not stall on a property nobody "
        "mentioned. SGS data per lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 先生，您好：\n\n"
        "CADI-SUN 供三星、LG 和本田的项目，自己做 PVC 与 XLPE 料，所以我们能补的口子很窄也很具体："
        "护套颜色，以及本地供应偏薄的阻燃牌号。面对这样的客户群，文件也必须和颜色一样硬。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "护套色上，我们对 PVC 和 XLPE 都按你们的料对色，分散度按挤出速度设定，耐光性按敷设环境核。"
        "阻燃上我们供无卤与耐火路线，并在你们试验之前就说清对拉伸强度和断裂伸长率的影响——"
        "免得认证卡在一项没人提过的性能上。每批附 SGS 数据。\n\n"
        "要不要做一次护套配色加阻燃样品？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[31] = dict(
    wa_en=("Hi {CONTACT}, {NAME} from {CITY} — colour for printed PE film, in case suppliers are being "
           "re-reviewed."),
    wa_zh=("{CONTACT} 您好，我是{公司名}的 {NAME}——做印刷 PE 膜配色，如果你们在重审供应商的话。"),
    wa2_en=("After the Field Packaging acquisition, supplier lists often get re-examined. Printed film "
            "colour is a low-risk place to compare. Free match?"),
    wa2_zh=("被 Field Packaging 收购之后，供应商名单往往会被重新看一遍。印刷膜配色是个低风险的比对起点。"
            "免费打样？"),
    sj_en="Printed PE film colour after the Field Packaging deal",
    sj_zh="Field Packaging 收购之后的印刷 PE 膜配色",
    m_en=(
        "Hi {CONTACT},\n\n"
        "With the Field Packaging acquisition, Buckeye is a business whose supplier list is likely being "
        "looked at again this year — not because anything is wrong, but because that is what happens "
        "after an integration. Printed PE film colour is a low-risk place to run a comparison: it is "
        "easy to sample, easy to judge, and it does not disturb production.\n\n"
        + WHO["three"] + "\n\n"
        "We do high-dispersion colour for PE film with the let-down verified at your ratio rather than a "
        "convenient one, and we match against your print target so the film and the printed panel read "
        "as one colour. Small-lot custom colour is normal business for us, so a trial does not require a "
        "volume commitment. SGS data with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "{CONTACT} 您好：\n\n"
        "被 Field Packaging 收购之后，Buckeye 的供应商名单今年大概率会被重新看一遍——不是因为出了"
        "什么问题，而是整合之后通常都会这样。印刷 PE 膜配色是个低风险的比对切入点：容易取样、"
        "容易判断，也不打扰生产。\n\n"
        "关于我们，三件相关的事：我们是工厂不是贸易商（深圳，{YEAR} 年起）；{LINES} 条进口线、"
        "年产 {CAPACITY} 万吨、{CERT}；26 名配色工程师负责对色与试模。\n\n"
        "我们做 PE 膜用高分散配色，添加比按你们实际的比值验证（而不是挑一个好做的比值），"
        "并按你们的印刷目标对色，让膜和印刷面板读作一个色。小批量定制配色对我们是常规业务，"
        "所以试一次不需要量的承诺。每批附 SGS 数据。\n\n"
        "要不要拿一个膜料牌号做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[32] = dict(
    wa_en=("Hello, {NAME} from {CITY} — PVC-U and CPVC fitting colour at very high volume, plus UV."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 PVC-U 与 CPVC 管件配色，极高量，含抗 UV。"),
    wa2_en=("Largest fittings maker means colour plus UV weathering at volume — both have to be repeatable. "
            "Free match on a fittings shade?"),
    wa2_zh=("最大的管件商意味着高量下的配色加抗 UV 老化——两者都必须可重复。拿一个管件颜色免费打样？"),
    sj_en="PVC-U and CPVC fitting colour at volume",
    sj_zh="高量下的 PVC-U 与 CPVC 管件配色",
    m_en=(
        "Hello,\n\n"
        "Spears is the largest PVC-U and CPVC fittings maker, which means two requirements at once: "
        "colour that repeats at very high volume, and UV weathering that holds on fittings stored or "
        "installed outdoors. On CPVC the second one is harder, because the processing window is narrower "
        "and pigment choice affects both heat stability and colour.\n\n"
        + WHO["old"] + "\n\n"
        "We supply PVC colour and UV-stabilised grades with pigment systems chosen for the CPVC "
        "processing window rather than adapted from PVC, and we verify weathering against the exposure "
        "your market specifies. For volume work the master is held on file so the fifth shipment matches "
        "the first, and SGS data ships with each lot.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Spears 是全球最大的 PVC-U 与 CPVC 管件制造商，这意味着同时有两个要求：极高量下颜色可重复，"
        "以及管件在仓储或户外安装时抗 UV 老化要守住。CPVC 上第二点更难，因为加工窗口更窄，"
        "颜料选择会同时影响热稳定性和颜色。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们供 PVC 配色与抗 UV 牌号，颜料体系是按 CPVC 的加工窗口选的，不是从 PVC 改过来的；"
        "老化验证按你们市场规定的暴露条件做。高量业务上色板留档，第五批和第一批对得上，"
        "每批附 SGS 数据。\n\n"
        "要不要拿一个管件颜色做免费打样？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[33] = dict(
    wa_en=("Hello, {NAME} from {CITY} — colour as a device specification, for ISO 13485 and FDA parts."),
    wa_zh=("您好，我是{公司名}的 {NAME}——把颜色当器械规格来做，ISO 13485 与 FDA 件。"),
    wa2_en=("On a haemostasis valve, colour is a device spec, not a preference — we ship it with SGS data. "
            "Free sample with documentation?"),
    wa2_zh=("止血阀上，颜色是器械规格而不是偏好——我们连同 SGS 数据一起交付。寄一份带文件的免费样品？"),
    sj_en="Colour as a device specification — Excel Medical",
    sj_zh="当颜色是器械规格——给 Excel Medical",
    m_en=(
        "Hello,\n\n"
        "Excel moulds haemostasis valves and connectors under ISO 13485 and FDA, where colour is a device "
        "specification rather than a preference. That changes the supplier requirement: the shade has to "
        "be reproducible lot to lot, and the documentation has to support the device file without "
        "somebody rebuilding it from emails.\n\n"
        + WHO["plant"] + "\n\n"
        "We supply medical-grade colour with SGS test data per lot as standard, keep the colour master "
        "on file for traceability across reorders, and confirm which documentation a grade carries "
        "before you spend time on a validation run. Where a part is colour-critical we will ask about "
        "resin lot and moulding conditions, because on small medical parts those move the result more "
        "than the pigment does.\n\n"
        + CTA["sample"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Excel 在 ISO 13485 与 FDA 体系下做止血阀和连接器，颜色在这里是器械规格，不是偏好。"
        "这就改变了供应商的要求：色必须批批可复现，文件要能直接支撑器械档案，"
        "而不是让人从一堆邮件里重建。\n\n"
        "我们是{公司名}，{YEAR} 年起做色母粒的工厂——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、"
        "{CERT}，每批附 SGS 数据。\n\n"
        "我们供医疗级配色，SGS 检测数据按批标配提供；色板留档，返单可追溯；在你们投入验证批之前"
        "先明确该牌号带哪些文件。颜色关键的件，我们会问树脂批号和成型条件——因为在小医疗件上，"
        "这两个变量对结果的影响比颜料更大。\n\n"
        "要不要寄一份带完整文件的免费样品？3-5 个工作日出样，DHL 我们承担。\n\n" + SIG_ZH),
)

A_COPY[34] = dict(
    wa_en=("Hello, {NAME} from {CITY} — high-temperature colour for Torlon, PEEK and PAI."),
    wa_zh=("您好，我是{公司名}的 {NAME}——做 Torlon、PEEK、PAI 用高温配色。"),
    wa2_en=("AS9100 and ITAR metal-replacement parts need colour that survives the same environment as "
            "the resin. Free high-temperature sample?"),
    wa2_zh=("AS9100 与 ITAR 的金属替代件，颜色必须和树脂扛同样的环境。寄一份高温配色免费样品？"),
    sj_en="High-temperature colour for Torlon, PEEK and PAI",
    sj_zh="Torlon、PEEK、PAI 的高温配色",
    m_en=(
        "Hello,\n\n"
        "Aztec moulds Torlon, PEEK and PAI to AS9100 and ITAR, where the plastic part replaces metal and "
        "therefore has to survive the same environment the metal did. Colour on those parts is not "
        "decorative: it is often a part identifier, and it has to hold through a melt temperature that "
        "would destroy a standard masterbatch.\n\n"
        + WHO["old"] + "\n\n"
        "We take high-temperature colour as small-lot work rather than as a catalogue item: carrier "
        "selected for the actual melt temperature, pigment chemistry chosen for heat stability, and a "
        "trial before committing to a shade depth, because the achievable range narrows at these "
        "temperatures. Documentation is SGS data per lot, which is what an AS9100 flow-down will ask for.\n\n"
        + CTA["talk"] + "\n\n" + SIG_EN),
    m_zh=(
        "您好：\n\n"
        "Aztec 按 AS9100 与 ITAR 做 Torlon、PEEK 和 PAI 注塑，塑料件在这里替代金属，"
        "所以必须扛住金属原来所处的同一套环境。这类件上的颜色不是装饰：它常常是零件标识，"
        "而且要在会把标准色母粒毁掉的熔温下守住。\n\n"
        "我们在深圳做色母粒，{YEAR} 年起——{YEARS} 多年、{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}。\n\n"
        "我们把高温配色当小批量业务接，不当目录产品：载体按实际熔温选，颜料化学按热稳定性选，"
        "在承诺色深之前先做试验——因为这个温度区间里可实现的色域会收窄。文件是每批 SGS 数据，"
        "正是 AS9100 传递要求会要的东西。\n\n"
        "要不要简短聊一次技术？我也可以先寄一个小批量试验样。\n\n" + SIG_ZH),
)


# ---------------------------------------------------------------- B/C 级模板
# 164 家没有「官网产品」，只能写到「在哪个国家、做哪类塑料件」这一层。
# 明确标 ⚠️ 个性化降级，让使用者知道这封是行业级、不是公司级。

IND_BODY = {
    "wire and cable": (
        "colour for PVC and XLPE insulation and sheathing, together with UL 94 / halogen-free "
        "flame-retardant grades where a cable family needs them",
        "PVC 与 XLPE 绝缘和护套配色，以及线缆系列需要的 UL 94 / 无卤阻燃牌号"),
    "film extrusion": (
        "high-dispersion colour for blown film, with the let-down ratio verified at the ratio you "
        "actually run and the match checked against your print target",
        "吹膜用高分散配色，添加比按你们实际运行的比值验证，并按印刷目标对色"),
    "blow moulding": (
        "colour for HDPE and PET bottles and jars, formulated for food-contact requirements and "
        "supplied with SGS data per lot",
        "HDPE 与 PET 瓶罐配色，按食品接触要求配方，每批附 SGS 数据"),
    "pipe and profile extrusion": (
        "UV-stabilised colour and carbon black grades for pipe and profile, with dispersion "
        "controlled so a high-output line does not streak",
        "管材型材用抗 UV 配色与炭黑牌号，分散度受控，高产线也不出条纹"),
    "medical moulding": (
        "medical-grade colour with SGS test data on every lot, and lot traceability kept intact "
        "across reorders",
        "医疗级配色，每批附 SGS 检测数据，返单保持批次可追溯"),
    "automotive parts": (
        "low-delta-E interior colour plus UV-stabilised and FR grades, quoted against your resin "
        "and wall thickness rather than a generic shade card",
        "低 ΔE 内饰配色，以及抗 UV 与阻燃牌号，按你们的树脂和壁厚报价，不套通用色卡"),
    "appliance parts": (
        "Class A appearance colour for housings, with pigment loading set so the shade repeats on "
        "your presses",
        "外壳用 Class A 外观配色，颜料含量设在你们机台上可重复的水平"),
    "packaging": (
        "food-contact compliant colour for packaging, with SGS data per lot so the compliance "
        "review does not become the bottleneck",
        "包装用食品接触级配色，每批附 SGS 数据，让合规审查不成为瓶颈"),
    "injection moulding": (
        "custom colour for injection moulding, matched from a physical sample or a Pantone and held "
        "on file so reorders do not drift",
        "注塑用定制配色，按实物样或 Pantone 对色，色板留档，返单不漂"),
    "recycled compounds": (
        "PCR-compatible colour that tolerates the shift recycled feedstock brings, so a high PCR "
        "let-down still reads as the approved shade",
        "兼容 PCR 的配色，能容忍再生料带来的色偏，高 PCR 添加下仍读作批过的那个色"),
    "plastic parts": (
        "custom colour masterbatch matched to your resin, with free colour matching and samples "
        "and SGS data with every lot",
        "按你们树脂定制的色母粒，免费配色打样，每批附 SGS 数据"),
}


IND_MAP = [
    (("电线", "电缆", "线缆", "wire", "cable"), "wire and cable"),
    (("吹膜", "薄膜", "膜", "film"), "film extrusion"),
    (("吹塑", "blow"), "blow moulding"),
    (("管材", "型材", "挤出", "pipe", "profile"), "pipe and profile extrusion"),
    (("医疗", "医用", "medical"), "medical moulding"),
    (("汽车", "内饰", "汽配", "automotive"), "automotive parts"),
    (("家电", "appliance"), "appliance parts"),
    (("食品", "包装", "packaging"), "packaging"),
    (("注塑", "injection"), "injection moulding"),
    (("回收", "再生", "recycl"), "recycled compounds"),
]


def ind_en(text: str) -> str:
    t = (text or "").lower()
    for keys, label in IND_MAP:
        if any(k in t for k in keys):
            return label
    return "plastic parts"


def _ind_pair(industry: str):
    key = ind_en(industry)
    return IND_BODY.get(key, IND_BODY["plastic parts"]), key


def _first(contact: str) -> str:
    import re
    s = (contact or "").strip()
    m = re.match(r"^([A-Z][a-zA-Z\-']+)\s+[A-Z]", s)
    return m.group(1) if m else ""


def pick(rank, name, industry, city, country, contact, grade, prod=""):
    """返回一家客户的 WhatsApp 两句 + 邮件主题 + 完整邮件（中英）。"""
    if rank in A_COPY:
        c = A_COPY[rank]
        return {
            "wa_en": c["wa_en"] + "\n" + c["wa2_en"],
            "wa_zh": c["wa_zh"] + "\n" + c["wa2_zh"],
            "sj_en": c["sj_en"], "sj_zh": c["sj_zh"],
            "m_en": c["m_en"], "m_zh": c["m_zh"],
            "pers": True,
        }

    fn = _first(contact)
    greet_en = f"Hi {fn}" if fn else "Hello"
    greet_zh = f"{fn} 您好" if fn else "您好"
    place = city or country or ""
    (body_en, body_zh), key = _ind_pair(industry)
    label_en = key
    label_zh = industry or "塑料件"

    # 4 套句式轮换：164 家散在不同批次里，连着打不会读到同一句
    v = rank % 4
    if v == 0:
        wa_en = (
            f"{greet_en}, {NAME} here from {CITY} — we produce colour masterbatch for {label_en}, "
            f"{CAPACITY} t/yr since {YEAR}.\n"
            f"If you buy colour for {label_en}, I can free-match one of your current grades and ship "
            f"the sample with SGS data. Worth a quick look?")
        wa_zh = (
            f"{greet_zh}，我是{公司名}的 {NAME}——做{label_zh}用色母粒，{YEAR} 年起，年产 {CAPACITY} 万吨。\n"
            f"如果贵司采购{label_zh}的配色，我可以按你们现有牌号免费打样，样品连同 SGS 数据一起寄。"
            f"要不要看一眼？")
    elif v == 1:
        wa_en = (
            f"{greet_en}, a quick one from {CITY} — we make the colour masterbatch behind "
            f"{label_en} parts.\n"
            f"If batch-to-batch consistency or colour cost is on your list this quarter, I can "
            f"free-match one grade and send the sample with SGS data.")
        wa_zh = (
            f"{greet_zh}，深圳这边一句短的——{label_zh}件用的色母粒是我们做的。\n"
            f"如果这一季你们在看批间一致性或配色成本，我可以按一个牌号免费打样，"
            f"样品连同 SGS 数据一起寄。")
    elif v == 2:
        wa_en = (
            f"{greet_en}, {NAME} in {CITY} — {YEARS}+ years compounding colour for {label_en}.\n"
            f"Send me a resin grade and a target shade and I will return a free match in 3-5 days, "
            f"with the SGS report. Worth trying one?")
        wa_zh = (
            f"{greet_zh}，我是{公司名}的 {NAME}——给{label_zh}做配色 {YEARS} 多年。\n"
            f"把树脂牌号和目标色给我，3-5 天出免费打样，附 SGS 报告。要不要先试一个？")
    else:
        wa_en = (
            f"{greet_en}, this is {NAME} from {CITY} — colour masterbatch for {label_en}, "
            f"our own plant at {CAPACITY} t/yr.\n"
            f"One question: is colour consistency on your problem list? If it is, I will send a "
            f"free matched sample with SGS data, no charge either way.")
        wa_zh = (
            f"{greet_zh}，我是{公司名}的 {NAME}——做{label_zh}用色母粒，自有工厂，年产 {CAPACITY} 万吨。\n"
            f"问一句：颜色一致性在你们的问题清单上吗？如果在，我寄一份免费匹配样加 SGS 数据，"
            f"成不成都不收费。")

    sj_en = f"Colour masterbatch for {label_en} — free match for {name}"
    sj_zh = f"{label_zh}用色母粒——给 {name} 的免费打样"

    who = WHO[list(WHO.keys())[v]]

    m_en = (
        f"{greet_en},\n\n"
        f"I am writing to {name} because we supply colour masterbatch into {label_en}"
        + (f" around {place}" if place else "") + ", and I would rather check whether it is relevant "
        "than assume it is not.\n\n"
        + who + "\n\n"
        f"What we would bring you is {body_en}. Colour is matched from your physical sample or a "
        "Pantone, and the master stays on file so the second order matches the first without a new "
        "approval round.\n\n"
        + CTA["sample2"] + "\n\n" + SIG_EN)
    m_zh = (
        f"{greet_zh}：\n\n"
        f"写信给您是因为我们向{label_zh}行业供应色母粒"
        + (f"（{place}一带）" if place else "") + "，与其假设不相关，不如先确认一下是否用得上。\n\n"
        "{公司名}在深圳做色母粒，{YEAR} 年起——{AREA} ㎡、{LINES} 条进口线、年产 {CAPACITY} 万吨、{CERT}，"
        "每批附 SGS 数据。\n\n"
        f"我们能提供的是{body_zh}。颜色可按实物样或 Pantone 对色，色板留档，"
        "第二批不用再走一轮审批就对得上第一批。\n\n"
        "如果方便，我可以按你们现有牌号做一次免费打样：树脂加目标色给我即可，"
        "3-5 个工作日出样并附 SGS 报告，运费我们承担。\n\n" + SIG_ZH)

    return {
        "wa_en": wa_en, "wa_zh": wa_zh,
        "sj_en": sj_en, "sj_zh": sj_zh,
        "m_en": m_en, "m_zh": m_zh,
        "pers": False,
    }


if __name__ == "__main__":
    print(f"A 级逐家定制：{len(A_COPY)} 家")
    c = pick(1, "{CUSTOMER}", "PET包装", "{CITY_DEMO}", "{COUNTRY_DEMO}",
             "{CONTACT_FULL}", "A")
    print("=" * 60)
    print("[WhatsApp]\n" + c["wa_en"])
    print("=" * 60)
    print("[Subject] " + c["sj_en"])
    print("=" * 60)
    print(c["m_en"])
    print("=" * 60)
    b = pick(99, "Example Plastics", "电线电缆", "Ohio", "美国", "Tom Reed", "B")
    print("[B 级样例 WhatsApp]\n" + b["wa_en"])
    print("[B 级样例 Subject] " + b["sj_en"])
    print("[pers]", b["pers"])


