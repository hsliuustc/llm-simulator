# Queue Process Impact Study on TTFT

This document provides a comprehensive guide to studying the impact of queue processes on Time-To-First-Token (TTFT) performance in LLM serving systems.

## Overview

The queue process impact study is designed to analyze how different queueing scenarios affect TTFT performance under FCFS (First-Come-First-Served) scheduling. This study helps understand:

1. **Queue Wait Times**: How waiting in queues affects TTFT
2. **Resource Utilization**: How resource bottlenecks impact performance
3. **Load Sensitivity**: How TTFT changes with different arrival rates
4. **Architecture Comparison**: Monolithic vs disaggregated queueing characteristics

## Key Concepts

### Queue Process in LLM Serving

In disaggregated LLM serving, requests pass through multiple queues:

1. **Prefill Queue**: Requests wait for prefill GPU resources
2. **Decode Queue**: Requests wait for decode GPU resources

Each queue follows FCFS scheduling, where requests are served in the order they arrive.

### TTFT Components

TTFT consists of several components:

```
TTFT = Prefill_Queue_Wait + Prefill_Service_Time + Decode_Queue_Wait + Decode_Service_Time
```

Where:
- **Queue Wait Times**: Time spent waiting for available resources
- **Service Times**: Actual processing time for the request

## Study Scenarios

### 1. Low Load FCFS (`low_load_fcfs`)

**Purpose**: Establish baseline TTFT without significant queueing effects.

**Parameters**:
- Arrival rate: 0.5 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- Prefill rate: 8000 tokens/s
- Decode rate: 2000 tokens/s

**Expected Results**:
- Low TTFT (< 0.5s)
- Minimal queue wait times
- Low resource utilization

**Use Case**: Baseline performance measurement.

### 2. Medium Load FCFS (`medium_load_fcfs`)

**Purpose**: Observe moderate queueing effects.

**Parameters**:
- Arrival rate: 2.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- Prefill rate: 8000 tokens/s
- Decode rate: 2000 tokens/s

**Expected Results**:
- Moderate TTFT (0.5-1.0s)
- Some queue wait times
- Moderate resource utilization

**Use Case**: Typical production load analysis.

### 3. High Load FCFS (`high_load_fcfs`)

**Purpose**: Observe significant queueing effects.

**Parameters**:
- Arrival rate: 4.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- Prefill rate: 8000 tokens/s
- Decode rate: 2000 tokens/s

**Expected Results**:
- High TTFT (> 1.0s)
- Significant queue wait times
- High resource utilization

**Use Case**: High-load performance analysis.

### 4. Slow Prefill FCFS (`slow_prefill_fcfs`)

**Purpose**: Study prefill queue impact.

**Parameters**:
- Arrival rate: 2.0 req/s
- Prefill GPUs: 1 (reduced)
- Decode GPUs: 2
- Prefill rate: 4000 tokens/s (reduced)
- Decode rate: 2000 tokens/s

**Expected Results**:
- Prefill bottleneck
- Increased prefill queue wait times
- High prefill utilization

**Use Case**: Prefill resource planning.

### 5. Slow Decode FCFS (`slow_decode_fcfs`)

**Purpose**: Study decode queue impact.

**Parameters**:
- Arrival rate: 2.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 1 (reduced)
- Prefill rate: 8000 tokens/s
- Decode rate: 1000 tokens/s (reduced)

**Expected Results**:
- Decode bottleneck
- Increased decode queue wait times
- High decode utilization

**Use Case**: Decode resource planning.

### 6. Balanced FCFS (`balanced_fcfs`)

**Purpose**: Study balanced processing times.

**Parameters**:
- Arrival rate: 2.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- Prefill rate: 4000 tokens/s
- Decode rate: 4000 tokens/s

**Expected Results**:
- Balanced queue utilization
- Moderate TTFT
- Similar prefill and decode wait times

**Use Case**: Balanced architecture design.

### 7. Monolithic FCFS (`monolithic_fcfs`)

**Purpose**: Compare with disaggregated FCFS.

**Parameters**:
- Arrival rate: 2.0 req/s
- GPUs: 4
- Prefill rate: 8000 tokens/s
- Decode rate: 2000 tokens/s

**Expected Results**:
- Different queueing characteristics
- Single queue vs dual queue
- Different resource utilization patterns

**Use Case**: Architecture comparison.

### 8. Queue Saturation Study (`queue_saturation_study`)

**Purpose**: Study queue saturation effects.

**Parameters**:
- Arrival rate: 6.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- Prefill rate: 8000 tokens/s
- Decode rate: 2000 tokens/s

**Expected Results**:
- Very high TTFT
- Queue saturation
- Performance degradation

**Use Case**: System limits analysis.

