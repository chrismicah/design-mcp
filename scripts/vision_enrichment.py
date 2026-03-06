"""
Vision-based enrichment pipeline for design patterns.
Uses OpenCLIP with binary-prompt classification for accurate UI metadata extraction.
"""
import json
import time
import sys
from pathlib import Path
from collections import Counter

import torch
import open_clip
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
PATTERNS_PATH = BASE_DIR / "data" / "patterns.json"
MODEL_OUTPUT_PATH = BASE_DIR / "data" / "vision_model.json"

# ============================================================
# Binary detection prompts (positive / negative pairs)
# CLIP is much more accurate with "this image contains X" vs "this image does not contain X"
# ============================================================

UI_ELEMENT_PROMPTS = {
    "Navigation Bar": ("a user interface with a navigation bar at the top", "a user interface without a navigation bar"),
    "Sidebar": ("a user interface with a sidebar menu on the left", "a user interface without a sidebar"),
    "Search Bar": ("a user interface with a search input field", "a user interface without search"),
    "Button": ("a user interface with clickable buttons", "a user interface without buttons"),
    "Card": ("a user interface with card components", "a user interface without cards"),
    "Data Table": ("a user interface with a data table or list of rows", "a user interface without tables"),
    "Form": ("a user interface with form input fields", "a user interface without forms"),
    "Dropdown": ("a user interface with dropdown menus or select inputs", "a user interface without dropdowns"),
    "Modal": ("a user interface with a modal or dialog popup", "a user interface without modals"),
    "Tabs": ("a user interface with tab navigation", "a user interface without tabs"),
    "Chart": ("a user interface with charts graphs or data visualization", "a user interface without charts"),
    "Avatar": ("a user interface with user avatar or profile photos", "a user interface without avatars"),
    "Badge": ("a user interface with notification badges or counters", "a user interface without badges"),
    "Progress Bar": ("a user interface with a progress bar or loading indicator", "a user interface without progress indicators"),
    "Hero Section": ("a landing page with a large hero section and headline", "an application interface without a hero"),
    "Footer": ("a web page with a footer section at the bottom", "a web page without a footer"),
    "Pricing Table": ("a pricing page with plan comparison", "a page without pricing information"),
    "Image Gallery": ("a user interface with an image gallery or grid of photos", "a user interface without image galleries"),
    "Testimonials": ("a page with customer testimonials or reviews", "a page without testimonials"),
    "Icon Grid": ("a user interface with a grid of icons or feature icons", "a user interface without icon grids"),
    "Stats": ("a user interface showing statistics numbers or metrics", "a user interface without statistics"),
    "Timeline": ("a user interface with a timeline or activity feed", "a user interface without timelines"),
    "Toggle": ("a user interface with toggle switches", "a user interface without toggles"),
    "Tooltip": ("a user interface with tooltips on hover", "a user interface without tooltips"),
}

VISUAL_STYLE_PROMPTS = {
    "Minimal": ("a minimal clean simple user interface design", "a complex busy cluttered interface design"),
    "Bold": ("a bold colorful vibrant interface with strong colors", "a muted subtle interface with soft colors"),
    "Glassmorphism": ("a glassmorphism interface with frosted glass blur effects", "a flat solid interface without glass effects"),
    "Gradient": ("an interface with colorful gradients", "an interface with flat solid colors"),
    "Corporate": ("a professional corporate business interface", "a casual playful creative interface"),
    "Playful": ("a playful creative fun colorful interface", "a serious professional corporate interface"),
    "Premium": ("a luxury premium high-end elegant interface", "a basic simple budget interface"),
    "Futuristic": ("a futuristic sci-fi modern tech interface with neon", "a traditional classic conventional interface"),
    "Editorial": ("an editorial magazine newspaper style layout", "a standard web application interface"),
    "Flat": ("a flat design interface without shadows or depth", "an interface with shadows depth and dimension"),
    "3D": ("an interface with 3D elements depth and perspective", "a flat 2D interface without depth"),
}

