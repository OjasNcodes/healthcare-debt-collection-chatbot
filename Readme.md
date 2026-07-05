# 🏥 AI-Powered Healthcare Debt Collection Chatbot

An AI-powered healthcare collections assistant built using **Streamlit** and the **Groq API (Llama 3.1 8B Instant)**. The chatbot authenticates patients, discusses outstanding medical balances, negotiates payment plans using deterministic business rules, and generates a structured session summary at the end of each conversation.

---

# Features

- 🔐 Patient authentication using Full Name and Date of Birth
- 🎯 Configurable patient information from the Streamlit sidebar
- 💳 Configurable outstanding balance
- 🤖 AI-powered conversational experience using Groq Llama 3.1
- 📋 Rule-based payment plan calculation
- 📄 Structured JSON session report
- 📊 Interactive session summary dashboard
- 🔄 Retry limits to prevent infinite conversation loops
- 📌 Automatic session reference number generation
- 🟢 Session status tracking (Active / Accepted / Declined / Authentication Failed)

---

# Technology Stack

- Python 3.10+
- Streamlit
- Groq API
- Llama-3.1-8B-Instant
- Python-dotenv

---

# Healthcare Journey

The chatbot follows a structured healthcare debt collection workflow.

## 1. Patient Authentication

The chatbot verifies the patient's identity by requesting:

- Full Name
- Date of Birth (DD/MM/YYYY)

Authentication is limited to **three attempts** for security.

---

## 2. Outstanding Balance Discussion

After successful authentication, the chatbot:

- Confirms identity
- Explains the outstanding medical balance
- Displays the due amount
- Asks whether the patient can make a payment today

---

## 3. Payment Negotiation

The chatbot enforces the following payment rules:

| Today's Payment | Outcome |
|----------------|---------|
| Less than **$50** | Payment Rejected |
| **$50 – $99.99** | Remaining balance divided into **12 monthly installments** |
| **$100 or more** | Remaining balance divided into **9 monthly installments** |
| Full balance | Account settled immediately |

These business rules are implemented entirely in Python to ensure deterministic behaviour.

The Large Language Model (LLM) is responsible only for generating natural conversational responses.

---

## 4. Payment Confirmation

After presenting the payment arrangement, the chatbot asks the patient to confirm the proposed plan.

The conversation then ends as one of the following:

- ✅ Payment Plan Agreed
- ❌ Patient Declined
- 🔒 Authentication Failed

---

## 5. Session Summary

Once the session ends, the application automatically generates:

- Session metadata
- Reference number
- Patient information
- Customer payment decision
- Payment details
- Complete conversation transcript
- Structured JSON report

---

# Project Structure

```text
Healthcare-Debt-Collection-Chatbot/
│
├── app.py
├── chatbot.py
├── payment.py
├── requirements.txt
├── README.md
├── screenshots/
│   ├── dashboard.png
│   ├── chat1.png
│   ├── chat2.png
│   └── chat3.png
└── .env
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/YourGitHubUsername/healthcare-debt-collection-chatbot.git
```

Navigate to the project directory

```bash
cd healthcare-debt-collection-chatbot
```

Install the required packages

```bash
pip install -r requirements.txt
```

---

# Groq API Setup

This project uses the **Groq API**.

### Step 1

Create a free account at:

https://console.groq.com

### Step 2

Generate a free API key.

### Step 3

Create a `.env` file in the project root directory.

Example:

```env
GROQ_API_KEY=your_api_key_here
```

---

# Running the Application

Run the Streamlit application:

```bash
streamlit run app.py
```

The application will automatically open in your default browser.

---

# Configuration

The Streamlit sidebar allows the following values to be configured before starting a conversation:

- Groq API Key
- Customer Full Name
- Date of Birth
- Outstanding Balance

This makes it easy to simulate different healthcare collection scenarios without modifying the source code.

---

# Payment Logic

The payment rules are enforced using deterministic Python logic.

```text
Today's Payment

< $50
    ↓
Rejected

$50 – $99.99
    ↓
Accepted
+
12 Monthly Installments

≥ $100
    ↓
Accepted
+
9 Monthly Installments

Full Balance
    ↓
Account Settled
```

The LLM **never calculates payment plans**.

Instead:

- Python determines the payment plan.
- The LLM communicates the result naturally.

---

# Conversation Flow

```text
Patient Authentication
          │
          ▼
Identity Verification
          │
          ▼
Outstanding Balance Discussion
          │
          ▼
Payment Negotiation
          │
          ▼
Payment Plan Confirmation
          │
          ▼
Accepted / Declined
          │
          ▼
Session Summary
```

---

# Sample Test Conversations

## Scenario 1 – Authentication Success

```
Bot:
May I have your full name?

User:
John Smith

Bot:
Please provide your date of birth.

User:
01/15/1985

Bot:
Identity verified successfully.
```

---

## Scenario 2 – Payment Plan Accepted

```
User:
I can pay 80

Bot:
Today's payment: $80

Remaining balance: $770

12 monthly installments of $64.17

User:
Yes

Bot:
Payment arrangement confirmed.
```

---

## Scenario 3 – Payment Rejected

```
User:
I can pay 30

Bot:
The minimum payment accepted today is $50.

User:
No

Bot:
The session has been closed.
```

---

## Scenario 4 – Authentication Failure

```
User:
Incorrect Name

User:
Incorrect Name

User:
Incorrect Name

Bot:
Authentication failed.

Session closed.
```

---

# Application Screenshots

## Dashboard

Configure patient details, outstanding balance and API key before starting a session.

![Dashboard](screenshots/dashboard.png)

---

## Authentication & Debt Discussion

Patient authentication followed by discussion of the outstanding balance.

![Chat 1](screenshots/chat1.png)

---

## Payment Negotiation

Example of payment negotiation based on deterministic payment rules.

![Chat 2](screenshots/chat2.png)

---

## Session Summary

Displays the final outcome together with the generated JSON session report.

![Chat 3](screenshots/chat3.png)

---

# Design Decisions

This project adopts a **hybrid architecture** combining deterministic business logic with an LLM.

## Rule-Based Components

- Patient authentication
- Payment rule enforcement
- Installment calculation
- Conversation state management
- Retry limits
- Session summary generation
- JSON report generation

## LLM Responsibilities

- Natural conversation
- Empathetic communication
- Explaining payment options
- Presenting payment plans
- Answering user questions
- Guiding the healthcare collections journey

This separation guarantees that payment calculations remain deterministic while providing a natural conversational experience.

---

# Future Improvements

- Secure payment gateway integration
- Database-backed patient records
- Multi-language support
- Voice-based conversations
- SMS and email notifications
- Integration with Electronic Health Record (EHR) systems

---

# License

This project was developed for educational purposes as part of an AI application assignment.