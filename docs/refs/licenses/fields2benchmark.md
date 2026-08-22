# Fields2Benchmark 许可证原文摘录与解读

**取得方式**：2026-08-21 直接下载 Zenodo 记录 14524735 的 `LICENSE`（20 131 字节）
与 `README.md`（5 734 字节）两个文件本体，逐字节读取。
**不是**元数据摘要，**不是**任何第三方转述。

**状态：待人裁定。** 本文件给出原文与解读依据；代码只实现了机制
（`export_corpus(allow_analysis=…, allow_redistribution=…)`，两个开关都无默认值），
**没有替任何人做法律判断，也没有改动任何默认值**。

---

## 一、记录本体的许可

Zenodo 记录 14524735 的文件清单：

| 文件 | 大小 |
|---|---:|
| `imgs.zip` | 145 310 040 B |
| `wkt.zip` | **211 710 B** |
| `LICENSE` | 20 131 B |
| `README.md` | 5 734 B |

`LICENSE` 文件的首行原文：

```
Attribution-ShareAlike 4.0 International
```

即 **CC BY-SA 4.0** 全文。该文件中 **不含任何 `NonCommercial` 或 `commercial` 字样**
（全文检索为零命中）。其 ShareAlike 条款原文：

> "The Adapter's License You apply must be a Creative Commons license with the same
> License Elements, this version or later, or a BY-SA Compatible License."

**⚠️ 第一处不一致**：Zenodo 记录的**元数据字段**写的是 `CC-BY-4.0`（无 SA），
而记录里的 `LICENSE` **文件**是 `CC BY-SA 4.0`（有 SA）。两者不是同一个许可。
以哪个为准需要人裁定；本仓库两种解读下的行为相同（都不影响 LT 那 113 块的结论）。

---

## 二、README 里的逐国来源与许可（原文逐条）

### 荷兰

```
#### License
- PDOK Data
    - [CC0 1.0 Universal (CC0 1.0) Public Domain Dedication ](http://creativecommons.org/publicdomain/zero/1.0/deed.nl)
    - [no conditions to access and use](http://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply)
    - [no limitations to public access](https://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations)
- Nationaal Georegister Data: [Public Domain Mark 1.0](http://creativecommons.org/publicdomain/mark/1.0/deed.nl) (No Copyright)
```

### 爱沙尼亚

```
#### License Terms
##### Conditions Applying To Access And Use
[Andmete kasutamisel nõustute Creative Commons 3.0 litsentsiga](https://creativecommons.org/licenses/by-sa/3.0/ee/legalcode)
##### Limitations On Public Access
avaliku juurdepääsu piirangud puuduvad (_no public access restrictions_)
```

链接指向 **CC BY-SA 3.0 EE**。

### 立陶宛 —— 这一条是全部争议所在

```
Teisiniai apribojimai (1) (Legal Constraints (1))
Metaduomenys (Metadata) / Duomenų resursas (1) (Data Identification (1)) / Teisiniai apribojimai (1) (Legal Constraints (1))
	Naudojimo ribotumas (Use Limitation): Tik nekomerciniam naudojimui (Non-commercial use only)
	Prieigos apribojimai (Access Constraints): Autoriaus teisės (Copyright)
	Naudojimo apribojimai (Use Constraints): Autoriaus teisės (Copyright)
```

---

## 三、我的解读与依据

**逐条对着上面的原文，不引申。**

1. **「Non-commercial use only」限制的是_使用_，且它出现在 `Use Limitation` 这个字段里。**
   ISO 19115 / INSPIRE 元数据里 `Use Limitation` 与 `Use Constraints` 是两个不同字段：
   前者是用途上的限制说明，后者是法律约束类型。原文把「非商业」放在 `Use Limitation`，
   把「Copyright」放在 `Access Constraints` 与 `Use Constraints`。
   → **学术研究属于非商业使用，因此「用于分析」有明文许可支持。**

2. **原文没有任何再分发授权。** `Access Constraints` 与 `Use Constraints` 两栏都只写
   `Autoriaus teisės (Copyright)`——即「适用著作权」，没有给出任何许可条款。
   默认著作权规则下，未获授权即不得再分发。
   → **「公开再分发」缺乏授权依据，应视为不允许。**

3. **F2B 的 CC BY-SA 4.0 不能覆盖上游。** 打包方不可能就它自己不拥有的权利授权他人。
   记录级许可对 NL/EE 部分成立；对 LT 部分，上游的 Copyright 约束优先，不因被打包而消失。

4. **⚠️ 第二处不一致（提请注意）**：F2B 记录整体以 CC BY-SA 4.0 发布，
   而其中 LT 部分上游是 Copyright + 非商业限定。这两者在再分发这一点上互相冲突。
   这是**上游数据集自身的问题**，不是本仓库造成的；本仓库的处置是按上游更严的一方执行。

### 结论（**待人裁定**）

| 用途 | NL (CC0/PDM) | EE (BY-SA 3.0) | LT (非商业+Copyright) |
|---|:--:|:--:|:--:|
| 分析（不外发） | ✅ | ✅ | ✅ 有明文支持 |
| 公开再分发 | ✅ | ✅（附 BY-SA 义务） | ❌ 无授权依据 |

若裁定采纳，可用样本量：

| 场景 | n |
|---|---:|
| 现状（一刀切过滤 LT） | **235** |
| 分析用全量（350 − 2 块自交隔离） | **348** |
| 公开发布的衍生数据 | **235** |

样本量 **+48%**，且公开发布物不变。

---

## 四、代码里的落点

- `src/agriautolab/datasets/fields2benchmark.py`
  - `LICENSE_PERMITS_ANALYSIS` / `LICENSE_PERMITS_REDISTRIBUTION`：上表的机器可读形式，
    注释里带原文摘录。**这是解读，不是事实。**
  - `export_corpus(..., allow_analysis: bool, allow_redistribution: bool)`：
    两个开关**均无默认值**；两项都为 False 直接抛错（那不是保守，是没说要干什么）。
  - 含非商业记录且未声明再分发时，manifest 带警告
    「本导出包含仅限非商业使用的数据；已按 allow_redistribution=False 导出，不得公开再分发」。
- `scripts/import_fields2benchmark.py`
  - `--allow-analysis/--no-allow-analysis` 与 `--allow-redistribution/--no-allow-redistribution`，
    两个都必须显式给，缺一个就 `parser.error`。

**本轮没有用 `allow_redistribution=False` 重跑语料。** 在裁定之前不扩样本，
这是任务书「最终由人拍板」的直接执行。
