# Tutorials

This directory contains comprehensive tutorials and analysis guides for the LLM Simulator project.

## 📁 Directory Structure

```
tutorial/
├── README.md                           # This file
├── assets/                             # Analysis results and visualizations
│   ├── arrival_rate_sweep_report.json  # Arrival rate sweep analysis results
│   ├── arrival_rate_sweep.png          # Arrival rate sweep visualization
│   ├── decode_queue_report.json        # Decode queue analysis results
│   ├── decode_queue_impact.png         # Decode queue impact visualization
│   ├── queue_impact_report.json        # Queue impact study results
│   └── queue_impact_analysis.png       # Queue impact analysis visualization
├── arrival_rate_sweep_analysis.md      # Comprehensive arrival rate analysis (0.5-10 req/s)
├── decode_queue_impact_analysis.md     # Decode queue impact study
├── queue_impact_study.md               # Queue process impact study guide
└── readthedocs_fix_summary.md          # ReadTheDocs configuration fix documentation
```

## 🎯 Tutorial Contents

### 1. **Arrival Rate Sweep Analysis**
- **File**: `arrival_rate_sweep_analysis.md`
- **Assets**: `arrival_rate_sweep_report.json`, `arrival_rate_sweep.png`
- **Description**: Comprehensive analysis of decode queue impact across arrival rates from 0.5 to 10 requests per second

### 2. **Decode Queue Impact Analysis**
- **File**: `decode_queue_impact_analysis.md`
- **Assets**: `decode_queue_report.json`, `decode_queue_impact.png`
- **Description**: Specialized study of decode queue effects on TTFT performance

### 3. **Queue Impact Study**
- **File**: `queue_impact_study.md`
- **Assets**: `queue_impact_report.json`, `queue_impact_analysis.png`
- **Description**: Comprehensive guide to studying queue process impact on TTFT

### 4. **ReadTheDocs Configuration Fix**
- **File**: `readthedocs_fix_summary.md`
- **Description**: Documentation of ReadTheDocs configuration fixes and improvements

## 🔍 Key Insights

### Performance Optimization
- **Bottleneck Detection**: Monitor decode utilization > 80%
- **Scaling Guidelines**: Add decode nodes when arrival rate > 8 req/s
- **Resource Planning**: Balance performance vs cost for optimal configuration

### System Design
- **Queue Theory**: M/M/c queue models accurately predict performance
- **Architecture Impact**: Decode queue configuration critical for TTFT
- **Capacity Planning**: Match capacity to expected load patterns