### 9. Variable Load FCFS (`variable_load_fcfs`)

**Purpose**: Study queue dynamics under variable load.

**Parameters**:
- Arrival rate: 3.0 req/s
- Prefill GPUs: 2
- Decode GPUs: 2
- High variance in token distributions

**Expected Results**:
- Increased TTFT variance
- Variable queue wait times
- Dynamic resource utilization

**Use Case**: Variable workload analysis.

## Running the Study

### Quick Start

```bash
# Run comprehensive study with all scenarios
python -m src.cli.queue_study --comprehensive

# Run specific scenario
python -m src.cli.queue_study --scenario medium_load

# Run load sweep for a scenario
python -m src.cli.queue_study --scenario medium_load --load-sweep --rates 0.5,1,2,3,4
```

### Advanced Usage

```bash
# Custom simulation parameters
python -m src.cli.queue_study --scenario high_load --sim-seconds 1200 --warmup-seconds 120

# Custom output directory
python -m src.cli.queue_study --comprehensive --output-dir ./results

# Skip plots or reports
python -m src.cli.queue_study --comprehensive --no-plots --no-report
```

## Interpreting Results

### Key Metrics

1. **TTFT Percentiles**:
   - **P50**: Median TTFT (typical performance)
   - **P90**: 90th percentile (performance under load)
   - **P99**: 99th percentile (worst-case performance)

2. **Queue Wait Times**:
   - **Prefill Queue Wait**: Time waiting for prefill resources
   - **Decode Queue Wait**: Time waiting for decode resources

3. **Resource Utilization**:
   - **Prefill Utilization**: Fraction of time prefill GPUs are busy
   - **Decode Utilization**: Fraction of time decode GPUs are busy

4. **Throughput**:
   - **Requests per second**: System throughput
   - **Efficiency**: Throughput vs arrival rate ratio

### Analysis Guidelines

#### Low TTFT (< 0.5s)
- Minimal queueing impact
- System operating well below capacity
- Good user experience

#### Moderate TTFT (0.5-1.0s)
- Some queueing impact
- System approaching capacity
- Acceptable user experience

#### High TTFT (> 1.0s)
- Significant queueing impact
- System near or at capacity
- Poor user experience

#### Bottleneck Analysis
- **Prefill Bottleneck**: `utilization_prefill > 0.9`
- **Decode Bottleneck**: `utilization_decode > 0.9`
- **Balanced**: Both utilizations similar

## Expected Findings

### Queue Impact Patterns

1. **Arrival Rate Impact**:
   - TTFT increases exponentially with arrival rate
   - Queue wait times dominate at high loads
   - Throughput saturates at bottleneck capacity

2. **Resource Bottlenecks**:
   - Prefill bottlenecks: High prefill queue wait times
   - Decode bottlenecks: High decode queue wait times
   - Balanced bottlenecks: Similar wait times in both queues

3. **Architecture Comparison**:
   - Monolithic: Single queue, different utilization patterns
   - Disaggregated: Dual queues, potential for better resource utilization

### Performance Insights

1. **Queue Saturation**:
   - Occurs when utilization approaches 1.0
   - Causes exponential TTFT increase
   - Requires load shedding or capacity increase

2. **Resource Planning**:
   - Balance prefill and decode resources
   - Consider workload characteristics
   - Plan for peak loads

3. **System Design**:
   - Disaggregated architecture provides flexibility
   - FCFS scheduling may not be optimal for all workloads
   - Consider priority queues for latency-sensitive requests

## Troubleshooting

### Common Issues

1. **High TTFT in Low Load**:
   - Check resource configuration
   - Verify token distribution parameters
   - Ensure warmup period is sufficient

2. **Unexpected Bottlenecks**:
   - Review resource allocation
   - Check processing rates
   - Analyze workload characteristics

3. **Inconsistent Results**:
   - Verify random seed
   - Check simulation duration
   - Ensure sufficient warmup period

### Performance Optimization

1. **Reduce Queue Wait Times**:
   - Increase resource capacity
   - Optimize processing rates
   - Implement better scheduling

2. **Balance Resource Utilization**:
   - Adjust resource allocation
   - Match workload characteristics
   - Consider dynamic scaling

3. **Improve System Design**:
   - Consider alternative architectures
   - Implement priority queues
   - Add admission control

## Conclusion

The queue process impact study provides valuable insights into:

- **Queue Dynamics**: How queues affect TTFT performance
- **Resource Planning**: Optimal resource allocation strategies
- **System Design**: Architecture trade-offs and optimization
- **Performance Tuning**: Methods to improve TTFT performance

By understanding these queue processes, you can design more efficient LLM serving systems and optimize for better TTFT performance.