PAGE_TYPE_PROMPTS = {
    "Dashboard": ("a dashboard interface showing metrics charts and data panels", "a simple landing page or blog"),
    "Landing Page": ("a marketing landing page with hero section and call to action", "an application dashboard or admin panel"),
    "E-commerce": ("an online shopping e-commerce product page or store", "a non-commercial application interface"),
    "Auth": ("a login signup authentication page with email and password fields", "a main application page with content"),
    "Settings": ("a settings or preferences configuration page", "a content page with articles or products"),
    "Profile": ("a user profile page showing personal information", "a data dashboard or landing page"),
    "Blog": ("a blog article or content reading page", "an application interface or dashboard"),
    "Chat": ("a chat messaging conversation interface", "a non-messaging interface"),
    "Portfolio": ("a creative portfolio showcasing work or projects", "a data-driven application interface"),
    "Admin Panel": ("an admin panel or back-office management interface", "a public-facing marketing page"),
    "Analytics": ("an analytics or reporting page with charts and metrics", "a content page without data visualization"),
    "Pricing": ("a pricing page comparing plans and features", "a page without pricing information"),
    "Documentation": ("a documentation or help page with text and code", "a visual application interface"),
    "Social Feed": ("a social media feed with posts and interactions", "a non-social application interface"),
    "CRM": ("a CRM customer relationship management interface", "a non-business application"),
    "Calendar": ("a calendar or scheduling interface", "a non-calendar application"),
    "Kanban": ("a kanban board with draggable cards in columns", "a non-kanban interface"),
    "File Manager": ("a file manager interface with folders and files", "a non-file-management interface"),
}

LAYOUT_PROMPTS = {
    "sidebar_detail": ("a layout with sidebar navigation and main content area", "a layout without sidebar"),
    "single_column": ("a single column centered layout", "a multi-column wide layout"),
    "split_screen": ("a split screen two column layout", "a single column layout"),
    "card_grid": ("a grid layout with multiple cards", "a single column text layout"),
    "full_bleed": ("a full width edge to edge layout", "a contained centered layout"),
    "dashboard_panels": ("a dashboard layout with multiple panels and widgets", "a simple single content layout"),
}

COLOR_MODE_PROMPTS = {
    "dark": ("a dark mode user interface with dark background", "a light mode user interface with white background"),
}


