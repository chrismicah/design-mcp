"""Parse Dribbble onboarding-fintech shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

shots = [
    {"title": "Cryptid onboarding Fintech Login", "tags": "agency app clean crypto dashboard design system fintech login minimalist onboarding react saas shadcn sign up webapp website widget", "url": "/shots/27144262-Cryptid-onboarding-Fintech-Login", "designer": "", "likes": "0", "views": "1k"},
    {"title": "Mobile app onboarding - Fintech App", "tags": "app application clean design figma fintech illustration ios light look minimal onboarding simple ui ux", "url": "/shots/26041121-Mobile-app-onboarding-Fintech-App", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Onboarding Fintech App", "tags": "branding clean design fintech interaction iphone minimal mobile motion onboarding ui ux", "url": "/shots/23858225-Onboarding-Fintech-App", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Mobile app Quppy Wallet Onboarding Fintech", "tags": "animation app banking banking app cryptocurrencies finance fintech illustration mobile app neobank onboarding product design startup ui ux wallet", "url": "/shots/9951021-Mobile-app-Quppy-Wallet-Onboarding-Fintech", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Fintech Onboarding App Design", "tags": "android app banking biometrics crypto dark mode ui finance ui fintech app fintech design futuristic ios mobile app money management neobanking onboarding design product design secure finance", "url": "/shots/26871398-Fintech-Onboarding-App-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Secure Onboarding Flow Fintech App", "tags": "app biometric login blockchain crypto dark ui digital banking finance fintech futuristic ui ios mobile app neobank onboarding ui product design wallet design", "url": "/shots/26293279-Secure-Onboarding-Flow-Fintech-App", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Fintech Onboarding Page", "tags": "app cansaas clean create account design interface login onboarding onboarding page product design register saas sign up signup ui ux web app website", "url": "/shots/25120421-Fintech-Onboarding-Page", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Credly Onboarding Signup Fintech Dashboard", "tags": "ai dashboard banking charts crypto dark theme dashboard ecommerce finance fintech dashboard fintech web landing page login sign up stocks trading web design web3 dashboard", "url": "/shots/25580984-Credly-Onboarding-Signup-Fintech-Dashboard", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Fintech Onboarding Flow", "tags": "appdesign darkmode financeapp fintech mobileui moneymanagement onboarding productdesign uxdesign", "url": "/shots/26988101-Fintech-Onboarding-Flow", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Finance Onboarding Screens Fintech App", "tags": "banking digital finance financial services fintech fintech app fintech onboarding mobile onboarding money management onboarding design onboarding flow payment app personal finance wallet app", "url": "/shots/26908537-Finance-Onboarding-Screens-Fintech-App", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Fintech Onboarding Light and Dark Mode", "tags": "app bankapp bankonboarding design figma fintech fintechapp mobileapp mobilebanking onboarding ui uidesign ux", "url": "/shots/26965345-Fintech-Onboarding-Light-and-Dark-Mode", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Signzy Fintech Onboarding Compliance Web Design", "tags": "ai cleanui compliance design fintech innovation interface minimaldesign modernui onboarding productdesign regtech uidesign uiux uxdesign webdesign", "url": "/shots/26778304-Signzy-Fintech-Onboarding-Compliance-Web-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Client KYC Review Panel FractionAcre", "tags": "admindashboard app clientdetails clientmanagement complianceux design fintechui internaltools kyc productdesign proptech saasdesign uidesign uxdesign webappdesign", "url": "/shots/26996864-Client-KYC-Review-Panel-FractionAcre", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Onboarding Widgets FinTech App", "tags": "app dashboard design illustration interface onboarding slick ui", "url": "/shots/22522592-Onboarding-Widgets-FinTech-App", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Onboarding Screen FinTech Experience", "tags": "create account dashboard email login mobile app password saas sign in sign up sso", "url": "/shots/25663152-Onboarding-Screen-FinTech-Experience", "designer": "", "likes": "0", "views": "5k"},
]

ingest_shots(shots, "onboarding-fintech")
