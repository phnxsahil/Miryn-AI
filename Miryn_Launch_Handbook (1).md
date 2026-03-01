

## MIRYN AI
## Launch Preparation Handbook
Figma Handoff  ·  Remaining Backend  ·  Import/Export  ·  PostHog  ·  Launch Checklist
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CONTENTS

## Part 1 — Figma Handoff: Remaining Screens
Part 2 — PostHog: Full Analytics Implementation
## Part 3 — Remaining Backend Modules
Part 4 — ChatGPT Import Module
## Part 5 — Gemini / Google Export Module
## Part 6 — Settings Page: Full Spec
Part 7 — Legal Pages (Privacy Policy + Terms)
## Part 8 — Production Launch Checklist


## PART 1 — FIGMA HANDOFF: REMAINING SCREENS
Settings · Import/Export · Legal · Mobile · Notifications · Error States

These screens are not yet designed or built. Spec them in Figma first, then hand to Codex.

## Settings Page — Full Layout
## LAYOUT
## Desktop
Two column. Left nav 220px fixed. Right content flex-1. Max-width 960px centered.
## Mobile
Single column. Nav collapses to horizontal tabs at top.
## Background
#030303. Content area panels use #0a0a0a surface.

## NAV SECTIONS
## Account
Email, display name, change password, connected accounts (Google).
## Notifications
Toggle: check-in reminders, weekly digest, browser push.
## Privacy
Memory encryption status, data retention period selector, session log.
## Appearance
Theme (dark only for now), font size (default/comfortable/compact).
## Danger Zone
Delete account. Red bordered card. Requires typing DELETE.

## Notification Centre
## DESIGN SPEC
## Trigger
Bell icon in chat header. Badge count (red dot) when unread exist.
## Panel
Slide-in from right, 320px wide, full height. Overlay with blur backdrop.
Each item
Icon left (type-based). Title Space Grotesk 500 14px. Body 13px --text-muted. Time
JetBrains Mono 11px bottom right. Unread: left accent border 2px.
## Types
check_in (purple ◉), reflection_ready (amber ✦), open_loop (teal ↩), system (grey
ⓘ).
Empty state
EB Garamond italic center: 'No notifications yet — Miryn will reach out when it
notices something.'

## Import Flow — Full Screen Modal
## CHATGPT IMPORT DESIGN
Entry point
Settings → Account → 'Import from ChatGPT' button. Also shown in onboarding
Step 5 as optional.
## Step 1
Full screen modal. Heading: 'Import your ChatGPT history.' Instruction block
showing exactly how to export from ChatGPT (Settings → Data Controls → Export).
Download icon animation.
## Step 2
Drag-and-drop zone for conversations.json. Dashed border --accent-dim, radius
12px, center: upload icon + 'Drop your conversations.json here'. Click to browse.

## Step 3
Processing state. Progress bar with status text: 'Analysing 247 conversations...' →
'Extracting beliefs...' → 'Building your profile...' Animated --accent fill.
## Step 4
Success. Shows summary: '12 beliefs extracted · 8 patterns identified · 34
memories added'. CTA: 'View your Identity' button.
Error state
Red card: 'This file doesn't look like a ChatGPT export. Make sure you upload
conversations.json not the ZIP.' Retry button.

## Error States — Full Set
## EVERY ERROR SCREEN NEEDED
404 page
Centered. EB Garamond italic large: 'This page doesn't exist.' Subtext: 'But your
thoughts do.' CTA: 'Back to Miryn'
500 page
Centered. 'Something went wrong on our end.' Subtext: 'We've been notified. Try
again in a moment.' Retry button.
Auth expired
Inline toast (not redirect): 'Your session expired. Logging you back in...' Auto-retry
with refresh token.
LLM error
In chat: system message bubble: 'Miryn is thinking but something went wrong. Try
sending again.' Retry inline.
## Offline
Top banner: 'You appear to be offline. Messages will send when you reconnect.' --
bg-surface, amber text.
Empty identity
On /identity with no data: centered EB Garamond italic: 'Miryn is still getting to know
you. Start a conversation.'

## Mobile Screens — Key Differences
## MOBILE-SPECIFIC DESIGN
## Chat
No sidebar. Top bar: hamburger left + 'Miryn' center + bell right. Input pinned to
bottom above safe area.
## Onboarding Step 2
Preset cards: single column scroll. Cards full width. Selected indicator: full accent
border + checkmark top right.
## Identity
Sections stack vertically. Stats row: 2×2 grid not 4-column. Timeline entries full
width.
## Memory
Cards full width. Forget button always visible (no hover on mobile).
## Settings
Nav becomes horizontal scroll tabs at top. Content below.



