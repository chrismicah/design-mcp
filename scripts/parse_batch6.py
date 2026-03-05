"""Parse Dribbble settings-page-minimal shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

shots = [
    {"title": "Minimal Settings page Token based Light", "tags": "settings page light ui token based minimal clean saas", "url": "/shots/27103818-Minimal-Settings-page-Token-based-Light", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Minimal Settings page Token based Dark", "tags": "settings page dark ui token based minimal clean saas", "url": "/shots/27103812-Minimal-Settings-page-Token-based-dark", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Default apps settings Untitled UI", "tags": "figma files minimal nav preferences product design saas settings settings page table tabs ui design ui library", "url": "/shots/24566263-Default-apps-settings-Untitled-UI", "designer": "", "likes": "0", "views": "20k"},
    {"title": "Setting design for SaaS platform", "tags": "design ui minimal setting page setting saas design clean ui section", "url": "/shots/21334351-Setting-design-for-SaaS-platform", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Account details Untitled UI", "tags": "account details form product design settings sidebar sidenav ui design user interface", "url": "/shots/26212069-Account-details-Untitled-UI", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Account settings Untitled UI", "tags": "account settings form product design saas settings tabs ui design user interface", "url": "/shots/26999482-Account-settings-Untitled-UI", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Account Untitled UI Dark Mode", "tags": "account settings dark mode form product design saas ui design user interface", "url": "/shots/27063151-Account-Untitled-UI-Dark", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Oratrix Clean Account Settings Dashboard", "tags": "account page account setting admin panel dashboard design desktop human resources manager dashboard settings", "url": "/shots/26416283-Oratrix-Clean-Account-Settings-Dashboard", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Settings page Untitled UI", "tags": "checkboxes dashboard form minimal navigation preferences product design settings sidebar ui design user interface", "url": "/shots/22457394-Settings-page-Untitled-UI", "designer": "", "likes": "0", "views": "30k"},
    {"title": "Notification settings page Untitled UI", "tags": "checkboxes clean ui dashboard design system figma form layout minimal notification settings preferences sidebar", "url": "/shots/17219721-Notification-settings-page-Untitled-UI", "designer": "", "likes": "0", "views": "30k"},
    {"title": "Profile settings page Untitled UI", "tags": "dashboard design system figma minimal preferences profile settings sidebar sidenav", "url": "/shots/16586392-Profile-settings-page-Untitled-UI", "designer": "", "likes": "0", "views": "30k"},
    {"title": "TimeTracker Settings Page", "tags": "admin billing minimal nav notifications preferences product design saas settings settings page security", "url": "/shots/20448703-TimeTracker-Settings-Page", "designer": "", "likes": "0", "views": "15k"},
    {"title": "Integrations settings page Untitled UI", "tags": "dashboard design system figma integrations minimal preferences settings sidebar sidenav", "url": "/shots/17412065-Integrations-settings-page-Untitled-UI", "designer": "", "likes": "0", "views": "20k"},
    {"title": "Prime Pay Finance Dashboard Setting Page", "tags": "admin panel settings card design clean ui crm customization dashboard finance settings", "url": "/shots/26113530-Prime-Pay-Finance-Dashboard-Setting-Page", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Settings page Account Security", "tags": "2fa account security email figma light mode minimal preferences product design saas session settings", "url": "/shots/25218098-Settings-page-Account-Security", "designer": "", "likes": "0", "views": "10k"},
    {"title": "SaaS Settings page", "tags": "minimal ui modern saas settings saas ui settings page settings ui web design", "url": "/shots/24003038-SaaS-Settings-page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Project Settings Page", "tags": "dashboard form functional minimal product settings settings page ui ux web web design", "url": "/shots/26504105-Project-Settings-Page", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Settings Modal Appearance Settings Page UI", "tags": "appearance clean dark mode dashboard interface light mode minimal modal preferences product settings", "url": "/shots/26592064-Settings-Modal-Appearance-Settings-Page-UI", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Notalx Dashboard AI SAAS Writing Setting Page", "tags": "ai clean dashboard ai design document modern saas saas dashboard setting writing", "url": "/shots/26248677-Notalx-Dashboard-AI-SAAS-Writing-Setting-Page", "designer": "", "likes": "0", "views": "5k"},
    {"title": "OxlenHub Settings Page", "tags": "admin panel clean ui compliance crm dashboard detail page general setting management settings", "url": "/shots/26626006-OxlenHub-Settings-Page", "designer": "", "likes": "0", "views": "5k"},
]

ingest_shots(shots, "settings-page-minimal")
