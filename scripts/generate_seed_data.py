"""
Generate a high-quality seed dataset of design patterns based on
well-known products and established design systems.

This provides immediate value while the full webui-7kbal dataset
(60GB) can be ingested later as a supplement.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase

SEED_PATTERNS = [
    # === DASHBOARDS ===
    DesignPattern(
        id="seed-stripe-dashboard",
        name="Stripe Dashboard",
        source="curated",
        source_url="https://dashboard.stripe.com",
        page_type="Dashboard",
        ux_patterns=["Skeleton Loading", "Empty State", "Search with Filters", "Tab Navigation"],
        ui_elements=["Navigation Bar", "Sidebar", "Card", "Data Table", "Badge", "Button", "Input", "Tabs", "Breadcrumb"],
        industry="Fintech",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Fixed 240px sidebar, main content area with 24px grid gap, responsive collapse to hamburger",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#635bff", "#0a2540", "#f6f9fc"],
        behavioral_description="Dashboard shows overview metrics in cards at top, recent activity in data table below. Empty state educates on first use with illustration and CTA. Loading shows skeleton matching exact card + table layout. Error states preserve context with inline retry.",
        component_hints=[
            {"name": "MetricCard", "props": ["title", "value", "change_percent", "trend", "icon"]},
            {"name": "TransactionTable", "props": ["columns", "data", "sortable", "filterable", "pagination"]},
        ],
        accessibility_notes="ARIA landmarks for nav, main, complementary. Data table has proper th scope. All interactive elements have visible focus indicators. Color contrast meets WCAG AA.",
        semantic_tokens={"color-bg-primary": "#f6f9fc", "color-brand": "#635bff", "spacing-section": "32px", "border-radius-card": "8px", "font-heading": "Inter"},
        quality_score=9.5,
        tags=["fintech", "dashboard", "stripe", "data-table", "saas", "professional"]
    ),
    DesignPattern(
        id="seed-linear-dashboard",
        name="Linear Project Dashboard",
        source="curated",
        source_url="https://linear.app",
        page_type="Dashboard",
        ux_patterns=["Command Palette", "Drag and Drop", "Inline Editing", "Skeleton Loading"],
        ui_elements=["Sidebar", "Navigation Bar", "Card", "Badge", "Button", "Input", "Tabs", "Tooltip"],
        industry="Productivity",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Collapsible 200px sidebar, main content with kanban or list view, command palette overlay",
        platform=Platform.WEB,
        color_mode="dark",
        visual_style=["Minimal", "Futuristic"],
        primary_colors=["#5e6ad2", "#1a1a2e", "#e8e8e8"],
        behavioral_description="Dashboard shows project issues in list or board view. Command palette (Cmd+K) for quick navigation. Inline editing on issue titles. Drag and drop for priority/status changes. Optimistic updates with undo.",
        component_hints=[
            {"name": "IssueRow", "props": ["title", "status", "priority", "assignee", "labels", "created_at"]},
            {"name": "CommandPalette", "props": ["query", "results", "categories", "recent_actions"]},
        ],
        accessibility_notes="Full keyboard navigation. Command palette accessible via Cmd+K. Drag and drop has keyboard alternative. Focus management on modal open/close.",
        semantic_tokens={"color-bg-primary": "#1a1a2e", "color-brand": "#5e6ad2", "spacing-section": "24px", "border-radius-card": "6px"},
        quality_score=9.5,
        tags=["productivity", "dashboard", "dark-mode", "command-palette", "kanban"]
    ),
    DesignPattern(
        id="seed-vercel-dashboard",
        name="Vercel Project Dashboard",
        source="curated",
        source_url="https://vercel.com/dashboard",
        page_type="Dashboard",
        ux_patterns=["Skeleton Loading", "Tab Navigation", "Search with Filters", "Toast Notifications"],
        ui_elements=["Navigation Bar", "Card", "Badge", "Button", "Input", "Tabs", "Avatar", "Dropdown"],
        industry="Developer Tools",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Top nav, single column content with max-width 1200px, deployment cards in list",
        platform=Platform.WEB,
        color_mode="dark",
        visual_style=["Minimal", "Monochrome"],
        primary_colors=["#000000", "#ffffff", "#0070f3"],
        behavioral_description="Shows project deployments in a list. Each card shows status, branch, commit, and time. Real-time status updates. Toast notifications for deployment completion. Search filters by project name.",
        component_hints=[
            {"name": "DeploymentCard", "props": ["status", "branch", "commit_msg", "timestamp", "domain", "author"]},
        ],
        accessibility_notes="High contrast dark theme. Status indicators use both color and icon. Semantic HTML throughout.",
        semantic_tokens={"color-bg-primary": "#000000", "color-brand": "#0070f3", "spacing-section": "32px", "border-radius-card": "8px"},
        quality_score=9.0,
        tags=["developer-tools", "dashboard", "dark-mode", "minimal", "deployments"]
    ),

    # === PRICING PAGES ===
    DesignPattern(
        id="seed-stripe-pricing",
        name="Stripe Pricing Page",
        source="curated",
        source_url="https://stripe.com/pricing",
        page_type="Pricing",
        ux_patterns=["Tab Navigation", "Progressive Disclosure"],
        ui_elements=["Card", "Button", "Badge", "Toggle", "Tabs", "Tooltip", "Divider"],
        industry="Fintech",
        layout_type=LayoutType.CSS_GRID,
        layout_notes="3-column grid for pricing tiers, responsive to single column on mobile, feature comparison table below",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#635bff", "#0a2540", "#ffffff"],
        behavioral_description="Three pricing tiers in cards with highlighted 'popular' option. Toggle between monthly/annual billing. Feature comparison table with tooltips for details. CTA buttons change text based on tier.",
        component_hints=[
            {"name": "PricingCard", "props": ["tier_name", "price", "billing_period", "features", "cta_text", "is_popular", "description"]},
            {"name": "BillingToggle", "props": ["options", "selected", "discount_label"]},
        ],
        accessibility_notes="Toggle has proper role and aria-checked. Feature tooltips accessible via keyboard. Price changes announced to screen readers on toggle.",
        semantic_tokens={"color-bg-primary": "#ffffff", "color-brand": "#635bff", "spacing-section": "48px", "border-radius-card": "12px"},
        quality_score=9.0,
        tags=["fintech", "pricing", "stripe", "saas", "comparison"]
    ),
    DesignPattern(
        id="seed-saas-pricing-dark",
        name="SaaS Dark Pricing Page",
        source="curated",
        source_url="https://example.com/pricing",
        page_type="Pricing",
        ux_patterns=["Progressive Disclosure", "Tab Navigation"],
        ui_elements=["Card", "Button", "Badge", "Toggle", "Divider", "Icon"],
        industry="SaaS",
        layout_type=LayoutType.CSS_GRID,
        layout_notes="3-column grid, center card elevated with glow effect, gradient background",
        platform=Platform.WEB,
        color_mode="dark",
        visual_style=["Glassmorphism", "Gradient-Heavy"],
        primary_colors=["#7c3aed", "#1e1b4b", "#f0abfc"],
        behavioral_description="Dark background with gradient. Center tier has glassmorphism card effect and is slightly elevated. Annual/monthly toggle with savings badge. Hover effects on cards reveal additional details.",
        component_hints=[
            {"name": "PricingCard", "props": ["tier", "price", "features", "cta", "is_featured", "glow_color"]},
        ],
        accessibility_notes="Ensure glassmorphism cards maintain text contrast. Focus indicators visible on dark background.",
        quality_score=8.0,
        tags=["saas", "pricing", "dark-mode", "glassmorphism", "gradient"]
    ),

    # === ONBOARDING ===
    DesignPattern(
        id="seed-notion-onboarding",
        name="Notion Onboarding Flow",
        source="curated",
        source_url="https://notion.so",
        page_type="Onboarding",
        ux_patterns=["Multi-Step Form", "Onboarding Flow", "Stepper", "Progressive Disclosure"],
        ui_elements=["Stepper", "Input", "Button", "Avatar", "Card", "Progress Bar", "Radio Button"],
        industry="Productivity",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Centered card, max-width 480px, step indicator at top, content changes per step",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Playful"],
        primary_colors=["#000000", "#ffffff", "#2eaadc"],
        behavioral_description="3-step onboarding: 1) Use case selection (radio cards), 2) Team size, 3) Template selection. Progress indicator shows current step. Skip option always visible. Demonstrates value by showing template previews.",
        component_hints=[
            {"name": "OnboardingStep", "props": ["step_number", "title", "description", "content", "can_skip"]},
            {"name": "UseCaseCard", "props": ["icon", "title", "description", "is_selected"]},
        ],
        accessibility_notes="Step changes announced via aria-live. Radio cards have proper role. Progress bar has aria-valuenow. Focus trapped within current step.",
        quality_score=9.0,
        tags=["productivity", "onboarding", "multi-step", "minimal"]
    ),

    # === LOGIN / AUTH ===
    DesignPattern(
        id="seed-auth-split-screen",
        name="Split Screen Login",
        source="curated",
        source_url="https://example.com/login",
        page_type="Login",
        ux_patterns=["Progressive Disclosure"],
        ui_elements=["Input", "Button", "Divider", "Icon", "Card"],
        industry="SaaS",
        layout_type=LayoutType.SPLIT_SCREEN,
        layout_notes="50/50 split: left side brand illustration/gradient, right side login form centered",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#4f46e5", "#ffffff", "#f3f4f6"],
        behavioral_description="Split layout with brand visual on left, form on right. Social login buttons (Google, GitHub) above divider. Email/password below. Form validation on blur. Password visibility toggle. Forgot password link below form.",
        component_hints=[
            {"name": "LoginForm", "props": ["email", "password", "remember_me", "social_providers"]},
            {"name": "SocialButton", "props": ["provider", "icon", "label"]},
        ],
        accessibility_notes="Form labels properly associated. Password field has show/hide toggle with aria-label. Error messages linked via aria-describedby. Autofill supported.",
        quality_score=8.5,
        tags=["auth", "login", "split-screen", "social-login"]
    ),

    # === SETTINGS ===
    DesignPattern(
        id="seed-github-settings",
        name="GitHub Settings Page",
        source="curated",
        source_url="https://github.com/settings",
        page_type="Settings",
        ux_patterns=["Tab Navigation", "Accordion Navigation", "Progressive Disclosure"],
        ui_elements=["Sidebar", "Input", "Button", "Toggle", "Avatar", "Divider", "Select", "Switch"],
        industry="Developer Tools",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left sidebar with settings categories (240px), main content area with form sections separated by dividers",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#0d1117", "#ffffff", "#238636"],
        behavioral_description="Settings organized by category in left sidebar. Each section has a heading, description, and form fields. Save buttons per section (not global). Danger zone at bottom with red-bordered section for destructive actions. Confirmation modal for dangerous operations.",
        component_hints=[
            {"name": "SettingsSection", "props": ["title", "description", "fields", "save_action"]},
            {"name": "DangerZone", "props": ["actions", "confirmation_required"]},
        ],
        accessibility_notes="Navigation sidebar has proper nav landmark. Form sections use fieldset/legend. Danger zone has aria-label warning. Confirmation dialogs trap focus.",
        quality_score=9.0,
        tags=["developer-tools", "settings", "form", "sidebar-navigation"]
    ),

    # === 404 / ERROR ===
    DesignPattern(
        id="seed-creative-404",
        name="Creative 404 Page",
        source="curated",
        source_url="https://example.com/404",
        page_type="404 Page",
        ux_patterns=["Empty State"],
        ui_elements=["Button", "Icon"],
        industry="SaaS",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Centered content, illustration or animation above text, max-width 600px",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Playful", "Minimal"],
        primary_colors=["#6366f1", "#ffffff", "#1f2937"],
        behavioral_description="Engaging 404 with custom illustration or animation. Friendly headline ('Page not found' or creative variant). Brief explanation. Primary CTA to go home, secondary to go back. Optional search bar.",
        component_hints=[
            {"name": "ErrorPage", "props": ["illustration", "title", "description", "primary_cta", "secondary_cta", "show_search"]},
        ],
        accessibility_notes="Meaningful alt text on illustration. CTAs clearly labeled. Page title updated to indicate error.",
        quality_score=8.0,
        tags=["404", "error", "illustration", "playful"]
    ),

    # === E-COMMERCE ===
    DesignPattern(
        id="seed-ecommerce-checkout",
        name="Modern E-Commerce Checkout",
        source="curated",
        source_url="https://example.com/checkout",
        page_type="Checkout",
        ux_patterns=["Multi-Step Form", "Stepper", "Progressive Disclosure"],
        ui_elements=["Input", "Button", "Card", "Stepper", "Divider", "Radio Button", "Badge", "Icon"],
        industry="E-Commerce",
        layout_type=LayoutType.SPLIT_SCREEN,
        layout_notes="60/40 split: left side form steps, right side order summary sticky",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#111827", "#ffffff", "#059669"],
        behavioral_description="3-step checkout: shipping info, payment, review. Order summary sticky on right side. Form validation on blur with inline errors. Express checkout options (Apple Pay, Google Pay) at top. Progress saved between steps.",
        component_hints=[
            {"name": "CheckoutStep", "props": ["step", "title", "fields", "is_active", "is_complete"]},
            {"name": "OrderSummary", "props": ["items", "subtotal", "tax", "shipping", "total", "promo_code"]},
        ],
        accessibility_notes="Step progress announced to screen readers. Form errors linked via aria-describedby. Payment fields use autocomplete attributes. Express pay buttons clearly labeled.",
        quality_score=8.5,
        tags=["e-commerce", "checkout", "multi-step", "payment"]
    ),

    # === CHAT INTERFACE ===
    DesignPattern(
        id="seed-chat-interface",
        name="Modern Chat Interface",
        source="curated",
        source_url="https://example.com/chat",
        page_type="Chat Interface",
        ux_patterns=["Infinite Scroll", "Lazy Loading", "Toast Notifications", "Inline Editing"],
        ui_elements=["Input", "Avatar", "Badge", "Button", "Sidebar", "Divider", "Icon", "Text Area"],
        industry="Social Media",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left sidebar with conversation list (320px), main chat area with messages and input at bottom",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#0084ff", "#ffffff", "#e4e6eb"],
        behavioral_description="Conversation list on left, active chat on right. Messages load with infinite scroll upward. New messages appear at bottom with smooth scroll. Typing indicators show when other user is typing. Message status (sent, delivered, read) shown with icons.",
        component_hints=[
            {"name": "MessageBubble", "props": ["content", "sender", "timestamp", "status", "is_own", "reactions"]},
            {"name": "ConversationItem", "props": ["avatar", "name", "last_message", "timestamp", "unread_count", "is_active"]},
        ],
        accessibility_notes="Messages use aria-live for new incoming. Conversation list is navigable by keyboard. Input has proper label. Emoji picker accessible.",
        quality_score=8.5,
        tags=["chat", "messaging", "real-time", "social"]
    ),

    # === ANALYTICS ===
    DesignPattern(
        id="seed-analytics-dashboard",
        name="Analytics Dashboard",
        source="curated",
        source_url="https://example.com/analytics",
        page_type="Analytics",
        ux_patterns=["Skeleton Loading", "Tab Navigation", "Search with Filters"],
        ui_elements=["Card", "Data Table", "Badge", "Button", "Dropdown", "Date Picker", "Tabs", "Sidebar"],
        industry="SaaS",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Sidebar nav, top row of KPI cards, chart area below, data table at bottom",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#4f46e5", "#f9fafb", "#111827"],
        behavioral_description="Top KPI cards show key metrics with sparklines. Date range picker in top right. Charts update on date change with loading animation. Data table below charts with export and filter options. Skeleton loading matches exact card + chart + table layout.",
        component_hints=[
            {"name": "KPICard", "props": ["title", "value", "change", "sparkline_data", "icon"]},
            {"name": "ChartPanel", "props": ["type", "data", "title", "time_range", "loading"]},
        ],
        accessibility_notes="Charts have text alternatives. Data table sortable by keyboard. Date picker accessible. Color is not sole indicator of trends.",
        semantic_tokens={"color-bg-primary": "#f9fafb", "color-brand": "#4f46e5", "spacing-section": "24px"},
        quality_score=8.5,
        tags=["analytics", "dashboard", "charts", "kpi", "data-visualization"]
    ),

    # === LANDING PAGE ===
    DesignPattern(
        id="seed-saas-landing",
        name="SaaS Landing Page",
        source="curated",
        source_url="https://example.com",
        page_type="Landing Page",
        ux_patterns=["Lazy Loading", "Progressive Disclosure"],
        ui_elements=["Navigation Bar", "Button", "Card", "Badge", "Icon", "Input", "Avatar", "Carousel"],
        industry="SaaS",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Full width sections stacked: hero, social proof, features grid, testimonials, pricing preview, CTA, footer",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#6366f1", "#ffffff", "#1e1b4b"],
        behavioral_description="Hero section with headline, subhead, CTA, and product screenshot. Social proof logos below. Feature sections alternate layout (image left/right). Testimonial carousel with auto-advance. Pricing preview with CTA to full pricing page. Sticky nav on scroll.",
        component_hints=[
            {"name": "HeroSection", "props": ["headline", "subheadline", "cta_text", "cta_url", "product_image"]},
            {"name": "FeatureCard", "props": ["icon", "title", "description", "image", "image_position"]},
            {"name": "TestimonialCard", "props": ["quote", "author_name", "author_title", "author_avatar", "company"]},
        ],
        accessibility_notes="Sticky nav has proper landmark. Images have alt text. CTA buttons clearly labeled. Carousel has pause control and keyboard navigation.",
        quality_score=8.5,
        tags=["saas", "landing-page", "hero", "features", "testimonials"]
    ),

    # === ADMIN PANEL ===
    DesignPattern(
        id="seed-admin-panel",
        name="Admin Panel with Data Tables",
        source="curated",
        source_url="https://example.com/admin",
        page_type="Admin Panel",
        ux_patterns=["Bulk Actions", "Search with Filters", "Inline Editing", "Contextual Menu"],
        ui_elements=["Sidebar", "Data Table", "Checkbox", "Button", "Dropdown", "Badge", "Input", "Modal", "Pagination"],
        industry="SaaS",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Fixed sidebar with icon + text nav, main area has search/filter bar, data table with pagination",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#111827", "#f9fafb", "#3b82f6"],
        behavioral_description="Sidebar navigation with collapsible sections. Main area shows filterable data table. Row selection enables bulk action toolbar. Right-click context menu for row actions. Inline editing on double-click. Pagination with page size selector.",
        component_hints=[
            {"name": "DataTable", "props": ["columns", "data", "selectable", "sortable", "filterable", "page_size", "total_count"]},
            {"name": "BulkActionBar", "props": ["selected_count", "actions"]},
        ],
        accessibility_notes="Table uses proper th/td markup with scope. Checkboxes labeled. Context menu accessible via keyboard. Pagination announces current page.",
        quality_score=8.0,
        tags=["admin", "data-table", "crud", "management"]
    ),

    # === KANBAN BOARD ===
    DesignPattern(
        id="seed-kanban-board",
        name="Kanban Board",
        source="curated",
        source_url="https://example.com/board",
        page_type="Kanban Board",
        ux_patterns=["Drag and Drop", "Inline Editing", "Contextual Menu", "Lazy Loading"],
        ui_elements=["Card", "Button", "Badge", "Avatar", "Dropdown", "Input", "Sidebar"],
        industry="Productivity",
        layout_type=LayoutType.FLEXBOX,
        layout_notes="Horizontal scrollable columns, each column has vertical card stack, cards draggable between columns",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#0052cc", "#ffffff", "#f4f5f7"],
        behavioral_description="Columns represent statuses (To Do, In Progress, Done). Cards show task title, assignee avatar, priority badge, and due date. Drag and drop between columns updates status. Click card opens detail modal. Add card button at column bottom. Column header shows count.",
        component_hints=[
            {"name": "KanbanColumn", "props": ["title", "cards", "count", "color", "can_add"]},
            {"name": "TaskCard", "props": ["title", "assignee", "priority", "due_date", "labels", "comments_count"]},
        ],
        accessibility_notes="Drag and drop has keyboard alternative (select + arrow keys). Card details accessible via Enter. Column counts announced. Task priority indicated by both color and text.",
        quality_score=8.5,
        tags=["kanban", "project-management", "drag-drop", "productivity"]
    ),

    # === DOCUMENTATION ===
    DesignPattern(
        id="seed-docs-page",
        name="Documentation Page",
        source="curated",
        source_url="https://example.com/docs",
        page_type="Documentation",
        ux_patterns=["Breadcrumb Navigation", "Search with Filters", "Accordion Navigation", "Lazy Loading"],
        ui_elements=["Sidebar", "Breadcrumb", "Code Snippet", "Navigation Bar", "Input", "Divider", "Tabs", "Accordion"],
        industry="Developer Tools",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left sidebar nav (260px), main content (max-width 800px), right TOC sidebar (200px)",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#0f172a", "#ffffff", "#3b82f6"],
        behavioral_description="Three-column layout: left nav tree, center content, right table of contents. Search with instant results. Code blocks with syntax highlighting and copy button. Breadcrumbs show path. Previous/Next navigation at bottom. TOC highlights current section on scroll.",
        component_hints=[
            {"name": "DocSidebar", "props": ["sections", "current_path", "collapsible"]},
            {"name": "CodeBlock", "props": ["code", "language", "title", "copyable", "line_numbers"]},
            {"name": "TableOfContents", "props": ["headings", "active_heading"]},
        ],
        accessibility_notes="Code blocks have proper aria-label. Navigation sidebar is a nav landmark. Skip-to-content link. Headings properly nested. Search results announced via aria-live.",
        quality_score=9.0,
        tags=["documentation", "developer-tools", "code", "three-column"]
    ),

    # === SOCIAL FEED ===
    DesignPattern(
        id="seed-social-feed",
        name="Social Media Feed",
        source="curated",
        source_url="https://example.com/feed",
        page_type="Social Feed",
        ux_patterns=["Infinite Scroll", "Lazy Loading", "Optimistic Update", "Pull to Refresh"],
        ui_elements=["Card", "Avatar", "Button", "Icon", "Input", "Badge", "Dropdown"],
        industry="Social Media",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Single column feed, max-width 600px centered, stories/reels bar at top",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#1da1f2", "#ffffff", "#14171a"],
        behavioral_description="Vertical feed of posts. Each post has author info, content, media, and engagement actions. Like/repost/reply with optimistic updates. Infinite scroll loads more posts. New posts indicator at top. Image posts expand on click.",
        component_hints=[
            {"name": "PostCard", "props": ["author", "content", "media", "timestamp", "likes", "replies", "reposts", "is_liked"]},
            {"name": "ComposeBox", "props": ["placeholder", "max_length", "media_upload", "submit_label"]},
        ],
        accessibility_notes="Images have alt text. Engagement buttons clearly labeled. New content announced via aria-live. Focus management on modal open.",
        quality_score=8.0,
        tags=["social-media", "feed", "infinite-scroll", "engagement"]
    ),

    # === PROFILE PAGE ===
    DesignPattern(
        id="seed-profile-page",
        name="User Profile Page",
        source="curated",
        source_url="https://example.com/profile",
        page_type="Profile",
        ux_patterns=["Tab Navigation", "Lazy Loading"],
        ui_elements=["Avatar", "Button", "Tabs", "Card", "Badge", "Icon", "Divider"],
        industry="Social Media",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Header with cover image and avatar, stats row, tabbed content below (posts, about, photos)",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#1da1f2", "#ffffff", "#657786"],
        behavioral_description="Cover image at top with overlapping avatar. Name, bio, and stats (followers, following, posts). Action buttons (Follow, Message). Tabbed content: posts feed, about info, media gallery. Edit profile button for own profile.",
        component_hints=[
            {"name": "ProfileHeader", "props": ["cover_image", "avatar", "name", "bio", "stats", "is_own_profile"]},
            {"name": "StatsRow", "props": ["followers", "following", "posts"]},
        ],
        accessibility_notes="Avatar has alt text. Stats are semantically marked up. Tab panels properly linked to tabs.",
        quality_score=8.0,
        tags=["profile", "social-media", "tabs", "avatar"]
    ),

    # === MARKETPLACE ===
    DesignPattern(
        id="seed-marketplace",
        name="Product Marketplace",
        source="curated",
        source_url="https://example.com/marketplace",
        page_type="Marketplace",
        ux_patterns=["Search with Filters", "Lazy Loading", "Infinite Scroll"],
        ui_elements=["Card", "Input", "Button", "Badge", "Dropdown", "Checkbox", "Slider", "Sidebar", "Pagination"],
        industry="E-Commerce",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left filter sidebar (260px), product grid (3-4 columns responsive), sort dropdown in header",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Corporate"],
        primary_colors=["#ff6900", "#ffffff", "#333333"],
        behavioral_description="Filter sidebar with category checkboxes, price range slider, rating filter. Product grid shows image, title, price, rating. Sort by relevance/price/rating. Lazy load images. Product cards have hover effect showing quick-view button.",
        component_hints=[
            {"name": "ProductCard", "props": ["image", "title", "price", "original_price", "rating", "reviews_count", "is_sale"]},
            {"name": "FilterPanel", "props": ["categories", "price_range", "rating_filter", "active_filters"]},
        ],
        accessibility_notes="Filter changes announced. Product images have alt text. Price and discount clearly labeled. Grid layout announced to screen readers.",
        quality_score=8.0,
        tags=["marketplace", "e-commerce", "product-grid", "filters"]
    ),

    # === FILE EXPLORER ===
    DesignPattern(
        id="seed-file-explorer",
        name="File Explorer / Manager",
        source="curated",
        source_url="https://example.com/files",
        page_type="File Explorer",
        ux_patterns=["Drag and Drop", "Contextual Menu", "Breadcrumb Navigation", "Bulk Actions"],
        ui_elements=["Sidebar", "Breadcrumb", "Data Table", "Icon", "Button", "Dropdown", "Checkbox", "Modal"],
        industry="Productivity",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left sidebar with folder tree (240px), main area with breadcrumb + file grid/list view toggle",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#1a73e8", "#ffffff", "#5f6368"],
        behavioral_description="Folder tree in sidebar, files in main area. Toggle between grid (thumbnails) and list (detail) view. Breadcrumb navigation. Drag and drop for moving files. Right-click context menu for actions. Multi-select with Shift/Ctrl+Click for bulk operations.",
        component_hints=[
            {"name": "FileItem", "props": ["name", "type", "size", "modified", "thumbnail", "is_selected"]},
            {"name": "FolderTree", "props": ["tree_data", "expanded_nodes", "selected_node"]},
        ],
        accessibility_notes="File list uses proper grid role. Context menu accessible via keyboard (Shift+F10). Drag and drop has cut/paste keyboard alternative. File type indicated by both icon and text.",
        quality_score=8.0,
        tags=["file-explorer", "file-manager", "tree-view", "drag-drop"]
    ),

    # === CALENDAR ===
    DesignPattern(
        id="seed-calendar",
        name="Calendar Application",
        source="curated",
        source_url="https://example.com/calendar",
        page_type="Calendar",
        ux_patterns=["Drag and Drop", "Contextual Menu", "Inline Editing"],
        ui_elements=["Button", "Dropdown", "Modal", "Input", "Date Picker", "Sidebar", "Badge"],
        industry="Productivity",
        layout_type=LayoutType.SIDEBAR_MAIN,
        layout_notes="Left mini-calendar + calendar list (240px), main area with day/week/month grid view",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#1a73e8", "#ffffff", "#3c4043"],
        behavioral_description="Multiple views: day, week, month. Events shown as colored blocks. Click to create event. Drag to resize/move events. Event popover on click shows details with edit/delete. Color coding by calendar. Mini calendar in sidebar for quick navigation.",
        component_hints=[
            {"name": "CalendarGrid", "props": ["view", "date", "events", "calendars"]},
            {"name": "EventBlock", "props": ["title", "start", "end", "color", "calendar", "is_all_day"]},
            {"name": "EventPopover", "props": ["event", "on_edit", "on_delete"]},
        ],
        accessibility_notes="Calendar grid uses proper table role with date headers. Events have aria-label with full details. Keyboard navigation between days/events. Screen reader announces date on focus.",
        quality_score=8.5,
        tags=["calendar", "scheduling", "drag-drop", "productivity"]
    ),

    # === NOTIFICATION CENTER ===
    DesignPattern(
        id="seed-notifications",
        name="Notification Center",
        source="curated",
        source_url="https://example.com/notifications",
        page_type="Notifications",
        ux_patterns=["Infinite Scroll", "Lazy Loading", "Tab Navigation", "Bulk Actions"],
        ui_elements=["Card", "Avatar", "Badge", "Button", "Tabs", "Divider", "Icon", "Dropdown"],
        industry="SaaS",
        layout_type=LayoutType.SINGLE_COLUMN,
        layout_notes="Single column notification list, max-width 640px, tabs for All/Unread/Mentions",
        platform=Platform.WEB,
        color_mode="light",
        visual_style=["Minimal", "Flat"],
        primary_colors=["#3b82f6", "#ffffff", "#6b7280"],
        behavioral_description="Tabbed view: All, Unread, Mentions. Each notification shows actor avatar, action description, timestamp, and unread indicator. Mark all as read button. Individual mark as read on hover. Click notification navigates to context. Group notifications by date.",
        component_hints=[
            {"name": "NotificationItem", "props": ["actor", "action", "target", "timestamp", "is_read", "type", "link"]},
        ],
        accessibility_notes="Unread status conveyed via aria. Notification actions accessible by keyboard. New notifications announced via aria-live polite. Tab panels properly linked.",
        quality_score=7.5,
        tags=["notifications", "inbox", "activity-feed"]
    ),
]


def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "patterns.json")
    db = DesignDatabase(db_path)

    print(f"Generating {len(SEED_PATTERNS)} seed design patterns...")
    db.add_batch(SEED_PATTERNS)
    print(f"Database now has {db.count()} patterns")

    # Print summary
    page_types = set(p.page_type for p in SEED_PATTERNS)
    industries = set(p.industry for p in SEED_PATTERNS if p.industry)
    print(f"\nPage types covered: {len(page_types)}")
    for pt in sorted(page_types):
        count = sum(1 for p in SEED_PATTERNS if p.page_type == pt)
        print(f"  {pt}: {count}")
    print(f"\nIndustries covered: {', '.join(sorted(industries))}")
    print(f"\nSeed data written to: {db_path}")


if __name__ == "__main__":
    main()
