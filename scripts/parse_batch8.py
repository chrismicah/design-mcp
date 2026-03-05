"""Parse Dribbble admin-panel-analytics shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

shots = [
    {"title": "Event Management SaaS Dashboard Admin Panel Analytics UI", "tags": "admin panel ui analytics dashboard attendee management clean saas event management web design", "url": "/shots/27127486-Event-Management-SaaS-Dashboard-Admin-Panel", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Admin Panel Analytics Web App", "tags": "admin panel tables ui ux web app analytics dashboard data", "url": "/shots/22411143-Admin-Panel-Analytics-Web-App", "designer": "", "likes": "0", "views": "15k"},
    {"title": "Admin Panel Analytics Summary Card", "tags": "admin panel card dashboard fintech summary analytics", "url": "/shots/24361081-Admin-Panel-Analytics-Summary-Card", "designer": "", "likes": "0", "views": "10k"},
    {"title": "SaaS CRM Dashboard UI Design Modern Web App Admin Panel", "tags": "admin panel analytics b2b saas clean ui crm dashboard data visualization ui ux web app", "url": "/shots/26994021-SaaS-CRM-Dashboard-UI-Modern-Admin-Panel", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Smart Plant Care Dashboard UI Plant Monitoring Admin Panel", "tags": "admin panel agritech app design data analytics iot dashboard plant monitoring ui ux", "url": "/shots/27115008-Smart-Plant-Care-Dashboard-Admin-Panel", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Dashboard Notification UI Design", "tags": "admin dashboard alert system dashboard ui figma design minimal ui notification", "url": "/shots/26829550-Dashboard-Notification-UI-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Sailors Dashboard Admin Analytics UI Design", "tags": "clean design dashboard mockups modern design sailors ui wireframes admin analytics", "url": "/shots/27074677-Sailors-Dashboard-Admin-Analytics", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Modern Analytics Dashboard UI", "tags": "app banner cards chart clean dashboard dashboard uiux design fireart kpi admin analytics", "url": "/shots/26853159-Modern-Analytics-Dashboard-UI", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Dokan Sales Dashboard Design Ecommerce", "tags": "admin admin panel branding dashboard design ecommerce e commerce analytics sales", "url": "/shots/24486984-Dokan-Sales-Dashboard-Ecommerce", "designer": "", "likes": "0", "views": "15k"},
    {"title": "HireHub Talent Hiring Business Admin Dashboard", "tags": "admin panel ai agents app branding dashboard hr recruiting talent hiring business", "url": "/shots/26784957-HireHub-Talent-Hiring-Admin-Dashboard", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Shopsavvy Sales Dashboard Design Ecommerce", "tags": "admin dashboard admin panel analytics dashboard crm ecommerce application design sales", "url": "/shots/24685627-Shopsavvy-Sales-Dashboard-Ecommerce", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Customer Details Sales CRM 360 Dashboard", "tags": "adminpanel calendar view crmdesign customer details dashboard analytics sales ui ux", "url": "/shots/27024752-Customer-Details-Sales-CRM-360", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Sales Dashboard UI Clean", "tags": "adminpanel analytics cleanui dashboard dashboarddesign datavisualization designinspiration", "url": "/shots/26886618-Sales-Dashboard-UI-Clean", "designer": "", "likes": "0", "views": "5k"},
    {"title": "CEO Dashboard Collapse View", "tags": "adminpanel analyticsui collapsview crmui dashboarddesign datavisualization fintechui productdesign", "url": "/shots/27024688-CEO-Dashboard-Collapse-view", "designer": "", "likes": "0", "views": "5k"},
]

ingest_shots(shots, "admin-panel-analytics")
