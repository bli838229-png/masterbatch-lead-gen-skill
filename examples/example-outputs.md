# 示例：开发信与线索表（脱敏版）

> ⚠️ 以下为**脱敏示例**，仅展示输出格式。真实客户数据（企业名、邮箱、电话）应保存在本地，**绝不提交到公开仓库**。

## 开发信示例（越南语 · 脱敏）

**收件**：`sales@example-company.vn`
**主题**：`Hạt màu & hạt chống cháy cho linh kiện điện gia dụng`

> Kính gửi Quý Công ty **[Tên Công Ty]**,
>
> Tôi là **[Tên]** từ **[Công ty của bạn]** — nhà sản xuất hạt màu masterbatch chuyên về hạt màu theo yêu cầu, phối màu và hạt masterbatch chống cháy.
>
> Chúng tôi được biết quý công ty chuyên sản xuất **[linh kiện điện gia dụng / bao bì dược phẩm]**. Chúng tôi cung cấp hạt màu theo yêu cầu và hạt chống cháy đạt tiêu chuẩn UL 94 / RoHS / REACH, cùng phòng lab phối màu riêng để lấy mẫu nhanh.
>
> Nếu quý công ty đang tìm nguồn hạt màu, tôi rất mong được gửi mẫu hoặc trao đổi thêm.
>
> Trân trọng,
> **[Tên]** | **[Công ty]** | **[Email]** | **[Zalo]**

## 线索池 CSV 示例（脱敏）

```csv
company_name,country,city,industry,website,email,phone_whatsapp,linkedin,buyer_hint,products_needed,score,grade,source_url,status
[Company A],Vietnam,Ho Chi Minh City,Injection molding,https://example-a.vn,sales@example-a.vn,+84-xxx,,[purchasing contact],custom color masterbatch,22,A,https://source.example,not_contacted
[Company B],Vietnam,Binh Duong,Engineering plastic (POM/PA6),https://example-b.vn,info@example-b.vn,+84-xxx,,,custom color masterbatch,21,A,https://source.example,not_contacted
```

## 如何使用真实数据

1. 运行 skill 生成真实线索后，保存到本地（如 `leads/vietnam.csv`）。
2. 该目录已在 `.gitignore` 中排除，不会进仓库。
3. 上传 GitHub 前运行 `git status` 确认没有真实客户数据被暂存。
