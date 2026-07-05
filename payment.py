"""
payment.py — Payment plan calculation logic for healthcare collections chatbot.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PaymentPlan:
    """Represents the outcome of a payment negotiation."""
    status: str                        # "accepted", "rejected", "full_payment"
    today_payment: float = 0.0
    remaining_balance: float = 0.0
    monthly_installment: float = 0.0
    num_installments: int = 0
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "today_payment": round(self.today_payment, 2),
            "remaining_balance": round(self.remaining_balance, 2),
            "monthly_installment": round(self.monthly_installment, 2),
            "num_installments": self.num_installments,
            "rejection_reason": self.rejection_reason,
        }

    def summary_text(self) -> str:
        """Human-readable summary of the plan to present to the patient."""
        if self.status == "rejected":
            return (
                f"I'm sorry, but we cannot accept payments below $50.00. "
                f"The minimum payment we can process is $50.00. "
                f"Would you be able to make a payment of at least $50.00 today?"
            )
        elif self.status == "full_payment":
            return (
                f"That's wonderful! You'll be paying the full balance of "
                f"${self.today_payment:,.2f} today. This will completely "
                f"settle your account. Shall I confirm this arrangement?"
            )
        else:
            return (
                f"Here's the plan I can offer you:\n\n"
                f"• **Payment today:** ${self.today_payment:,.2f}\n"
                f"• **Remaining balance:** ${self.remaining_balance:,.2f}\n"
                f"• **Monthly installments:** {self.num_installments} payments "
                f"of ${self.monthly_installment:,.2f}/month\n\n"
                f"Does this arrangement work for you?"
            )


def calculate_plan(due_amount: float, today_payment: float) -> PaymentPlan:
    """
    Apply payment plan rules:
      - < $50       → reject
      - $50–$99.99  → accept + 12 monthly installments on remainder
      - $100+       → accept + 9 monthly installments on remainder
      - >= due_amount → full payment, no installments
    """
    due_amount = round(due_amount, 2)
    today_payment = round(today_payment, 2)

    if today_payment < 50:
        return PaymentPlan(
            status="rejected",
            today_payment=today_payment,
            rejection_reason="Payment below minimum threshold of $50.00",
        )

    if today_payment >= due_amount:
        return PaymentPlan(
            status="full_payment",
            today_payment=due_amount,
            remaining_balance=0.0,
            monthly_installment=0.0,
            num_installments=0,
        )

    remaining = due_amount - today_payment

    if today_payment < 100:
        num_installments = 12
    else:
        num_installments = 9

    monthly = remaining / num_installments

    return PaymentPlan(
        status="accepted",
        today_payment=today_payment,
        remaining_balance=remaining,
        monthly_installment=monthly,
        num_installments=num_installments,
    )
