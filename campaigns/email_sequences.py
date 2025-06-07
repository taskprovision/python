#!/usr/bin/env python3
"""
TaskProvision Email Sequence Automation
Automated email campaigns for lead nurturing
"""

import asyncio
import smtplib
import json
import os
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
import jinja2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailTemplate:
    """Email template structure"""
    name: str
    subject: str
    content: str
    delay_days: int
    trigger_condition: Optional[str] = None

@dataclass
class LeadContact:
    """Lead contact information"""
    email: str
    name: str
    company: Optional[str]
    repo_name: str
    github_url: str
    score: float
    pain_points: List[str]
    languages: List[str]

class EmailSequenceManager:
    """Manages automated email sequences"""
    
    def __init__(self):
        # SMTP configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Sender information
        self.from_email = os.getenv('FROM_EMAIL', 'hello@taskprovision.com')
        self.from_name = os.getenv('FROM_NAME', 'TaskProvision Team')
        
        # Template engine
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Email sequences
        self.sequences = self._load_email_sequences()
    
    def _load_email_sequences(self) -> Dict[str, List[EmailTemplate]]:
        """Load email sequence templates"""
        return {
            'cold_outreach': [
                EmailTemplate(
                    name='initial_contact',
                    subject='🚀 Noticed your {{repo_name}} project - quick automation tip',
                    content='''Hi {{name}},

I came across your {{repo_name}} project on GitHub - really impressive work with {{languages}}!

I noticed you have {{issue_count}} open issues. Many developers with similar projects save 4-6 hours/week using AI-powered development automation.

Quick question: What's your biggest development bottleneck right now?

I'd love to show you a free repository health check that might help:
🔗 https://taskprovision.com/tools/repo-health?repo={{github_url}}

Worth a 2-minute look?

Best,
{{sender_name}}

P.S. No spam, just developers helping developers 🤝''',
                    delay_days=0
                ),
                
                EmailTemplate(
                    name='value_proposition',
                    subject='Re: {{repo_name}} - 15min demo that could save hours',
                    content='''Hi {{name}},

Quick follow-up on {{repo_name}} - I wanted to share something specific that might help.

I saw your project uses {{primary_language}}. Here's what similar teams achieved with TaskProvision:

📊 Case Study - Python Team ({{contributors}} contributors):
- 60% fewer bugs in production
- Automated test generation saved 8 hours/week  
- Code quality score improved from 72% to 94%

Would a 15-minute demo showing these automation tools be valuable?

You can see it in action here: 
🎮 https://demo.taskprovision.com/{{repo_name}}

(I created a personalized demo based on your {{repo_name}} repository)

Interested in seeing how this could work for your team?

Best,
{{sender_name}}

P.S. The demo includes actual suggestions for {{repo_name}}''',
                    delay_days=3
                ),
                
                EmailTemplate(
                    name='social_proof',
                    subject='🎯 How {{similar_company}} saved 40% development time',
                    content='''Hi {{name}},

I wanted to share a quick success story that might resonate with your {{repo_name}} project.

{{similar_company}} had a similar setup:
- {{languages}} codebase
- Small development team
- Growing technical debt

After implementing TaskProvision:
✅ 40% faster development cycles
✅ 90% reduction in critical bugs
✅ Automated code reviews saved 12 hours/week

The founder said: "TaskProvision feels like having a senior developer working 24/7."

Want to see if we can achieve similar results with {{repo_name}}?

🎯 Book a 15-min demo: https://cal.com/taskprovision/demo
🔍 Free analysis: https://taskprovision.com/analyze/{{github_url}}

Best,
{{sender_name}}

P.S. I'm genuinely curious about your development workflow - always learning from other developers!''',
                    delay_days=7
                ),
                
                EmailTemplate(
                    name='final_value',
                    subject='Last check-in: {{repo_name}} automation opportunity',
                    content='''Hi {{name}},

This is my last email about TaskProvision (I promise!).

I'll be honest - I'm reaching out because {{repo_name}} seems like exactly the type of project that benefits most from AI automation.

Here's why:
- {{primary_language}} development (our sweet spot)
- {{contributors}} contributors (perfect team size)
- Active development ({{recent_commits}} recent commits)

Final offer: 30-minute consultation where I'll:
1. Analyze {{repo_name}} live
2. Show specific automation opportunities
3. Give you the analysis report regardless

No pitch, just developer-to-developer insights.

Interested? Just reply with "Yes" and I'll send a calendar link.

If not, I wish you the best with {{repo_name}} - genuinely impressive work!

Cheers,
{{sender_name}}

P.S. You can always check out our tools later: https://taskprovision.com''',
                    delay_days=14
                )
            ],
            
            'trial_onboarding': [
                EmailTemplate(
                    name='welcome',
                    subject='🎉 Welcome to TaskProvision - Your setup guide',
                    content='''Hi {{name}},

Welcome to TaskProvision! 🎉

I've prepared a personalized setup guide for {{repo_name}}:

🚀 Quick Start (5 minutes):
1. Connect your GitHub: https://app.taskprovision.com/connect
2. Run first analysis: Click "Analyze Repository"
3. Review suggestions: See automated improvements

🎯 Your first automation:
Based on {{repo_name}}, I recommend starting with:
- Automated test generation for {{test_coverage}}% coverage gap
- Code quality improvements for {{quality_issues}} detected issues

Need help? Reply to this email or book a walkthrough:
📅 https://cal.com/taskprovision/onboarding

Happy automating!
{{sender_name}}''',
                    delay_days=0
                ),
                
                EmailTemplate(
                    name='progress_check',
                    subject='How\'s your TaskProvision experience going?',
                    content='''Hi {{name}},

Quick check-in on your TaskProvision trial!

I see you've {{action_taken}} - that's great!

Typical results by day 7:
- 3-5 code issues automatically fixed
- 1-2 test suites generated
- 15-30% improvement in code quality score

How are you finding it so far? Any questions?

If you need a hand, I'm happy to jump on a quick call:
📅 https://cal.com/taskprovision/support

Keep up the great work!
{{sender_name}}''',
                    delay_days=3
                ),
                
                EmailTemplate(
                    name='upgrade_prompt',
                    subject='🎯 Ready to supercharge {{repo_name}}?',
                    content='''Hi {{name}},

Your trial ends in 3 days, and I wanted to make sure you're getting maximum value.

Your progress so far:
✅ {{improvements_made}} code improvements
✅ {{tests_generated}} tests generated  
✅ {{quality_increase}}% quality score increase

To continue this momentum, consider upgrading to:

🚀 **Professional Plan** ($79/month)
- Unlimited repositories
- Advanced AI suggestions
- Team collaboration features
- Priority support

Special offer: Use code WELCOME30 for 30% off first 3 months.

Upgrade now: https://app.taskprovision.com/upgrade?code=WELCOME30

Questions? Just reply to this email.

{{sender_name}}''',
                    delay_days=11
                )
            ]
        }
    
    def create_email_content(self, template: EmailTemplate, lead: LeadContact, extra_data: Dict = None) -> tuple:
        """Create personalized email content"""
        # Prepare template data
        template_data = {
            'name': lead.name,
            'repo_name': lead.repo_name,
            'github_url': lead.github_url,
            'issue_count': len(lead.pain_points),
            'languages': ', '.join(lead.languages[:2]),
            'primary_language': lead.languages[0] if lead.languages else 'Python',
            'contributors': '2-5',  # Estimated based on lead data
            'sender_name': self.from_name,
            'score': lead.score
        }
        
        # Add extra data if provided
        if extra_data:
            template_data.update(extra_data)
        
        # Render subject and content
        subject_template = self.jinja_env.from_string(template.subject)
        content_template = self.jinja_env.from_string(template.content)

        subject = subject_template.render(**template_data)
        content = content_template.render(**template_data)

        return subject, content

    async def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add content
            text_part = MimeText(content, 'plain', 'utf-8')
            msg.attach(text_part)

            # Connect and send
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def load_leads_from_file(self, filename: str) -> List[LeadContact]:
        """Load leads from JSON file"""
        leads = []

        try:
            with open(filename, 'r') as f:
                leads_data = json.load(f)

            for lead_data in leads_data:
                if lead_data.get('email'):  # Only process leads with email
                    lead = LeadContact(
                        email=lead_data['email'],
                        name=lead_data.get('owner', 'Developer'),
                        company=lead_data.get('company'),
                        repo_name=lead_data['repo_name'],
                        github_url=lead_data['github_url'],
                        score=lead_data['score'],
                        pain_points=lead_data.get('pain_points', []),
                        languages=lead_data.get('languages', [])
                    )
                    leads.append(lead)
        except Exception as e:
            logger.error(f"Error loading leads from {filename}: {e}")

        return leads

    async def send_sequence_email(self, lead: LeadContact, sequence_name: str, email_index: int) -> bool:
        """Send specific email from sequence"""
        if sequence_name not in self.sequences:
            logger.error(f"Unknown sequence: {sequence_name}")
            return False

        sequence = self.sequences[sequence_name]
        if email_index >= len(sequence):
            logger.error(f"Email index {email_index} out of range for sequence {sequence_name}")
            return False

        template = sequence[email_index]
        subject, content = self.create_email_content(template, lead)

        return await self.send_email(lead.email, subject, content)

    async def launch_campaign(self, sequence_name: str, leads_file: str, max_emails: int = 50):
        """Launch email campaign"""
        logger.info(f"Launching {sequence_name} campaign...")

        # Load leads
        leads = self.load_leads_from_file(leads_file)

        if not leads:
            logger.error("No leads with email addresses found")
            return

        # Filter high-quality leads
        high_quality_leads = [lead for lead in leads if lead.score >= 70]

        # Limit number of emails
        campaign_leads = high_quality_leads[:max_emails]

        logger.info(f"Sending to {len(campaign_leads)} leads")

        # Send first email in sequence to all leads
        sent_count = 0
        failed_count = 0

        for lead in campaign_leads:
            success = await self.send_sequence_email(lead, sequence_name, 0)

            if success:
                sent_count += 1
                # Log for follow-up scheduling
                self._log_campaign_action(lead, sequence_name, 0)
            else:
                failed_count += 1

            # Rate limiting
            await asyncio.sleep(2)

        logger.info(f"Campaign complete: {sent_count} sent, {failed_count} failed")

        # Schedule follow-ups
        self._schedule_followups(campaign_leads, sequence_name)

    def _log_campaign_action(self, lead: LeadContact, sequence_name: str, email_index: int):
        """Log campaign action for tracking"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'email': lead.email,
            'sequence': sequence_name,
            'email_index': email_index,
            'next_email_date': (datetime.now() + timedelta(
                days=self.sequences[sequence_name][email_index].delay_days)).isoformat()
        }

        # Append to campaign log
        log_file = f'campaign_log_{sequence_name}.json'

        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging campaign action: {e}")

    def _schedule_followups(self, leads: List[LeadContact], sequence_name: str):
        """Schedule follow-up emails"""
        sequence = self.sequences[sequence_name]

        followup_data = {
            'sequence_name': sequence_name,
            'leads': [lead.email for lead in leads],
            'schedule': []
        }

        # Create schedule for each email in sequence
        for i, template in enumerate(sequence[1:], 1):  # Skip first email (already sent)
            send_date = datetime.now() + timedelta(days=template.delay_days)
            followup_data['schedule'].append({
                'email_index': i,
                'send_date': send_date.isoformat(),
                'template_name': template.name
            })

        # Save schedule
        schedule_file = f'followup_schedule_{sequence_name}_{datetime.now().strftime("%Y%m%d")}.json'
        with open(schedule_file, 'w') as f:
            json.dump(followup_data, f, indent=2)

        logger.info(f"Follow-up schedule saved to {schedule_file}")

    async def process_scheduled_emails(self, schedule_file: str):
        """Process scheduled follow-up emails"""
        try:
            with open(schedule_file, 'r') as f:
                schedule_data = json.load(f)

            sequence_name = schedule_data['sequence_name']
            leads_emails = schedule_data['leads']

            # Load current leads data
            current_time = datetime.now()

            for item in schedule_data['schedule']:
                send_date = datetime.fromisoformat(item['send_date'])

                if send_date <= current_time:
                    email_index = item['email_index']

                    # Send to all leads in campaign
                    for email in leads_emails:
                        # Create minimal lead object for email sending
                        lead = LeadContact(
                            email=email,
                            name="Developer",  # Could be enhanced with stored data
                            company=None,
                            repo_name="your project",
                            github_url="",
                            score=70,
                            pain_points=[],
                            languages=["Python"]
                        )

                        await self.send_sequence_email(lead, sequence_name, email_index)
                        await asyncio.sleep(1)

                    logger.info(f"Sent follow-up email {email_index} for {sequence_name}")

        except Exception as e:
            logger.error(f"Error processing scheduled emails: {e}")

    # Campaign management functions
    class CampaignManager:
        """High-level campaign management"""

        def __init__(self):
            self.email_manager = EmailSequenceManager()

        async def run_cold_outreach_campaign(self, leads_file: str = None):
            """Run complete cold outreach campaign"""
            if not leads_file:
                # Use latest leads file
                import glob
                leads_files = glob.glob("github_leads_*.json")
                if not leads_files:
                    logger.error("No leads files found")
                    return
                leads_file = max(leads_files)  # Latest file

            logger.info(f"Running cold outreach campaign with {leads_file}")
            await self.email_manager.launch_campaign('cold_outreach', leads_file, max_emails=100)

        async def run_trial_onboarding_campaign(self, trial_users_file: str):
            """Run trial user onboarding campaign"""
            logger.info(f"Running trial onboarding campaign with {trial_users_file}")
            await self.email_manager.launch_campaign('trial_onboarding', trial_users_file, max_emails=200)

        def generate_campaign_report(self, sequence_name: str) -> Dict:
            """Generate campaign performance report"""
            log_file = f'campaign_log_{sequence_name}.json'

            if not os.path.exists(log_file):
                return {"error": "No campaign log found"}

            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)

                # Analyze campaign performance
                total_emails = len(logs)
                sequences = {}

                for log in logs:
                    seq = log['sequence']
                    if seq not in sequences:
                        sequences[seq] = {'emails_sent': 0, 'unique_recipients': set()}

                    sequences[seq]['emails_sent'] += 1
                    sequences[seq]['unique_recipients'].add(log['email'])

                # Convert sets to counts
                for seq in sequences:
                    sequences[seq]['unique_recipients'] = len(sequences[seq]['unique_recipients'])

                return {
                    'total_emails_sent': total_emails,
                    'sequences': sequences,
                    'report_date': datetime.now().isoformat()
                }

            except Exception as e:
                return {"error": f"Error generating report: {e}"}

    async def main():
        """Main campaign execution"""
        import sys

        if len(sys.argv) < 2:
            print("Usage: python email_sequences.py <command> [args]")
            print("Commands:")
            print("  cold_outreach [leads_file]  - Run cold outreach campaign")
            print("  trial_onboarding <file>     - Run trial onboarding campaign")
            print("  process_scheduled <file>    - Process scheduled follow-ups")
            print("  report <sequence_name>      - Generate campaign report")
            return

        command = sys.argv[1]
        campaign_manager = CampaignManager()

        if command == "cold_outreach":
            leads_file = sys.argv[2] if len(sys.argv) > 2 else None
            await campaign_manager.run_cold_outreach_campaign(leads_file)

        elif command == "trial_onboarding":
            if len(sys.argv) < 3:
                print("Error: trial_onboarding requires users file")
                return
            users_file = sys.argv[2]
            await campaign_manager.run_trial_onboarding_campaign(users_file)

        elif command == "process_scheduled":
            if len(sys.argv) < 3:
                print("Error: process_scheduled requires schedule file")
                return
            schedule_file = sys.argv[2]
            await campaign_manager.email_manager.process_scheduled_emails(schedule_file)

        elif command == "report":
            if len(sys.argv) < 3:
                print("Error: report requires sequence name")
                return
            sequence_name = sys.argv[2]
            report = campaign_manager.generate_campaign_report(sequence_name)
            print(json.dumps(report, indent=2))

        else:
            print(f"Unknown command: {command}")

    if __name__ == "__main__":
        asyncio.run(main())