import os
import time
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
import schedule
from dotenv import load_dotenv

load_dotenv()

# 1. Fetch & parse entry-level Testing roles
def fetch_testing_roles():
    url = (
        "https://angel.co/jobs?filter=testing"
        "&experience=entry_level&sort=published_at"
    )
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for card in soup.select(".job-card")[:5]:  # top 5
        title = card.select_one(".title").get_text(strip=True)
        link = "https://angel.co" + card.select_one("a")['href']
        desc = card.select_one(".description").get_text(strip=True)
        if len(desc) > 150:
            desc = desc[:150] + "…"
        jobs.append({
            "title": title,
            "link": link,
            "desc": desc
        })
    return jobs

# 2. Create personalized LinkedIn message
def make_linkedin_message(job):
    tmpl = Template(
        "Hi Hiring Team at {{ company }},\n\n"
        "I’m Parth Awasthi, passionate about QA and quality assurance. "
        "I saw your {{ title }} role and love your startup's mission. "
        "Can we connect to discuss how I could help ensure top product quality?\n\n"
        "Thanks,\nParth"
    )
    # Derive company simply from title (customize as needed)
    company = job['title'].split('–')[-1].strip() if '–' in job['title'] else "team"
    return tmpl.render(company=company, title=job['title'])

# 3. Compose email body
def compose_email(jobs):
    tmpl = Template("""
Hello Parth,

Here are today's entry-level Testing roles (fetched at {{ ts }}):

{% for job in jobs %}
• {{ job.title }}
  {{ job.desc }}
  Apply: {{ job.link }}

Suggested LinkedIn outreach:
{{ job.message }}

{% endfor %}
Good luck!
"""
    )
    return tmpl.render(jobs=jobs, ts=time.strftime('%Y-%m-%d %H:%M'))

# 4. Send email via SMTP
def send_email(body):
    msg = MIMEText(body)
    msg['Subject'] = 'Daily Testing Roles @12 PM'
    msg['From'] = os.getenv('EMAIL_USER')
    msg['To'] = os.getenv('EMAIL_USER')

    with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        server.send_message(msg)

# 5. Routine that ties everything
def job_routine():
    jobs = fetch_testing_roles()
    for j in jobs:
        j['message'] = make_linkedin_message(j)
    email_body = compose_email(jobs)
    send_email(email_body)
    print('Email sent at', time.strftime('%Y-%m-%d %H:%M'))

# 6. Schedule daily at 12:00 PM
schedule.every().day.at('12:00').do(job_routine)

if __name__ == '__main__':
    print('Scheduler started...')
    while True:
        schedule.run_pending()
        time.sleep(30)

