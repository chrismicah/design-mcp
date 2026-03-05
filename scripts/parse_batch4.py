"""Parse Dribbble landing-page-startup shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

shots = [
    {"title": "AI Agent Landing Page - Startup", "tags": "ai ai agent ai automation ai landing page business integration startup web design", "url": "/shots/26710082-AI-Agent-Landing-Page-Startup", "designer": "", "likes": "0", "views": "10k"},
    {"title": "AI Landing page - Startup website", "tags": "ai agents ai landing page ai startup business integration saas web design", "url": "/shots/27087991-AI-Landing-page-Startup-website", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Landing page for a startup code editor", "tags": "code editor design homepage landing page marketing startup ui ux web design", "url": "/shots/21555428-Landing-page-for-a-startup-code-editor", "designer": "", "likes": "0", "views": "20k"},
    {"title": "Wavebox Modern SaaS Landing Page Built for Conversion", "tags": "ai agents b2b software landing page saas startup conversion web design", "url": "/shots/26262472-Wavebox-Modern-SaaS-Landing-Page", "designer": "", "likes": "0", "views": "15k"},
    {"title": "Salesforce CRM SaaS Landing Page Analytics Dashboard UI", "tags": "analytics dashboard b2b design crm dashboard saas landing page startup ui ux", "url": "/shots/27118775-Salesforce-CRM-SaaS-Landing-Page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Landing page for Startup", "tags": "brand branding clean design hero identity illustration landing page saas startup ui ux", "url": "/shots/25590331-Landing-page-for-Startup", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Landing page for Startup Dark", "tags": "3d icon dark mode faqs figma framer gradient hero section saas startup web design", "url": "/shots/26401760-Landing-page-for-Startup-Dark", "designer": "", "likes": "0", "views": "10k"},
    {"title": "SaaS Platform Landing Page for Startups", "tags": "corporate website creative landing page modern pricing saas startup web design", "url": "/shots/26661002-SaaS-Platform-Landing-Page-Startups", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Celeb Farm - Landing Page", "tags": "brand management community platform company creator management crm website startup landing page", "url": "/shots/21344201-Celeb-Farm-Landing-Page", "designer": "", "likes": "0", "views": "20k"},
    {"title": "Swif Landing Page for Multitasking Messenger", "tags": "clean landing page design startup messenger chat saas product design", "url": "/shots/21335587-Swif-Landing-Page-Multitasking-Messenger", "designer": "", "likes": "0", "views": "20k"},
    {"title": "MVP Landing Page for a New SaaS Product", "tags": "clean ui creative dark mode dark theme developer tools landing page product design saas startup", "url": "/shots/27083490-MVP-Landing-Page-New-SaaS-Product", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Fintech Landing Page UI UX Design for Startup", "tags": "finance landing page fintech landing page startup saas web design ui ux", "url": "/shots/27132081-Fintech-Landing-Page-Startup-SaaS", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Cupcake - Startup Accelerator", "tags": "3d agency animation blue company cta features illustration kickstart startup accelerator landing page", "url": "/shots/16644496-Cupcake-Startup-Accelerator", "designer": "", "likes": "0", "views": "30k"},
    {"title": "Neurix Ethical AI SaaS Landing Page Design", "tags": "interface product saas service startup ui ux responsive web design", "url": "/shots/26353865-Neurix-Ethical-AI-SaaS-Landing-Page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Launch Demo pixfort WordPress Theme", "tags": "3d ai bento bento boxes features blur dark mode gradient hero startup landing page", "url": "/shots/26401456-Launch-Demo-pixfort-WordPress-Theme", "designer": "", "likes": "0", "views": "10k"},
    {"title": "AI Innovation Platform", "tags": "ai ai landing page ai platform artificial intelligence future tech startup web design modern", "url": "/shots/26884704-AI-Innovation-Platform", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Polagon Strategy Business Landing Page", "tags": "agency consulting business consulting leaders automotive strategy corporate landing page", "url": "/shots/26460753-Polagon-Strategy-Business-Landing-Page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Eclipse Studio Photography Landing Page", "tags": "agency landing page photography studio brand portfolio creative ui ux", "url": "/shots/26470871-Eclipse-Studio-Photography-Landing-Page", "designer": "", "likes": "0", "views": "10k"},
]

ingest_shots(shots, "landing-page-startup")
