"""Parse Dribbble checkout-ecommerce shots."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ingest_dribbble import ingest_shots

shots = [
    {"title": "Multi Select Checkout eCommerce App", "tags": "app cart checkout clean ecommerce figma interface marketplace mobile multi select prototype shopping ui uiux ux", "url": "/shots/24234276-Multi-Select-Checkout-eCommerce-App", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Instant Checkout ECommerce App", "tags": "animation checkout clean ecommerce interaction loader microinteraction motion order payment product shop skeleton steps ui ux", "url": "/shots/11487714-Instant-Checkout-ECommerce-App", "designer": "", "likes": "0", "views": "30k"},
    {"title": "E-commerce Checkout Flow Skincare", "tags": "card checkout checkout page cosmetics dtc ecommerce interface minimal payment shopping cart skincare uiux web design", "url": "/shots/26828549-E-commerce-Checkout-Flow-Skincare", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Checkout Payment UI UX Organic E-commerce Store", "tags": "checkout clean ui dashboard ecommerce green grocery interface minimal organic payment shop shopify store ui design ux design web design", "url": "/shots/26626572-Checkout-Payment-Organic-E-commerce", "designer": "", "likes": "0", "views": "5k"},
    {"title": "eCommerce Checkout Flow UI Design", "tags": "design interface product service startup ecommerce checkout ui ux web website", "url": "/shots/27144957-eCommerce-Checkout-Flow-UI-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Ecommerce Checkout Page UX Website Design", "tags": "add to cart clean figma landing page marketplace minimal online store payment paypal product stripe ui ux web design", "url": "/shots/26951224-Ecommerce-Checkout-Page-UX", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Ecommerce checkout form Untitled UI", "tags": "checkout ecommerce form gumroad minimal order payment purchase shipping shopify shopping cart ui design user interface ux design web design", "url": "/shots/19338287-Ecommerce-checkout-form-Untitled-UI", "designer": "", "likes": "0", "views": "20k"},
    {"title": "Ecommerce Checkout UI Design", "tags": "checkout ui clean ui ecommerce website interface modern ui payment flow payment page product checkout responsive ui shopping cart ui ux design web design", "url": "/shots/26870608-Ecommerce-Checkout-UI-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Ecommerce Checkout page Design", "tags": "add to cart cart checkout checkout form checkout page ecommerce fashion form design order payment pricing purchase shop shopping ui web design website", "url": "/shots/25665013-Ecommerce-Checkout-page-Design", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Urbanmuse Fashion Ecommerce Checkout", "tags": "address checkout clean delivery design discount ecommerce payment payment method promo code shipping summary ui web design website", "url": "/shots/24308923-Urbanmuse-Fashion-Ecommerce-Checkout", "designer": "", "likes": "0", "views": "10k"},
    {"title": "PARFS Luxury Perfume eCommerce Checkout Flow", "tags": "add to cart checkout flow clean checkout ecommerce luxury checkout luxury ecommerce luxury ui online store payment ui perfume website shipping ui uiux design", "url": "/shots/26276319-PARFS-Luxury-Perfume-eCommerce-Checkout", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Rebillion eCommerce Checkout Web App", "tags": "add to cart checkout checkout page checkout service creditcard dashboard ecommerce order payment payment process shopping web app website", "url": "/shots/20584919-Rebillion-eCommerce-Checkout-Web-App", "designer": "", "likes": "0", "views": "10k"},
    {"title": "Smart Checkout Flow eCommerce UX Redesign", "tags": "checkoutflow ecommerce figma minimal mobile modern productdesign uxstrategy", "url": "/shots/26299891-Smart-Checkout-Flow-eCommerce", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Checkout page Ecommerce website design Orner", "tags": "checkout checkout page ecommerce redesign ecommerce ui ecommerce website gift shop mobile ui shopping cart ui ux design webshop design", "url": "/shots/26113601-Checkout-page-Ecommerce-Orner", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Ecommerce Checkout Outdoor Brand", "tags": "checkout designsystem ecommerce outdoor brand ui ux web design", "url": "/shots/26173609-Ecommerce-Checkout-Outdoor-Brand", "designer": "", "likes": "0", "views": "5k"},
    {"title": "3-step Ecommerce Checkout Screen", "tags": "design ecommerce checkout multi-step ui ux", "url": "/shots/26336873-3-step-Ecommerce-Checkout-Screen", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Modern Ecommerce Checkout UI", "tags": "checkout cleanui ecommerce minimaldesign mobile paymentui productdesign uidesign uxdesign webdesign", "url": "/shots/26606657-Modern-Ecommerce-Checkout-UI", "designer": "", "likes": "0", "views": "5k"},
    {"title": "Ecommerce Check-Out Glassmorphism", "tags": "app design glassmorphism ecommerce checkout prototype ui ux", "url": "/shots/16335052-Ecommerce-Check-Out-Glassmorphism", "designer": "", "likes": "0", "views": "10k"},
]

ingest_shots(shots, "checkout-ecommerce")
