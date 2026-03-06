"""Normalize vision results to match schema expectations."""
import json, re, sys

# Mapping from creative names to standard names
ELEMENT_MAP = {
    'navigation_bar': 'Navigation Bar', 'navigation_menu': 'Navigation Bar', 'nav': 'Navigation Bar',
    'horizontal_menu': 'Navigation Bar', 'menu_links': 'Navigation Bar',
    'hero_section': 'Hero Section', 'hero_image': 'Hero Section', 'hero_text': 'Hero Section',
    'hero_3d_illustration': 'Hero Section', 'oversized_headline': 'Hero Section',
    'hero_oversized_text': 'Hero Section', 'large_name_typography': 'Hero Section',
    'large_headline': 'Hero Section', 'large_typography': 'Hero Section',
    'button': 'Button', 'cta_button': 'Button', 'reserve_button': 'Button', 'menu_button': 'Button',
    'card': 'Card', 'promotional_card': 'Card', 'project_card': 'Card',
    'icon': 'Icon', 'circular_element': 'Icon', 'logo': 'Icon',
    'badge': 'Badge', 'shortlist_counter': 'Badge',
    'divider': 'Divider', 'split_layout': 'Divider',
    'footer': 'Footer', 'input': 'Input', 'tabs': 'Tabs', 'carousel': 'Carousel',
    'avatar': 'Avatar', 'toggle': 'Toggle', 'dropdown': 'Dropdown',
    'sidebar': 'Sidebar', 'chart': 'Chart', 'data_table': 'Data Table',
    'testimonials': 'Testimonials', 'icon_grid': 'Icon Grid', 'chip': 'Chip',
    'breadcrumb': 'Breadcrumb', 'pagination': 'Pagination', 'progress_bar': 'Progress Bar',
    'stepper': 'Stepper', 'code_snippet': 'Code Snippet', 'tooltip': 'Tooltip',
    'modal': 'Modal', 'calendar': 'Calendar',
    'contact_link': 'Button', 'email_link': 'Button',
    'language_switcher': 'Dropdown', 'timestamp': 'Badge',
    'subtitle_text': 'Divider', 'description_text': 'Divider', 'tagline_text': 'Divider',
    'floating_project_thumbnails': 'Card', 'registered_trademark': 'Badge',
}

STYLE_MAP = {
    'minimalist': 'Minimal', 'minimal': 'Minimal', 'clean': 'Minimal',
    'glassmorphism': 'Glassmorphism', 'brutalist': 'Brutalist', 'neubrutalism': 'Neubrutalism',
    'gradient': 'Gradient', 'dark_mode': 'Dark Mode', 'dark_theme': 'Dark Mode',
    'light_mode': 'Light Mode', 'colorful': 'Colorful', 'monochrome': 'Monochrome',
    'corporate': 'Corporate', 'playful': 'Playful', 'retro': 'Retro', 'futuristic': 'Futuristic',
    'flat': 'Flat', 'bold_typography': 'Minimal', 'editorial': 'Minimal',
    'high_contrast': 'Monochrome', 'black_and_white': 'Monochrome',
    '3d_graphics': 'Futuristic', 'experimental': 'Brutalist', 'industrial': 'Brutalist',
    'cinematic': 'Futuristic', 'luxury': 'Minimal', 'elegant_serif': 'Minimal',
    'immersive_photography': 'Minimal', 'warm_tones': 'Colorful',
    'fashion_photography': 'Minimal', 'split_screen': 'Minimal',
    'scattered_layout': 'Brutalist', 'full_bleed_imagery': 'Minimal',
    'mixed_typography': 'Minimal', 'monospace_text': 'Brutalist', 'grid_overlay': 'Minimal',
}

LAYOUT_MAP = {
    'full_bleed': 'full_bleed', 'single_column': 'single_column', 'split_screen': 'split_screen',
    'sidebar_main': 'sidebar_main', 'card_grid': 'card_grid', 'masonry': 'masonry',
    'hero_centered': 'hero_centered', 'stacked': 'stacked', 'editorial': 'editorial',
    'asymmetric': 'asymmetric', 'flexbox': 'flexbox', 'css_grid': 'css_grid',
    'bento_grid': 'bento_grid', 'dashboard_panels': 'dashboard_panels',
    'holy_grail': 'holy_grail', 'sticky_header': 'sticky_header',
    'hero_oversized_text': 'hero_centered', 'freeform_scattered': 'asymmetric',
    'full_screen_hero': 'full_bleed',
}

PAGE_MAP = {
    'agency_homepage': 'Agency', 'portfolio_homepage': 'Portfolio',
    'talent_platform_homepage': 'Landing Page', 'hospitality_landing': 'Landing Page',
}

def normalize(results):
    normalized = []
    for r in results:
        # Normalize page_type
        pt = r.get('page_type', 'Other')
        pt = PAGE_MAP.get(pt.lower().replace(' ', '_'), pt)
        
        # Normalize elements
        raw_elements = r.get('ui_elements', [])
        elements = set()
        for e in raw_elements:
            key = e.lower().replace(' ', '_')
            mapped = ELEMENT_MAP.get(key)
            if mapped:
                elements.add(mapped)
        
        # Normalize styles
        raw_styles = r.get('visual_style', [])
        styles = set()
        for s in raw_styles:
            key = s.lower().replace(' ', '_')
            mapped = STYLE_MAP.get(key)
            if mapped:
                styles.add(mapped)
        
        # Normalize layout
        lt = r.get('layout_type', 'stacked')
        lt = LAYOUT_MAP.get(lt.lower().replace(' ', '_'), 'stacked')
        
        normalized.append({
            'page_type': pt,
            'ui_elements': sorted(list(elements)),
            'visual_style': sorted(list(styles)),
            'color_mode': r.get('color_mode', 'light'),
            'primary_colors': r.get('primary_colors', [])[:3],
            'layout_type': lt,
            'quality_score': min(10, max(1, r.get('quality_score', 5)))
        })
    
    return normalized

if __name__ == '__main__':
    data = json.loads(sys.stdin.read())
    print(json.dumps(normalize(data)))
