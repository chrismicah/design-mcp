"""Parse Dribbble 404-page-creative and admin-panel shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

# 404 pages
shots_404 = [
    {"title": "404 Error Page UI Creative Not Found Experience", "tags": "404 404 error page 404 page design 500 page design brand storytelling creative error page ui ux web design", "url": "/shots/26947470-404-Error-Page-UI-Creative", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Creative 404 Page Concept", "tags": "404 404 page airplane brand building concept cute error error page experiment fun funny humor illustration playful", "url": "/shots/24750695-Creative-404-Page-Concept", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Creative 404 Page UI Design", "tags": "404 404 page app design branding design digital graphic graphic design landing page illustration web design", "url": "/shots/26938042-Creative-404-Page-UI-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Creative 404 Page Design User Engagement", "tags": "404 design 404 error 404 page 404 screen app design creative ui ux engagement web design", "url": "/shots/27071083-Creative-404-Page-User-Engagement", "designer": "", "likes": "0", "views": "5k"},
    {"title": "404 Page for Digital Creative Agency", "tags": "404 abstract design digital sketch ui user experience ux watercolor web design", "url": "/shots/3537472-404-Page-Digital-Creative-Agency", "designer": "", "likes": "0", "views": "30k"},
    {"title": "404 Error Page", "tags": "404 404 error 404 page buttons creative design error page illustration link web design", "url": "/shots/21014183-404-Error-Page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "404 page illustration Underwater depths Kubeshop", "tags": "3d 3d illustration 404 page 404 page illustration atmospheric bioluminescent underwater web design", "url": "/shots/26685107-404-page-illustration-Underwater-Kubeshop", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Creative 404 Error Page Design", "tags": "404 404 error 404 error page brand personality creative design error navigation responsive ui ux web design", "url": "/shots/24456780-Creative-404-Error-Page-Design", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Explorer Error Creative Twist 404 Page", "tags": "404 404 page ui creative agency graphic design illustration ui ux web design playful", "url": "/shots/24475609-Explorer-Error-Creative-404-Page", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Creative 404 Error Page Lost in Desert", "tags": "404page cleanui creative404 deserttheme design ecommerce emptystate error illustration web design", "url": "/shots/26592286-Creative-404-Error-Page-Desert", "designer": "", "likes": "0", "views": "5k"},
    {"title": "404 Page UI Design Creative Startup", "tags": "404design 404page darkui design errorpage figma graphic design mobile productdesign startup", "url": "/shots/26976361-404-Page-UI-Creative-Startup", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Daily UI 404 Page Design Dark Theme", "tags": "404 404 page cinema creative dailyui dark dark theme design error figma illustration", "url": "/shots/26085147-Daily-UI-404-Page-Dark", "designer": "", "likes": "0", "views": "5k"},
    {"title": "404 Page Website Animated", "tags": "404 404 page 404 ui animation design beautiful error web uiux", "url": "/shots/25867237-404-Page-Website-Animated", "designer": "", "likes": "0", "views": "10k"},
]

ingest_shots(shots_404, "404-page-creative")
