# Transaction Fraud Detection - Dashboard Test Guide

## Sample Data Overview

This test uses real-world transaction fraud detection scenarios:

### Dataset 1: `transactions.csv`
- **Records**: 30 transactions
- **Features**:
  - `amount`: Transaction amount (numeric) - KEY FEATURE
  - `previous_transactions`: User's transaction history (numeric) - KEY FEATURE
  - `days_since_signup`: Account age (numeric) - KEY FEATURE
- **Patterns in Data**:
  - **Low-Risk Transactions**: US domestic, amount $50-300, many prior transactions
  - **High-Risk Transactions**: Large transfers ($2000-12000), new accounts, non-US countries
  - **Fraud Indicators**: Very high amounts, brand new account (0-5 days), unusual countries

### Dataset 2: `transactions_additional.json`
- **Records**: 10 additional transactions
- **Complements CSV with more diverse patterns**

### Expected Clusters

When clustering this transaction data, the algorithm should naturally separate:

1. **Cluster 1 (Legitimate)**: 
   - Small purchases ($20-200)
   - Desktop/Mobile payments
   - Established accounts (50+ days)
   - US transactions

2. **Cluster 2 (High-Risk)**:
   - Large transfers ($3000-12000)
   - New accounts (0-10 days)
   - Non-US destinations (NG, CN, RU, IN, BR, etc.)
   - Unusual patterns

3. **Cluster 3 (Medium-Risk)**:
   - Medium transfers ($500-2000)
   - Mid-range account age
   - International but different risk profile

## Dashboard Walkthrough

### Step 1: Data Ingestion

**What happens:**
1. Click "🔄 Ingest Data"
2. Pipeline reads `config.yaml`
3. Finds `transactions.csv` and `transactions_additional.json`
4. Parses both files
5. Creates SQLite tables

**Expected Output:**
```
✓ Data ingestion completed! Loaded 2 sources

Tables created:
  • transactions
  • transactions_additional
```

**Check Functionality:**
- Click "Show tables after ingestion"
- Verify both tables appear

### Step 2: Clustering

**Configuration:**

Select clustering parameters for fraud detection:

**Recommended K values to test:**
- K=3 (Expected: Legitimate, Medium-Risk, High-Risk)
- K=5 (More granular fraud segments)
- K=8 (Very detailed risk stratification)

**Why these K values:**
- K=3: Natural fraud risk triplet
- K=5: Detects subtle risk gradations
- K=8: Maximum segmentation

**Workflow:**
1. Select "transactions" from dropdown
2. Check K=3, K=5 checkboxes
3. Click "🚀 Perform Clustering"

**Expected Results:**

| Variant | Silhouette | Use Case |
|---------|-----------|----------|
| KMeans K=3 | ~0.45-0.55 | Best for fraud/legitimate binary + medium |
| KMeans K=5 | ~0.35-0.45 | Risk spectrum across 5 levels |
| DBSCAN eps=0.3 | ~0.30-0.50 | Density-based risk clusters |
| DBSCAN eps=0.5 | ~0.40-0.60 | Default density - often good |
| DBSCAN eps=0.7 | ~0.20-0.40 | Larger neighborhoods, fewer clusters |

**Key Metrics to Observe:**
- **Silhouette Score**: 
  - >0.5 = Excellent separation
  - 0.3-0.5 = Good clustering
  - <0.3 = Consider different K

**What Each Variant Reveals:**

```
KMeans K=3:
  Cluster 0: Small purchases (~$50-200), established users
  Cluster 1: Large transfers ($2000-5000), newer users
  Cluster 2: Very large transfers ($5000+), very new accounts

KMeans K=5:
  Cluster 0: Tiny purchases (<$100)
  Cluster 1: Medium purchases ($100-500)
  Cluster 2: Large transfers ($500-2000)
  Cluster 3: Very large transfers ($2000-6000)
  Cluster 4: Massive transfers ($6000+)

DBSCAN eps=0.5:
  Cluster 0: Dense core legitimate transactions
  Cluster 1: Outlier high-risk transactions
  Noise points: Extremely unusual patterns
```

