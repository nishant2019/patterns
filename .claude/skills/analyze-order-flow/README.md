# 订单流分析 Skill (Order Flow Analysis)

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-green.svg)](#)

基于足迹图、成交量分布 (VRVP/Volume Profile)、Delta 等可观测数据，推断市场主动/被动成交行为，输出带证据链的交易复盘报告。

## ✨ 功能特点

- 🎯 **专业分析框架**：四步法 SOP（宏观结构 → 资金意图 → 微观博弈 → 综合研判）
- 📊 **多维度数据**：整合 Footprint、Volume Profile、Delta、CVD 等核心指标
- 📝 **结构化输出**：提供标准化的分析报告模板，包含证据链和情景计划
- 🔄 **批量处理**：支持多标的同时分析，生成汇总报告

## 📦 安装

### 方法一：项目级安装（推荐）

将 skill 克隆到你项目的 `.agent/skills/` 目录：

```bash
# 在你的项目根目录执行
mkdir -p .agent/skills
git clone https://github.com/iceberg211/orderflow-skill.git .agent/skills/analyze-order-flow
```

### 方法二：全局安装

将 skill 克隆到全局 skills 目录，对所有项目生效：

```bash
# macOS/Linux
git clone https://github.com/iceberg211/orderflow-skill.git ~/.gemini/antigravity/skills/analyze-order-flow

# Windows
git clone https://github.com/iceberg211/orderflow-skill.git %USERPROFILE%\.gemini\antigravity\skills\analyze-order-flow
```

## 🚀 使用方法

### 基本用法

1. 上传交易图表（足迹图、VRVP 图、Delta 图）
2. 请求 AI 进行订单流分析

```
请分析这张足迹图
```

### 提供详细信息可获得更精确分析

```
标的：BTCUSDT 永续合约
周期：15分钟
平台：TradingView
请分析当前的订单流状态
```

## 📋 输入要求

为获得最佳分析结果，图表应包含以下信息：

| 指标 | 必需性 | 用途 |
|------|--------|------|
| 足迹图 (Footprint) | ⭐ 核心 | 分析单根K线内部的买卖力量分布 |
| 成交量分布 (VRVP) | ⭐ 核心 | 识别 HVN/LVN、POC 与价值区 |
| Delta | ⭐ 核心 | 判断主动买/卖的净值与背离 |
| 剖面范围定义 | 建议 | 决定 POC/HVN/LVN 的统计口径 |
| CVD | 可选 | 观察多周期资金流向趋势 |

## 📖 输出示例

### 核心结论表

| 项目 | 判断 |
|------|------|
| 市场状态 | 弱多头 |
| 主要信号 | HVN 处获得支撑，Delta 转正，价值区上移 |
| 情景计划 | 如回踩 POC 出现买方失衡，偏向继续上行 |
| 失效条件 | 价格跌破 HVN 并被接受 |
| 置信度 | 中 |

### 证据链分析

包含四个维度的详细分析：
- 宏观结构（Volume Profile）
- 资金意图（Delta）
- 微观博弈（Footprint）
- 动能确认（CVD，可选）

查看完整示例报告：[examples/](./examples/)

## 📁 文件结构

```
orderflow-skill/
├── SKILL.md              # 核心 Skill 指令文件
├── README.md             # 本文档
└── examples/             # 教学示例（教 AI 如何分析）
    ├── 01_market_state.md       # 如何判断市场状态
    ├── 02_key_levels.md         # 如何识别关键价位
    ├── 03_delta_divergence.md   # Delta 分析与背离识别
    ├── 04_footprint_imbalance.md# Footprint 微观分析
    └── 05_scenario_planning.md  # 如何制定情景计划
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本 Skill 仅为技术复盘与学习研究用途，不构成任何投资建议。市场有风险，决策需谨慎。
