## NOTE: See the interactive Dashboard from the deployments.

## 📊 Key Business Insights & Strategic Recommendations

1. **High Churn in Discounted Plans**
   * **What happened?** Users on promotional / discounted plans exhibit a 40% higher churn rate after month 3 compared to full-price users.
   * **Why did it happen?** High price sensitivity. Once the discount ends, the perceived value does not match the standard price.
   * **Leadership Action:** Shift from permanent discounts to temporary trial periods, or lock discounted rates behind annual upfront commitments to guarantee payback period.

2. **Usage Decline as a Leading Indicator**
   * **What happened?** A 30% drop in core feature usage over a rolling 14-day window is the strongest predictor of voluntary churn.
   * **Why did it happen?** Users failed to integrate the SaaS tool into their daily workflows (poor onboarding/adoption).
   * **Leadership Action:** Implement automated engagement nudges (email/in-app) triggered when usage drops below the 'Medium Risk' threshold.

3. **Involuntary Churn Impact**
   * **What happened?** ~15% of all churn was Involuntary (payment failures/expired cards).
   * **Why did it happen?** Lack of an aggressive dunning process.
   * **Leadership Action:** Implement an automated retry logic engine (Stripe/Chargebee) and send pre-expiration card alerts to capture "lost" revenue.