## PART 2 — POSTHOG: FULL ANALYTICS IMPLEMENTATION
Free up to 1M events/month · Install before any real users arrive


## Setup
## INSTALL
cd miryn/frontend
npm install posthog-js

INITIALISE IN app/layout.tsx
import posthog from 'posthog-js'

if (typeof window !== 'undefined') {
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
api_host: 'https://app.posthog.com',
capture_pageview: true,
capture_pageleave: true,
session_recording: { maskAllInputs: true }
## })
## }

ADD TO .env.local
NEXT_PUBLIC_POSTHOG_KEY=phc_your_key_here

Events to Track — Full List
Add these in the exact files shown. Never track PII — no emails, no message content.

## AUTH EVENTS
## Event
## File + Location
user_signed_up
app/(auth)/signup/page.tsx — after api.signup() succeeds. Props: {method:
## 'email'|'google'}
user_logged_in
app/(auth)/login/page.tsx — after api.login() succeeds. Props: {method:
## 'email'|'google'}
user_logged_out
wherever logout is triggered. Props: none.

## ONBOARDING EVENTS
onboarding_started
OnboardingFlow.tsx — on mount of step 1.
onboarding_step_completed
OnboardingFlow.tsx — on Next click. Props: {step: 1|2|3|4|5}
onboarding_preset_selected
Step 2 — on card click. Props: {preset: 'thinker'|'companion'|...}
onboarding_completed
OnboardingFlow.tsx — after api.completeOnboarding() succeeds. Props:
{preset, goals[], has_seed_belief: bool}
onboarding_abandoned
OnboardingFlow.tsx — on Back from step 1 or page leave. Props:
{last_step: number}


## CHAT EVENTS
message_sent
ChatInterface.tsx — on sendMessage(). Props: {conversation_count,
is_first_message: bool}
stream_started
ChatInterface.tsx — when first chunk arrives. Props: {conversation_id}
stream_completed
ChatInterface.tsx — on done event. Props: {response_length_chars}
new_conversation_created
ChatInterface.tsx — when conversation_id first set. Props: none.
suggestion_chip_clicked
Empty state chips. Props: {suggestion_text}

## IDENTITY EVENTS
identity_dashboard_viewed
app/(app)/identity/page.tsx — on mount. Props: {identity_version,
beliefs_count, traits_count}
evolution_timeline_viewed
IdentityDashboard.tsx — when timeline section scrolls into view. Props:
## {entries_count}

## MEMORY EVENTS
memory_page_viewed
app/(app)/memory/page.tsx — on mount. Props: {facts_count, emotions_count,
recent_count}
memory_deleted
MemorySnapshot — on delete confirm. Props: {memory_tier, importance_score}
data_export_requested
Memory page export button. Props: none.

## IMPORT EVENTS
import_started
ImportModal — on file drop/select. Props: {source: 'chatgpt'|'gemini'}
import_completed
ImportModal — on success. Props: {source, conversations_count, beliefs_extracted,
memories_added}
import_failed
ImportModal — on error. Props: {source, error_type}

## RETENTION SIGNALS — MOST IMPORTANT
session_started
app/layout.tsx — on every app load when authed. Props: {days_since_signup}
returned_user
app/layout.tsx — if days_since_signup >= 1. Props: {days_since_signup,
total_conversations}
power_user_milestone
ChatInterface.tsx — when conversation_count hits 10, 25, 50. Props: {milestone}

PostHog Dashboards to Build
## Funnel
signed_up → onboarding_completed → message_sent → returned_user (D1) →
returned_user (D7). This is your core acquisition funnel.
## Retention
Cohort retention table. Week-over-week. Target: D7 > 35%.
Preset popularity
onboarding_preset_selected grouped by preset. Shows which archetype resonates
most.
## Drop-off
onboarding_step_completed by step number. Where do users quit the wizard?
Feature adoption
identity_dashboard_viewed / memory_page_viewed as % of active users.




## PART 3 — REMAINING BACKEND MODULES
What needs to be built before public launch


Module 1 — Email Service (Resend)
Currently forgot-password just logs the token to console. Wire real email before alpha.
## INSTALL
pip install resend

CREATE miryn/backend/app/services/email_service.py
import resend
from app.config import settings

resend.api_key = settings.RESEND_API_KEY

def send_password_reset(email: str, token: str):
reset_url = f'{settings.FRONTEND_URL}/reset-password?token={token}'
resend.Emails.send({
"from": "Miryn <hello@miryn.ai>",
"to": email,
"subject": "Reset your Miryn password",
"html": f"""
<p>Click below to reset your password.</p>
<a href="{reset_url}">Reset password</a>
<p>This link expires in 15 minutes.</p>
## """
## })

def send_welcome(email: str, name: str):
resend.Emails.send({
"from": "Sahil at Miryn <sahil@miryn.ai>",
"to": email,
"subject": "You're in — here's what Miryn is",
"html": f"""
<p>Hey {name},</p>
<p>You just created your Miryn. It starts learning about you from your first
message.</p>
<p>One thing to know: the more you share, the more useful it becomes.</p>
## <p>— Sahil</p>
## """
## })
ADD TO config.py
RESEND_API_KEY: Optional[str] = None
CALL IN auth.py forgot-password
from app.services.email_service import send_password_reset
send_password_reset(payload.email, token)

Module 2 — Conversation List API
Chat sidebar needs a list of past conversations with auto-generated titles.
ADD TO miryn/backend/app/api/chat.py
## @router.get('/conversations')
def list_conversations(user_id: str = Depends(get_current_user_id)):

# Return conversations ordered by updated_at DESC
# Include: id, title, created_at, updated_at, message_count

## @router.patch('/conversations/{conversation_id}/title')
async def update_title(conversation_id: str, payload: TitleUpdate,
user_id: str = Depends(get_current_user_id)):
# Update conversation title
# Auto-generate title: call LLM with first message if title is null

ADD TO frontend/lib/api.ts
async listConversations() {
return this.request('/chat/conversations')
## }
async updateConversationTitle(id: string, title: string) {
return this.request(`/chat/conversations/${id}/title`, {
method: 'PATCH', body: JSON.stringify({ title })
## })
## }

Module 3 — Health Check (Real)
Current /health just returns {status: healthy}. Make it actually check DB and Redis.
UPDATE main.py
## @app.get('/health')
async def health_check():
checks = {}
try:
with get_sql_session() as s:
s.execute(text('SELECT 1'))
checks['db'] = 'ok'
except Exception as e:
checks['db'] = f'error: {str(e)[:50]}'
try:
redis_client.ping()
checks['redis'] = 'ok'
except Exception as e:
checks['redis'] = f'error: {str(e)[:50]}'
status = 'healthy' if all(v == 'ok' for v in checks.values()) else 'degraded'
return {'status': status, 'checks': checks, 'version': '0.1.0'}

## Module 4 — Rate Limiting Per User
Prevent single users burning your entire LLM budget. Wire to existing rate_limit.py.
ADD TO config.py
MAX_MESSAGES_PER_DAY: int = 50
MAX_MESSAGES_PER_HOUR: int = 20
ADD TO api/chat.py before orchestrator.handle_message()
day_key = f'msg_day:{user_id}:{datetime.utcnow().strftime("%Y%m%d")}'
hour_key = f'msg_hour:{user_id}:{datetime.utcnow().strftime("%Y%m%d%H")}'
day_count = int(redis_client.incr(day_key))
if day_count == 1: redis_client.expire(day_key, 86400)
hour_count = int(redis_client.incr(hour_key))
if hour_count == 1: redis_client.expire(hour_key, 3600)
if day_count > settings.MAX_MESSAGES_PER_DAY:
raise HTTPException(429, 'Daily message limit reached. Resets at midnight.')
if hour_count > settings.MAX_MESSAGES_PER_HOUR:
raise HTTPException(429, 'Hourly message limit reached. Try again soon.')


## Module 5 — Proactive Check-ins
OutreachScheduler already scans open_loops. Add the LLM message generation step.
UPDATE workers/outreach_worker.py
from app.services.llm_service import LLMService
from app.services.email_service import send_checkin

llm = LLMService()

async def generate_checkin_message(user_id: str, loop_topic: str) -> str:
prompt = f"""You are Miryn checking in with a user.
They mentioned "{loop_topic}" in a past conversation but never resolved it.
Write a single warm, natural opening message (2-3 sentences max) to reconnect.
Don't be pushy. Just open the door.
Return only the message text, nothing else."""
return await llm.generate(prompt)

# Add to scan() loop after finding open loops:
# message = await generate_checkin_message(user_id, loop.topic)
# send_checkin(user_email, message)
# Create notification in DB



## PART 4 — CHATGPT IMPORT MODULE
Let users bring their history — eliminates cold start problem


OpenAI lets users export their full chat history as a ZIP containing conversations.json. Each conversation is a list of
messages with role and content. We run these through the reflection pipeline to seed the identity before the user's first
Miryn conversation.

How ChatGPT Export Works
User action
ChatGPT Settings → Data Controls → Export Data → Download ZIP → Extract →
conversations.json
File format
JSON array of conversation objects. Each has: title, create_time, mapping (dict of
nodes), each node has message.role and message.content.parts[]
## Size
Heavy users: 50-200MB. Average: 5-20MB. Max we should accept: 50MB.
What we extract
All user messages only (role='user'). Run each through reflection_engine. Extract
beliefs, emotions, patterns, topics. Write to identity.

## Backend Implementation
CREATE miryn/backend/app/api/import_data.py
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from app.core.security import get_current_user_id
from app.workers.import_worker import process_chatgpt_import

router = APIRouter(prefix='/import', tags=['import'])

## @router.post('/chatgpt')
async def import_chatgpt(
background_tasks: BackgroundTasks,
file: UploadFile = File(...),
user_id: str = Depends(get_current_user_id)
## ):
if file.size > 50 * 1024 * 1024:
raise HTTPException(413, 'File too large. Max 50MB.')
if not file.filename.endswith('.json'):
raise HTTPException(400, 'Upload conversations.json from your ChatGPT export.')
content = await file.read()
background_tasks.add_task(process_chatgpt_import, user_id, content)
return {'status': 'processing', 'message': 'Import started. Check back in a minute.'}

## @router.get('/status')
def get_import_status(user_id: str = Depends(get_current_user_id)):
# Return status from Redis key: import_status:{user_id}
status = redis_client.get(f'import_status:{user_id}')
return json.loads(status) if status else {'status': 'none'}

CREATE miryn/backend/app/workers/import_worker.py
import json
from app.services.reflection_engine import ReflectionEngine
from app.services.identity_engine import IdentityEngine
from app.core.cache import redis_client


reflection = ReflectionEngine()
identity = IdentityEngine()

async def process_chatgpt_import(user_id: str, raw_content: bytes):
try:
redis_client.setex(f'import_status:{user_id}', 3600,
json.dumps({'status': 'processing', 'progress': 0}))

conversations = json.loads(raw_content)
total = len(conversations)
beliefs_found, patterns_found, memories_added = 0, 0, 0

for i, conv in enumerate(conversations[:100]):  # Cap at 100 convs
messages = _extract_messages(conv)
if not messages: continue

result = await reflection.analyze_conversation(
user_id=user_id,
messages=messages,
conversation_id=f'import_{i}'
## )

if result.get('emotions', {}).get('primary_emotion'):
identity.update_identity(user_id, {'emotions': [result['emotions']]},
trigger_type='chatgpt_import')

for topic in result.get('topics', []):
identity.track_open_loop(user_id, topic, importance=1)
memories_added += 1

progress = int((i + 1) / min(total, 100) * 100)
redis_client.setex(f'import_status:{user_id}', 3600,
json.dumps({'status': 'processing', 'progress': progress}))

redis_client.setex(f'import_status:{user_id}', 3600, json.dumps({
## 'status': 'complete',
'conversations_processed': min(total, 100),
'memories_added': memories_added,
## }))

except Exception as e:
redis_client.setex(f'import_status:{user_id}', 3600,
json.dumps({'status': 'error', 'message': str(e)[:200]}))

def _extract_messages(conv: dict) -> list:
messages = []
mapping = conv.get('mapping', {})
for node in mapping.values():
msg = node.get('message')
if not msg: continue
role = msg.get('author', {}).get('role', '')
if role not in ('user', 'assistant'): continue
parts = msg.get('content', {}).get('parts', [])
content = ' '.join(str(p) for p in parts if isinstance(p, str))
if content.strip():
messages.append({'role': role, 'content': content})
return messages

REGISTER IN main.py
from app.api import import_data
app.include_router(import_data.router)


## Frontend Implementation
CREATE components/Import/ChatGPTImport.tsx
Multi-step modal component. Steps: Instructions → Upload → Processing → Complete. Use existing card styling. Progress
bar during processing uses polling GET /import/status every 2 seconds.

ADD TO frontend/lib/api.ts
async importChatGPT(file: File) {
const form = new FormData()
form.append('file', file)
const res = await fetch(`${API_URL}/import/chatgpt`, {
method: 'POST',
headers: { 'Authorization': `Bearer ${this.token}` },
body: form
## })
if (!res.ok) throw new Error(await res.text())
return res.json()
## }

async getImportStatus() {
return this.request('/import/status')
## }



## PART 5 — GEMINI / GOOGLE TAKEOUT EXPORT
Import from Google AI Studio and Gemini history


Google Takeout includes Gemini conversation history. Users can export via takeout.google.com. The export format is
different from ChatGPT but can use the same import pipeline.

## Google Takeout Format
Export path
takeout.google.com → Select 'Gemini Apps Activity' → Export → Download ZIP
## File
MyActivity.json inside the ZIP. Contains array of activity items.
## Structure
Each item: title, time, products[], details[]. Details contain the actual message text.
Difference from
ChatGPT
No role separation in older exports. Newer Gemini exports have conversationId and
role fields.

## Backend Implementation
ADD TO miryn/backend/app/api/import_data.py
## @router.post('/gemini')
async def import_gemini(
background_tasks: BackgroundTasks,
file: UploadFile = File(...),
user_id: str = Depends(get_current_user_id)
## ):
content = await file.read()
background_tasks.add_task(process_gemini_import, user_id, content)
return {'status': 'processing'}

ADD TO miryn/backend/app/workers/import_worker.py
async def process_gemini_import(user_id: str, raw_content: bytes):
data = json.loads(raw_content)
messages = []

for item in data:
for detail in item.get('details', []):
text = detail.get('activityValue', {}).get('stringValue', '')
if text.strip():
messages.append({'role': 'user', 'content': text})

# Batch into fake conversations of 20 messages each
batch_size = 20
for i in range(0, min(len(messages), 2000), batch_size):
batch = messages[i:i+batch_size]
result = await reflection.analyze_conversation(
user_id=user_id, messages=batch,
conversation_id=f'gemini_import_{i}'
## )
for topic in result.get('topics', []):
identity.track_open_loop(user_id, topic, importance=1)

Data Export (Your Data Download)

Users should be able to export everything Miryn knows about them. Required for trust and GDPR.
ADD TO miryn/backend/app/api/memory.py
from fastapi.responses import JSONResponse

## @router.get('/export')
def export_user_data(user_id: str = Depends(get_current_user_id)):
identity = identity_engine.get_identity(user_id)
memories = _get_all_memories(user_id)  # No tier filter
return JSONResponse(
content={'identity': identity, 'memories': memories,
'exported_at': datetime.utcnow().isoformat()},
headers={'Content-Disposition': 'attachment; filename=miryn_data.json'}
## )



## PART 6 — SETTINGS PAGE: FULL IMPLEMENTATION SPEC
Everything the settings page needs to do


Codex Prompt — Build the whole settings page
Run this as a single Codex task after the rest of the app is stable.

Read miryn/frontend/app/(app)/layout.tsx and
miryn/frontend/lib/api.ts and
miryn/frontend/lib/types.ts and
miryn/backend/app/api/auth.py.

Create miryn/frontend/app/(app)/settings/page.tsx with 5 sections:

## 1. ACCOUNT
- Display current email (read-only)
- Change password form: current password + new password + confirm
- Connected accounts: show Google connected/not connected
- Save button calls PATCH /auth/password (add this endpoint)

## 2. NOTIFICATIONS
- Toggle: Check-in reminders (default: on)
- Toggle: Weekly digest email (default: on)
- Toggle: Browser push notifications (default: off)
- Save calls PATCH /notifications/preferences (add this endpoint)

## 3. PRIVACY
- Memory encryption: show status (enabled/disabled based on
whether ENCRYPTION_KEY is set). Read-only info card.
- Data retention: selector (Forever / 1 year / 6 months / 3 months)
- Session log: table of last 5 logins with IP and timestamp
from audit_logs table (add GET /auth/sessions endpoint)

## 4. APPEARANCE
- Theme toggle: Dark (only option for now, others 'coming soon')
- Text size: Default / Comfortable / Compact
Store in localStorage as 'miryn_text_size'
Apply class to html element: text-sm / text-base / text-lg

## 5. DANGER ZONE
- Red bordered card
- Heading: 'Delete your account'
- Body: what gets deleted (account, all memories, identity profile)
- Input: type DELETE to confirm
- Button disabled until value === 'DELETE'
- On confirm: call DELETE /auth/account → clear token → redirect /

Use existing dark theme. Add Settings link to sidebar nav.
Commit and push when done.



## PART 7 — LEGAL PAGES
Privacy Policy · Terms of Service · Required before public launch


You need these before any real users. They don't need to be written by a lawyer at MVP stage — they need to exist and
cover the basics honestly.

Privacy Policy — Key Sections to Cover
What we collect
Email address, conversation content, identity profile data (traits, beliefs, patterns),
technical data (IP, browser, timestamps).
How we use it
To provide the Miryn service. To improve Miryn's understanding of you. We do not
sell your data. We do not use it to train AI models without consent.
Memory and storage
Conversation content is stored encrypted at rest. You can delete any memory at any
time from the Memory page. You can delete your entire account and all data at any
time.
Third parties
We use: OpenAI/Anthropic (LLM processing), Neon (database), Vercel (hosting),
Railway (backend hosting), Resend (email), PostHog (analytics — anonymised).
List all.
Data export
You can download all your data at any time from Settings → Privacy → Export my
data.
Data deletion
Account deletion removes all data within 30 days. Email sahil@miryn.ai to request
manual deletion.
## Contact
sahil@miryn.ai for privacy questions.

Terms of Service — Key Sections
What Miryn is
An AI companion tool. Not a medical device. Not a substitute for professional mental
health support.
Age requirement
Must be 18 or older. No exceptions.
Acceptable use
No illegal content. No attempts to manipulate the AI for harmful outputs. No scraping
or reverse engineering.
No warranty
Miryn is provided as-is during alpha. We make no guarantees about uptime or
accuracy of insights.
Mental health
Miryn is not a therapist. If you're in crisis, contact a professional. Include crisis line.
## Changes
We may update these terms. We'll notify you by email 7 days in advance of material
changes.

## Implementation
## CREATE THESE PAGES IN NEXT.JS
miryn/frontend/app/(public)/privacy/page.tsx
miryn/frontend/app/(public)/terms/page.tsx
Use a (public) route group with no auth requirement. Simple markdown-rendered pages. Dark theme matching the rest of
the app. Link in footer of landing page and login page.


## Free Legal Resources
## Termly.io
Free privacy policy and terms generator. Outputs compliant text. Use this to get a
base then customise. termly.io/tools/privacy-policy-generator
iubenda
Free tier generates GDPR/CCPA compliant policies. Links to hosted version — fine
for MVP.
## Custom
Recommended: use Termly to generate, paste into your Next.js page, add Miryn-
specific sections about memory/identity data manually.



## PART 8 — PRODUCTION LAUNCH CHECKLIST
Complete every item before sending the waitlist email


 MUST HAVE — App doesn't work without these


## Priority Task Owner / Tool
## ☐  Critical
Fix streaming: update DATABASE_URL to Neon pooled
port 6543
Without this /chat/stream returns error
## Codex
## ☐  Critical
Deploy backend to Railway
Currently only frontend is on Vercel. Backend must be live.
Railway dashboard
## ☐  Critical
Set FRONTEND_URL env var on Railway to https://miryn-
ai.vercel.app
CORS will block all requests otherwise
Railway env vars
## ☐  Critical
Set NEXT_PUBLIC_API_URL on Vercel to Railway backend
## URL
Frontend won't know where to send requests
Vercel env vars
## ☐  Critical
Wire Resend to forgot-password endpoint
Currently logs token to console — useless in production
## Codex
## ☐  Critical
Run migrations 002-005 on production Neon
evolution_log, preset, memory_weights, user fields
neonctl sql
## ☐  Critical
Test full flow on production URL end to end
signup → onboard → chat → identity → memory → logout → login
## Manual
## ☐  Critical
Add Google OAuth client ID for production domain
Add miryn-ai.vercel.app to authorized origins in Google Console
## Google Console
## ☐  Critical
Privacy Policy page live at /privacy
Required before collecting any user data publicly
## Codex
## ☐  Critical
Terms of Service page live at /terms
Required before public signup
## Codex

 HIGH — Do before sending waitlist invites


## Priority Task Owner / Tool
## ☐  High
Install Sentry on backend and frontend
You're blind without error tracking in production
## Codex
## ☐  High
Install PostHog with 8 core events
Need retention data from day 1 — can't add retroactively
## Codex
## ☐  High
Add Uptime Robot monitoring on Railway URL
Know before users do when backend goes down
uptimerobot.com
## ☐  High
Build /reset-password frontend page
Resend sends this link — must exist
## Codex

## ☐  High
Build conversation list sidebar in /chat
Without this users can't find past conversations
## Codex
## ☐  High
Add error boundaries to all major components
Prevent white screen crashes
## Codex
## ☐  High
Wire waitlist counter to real signup count
Hardcoded number erodes trust
## Codex
## ☐  High
Update waitlist FAQ (remove 'early 2026' copy)
That date has passed
Direct edit
## ☐  High
Add Crisp live chat widget to app
Alpha users need a way to reach you immediately
crisp.chat
## ☐  High
Create Tally feedback form + link post-conversation
Collect structured feedback from first users
tally.so
## ☐  High
Send welcome email on signup via Resend
First impression. Personal tone from Sahil.
## Codex
## ☐  High
Rate limit /chat and /chat/stream per user
Protect LLM costs before scale
## Codex

 MEDIUM — Before batch 2 (users 21-100)


## Priority Task Owner / Tool
## ☐  Medium
ChatGPT import module fully working
Eliminates cold start — massive retention improvement
## Codex
## ☐  Medium
Settings page with account + danger zone
Users need to be able to delete their account
## Codex
## ☐  Medium
Auto-generated conversation titles
Sidebar is unusable without titles
## Codex
## ☐  Medium
Mobile responsive pass on all pages
Some users will come from mobile on first day
## Copilot
## ☐  Medium
D7 retention PostHog cohort set up
Your most important metric — needs to exist from week 1
PostHog dashboard
## ☐  Medium
Weekly digest email (Sunday cron)
Biggest retention driver after the product itself
## Codex
## ☐  Medium
Proactive check-in notifications
The feature that makes Miryn feel alive
## Codex
## ☐  Medium
Copy button on Miryn message bubble hover
Small UX thing users will notice is missing
## Copilot
## ☐  Medium
Keyboard shortcuts: Enter/Shift+Enter, Cmd+K new chat
Power users need this immediately
## Copilot
## ☐  Medium
Gemini import module
Second largest import source after ChatGPT
## Codex
## ☐  Medium
Data export (download your data) endpoint + button
Trust feature. Also GDPR.
## Codex


 POST-LAUNCH — After 100 users and retention data


## Priority Task Owner / Tool
## ☐  Later
Voice input via Whisper API
Changes intimacy of the experience completely
## Codex
## ☐  Later
People graph (names extracted from conversations)
Cards per mentioned person — powerful memory feature
## Codex
## ☐  Later
Goal tracking module
Explicit goals with status tracking
## Codex
## ☐  Later
Temporal identity graph visualization
Most powerful proof that Miryn works
## Codex
## ☐  Later
Product Hunt launch
Only after D7 retention > 35%. Need the number first.
## Manual
## ☐  Later
Prompt caching for system prompts (Anthropic)
Cuts costs 90% for repeated system prompt
## Codex
## ☐  Later
Monetisation: Stripe subscription
$12-15/month. Only add when retention justifies it.
## Codex

The Alpha Launch Sequence — Day by Day
## Day -7
Email 73 waitlist: 'Alpha opens in 7 days. Reply with I'm in for early access.'
## Day -3
Post on X: streaming demo video. Post on LinkedIn: founder story.
## Day -1
Email confirmed people with exact launch time. Reddit post in r/Journaling.
## Day 0
Send invite links to first 20 confirmed people. Monitor Sentry + PostHog all day.
Reply to every message within 1 hour.
## Day 1
Post on X: 'First users are in. Here's what happened.' Share an anonymised insight.
## Day 3
Personal message to each of the 20 asking for 10-min feedback call.
## Day 7
Check PostHog D7 retention. If > 35%: post the number publicly. Invite batch 2 (50
people).
## Day 14
Write and post a build-in-public thread about what the first 2 weeks taught you.
## Day 30
Review: what's the most common thing users talk about with Miryn? That's your
marketing message.

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Miryn Launch Handbook v1.0  ·  Build something people come back to.