### Step 3: Approval & Final Selection

**Recommendation for Fraud Detection:**

Choose: **KMeans K=3** or **KMeans K=5**

**Reasoning:**
1. **KMeans K=3**: 
   - Clear fraud/legitimate binary
   - + Medium-risk middle ground
   - Best for immediate deployment
   
2. **KMeans K=5**:
   - Risk spectrum from low→high
   - Better for risk-based pricing/controls
   - More nuanced fraud detection

**DO NOT select:**
- DBSCAN with very large eps (>0.7)
- Clusters with negative silhouette (<0.2)

**Approval Process:**

1. Go to "Approval" page
2. Review cluster metrics
3. Preview transactions with cluster labels
4. Click "✅ Approve This Clustering"

**Example Final Table:**

```
transactions_kmeans_k3_final

transaction_id | amount | days_since_signup | cluster | risk_level
T001          | 150.50 | 30               | 0       | LOW
T003          | 2500.00| 7                | 1       | MEDIUM
T006          | 5000.00| 30               | 2       | HIGH
T011          | 8000.00| 2                | 2       | HIGH
T024          | 34.75  | 90               | 0       | LOW
```

## Interpretation Guide

### Low-Risk Transactions (Cluster with small amounts, established accounts)

```
Characteristics:
  ✓ Amount: $20-500
  ✓ Account age: >30 days
  ✓ Previous transactions: >5
  ✓ Country: Primarily US/UK/developed nations
  ✓ Device: Any (mobile, desktop, tablet)

Action: APPROVE instantly
```

### Medium-Risk Transactions (Cluster with medium amounts, mixed profile)

```
Characteristics:
  ⚠ Amount: $500-2500
  ⚠ Account age: 10-50 days
  ⚠ Previous transactions: 3-10
  ⚠ Country: Developed or verified nations
  ⚠ Device: Typically desktop

Action: REVIEW with additional checks
        - Verify user identity
        - Check merchant reputation
        - Validate payment method
```

### High-Risk Transactions (Cluster with large amounts, new accounts)

```
Characteristics:
  ✗ Amount: $3000+
  ✗ Account age: <10 days (CRITICAL)
  ✗ Previous transactions: <3
  ✗ Country: Emerging markets or high-fraud nations
  ✗ Device: Mobile (higher fraud rate)
  ✗ Type: Transfer (not purchase)

Action: BLOCK or REQUIRE IMMEDIATE VERIFICATION
        - Contact user
        - Request ID verification
        - Confirm high-risk country
        - May require phone OTP
```

## Hands-On Test Scenario

### Test Case 1: Detect Fraud Patterns

**Objective**: Can the clustering separate legitimate from fraudulent transactions?

**Transactions to Watch:**

Legitimate (Should be in same cluster):
- T002: $45.99, 12 prior tx, US
- T007: $34.25, 18 prior tx, US
- T015: $67.50, 22 prior tx, US

High-Risk (Should be in different cluster):
- T018: $12000, 0 prior tx, 1 day old, Thailand
- T037: $11000, 0 prior tx, 2 days old, Kenya
- T011: $8000, 1 prior tx, 2 days old, Russia

**Result**: ✓ PASS if separated into different clusters

### Test Case 2: K Value Sensitivity

**Objective**: Compare how K affects cluster purity

**Steps:**
1. Run K=3 clustering
2. Run K=5 clustering
3. Compare silhouette scores
4. Note which distinguishes fraud better

**Expected**: K=5 gives more granular fraud detection

### Test Case 3: Multi-Source Consistency

**Objective**: Verify CSV and JSON load consistently

**Steps:**
1. Ingest both files
2. Cluster both "transactions" and "transactions_additional"
3. Compare cluster assignments

**Expected**: Similar patterns despite different file formats

## Metrics Interpretation

