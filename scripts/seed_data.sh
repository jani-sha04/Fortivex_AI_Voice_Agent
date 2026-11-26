#!/usr/bin/env bash
# Seed the database with sample data for demonstration
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"
cd "$BACKEND_DIR"

source venv/bin/activate 2>/dev/null || true

python3 -c "
import sys
sys.path.insert(0, '.')

from app.database.database import init_db, SessionLocal
from app.models.lead import Lead
from app.models.conversation import Conversation, Message, CallSummary
from app.models.appointment import Appointment

init_db()
db = SessionLocal()

# Check if data exists
if db.query(Lead).count() > 0:
    print('Sample data already exists. Skipping seed.')
    db.close()
    sys.exit(0)

# Sample conversations
conv1 = Conversation(session_id='demo-session-001', customer_name='Sarah Chen', customer_email='sarah@techcorp.com', status='completed', sentiment='POSITIVE', lead_score=85.0, buying_intent='high')
conv2 = Conversation(session_id='demo-session-002', customer_name='Michael Torres', customer_email='m.torres@globalfirm.com', status='completed', sentiment='NEUTRAL', lead_score=55.0, buying_intent='medium')
conv3 = Conversation(session_id='demo-session-003', customer_name='Emily Watson', customer_email='emily@startup.io', status='completed', sentiment='POSITIVE', lead_score=40.0, buying_intent='low')
db.add_all([conv1, conv2, conv3])
db.flush()

# Sample messages
db.add(Message(conversation_id=conv1.id, role='user', content='Hi, I need a CRM solution for our 50-person sales team. We have a budget around 30,000/year.'))
db.add(Message(conversation_id=conv1.id, role='assistant', content='Hello Sarah! NovaCRM Pro sounds like an excellent fit. With 50 users and that budget, you are right in our Enterprise range. What are your biggest CRM pain points currently?'))
db.add(Message(conversation_id=conv1.id, role='user', content='Lead tracking and pipeline visibility. We close deals faster with better data.'))

db.add(Message(conversation_id=conv2.id, role='user', content='I am researching helpdesk options. We get about 500 tickets per week.'))
db.add(Message(conversation_id=conv2.id, role='assistant', content='NovaDesk Enterprise handles that volume easily with AI routing that cuts resolution time by 60%. What systems are you using currently?'))

db.add(Message(conversation_id=conv3.id, role='user', content='Just exploring options. What does NovaAnalytics cost?'))
db.add(Message(conversation_id=conv3.id, role='assistant', content='NovaAnalytics starts at \$149/month for Starter. Would you like to tell me more about your analytics needs?'))

db.flush()

# Sample leads
leads = [
    Lead(name='Sarah Chen', email='sarah@techcorp.com', phone='+1-415-555-0101', company='TechCorp Inc', industry='Technology', requirements='CRM for 50-person sales team, pipeline visibility', product_interest='NovaCRM Pro', budget='30,000/year', timeline='Q1 2026', intent='high', sentiment='POSITIVE', lead_score=85.0, status='HOT', conversation_id=conv1.id),
    Lead(name='Michael Torres', email='m.torres@globalfirm.com', phone='+1-212-555-0202', company='Global Firm LLC', industry='Financial Services', requirements='Helpdesk automation for 500 tickets/week', product_interest='NovaDesk Enterprise', budget='20,000-50,000', timeline='Q2 2026', intent='medium', sentiment='NEUTRAL', lead_score=55.0, status='WARM', conversation_id=conv2.id),
    Lead(name='Emily Watson', email='emily@startup.io', company='Startup.io', industry='SaaS', requirements='Basic analytics dashboard', product_interest='NovaAnalytics Starter', budget='Under 5,000', timeline='Exploring', intent='low', sentiment='POSITIVE', lead_score=40.0, status='COLD', conversation_id=conv3.id),
    Lead(name='David Kumar', email='d.kumar@enterprise.com', company='Enterprise Corp', industry='Manufacturing', requirements='Full business automation suite', product_interest='NovaSuite Complete', budget='100,000+', timeline='Immediate', intent='high', sentiment='POSITIVE', lead_score=95.0, status='HOT'),
]
db.add_all(leads)
db.flush()

# Sample appointments
appts = [
    Appointment(lead_id=leads[0].id, customer_name='Sarah Chen', customer_email='sarah@techcorp.com', appointment_date='2026-12-02', appointment_time='10:00', purpose='NovaCRM Pro Demo', status='scheduled', confirmed=True),
    Appointment(lead_id=leads[1].id, customer_name='Michael Torres', customer_email='m.torres@globalfirm.com', appointment_date='2026-12-03', appointment_time='14:00', purpose='NovaDesk Enterprise Demo', status='scheduled', confirmed=True),
    Appointment(lead_id=leads[3].id, customer_name='David Kumar', customer_email='d.kumar@enterprise.com', appointment_date='2026-12-01', appointment_time='09:00', purpose='NovaSuite Complete Consultation', status='completed', confirmed=True),
]
db.add_all(appts)

# Sample call summaries
cs1 = CallSummary(conversation_id=conv1.id, full_summary='Sarah Chen from TechCorp Inc. discussed CRM needs for 50-person sales team with 30k/year budget. High buying intent and ready to move in Q1 2026. Demo booked.', requirements='CRM for 50 sales reps, pipeline visibility, lead tracking', products_discussed='NovaCRM Pro Enterprise', objections='None - positive throughout', sentiment='POSITIVE', buying_intent='high', lead_score=85.0, recommended_action='Send NovaCRM Pro proposal and confirm demo', customer_details={'name': 'Sarah Chen', 'email': 'sarah@techcorp.com', 'company': 'TechCorp Inc'})
db.add(cs1)

db.commit()
db.close()

print('✅ Sample data seeded successfully!')
print('   - 3 conversations')
print('   - 4 leads (1 HOT with 95 score, 2 WARM/HOT, 1 COLD)')
print('   - 3 appointments')
print('   - 1 call summary')
"
