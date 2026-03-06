"""Process remaining screenshots through vision analysis using Anthropic API."""
import json, os, sys, time, base64
sys.stdout.reconfigure(encoding='utf-8')

try:
    import anthropic
except ImportError:
    print("Installing anthropic...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "anthropic"], check=True)
    import anthropic

VISION_RESULTS_PATH = 'data/vision_results.json'
REMAINING_PATH = 'data/remaining_vision.json'
PATTERNS_PATH = 'data/patterns.json'
BATCH_SIZE = 10
SAVE_EVERY = 10

VISION_PROMPT = """Analyze this web design screenshot. Return a JSON object with:
{
  "page_type": "Dashboard|Landing Page|Login|Signup|Pricing|Blog Post|E-commerce|Portfolio|Documentation|Admin Panel|Checkout|Onboarding|Social Feed|Marketplace|Settings|404 Page|Other",
  "ui_elements": ["list of UI elements visible: Button, Card, Navigation Bar, Hero Section, Data Table, Input, Modal, Tabs, Accordion, Badge, Avatar, Toggle, Dropdown, Footer, Sidebar, Breadcrumb, Pagination, Tooltip, Carousel, Progress Bar, Chip, Stepper, Divider, Code Snippet, Testimonials, Icon Grid, Icon, Chart, Calendar"],
  "visual_style": ["list from: Minimal, Glassmorphism, Brutalist, Neubrutalism, Flat, Skeuomorphic, Gradient, Dark Mode, Light Mode, Colorful, Monochrome, Corporate, Playful, Retro, Futuristic"],
  "color_mode": "light|dark",
  "primary_colors": ["top 3 hex colors observed"],
  "layout_type": "flexbox|css_grid|bento_grid|single_column|sidebar_main|split_screen|masonry|stacked|full_bleed|dashboard_panels|editorial|card_grid|hero_centered|holy_grail|sticky_header|asymmetric",
  "quality_score": 1-10
}
Return ONLY the JSON, no markdown fences or explanation."""

def encode_image(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def get_media_type(path):
    ext = path.lower().split('.')[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/jpeg")

def main():
    # Load existing results
    with open(VISION_RESULTS_PATH) as f:
        vision_results = json.load(f)
    
    with open(REMAINING_PATH) as f:
        remaining = json.load(f)
    
    print(f"Existing results: {len(vision_results)}")
    print(f"Remaining to process: {len(remaining)}")
    
    # Filter out any already processed
    todo = [r for r in remaining if r['image_url'] not in vision_results]
    print(f"Actually need to process: {len(todo)}")
    
    if not todo:
        print("All done!")
        return
    
    client = anthropic.Anthropic()
    
    processed = 0
    errors = 0
    
    for item in todo:
        img_path = item['image_url']
        
        if not os.path.exists(img_path):
            print(f"  SKIP (missing): {img_path}")
            errors += 1
            continue
        
        try:
            img_data = encode_image(img_path)
            media_type = get_media_type(img_path)
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                        {"type": "text", "text": VISION_PROMPT}
                    ]
                }]
            )
            
            text = response.content[0].text.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            
            result = json.loads(text)
            vision_results[img_path] = result
            processed += 1
            
            if processed % SAVE_EVERY == 0:
                with open(VISION_RESULTS_PATH, 'w') as f:
                    json.dump(vision_results, f, indent=2)
                print(f"  Saved. {processed} done, {errors} errors, {len(todo) - processed - errors} remaining")
            
            # Rate limiting
            time.sleep(0.5)
            
        except json.JSONDecodeError as e:
            print(f"  JSON ERROR ({img_path}): {e}")
            errors += 1
        except anthropic.RateLimitError:
            print(f"  RATE LIMITED at {processed}. Saving and exiting.")
            with open(VISION_RESULTS_PATH, 'w') as f:
                json.dump(vision_results, f, indent=2)
            print(f"Saved {processed} new results. {len(todo) - processed - errors} still remaining.")
            return
        except Exception as e:
            print(f"  ERROR ({img_path}): {e}")
            errors += 1
            if errors > 20:
                print("Too many errors, stopping.")
                break
    
    # Final save
    with open(VISION_RESULTS_PATH, 'w') as f:
        json.dump(vision_results, f, indent=2)
    
    print(f"\nDone! Processed: {processed}, Errors: {errors}")
    print(f"Total vision results: {len(vision_results)}")

if __name__ == '__main__':
    main()