### Silhouette Score

```
Score Range    | Meaning           | Recommendation
0.71 - 1.00    | Strong clusters   | ✓ Use for production
0.51 - 0.70    | Reasonable        | ✓ Use with caution
0.21 - 0.50    | Weak              | ⚠ Consider alternatives
≤ 0.20         | No structure      | ✗ Reject clustering
```

### Inertia (KMeans only)

Lower inertia = tighter clusters = better separation

```
Comparing K=3 vs K=5:
  K=3 inertia: ~500 (larger clusters)
  K=5 inertia: ~300 (smaller, tighter)
  
Inference: K=5 provides better segmentation
```

### Noise Points (DBSCAN only)

```
High noise points (>20%): Data has outliers
Low noise points (<5%): Data is well-clustered

For fraud: Some outliers are expected (actual fraud)
```

## Production Checklist

Before deploying fraud detection clusters:

- [ ] Silhouette score > 0.4
- [ ] All clusters have meaningful size (not <5% of data)
- [ ] Risk profiles align with domain knowledge
- [ ] Can explain why transactions grouped together
- [ ] False positive rate acceptable (<5%)
- [ ] False negative rate acceptable (<2%)
- [ ] Clusters stable across different random seeds

## Troubleshooting

### "Silhouette score is very low (< 0.2)"

**Cause**: Data doesn't separate well into clusters
**Solution**: 
- Try different K values
- Consider data preprocessing (normalize amounts better)
- Use domain knowledge features (merchant category, location)

### "One cluster has most data, others have few"

**Cause**: K too high or data imbalanced
**Solution**:
- Reduce K value
- Use DBSCAN with different eps
- Apply stratified clustering

### "Results different between runs"

**Cause**: Random seed variation in KMeans
**Solution**:
- Set fixed random seed
- Results should be nearly identical
- Current code uses random_state=42

## Next Steps After Approval

Once cluster is approved and final table created:

1. **Analyze Cluster Characteristics**
   ```sql
   SELECT cluster, COUNT(*) as count, 
          AVG(amount) as avg_amount,
          AVG(days_since_signup) as avg_account_age
   FROM transactions_kmeans_k3_final
   GROUP BY cluster
   ```

2. **Define Risk Rules**
   ```
   Cluster 0 → APPROVE (Low-risk)
   Cluster 1 → REVIEW (Medium-risk)
   Cluster 2 → BLOCK (High-risk)
   ```

3. **Implement Real-Time Scoring**
   - New transaction comes in
   - Calculate features (amount, account_age, etc.)
   - Predict cluster using same model
   - Apply corresponding rule

4. **Monitor Performance**
   - Track false positives/negatives
   - Measure detection accuracy
   - Retrain quarterly with new data

## Sample Queries After Clustering

```sql
-- Show cluster distribution
SELECT cluster, COUNT(*) as transaction_count
FROM transactions_kmeans_k3_final
GROUP BY cluster;

-- Show average risk metrics per cluster
SELECT cluster, 
       AVG(amount) as avg_amount,
       AVG(previous_transactions) as avg_prior_tx,
       AVG(days_since_signup) as avg_account_age
FROM transactions_kmeans_k3_final
GROUP BY cluster
ORDER BY avg_amount DESC;

-- Identify high-risk countries
SELECT cluster, country, COUNT(*) as count
FROM transactions_kmeans_k3_final
WHERE cluster = 2  -- High-risk cluster
GROUP BY country
ORDER BY count DESC;
```

## Performance Expectations

**On Sample Data:**
- Ingestion: <1 second
- Clustering (K=3,5,8 + DBSCAN variants): 2-5 seconds
- Total workflow: <10 seconds

**On Production Data (10K+ transactions):**
- Ingestion: 5-10 seconds
- Clustering: 30-60 seconds
- Total workflow: 1-2 minutes

---

**Ready to test?** Follow the dashboard workflow above starting with "Step 1: Data Ingestion"