def load_model():
    """Load OpenCLIP model."""
    print("Loading OpenCLIP ViT-B/32...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    model.eval()
    print("Model loaded.")
    return model, preprocess, tokenizer


def binary_classify(model, preprocess, tokenizer, image, positive_text, negative_text):
    """Binary yes/no classification. Returns probability of positive class."""
    texts = tokenizer([positive_text, negative_text])
    
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(texts)
        
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarity = (image_features @ text_features.T).squeeze(0)
        probs = similarity.softmax(dim=-1)
    
    return probs[0].item()  # probability of positive class


def batch_binary_classify(model, preprocess, tokenizer, image, prompts_dict, threshold=0.55):
    """Run binary classification for all prompts, return labels above threshold."""
    results = {}
    
    # Batch all texts at once for efficiency
    all_texts = []
    label_order = []
    for label, (pos, neg) in prompts_dict.items():
        all_texts.extend([pos, neg])
        label_order.append(label)
    
    texts = tokenizer(all_texts)
    
    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(texts)
        
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        
        similarities = (image_features @ text_features.T).squeeze(0)
    
    # Process pairs
    for i, label in enumerate(label_order):
        pos_sim = similarities[i * 2].item()
        neg_sim = similarities[i * 2 + 1].item()
        # Softmax over the pair
        pair = torch.tensor([pos_sim, neg_sim])
        prob = pair.softmax(dim=0)[0].item()
        results[label] = prob
    
    # Return labels above threshold, sorted by confidence
    detected = {k: v for k, v in results.items() if v >= threshold}
    return dict(sorted(detected.items(), key=lambda x: -x[1]))


def assess_quality(model, preprocess, tokenizer, image):
    """Score visual quality 0-10."""
    quality_prompts = [
        ("a beautiful professional polished high quality user interface", 
         "an ugly amateur rough low quality user interface"),
        ("a well designed user interface with good typography and spacing",
         "a poorly designed user interface with bad typography and spacing"),
        ("a modern contemporary user interface design",
         "an outdated old-fashioned user interface design"),
    ]
    
    scores = []
    for pos, neg in quality_prompts:
        prob = binary_classify(model, preprocess, tokenizer, image, pos, neg)
        scores.append(prob)
    
    avg = sum(scores) / len(scores)
    return round(min(10.0, max(0.0, avg * 10.0)), 1)


def generate_component_hints(ui_elements):
    """Generate component hints based on detected UI elements."""
    component_props = {
        "Navigation Bar": {"name": "NavBar", "props": ["items", "activeItem", "logo", "onNavigate"]},
        "Sidebar": {"name": "Sidebar", "props": ["items", "collapsed", "activeItem", "onToggle"]},
        "Search Bar": {"name": "SearchInput", "props": ["placeholder", "value", "onChange", "onSubmit"]},
        "Button": {"name": "Button", "props": ["variant", "size", "onClick", "disabled", "loading"]},
        "Card": {"name": "Card", "props": ["title", "description", "image", "actions", "footer"]},
        "Data Table": {"name": "DataTable", "props": ["columns", "data", "sortable", "filterable", "pagination"]},
        "Form": {"name": "FormField", "props": ["label", "type", "placeholder", "value", "onChange", "error"]},
        "Dropdown": {"name": "Select", "props": ["options", "value", "onChange", "placeholder"]},
        "Modal": {"name": "Dialog", "props": ["open", "onClose", "title", "description"]},
        "Tabs": {"name": "Tabs", "props": ["items", "activeTab", "onChange", "variant"]},
        "Chart": {"name": "Chart", "props": ["type", "data", "options", "responsive"]},
        "Avatar": {"name": "Avatar", "props": ["src", "alt", "size", "fallback"]},
        "Badge": {"name": "Badge", "props": ["count", "variant", "dot"]},
        "Progress Bar": {"name": "Progress", "props": ["value", "max", "label"]},
        "Hero Section": {"name": "Hero", "props": ["title", "subtitle", "cta", "background"]},
        "Footer": {"name": "Footer", "props": ["links", "copyright", "social"]},
        "Pricing Table": {"name": "PricingCard", "props": ["plan", "price", "features", "cta", "popular"]},
        "Image Gallery": {"name": "Gallery", "props": ["images", "columns", "lightbox"]},
        "Testimonials": {"name": "Testimonial", "props": ["quote", "author", "role", "avatar"]},
        "Stats": {"name": "StatCard", "props": ["label", "value", "change", "trend"]},
        "Timeline": {"name": "Timeline", "props": ["items", "orientation"]},
        "Toggle": {"name": "Switch", "props": ["checked", "onChange", "label"]},
        "Icon Grid": {"name": "FeatureGrid", "props": ["items", "columns", "iconSize"]},
    }
    
    return [component_props[el] for el in ui_elements if el in component_props][:8]


def analyze_screenshot(model, preprocess, tokenizer, image_path):
    """Full analysis of a single screenshot using binary CLIP classification."""
    try:
        image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
    except Exception as e:
        return None
    
    result = {}
    
    # Detect UI elements
    elements = batch_binary_classify(model, preprocess, tokenizer, image, UI_ELEMENT_PROMPTS, threshold=0.55)
    result["ui_elements"] = list(elements.keys())[:10]
    result["ui_element_scores"] = {k: round(v, 3) for k, v in list(elements.items())[:10]}
    
    # Detect visual styles
    styles = batch_binary_classify(model, preprocess, tokenizer, image, VISUAL_STYLE_PROMPTS, threshold=0.55)
    result["visual_style"] = list(styles.keys())[:4]
    
    # Detect page type (use lower threshold, take top match)
    pages = batch_binary_classify(model, preprocess, tokenizer, image, PAGE_TYPE_PROMPTS, threshold=0.52)
    result["page_type"] = list(pages.keys())[0] if pages else None
    
    # Detect layout
    layouts = batch_binary_classify(model, preprocess, tokenizer, image, LAYOUT_PROMPTS, threshold=0.52)
    result["layout_type"] = list(layouts.keys())[0] if layouts else None
    
    # Color mode
    dark_prob = binary_classify(model, preprocess, tokenizer, image, 
        "a dark mode user interface with dark background",
        "a light mode user interface with white background")
    result["color_mode"] = "dark" if dark_prob > 0.55 else "light"
    
    # Quality
    result["visual_quality_score"] = assess_quality(model, preprocess, tokenizer, image)
    
    # Component hints
    result["component_hints"] = generate_component_hints(result["ui_elements"])
    
    return result


def enrich_patterns(model, preprocess, tokenizer):
    """Main enrichment pipeline."""
    with open(PATTERNS_PATH) as f:
        patterns = json.load(f)
    
    screenshot_patterns = [
        (i, p) for i, p in enumerate(patterns) 
        if p["id"].startswith("screenshot-")
    ]
    
    total = len(screenshot_patterns)
    enriched = 0
    failed = 0
    
    print(f"\nEnriching {total} screenshot patterns with vision model...")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    for idx, (pattern_idx, pattern) in enumerate(screenshot_patterns):
        image_path = BASE_DIR / pattern.get("image_url", "")
        
        if not image_path.exists():
            failed += 1
            continue
        
        try:
            analysis = analyze_screenshot(model, preprocess, tokenizer, image_path)
            
            if analysis is None:
                failed += 1
                continue
            
            # Update pattern
            if analysis["ui_elements"]:
                patterns[pattern_idx]["ui_elements"] = analysis["ui_elements"]
            
            if analysis["visual_style"]:
                patterns[pattern_idx]["visual_style"] = analysis["visual_style"]
            
            current_page = patterns[pattern_idx].get("page_type", "")
            if analysis["page_type"]:
                # Keep existing page_type if it's specific, override if generic
                if not current_page or current_page in ("Unknown", "Web Page", "Screenshot"):
                    patterns[pattern_idx]["page_type"] = analysis["page_type"]
            
            if analysis["layout_type"]:
                patterns[pattern_idx]["layout_type"] = analysis["layout_type"]
            
            patterns[pattern_idx]["color_mode"] = analysis["color_mode"]
            
            if analysis["component_hints"]:
                patterns[pattern_idx]["component_hints"] = analysis["component_hints"]
            
            # Blend quality score
            old_quality = patterns[pattern_idx].get("quality_score", 5.0)
            vision_quality = analysis["visual_quality_score"]
            new_quality = round(old_quality * 0.3 + vision_quality * 0.7, 1)
            metadata_bonus = min(1.5, len(analysis["ui_elements"]) * 0.1)
            patterns[pattern_idx]["quality_score"] = round(min(10.0, new_quality + metadata_bonus), 1)
            
            # Tag as enriched
            tags = patterns[pattern_idx].get("tags", [])
            if "vision-enriched" not in tags:
                tags.append("vision-enriched")
            patterns[pattern_idx]["tags"] = tags
            
            enriched += 1
            
            # Progress every 25
            if (idx + 1) % 25 == 0 or idx == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed
                remaining = (total - idx - 1) / rate if rate > 0 else 0
                print(f"  [{idx+1}/{total}] {enriched} enriched, {failed} failed | "
                      f"{rate:.1f} img/s | ETA: {remaining:.0f}s")
                print(f"    -> {pattern['name']}: {len(analysis['ui_elements'])} elements, "
                      f"{analysis['visual_style']}, quality={patterns[pattern_idx]['quality_score']}")
            
            # Save checkpoint every 100
            if (idx + 1) % 100 == 0:
                with open(PATTERNS_PATH, "w") as f:
                    json.dump(patterns, f, indent=2)
                print(f"    [checkpoint saved at {idx+1}]")
                
        except Exception as e:
            failed += 1
            if (idx + 1) % 50 == 0:
                print(f"  [{idx+1}/{total}] Error: {e}")
    
    elapsed = time.time() - start_time
    
    # Sort by quality
    patterns.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
    
    # Final save
    with open(PATTERNS_PATH, "w") as f:
        json.dump(patterns, f, indent=2)
    
    # Save model metadata
    model_meta = {
        "model": "ViT-B-32",
        "pretrained": "laion2b_s34b_b79k", 
        "method": "binary_clip_classification",
        "enrichment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "patterns_enriched": enriched,
        "patterns_failed": failed,
        "total_patterns": len(patterns),
        "thresholds": {
            "ui_element": 0.55,
            "visual_style": 0.55,
            "page_type": 0.52,
            "layout": 0.52,
            "color_mode": 0.55,
        }
    }
    with open(MODEL_OUTPUT_PATH, "w") as f:
        json.dump(model_meta, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed:.0f}s | {enriched} enriched, {failed} failed")
    print(f"{'='*60}")
    
    enriched_p = [p for p in patterns if "vision-enriched" in p.get("tags", [])]
    avg_el = sum(len(p.get("ui_elements", [])) for p in enriched_p) / max(1, len(enriched_p))
    avg_q = sum(p.get("quality_score", 0) for p in enriched_p) / max(1, len(enriched_p))
    
    all_elements = Counter()
    for p in enriched_p:
        for el in p.get("ui_elements", []):
            all_elements[el] += 1
    
    all_styles = Counter()
    for p in enriched_p:
        for s in p.get("visual_style", []):
            all_styles[s] += 1
    
    all_pages = Counter()
    for p in enriched_p:
        pt = p.get("page_type")
        if pt:
            all_pages[pt] += 1
    
    print(f"  Avg UI elements per pattern: {avg_el:.1f}")
    print(f"  Avg quality score: {avg_q:.1f}")
    print(f"\n  Top UI elements:")
    for elem, count in all_elements.most_common(15):
        print(f"    {elem}: {count}")
    print(f"\n  Visual styles:")
    for style, count in all_styles.most_common(10):
        print(f"    {style}: {count}")
    print(f"\n  Page types:")
    for page, count in all_pages.most_common(10):
        print(f"    {page}: {count}")


if __name__ == "__main__":
    model, preprocess, tokenizer = load_model()
    enrich_patterns(model, preprocess, tokenizer)
