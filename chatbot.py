"""
chatbot.py — LLM conversation engine and state machine for healthcare collections chatbot.
"""

import json
import re
from datetime import datetime
from typing import Optional
from groq import Groq
from payment import PaymentPlan, calculate_plan


# ── Conversation States ────────────────────────────────────────────────────────

class State:
    AUTH_NAME       = "AUTH_NAME"
    AUTH_DOB        = "AUTH_DOB"
    AUTH_FAILED     = "AUTH_FAILED"
    EXPLAIN_DEBT    = "EXPLAIN_DEBT"
    PAYMENT_AMOUNT  = "PAYMENT_AMOUNT"
    CONFIRM_PLAN    = "CONFIRM_PLAN"
    CLOSED_ACCEPTED = "CLOSED_ACCEPTED"
    CLOSED_REJECTED = "CLOSED_REJECTED"


# ── Helper: extract dollar amount from user text ──────────────────────────────

def extract_amount(text: str) -> Optional[float]:
    """Pull the first dollar figure or plain number from a string."""
    text = text.replace(",", "")
    patterns = [
        r'\$\s*(\d+(?:\.\d{1,2})?)',   # $200 or $200.00
        r'(\d+(?:\.\d{1,2})?)\s*(?:dollars?|USD)',
        r'\b(\d+(?:\.\d{1,2})?)\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


# ── System prompts per state ──────────────────────────────────────────────────

BASE_SYSTEM = """You are Alex, a compassionate and professional healthcare collections specialist
at MedCare Financial Services. Your role is to help patients resolve their outstanding medical bills
in a respectful, empathetic, and solution-focused manner.

Core principles:
- Always be polite, empathetic, and professional
- Never be aggressive or threatening
- Focus on finding a workable solution for the patient
- Keep responses concise (2-4 sentences max unless presenting a plan)
- Use the patient's name once you know it
"""

STATE_PROMPTS = {
    State.AUTH_NAME: """
Current task: Greet the patient warmly and ask for their full name to verify their account.
Do NOT ask for anything else yet. Just ask for their name.""",

    State.AUTH_DOB: """
Current task: The patient has provided their name. Now politely ask for their date of birth
to complete identity verification. Do NOT ask for anything else.""",

    State.AUTH_FAILED: """
Current task:

The customer has exceeded the maximum number of authentication attempts.

you were unable to verify their identity.

Politely explain that you cannot continue without successful authentication.

Advise the customer to contact the billing department or start a new session once they have the correct information available.

IMPORTANT:
- This is the FINAL message of the conversation.
- Do NOT ask any further questions.
- Do NOT ask them to try again.
- Do NOT continue the conversation.
- End with a polite goodbye.""",

    State.EXPLAIN_DEBT: """
Current task: Identity verified successfully. Warmly acknowledge the verification, then explain
that you're calling regarding an outstanding balance on their account.
State the exact amount: {due_amount}. Ask if they are able to make a payment today.
Be empathetic — acknowledge that medical bills can be stressful.""",

    State.PAYMENT_AMOUNT: """
Current task: The patient has indicated they can pay today. Ask them specifically how much
they are able to pay today. Be encouraging and flexible.""",

    State.CONFIRM_PLAN: """
Current task: Present the following payment plan to the patient and ask them to confirm:
{plan_summary}
Ask clearly: "Would you like to proceed with this arrangement?" """,

    State.CLOSED_ACCEPTED: """
Current task: The patient has accepted the payment plan. Thank them warmly, confirm the
arrangement details briefly, give them a reference number (use REF-{ref_number}),
and wish them well. Close the conversation professionally.""",

    State.CLOSED_REJECTED: """
Current task: The patient has declined the payment plan or is unable to pay today.
Respond with understanding and empathy. Let them know this account will remain outstanding
and provide a callback number (1-800-555-0199) and hours (Mon-Fri 8AM-6PM EST) to reach us
when they're ready. Thank them for their time and wish them well.""",
}


# ── Chat Session ──────────────────────────────────────────────────────────────

class ChatSession:
    def __init__(
        self,
        api_key: str,
        customer_name: str,
        date_of_birth: str,
        due_amount: float,
    ):
        self.client = Groq(api_key=api_key)
        self.expected_name = customer_name.strip().lower()
        self.expected_dob  = date_of_birth.strip()
        self.due_amount    = due_amount
        self.display_name  = customer_name.strip().title()

        self.state = State.AUTH_NAME
        self.messages: list[dict] = []          # full conversation history (user+assistant)
        self.plan: Optional[PaymentPlan] = None
        self.auth_attempts = 0
        self.started_at = datetime.now().isoformat()
        self.confirm_attempts = 0
        self.retry_count = 0
        self.ended_at: Optional[str] = None
        self.ref_number = datetime.now().strftime("%Y%m%d%H%M%S")

    # ── Internal: build the right system prompt for current state ─────────────

    def _system_prompt(self) -> str:
        template = STATE_PROMPTS.get(self.state, "")
        filled = template.format(
            due_amount=f"${self.due_amount:,.2f}",
            plan_summary=self.plan.summary_text() if self.plan else "",
            ref_number=self.ref_number,
        )
        return BASE_SYSTEM + filled

    # ── Internal: call Groq LLM ───────────────────────────────────────────────

    def _llm(self, extra_instruction: str = "") -> str:
        system = self._system_prompt()
        if extra_instruction:
            system += f"\n\nIMPORTANT: {extra_instruction}"

        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                *self.messages,
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()

    # ── Public: process one user message → returns assistant reply ────────────

    def process(self, user_text: str) -> str:
        # Append user message to history
        self.messages.append({"role": "user", "content": user_text})

        reply = self._handle(user_text)

        # Append assistant reply
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def _handle(self, user_text: str) -> str:
        
        text_lower = user_text.strip().lower()

        # ── State: AUTH_NAME ─────────────────────────────────────────────────
        if self.state == State.AUTH_NAME:
            # Check if the provided name matches (fuzzy: check if any word matches)
            provided = text_lower
            if self._name_matches(provided):
                self.state = State.AUTH_DOB
                return self._llm()
            else:
                self.auth_attempts += 1
                if self.auth_attempts >= 3:
                    self.state = State.AUTH_FAILED
                    self.ended_at = datetime.now().isoformat()
                    return self._llm()
                return self._llm(
                    "The name provided does not match. Politely say you couldn't find "
                    "a matching account and ask them to try again with their full name."
                )

        # ── State: AUTH_DOB ──────────────────────────────────────────────────
        elif self.state == State.AUTH_DOB:
            if self._dob_matches(user_text):
                self.state = State.EXPLAIN_DEBT
                return self._llm()
            else:
                self.auth_attempts += 1
                if self.auth_attempts >= 3:
                    self.state = State.AUTH_FAILED
                    self.ended_at = datetime.now().isoformat()
                    return self._llm()
                return self._llm(
                    "The date of birth provided does not match our records. "
                    "Politely ask them to double-check and try again."
                )

        # ── State: AUTH_FAILED ───────────────────────────────────────────────
        elif self.state == State.AUTH_FAILED:
            return self._llm()

        # ── State: EXPLAIN_DEBT ──────────────────────────────────────────────
        elif self.state == State.EXPLAIN_DEBT:

            amount = extract_amount(user_text)
            if amount is not None:
                self.state = State.PAYMENT_AMOUNT
                return self._handle(user_text)   
                
                
            elif self._says_yes(text_lower):
                self.state = State.PAYMENT_AMOUNT
                return self._llm()
        
            elif self._says_no(text_lower):
                self.state = State.CLOSED_REJECTED
                self.ended_at = datetime.now().isoformat()
                return self._llm()
        
            else:
                # Ambiguous — re-ask
                return self._llm(
                    "The patient hasn't clearly said yes or no. "
                    "Gently re-ask whether they are able to make a payment today."
                )

        # ── State: PAYMENT_AMOUNT ────────────────────────────────────────────
        elif self.state == State.PAYMENT_AMOUNT:
            amount = extract_amount(user_text)
            # print("Amount:", amount)
            if amount is not None:
                self.plan = calculate_plan(self.due_amount, amount)
                # print("="*50)
                # print("Amount:", amount)
                # print("Status:", self.plan.status)
                # print("="*50)
                if self.plan.status == "rejected":
                    # Stay in PAYMENT_AMOUNT — ask for higher amount
                    self.retry_count += 1

                    if self.retry_count >= 3:
                        self.state = State.CLOSED_REJECTED
                        self.ended_at = datetime.now().isoformat()
                        return (
                            "Since I haven't received a valid payment amount, "
                            "I'll close this session for now. "
                            "If you'd like to discuss your payment arrangement later, "
                            "please contact our billing department at the +1 123456789 or reopen this session. Thank you."
                        )
                     


                    return (
                        
                        # f"The patient offered ${amount:.2f} which is below the $50 minimum. "
                        # "Explain you cannot accept below $50 and ask if they can pay at least $50."

                        
                        
                        f"I'm sorry, but we cannot accept a payment of "
                        f"${amount:.2f}. "
                        "The minimum payment we can accept today is $50.00. "
                        "Would you be able to pay at least $50 today?"
                        
                    )
                else:

                    self.retry_count = 0 
                    self.state = State.CONFIRM_PLAN
                    return self._llm()
            else:

                self.retry_count += 1

                if self.retry_count >= 3:
                    self.state = State.CLOSED_REJECTED
                    self.ended_at = datetime.now().isoformat()
                    return (
                       " I understand. Since we couldn't reach a payment arrangement today, "
                        "I'll close this session for now. "
                        "Please contact our billing department if your circumstances change or reopen this session. "
                        "Thank you and have a good day."
                    )



                return self._llm(
                    "The patient hasn't given a clear dollar amount. "
                    "Politely ask them to specify how much they can pay today in dollars."
                )

        # ── State: CONFIRM_PLAN ──────────────────────────────────────────────
        elif self.state == State.CONFIRM_PLAN:
            if self._says_yes(text_lower):
                self.confirm_attempts = 0
                self.state = State.CLOSED_ACCEPTED
                self.ended_at = datetime.now().isoformat()
                return self._llm()
            elif self._says_no(text_lower):
                self.state = State.CLOSED_REJECTED
                self.confirm_attempts = 0
                self.ended_at = datetime.now().isoformat()
                return self._llm()
            else:
                self.confirm_attempts += 1
                if self.confirm_attempts >= 3:
                    self.state = State.CLOSED_REJECTED
                    self.ended_at = datetime.now().isoformat()
                    return (
                       "Since I haven't received a confirmation, "
            "I'll close this session for now. "
            "If you'd like to discuss your payment arrangement later, "
            "please contact our billing department at the +1 123456789.Thank you."
                    )

                return self._llm(
                     "Briefly answer the user's question, then ask them again to reply Yes or No to confirm the payment arrangement."
                )

        # ── Terminal states ──────────────────────────────────────────────────
        elif self.state in (State.CLOSED_ACCEPTED, State.CLOSED_REJECTED):
            return self._llm(
                "The session has ended. Politely let the patient know the conversation "
                "is concluded and wish them well."
            )

        return self._llm()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _name_matches(self, provided: str) -> bool:
        # expected_parts = self.expected_name.split()
        # provided_clean = re.sub(r"[^a-z\s]", "", provided)
        # return any(part in provided_clean for part in expected_parts if len(part) > 1)
        expected = re.sub(r"[^a-z]", "", self.expected_name.lower())
        provided = re.sub(r"[^a-z]", "", provided.lower())
        return expected == provided

    def _dob_matches(self, provided: str) -> bool:

        match = re.search(r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4})", provided)

        if not match:
            return False
        
        # Normalize: strip spaces, slashes, dashes then compare

        provided_date = match.group(1)

        def normalize(s):
            return re.sub(r"[\s/\-\.]", "", s)
        return normalize(provided_date) == normalize(self.expected_dob)

    def _says_yes(self, text: str) -> bool:
        yes_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "yup",
                     "absolutely", "correct", "affirmative", "i can", "i will",
                     "sounds good", "that works", "agree", "accept", "confirmed",
                     "proceed", "go ahead", "definitely", "of course"]
        return any(w in text for w in yes_words)

    def _says_no(self, text: str) -> bool:
        no_words = ["no", "nope", "nah", "cannot", "can't", "not able",
                    "unable", "decline", "reject", "don't", "do not",
                    "not today", "not right now", "refuse", "negative"]
        return any(w in text for w in no_words)

    # ── Is session over? ──────────────────────────────────────────────────────

    @property
    def is_closed(self) -> bool:
        return self.state in (
            State.CLOSED_ACCEPTED,
            State.CLOSED_REJECTED,
            State.AUTH_FAILED,
        )

    # ── Generate structured session summary ───────────────────────────────────

    def generate_summary(self) -> dict:
        outcome_map = {
            State.CLOSED_ACCEPTED: "PAYMENT_PLAN_AGREED",
            State.CLOSED_REJECTED: "PATIENT_DECLINED",
            State.AUTH_FAILED:     "AUTHENTICATION_FAILED",
        }

        # Build conversation log
        transcript = []
        for msg in self.messages:
            transcript.append({
                "role": msg["role"],
                "message": msg["content"],
            })

        summary = {
            "session_metadata": {
                "reference_number":  f"REF-{self.ref_number}",
                "started_at":        self.started_at,
                "ended_at":          self.ended_at or datetime.now().isoformat(),
                "agent":             "Alex — MedCare Financial Services",
                "outcome":           outcome_map.get(self.state, "UNKNOWN"),
            },
            "patient_info": {
                "name":          self.display_name,
                "date_of_birth": self.expected_dob,
                "due_amount":    self.due_amount,
            },
            # "payment_plan": self.plan.to_dict() if self.plan else None,
            "payment_plan": (
    {
        "customer_decision": (
            "accepted"
            if self.state == State.CLOSED_ACCEPTED
            else "declined"
        ),
        "today_payment": round(self.plan.today_payment, 2),
        "remaining_balance": round(self.plan.remaining_balance, 2),
        "monthly_installment": round(self.plan.monthly_installment, 2),
        "num_installments": self.plan.num_installments,
    }
    if self.plan
    else None
),
            "conversation_transcript": transcript,
        }

        return summary

    # ── Kickoff: generate first assistant message ─────────────────────────────

    def greet(self) -> str:
        reply = self._llm()
        self.messages.append({"role": "assistant", "content": reply})
        return reply
