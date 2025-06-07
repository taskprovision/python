# billing/stripe_integration.py
import stripe
from datetime import datetime, timedelta

stripe.api_key = "sk_test_..."  # Free account

class AutoDevBilling:
    def __init__(self):
        self.plans = {
            "starter": {"price": 29, "projects": 3},
            "professional": {"price": 79, "projects": -1},  # unlimited
            "enterprise": {"price": 199, "custom": True}
        }
    
    def create_customer_subscription(self, email, plan_type, github_username):
        """Create subscription with 14-day free trial"""
        
        customer = stripe.Customer.create(
            email=email,
            metadata={"github": github_username, "source": "autodev"}
        )
        
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": f"price_{plan_type}"}],
            trial_period_days=14,  # Free trial
            metadata={"plan": plan_type}
        )
        
        # Trigger welcome sequence
        self.send_onboarding_email(email, github_username)
        
        return subscription
    
    def usage_based_billing(self, customer_id, api_calls, generation_time):
        """Track usage for potential upselling"""
        
        # Log usage patterns
        usage_data = {
            "customer": customer_id,
            "api_calls": api_calls,
            "generation_time": generation_time,
            "timestamp": datetime.now()
        }
        
        # Auto-suggest plan upgrade if needed
        if api_calls > 1000:  # Starter limit
            self.suggest_upgrade(customer_id, "professional")